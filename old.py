import asyncio
import os
import sys
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext, ttk
from playwright.async_api import async_playwright
import re
import json
from datetime import datetime
import threading
import queue
import platform
from curl_helper import APIClient

# 创建API客户端实例
api_client = APIClient()

# 创建消息队列用于线程间通信
message_queue = queue.Queue()

# 抑制MacOS上的IMK警告
if platform.system() == 'Darwin':
    # 尝试重定向stderr来抑制IMK警告
    import io
    import contextlib


    @contextlib.contextmanager
    def suppress_stderr():
        # 保存原始stderr
        original_stderr = sys.stderr
        # 创建一个空的io
        sys.stderr = io.StringIO()
        try:
            yield
        finally:
            # 恢复原始stderr
            sys.stderr = original_stderr
else:
    @contextlib.contextmanager
    def suppress_stderr():
        yield


# 用户配置
class Config:
    def __init__(self):
        self.chrome_path = ""
        self.processed_accounts = []

    def save_to_file(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump({
                "chrome_path": self.chrome_path,
                "processed_accounts": self.processed_accounts
            }, f, ensure_ascii=False)

    def load_from_file(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chrome_path = data.get("chrome_path", "")
                    self.processed_accounts = data.get("processed_accounts", [])
                return True
            return False
        except Exception as e:
            print(f"读取配置文件出错: {e}")
            return False

    def auto_detect_chrome(self):
        """自动检测Chrome浏览器位置"""
        system = platform.system()

        if system == "Darwin":  # macOS
            possible_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
                '/Users/' + os.getlogin() + '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                # homebrew路径
                '/opt/homebrew/bin/chromium',
                # 更多可能的位置
                '/Applications/Chromium.app/Contents/MacOS/Chromium'
            ]
        elif system == "Windows":
            possible_paths = [
                os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                             'Google\\Chrome\\Application\\chrome.exe'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
                             'Google\\Chrome\\Application\\chrome.exe'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google\\Chrome\\Application\\chrome.exe')
            ]
        elif system == "Linux":
            possible_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/snap/bin/chromium'
            ]
        else:
            possible_paths = []

        # 检查路径是否存在
        for path in possible_paths:
            if os.path.exists(path):
                self.chrome_path = path
                self.save_to_file()
                return path

        return None


# 验证码输入弹窗
def get_verification_code(phone_number):
    result = {"code": None}

    # 安全地创建弹窗
    with suppress_stderr():
        # 创建弹窗
        code_window = tk.Toplevel()
        code_window.title("验证码输入")
        code_window.geometry("300x150")
        code_window.resizable(False, False)

        # 居中显示
        screen_width = code_window.winfo_screenwidth()
        screen_height = code_window.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 150) // 2
        code_window.geometry(f"300x150+{x}+{y}")

        # 验证码输入框
        tk.Label(code_window, text=f"请输入手机 {phone_number} 收到的验证码:", pady=10).pack()
        code_var = tk.StringVar()
        entry = tk.Entry(code_window, textvariable=code_var, font=("Arial", 14), width=10, justify="center")
        entry.pack(pady=10)
        entry.focus()

        def on_submit():
            code = code_var.get()
            if len(code) == 6 and code.isdigit():
                result["code"] = code
                code_window.destroy()

        # 自动检测输入长度
        def check_code_length(*args):
            code = code_var.get()
            if len(code) == 6 and code.isdigit():
                on_submit()

        code_var.trace_add("write", check_code_length)

        # 提交按钮
        tk.Button(code_window, text="确定", command=on_submit, width=10).pack(pady=10)

        # 当窗口关闭时的处理
        def on_closing():
            result["code"] = None
            code_window.destroy()

        code_window.protocol("WM_DELETE_WINDOW", on_closing)

        # 等待窗口关闭
        code_window.wait_window()

    return result["code"]


# 发送账号信息到API
def send_account_info(phone, cookie):
    try:
        # 准备要发送的数据
        data = {
            "phone": phone,
            "cookie": cookie,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 调用API发送数据
        response = api_client.account(data)

        if response and response.get("code") == 0:
            message_queue.put(f"账号 {phone} 的信息已成功发送到服务器")
            return True
        else:
            error_msg = response.get("msg", "未知错误") if response else "请求失败"
            message_queue.put(f"账号 {phone} 的信息发送失败: {error_msg}")
            return False
    except Exception as e:
        message_queue.put(f"发送账号信息时出错: {e}")
        return False


async def process_single_account(phone_number, config, playwright):
    message_queue.put(f"开始处理账号: {phone_number}")

    user_info_cookie = None
    user_info_request_found = False

    # 启动浏览器
    browser_type = playwright.chromium
    browser = await browser_type.launch_persistent_context(
        user_data_dir="",  # 空字符串表示使用临时目录
        executable_path=config.chrome_path if config.chrome_path else None,
        headless=False,
        args=["--incognito"]  # 启用无痕模式
    )

    # 创建新页面
    page = await browser.new_page()

    # 设置网络请求监听 - 监听响应
    async def handle_response(response):
        nonlocal user_info_cookie, user_info_request_found
        # 捕获 user/info 请求
        if "uc.e.kuaishou.com/rest/web/user/info" in response.url and not user_info_request_found:
            message_queue.put("\n检测到用户信息请求！")
            message_queue.put(f"响应URL: {response.url}")

            # 从页面获取所有Cookie
            cookies = await page.context.cookies()
            if cookies:
                # 提取所有cookie并格式化为cookie字符串
                cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                user_info_cookie = cookie_string
                message_queue.put(f"获取到Cookie: {user_info_cookie}")
                user_info_request_found = True
                # 发送账号信息到API
                if send_account_info(phone_number, user_info_cookie):
                    message_queue.put(f"账号 {phone_number} 的信息已发送到服务器")
                else:
                    message_queue.put(f"账号 {phone_number} 的信息发送失败")

    # 注册响应监听器
    page.on("response", handle_response)

    # 也要继续监听请求
    async def handle_request(request):
        nonlocal user_info_cookie, user_info_request_found
        # 捕获 user/info 请求
        if "uc.e.kuaishou.com/rest/web/user/info" in request.url and not user_info_request_found:
            message_queue.put("\n检测到用户信息请求！")
            message_queue.put(f"请求URL: {request.url}")

            # 从请求中提取Cookie
            headers = request.headers
            if "cookie" in headers:
                req_cookie = headers["cookie"]
                message_queue.put(f"请求中的Cookie: {req_cookie}")
                user_info_cookie = req_cookie
                user_info_request_found = True
                # 发送账号信息到API
                if send_account_info(phone_number, user_info_cookie):
                    message_queue.put(f"账号 {phone_number} 的信息已发送到服务器")
                else:
                    message_queue.put(f"账号 {phone_number} 的信息发送失败")

    # 注册请求监听器
    page.on("request", handle_request)

    # 导航到快手电商牛平台
    message_queue.put("正在导航到快手电商牛平台...")
    await page.goto("https://niu.e.kuaishou.com/welcome")

    # 等待页面加载完成
    message_queue.put("页面加载完成...")

    # 检测是否有"立即登录"按钮
    message_queue.put("检测是否存在'立即登录'按钮...")
    try:
        # 使用多种选择器尝试定位按钮
        login_button = None

        # 方法1：通过文本内容查找按钮
        if not login_button:
            login_button = await page.wait_for_selector("button:has-text('立即登录')", timeout=5000)

        # 方法2：使用更具体的选择器
        if not login_button:
            login_button = await page.wait_for_selector("button.ant-btn span:has-text('立即登录')", timeout=5000)
            if login_button:
                # 获取父按钮元素
                login_button = await login_button.evaluate("el => el.closest('button')")

        # 方法3：使用XPath
        if not login_button:
            login_button = await page.wait_for_selector(
                "//button[contains(@class, 'ant-btn')][.//span[text()='立即登录']]", timeout=5000)

        if login_button:
            message_queue.put("找到'立即登录'按钮，点击中...")
            await login_button.click()
            message_queue.put("已点击'立即登录'按钮")

            # 等待登录页面加载
            await page.wait_for_timeout(2000)

            # 点击"验证码登录"选项卡
            message_queue.put("查找'验证码登录'选项卡...")
            code_login_tab = await page.wait_for_selector("div.tab.svelte-rlva34:has-text('验证码登录')", timeout=5000)
            if code_login_tab:
                message_queue.put("找到'验证码登录'选项卡，点击中...")
                await code_login_tab.click()
                message_queue.put("已切换到验证码登录模式")

                # 输入手机号
                message_queue.put(f"正在输入手机号: {phone_number}")
                phone_input = await page.wait_for_selector("input.component-input-real-value[placeholder='手机号']",
                                                           timeout=5000)
                await phone_input.fill(phone_number)
                message_queue.put(f"已输入手机号: {phone_number}")

                # 点击发送验证码
                send_code_button = await page.wait_for_selector("span.svelte-9i4e5y:has-text('发送手机验证码')",
                                                                timeout=5000)
                await send_code_button.click()
                message_queue.put("已点击发送验证码按钮")

                # 弹窗获取验证码
                message_queue.put("等待用户输入验证码...")
                verification_code = get_verification_code(phone_number)

                if verification_code:
                    message_queue.put(f"获取到验证码: {verification_code}")

                    # 输入验证码
                    code_input = await page.wait_for_selector(
                        "input.component-input-real-value[placeholder='请输入验证码']", timeout=5000)
                    await code_input.fill(verification_code)

                    # 勾选复选框
                    checkbox = await page.wait_for_selector("input.component-checkbox-input.svelte-1x8ouvx",
                                                            timeout=5000)
                    if not await checkbox.is_checked():
                        await checkbox.check()
                        message_queue.put("已勾选同意条款复选框")

                    # 点击登录按钮
                    submit_button = await page.wait_for_selector(
                        "button.component-button.submit.component-button-primary", timeout=5000)
                    await submit_button.click()
                    message_queue.put("已点击登录按钮")

                    # 等待登录成功，检测登录弹窗是否消失
                    message_queue.put("等待登录完成...")
                    try:
                        # 等待登录弹窗消失
                        await page.wait_for_selector("div.tab.svelte-rlva34", state="hidden", timeout=30000)
                        message_queue.put("登录弹窗已消失，登录成功！")

                        # 登录成功后尝试访问用户信息
                        if not user_info_request_found:
                            message_queue.put("尝试加载用户信息页面...")
                            # 主动访问用户信息页面
                            await page.goto("https://uc.e.kuaishou.com/rest/web/user/info", wait_until="networkidle")
                            await page.wait_for_timeout(2000)

                        # 等待获取Cookie
                        max_wait = 30  # 最多等待30秒
                        for i in range(max_wait):
                            if user_info_request_found:
                                break
                            await page.wait_for_timeout(1000)

                        if user_info_request_found:
                            message_queue.put(f"账号 {phone_number} 登录成功！Cookie已获取")
                            # 添加到已处理列表
                            if phone_number not in config.processed_accounts:
                                config.processed_accounts.append(phone_number)
                                config.save_to_file()
                        else:
                            message_queue.put(f"账号 {phone_number} 登录成功，但未能获取Cookie")
                    except Exception as e:
                        message_queue.put(f"等待登录完成时出错: {e}")
                else:
                    message_queue.put("未获取到验证码，取消登录")
            else:
                message_queue.put("未找到'验证码登录'选项卡")
        else:
            message_queue.put("未找到'立即登录'按钮")
    except Exception as e:
        message_queue.put(f"登录操作出错: {e}")

    # 关闭浏览器
    await browser.close()
    return user_info_request_found


# 主应用类
class Application(tk.Tk):
    def __init__(self):
        # 在创建Tk窗口前抑制警告
        with suppress_stderr():
            super().__init__()

        self.title("快手账号批量登录工具")
        self.geometry("800x600")
        self.config = Config()
        self.config.load_from_file()

        # 自动检测Chrome路径（如果配置中没有）
        if not self.config.chrome_path or not os.path.exists(self.config.chrome_path):
            detected_path = self.config.auto_detect_chrome()
            if detected_path:
                print(f"自动检测到Chrome路径: {detected_path}")

        self.create_widgets()
        self.processing = False

        # 确保存在必要的目录
        os.makedirs("accounts", exist_ok=True)

        # 启动消息处理线程
        threading.Thread(target=self.process_messages, daemon=True).start()

    def create_widgets(self):
        # 在创建组件时抑制警告
        with suppress_stderr():
            # 创建主框架
            main_frame = ttk.Frame(self)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 创建左右分栏
            left_frame = ttk.Frame(main_frame)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            right_frame = ttk.Frame(main_frame)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

            # 左侧：设置和账号输入
            settings_frame = ttk.LabelFrame(left_frame, text="设置")
            settings_frame.pack(fill=tk.X, pady=(0, 10))

            # Chrome路径设置
            chrome_frame = ttk.Frame(settings_frame)
            chrome_frame.pack(fill=tk.X, padx=5, pady=5)

            ttk.Label(chrome_frame, text="Chrome路径:").pack(side=tk.LEFT)
            self.chrome_path_var = tk.StringVar(value=self.config.chrome_path)
            chrome_entry = ttk.Entry(chrome_frame, textvariable=self.chrome_path_var)
            chrome_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
            ttk.Button(chrome_frame, text="选择", command=self.select_chrome_path).pack(side=tk.RIGHT)

            # 账号输入区域
            accounts_frame = ttk.LabelFrame(left_frame, text="账号管理")
            accounts_frame.pack(fill=tk.BOTH, expand=True)

            # 账号输入
            ttk.Label(accounts_frame, text="输入账号（每行一个手机号）:").pack(anchor=tk.W, padx=5, pady=(5, 0))

            # 账号输入框
            self.accounts_text = scrolledtext.ScrolledText(accounts_frame, height=10)
            self.accounts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # 账号操作按钮
            buttons_frame = ttk.Frame(accounts_frame)
            buttons_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

            ttk.Button(buttons_frame, text="从文件导入", command=self.import_accounts).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="清空", command=self.clear_accounts).pack(side=tk.LEFT)

            # 操作按钮
            action_frame = ttk.Frame(left_frame)
            action_frame.pack(fill=tk.X, pady=(10, 0))

            self.start_button = ttk.Button(action_frame, text="开始处理", command=self.start_processing)
            self.start_button.pack(fill=tk.X)

            # 右侧：日志输出
            log_frame = ttk.LabelFrame(right_frame, text="处理日志")
            log_frame.pack(fill=tk.BOTH, expand=True)

            self.log_text = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED)
            self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # 状态栏
            self.status_var = tk.StringVar(value="就绪")
            status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def select_chrome_path(self):
        with suppress_stderr():
            chrome_dir = filedialog.askdirectory(title="请选择Chrome浏览器所在的文件夹")

        if chrome_dir:
            # 在所选目录中查找Chrome可执行文件
            possible_names = []

            # 根据操作系统确定可能的文件名
            if platform.system() == "Darwin":  # macOS
                possible_names = ["Google Chrome", "Google Chrome Canary", "Chromium"]
            elif platform.system() == "Windows":
                possible_names = ["chrome.exe", "chromium.exe"]
            else:  # Linux
                possible_names = ["google-chrome", "chromium-browser", "chromium"]

            found = False
            for name in possible_names:
                path = os.path.join(chrome_dir, name)
                if os.path.exists(path):
                    self.chrome_path_var.set(path)
                    self.config.chrome_path = path
                    self.config.save_to_file()
                    found = True
                    break

            # 如果在当前目录没找到，macOS还需要检查特殊路径
            if not found and platform.system() == "Darwin":
                for name in ["Google Chrome.app", "Google Chrome Canary.app", "Chromium.app"]:
                    app_path = os.path.join(chrome_dir, name)
                    if os.path.exists(app_path):
                        # macOS应用程序中的可执行文件在Contents/MacOS目录
                        exec_path = os.path.join(app_path, "Contents", "MacOS")
                        if os.path.exists(exec_path):
                            # 找到可执行文件
                            for exec_name in os.listdir(exec_path):
                                if "Chrome" in exec_name or "Chromium" in exec_name:
                                    full_path = os.path.join(exec_path, exec_name)
                                    self.chrome_path_var.set(full_path)
                                    self.config.chrome_path = full_path
                                    self.config.save_to_file()
                                    found = True
                                    break
                        if found:
                            break

            # 如果没找到，尝试在子目录中查找
            if not found:
                for root, dirs, files in os.walk(chrome_dir):
                    for file in files:
                        file_lower = file.lower()
                        if (platform.system() == "Windows" and file_lower == "chrome.exe") or \
                                (platform.system() != "Windows" and (
                                        "chrome" in file_lower or "chromium" in file_lower)):
                            path = os.path.join(root, file)
                            self.chrome_path_var.set(path)
                            self.config.chrome_path = path
                            self.config.save_to_file()
                            found = True
                            break
                    if found:
                        break

            if found:
                self.log(f"已选择Chrome浏览器: {self.config.chrome_path}")
            else:
                messagebox.showwarning("警告", "在选定目录中未找到Chrome浏览器")

    def import_accounts(self):
        with suppress_stderr():
            file_path = filedialog.askopenfilename(title="选择账号文件", filetypes=[("文本文件", "*.txt")])

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    accounts = [line.strip() for line in f if line.strip()]
                    self.accounts_text.delete(1.0, tk.END)
                    self.accounts_text.insert(tk.END, "\n".join(accounts))
                self.log(f"从文件导入了 {len(accounts)} 个账号")
            except Exception as e:
                messagebox.showerror("错误", f"导入账号失败: {e}")

    def clear_accounts(self):
        self.accounts_text.delete(1.0, tk.END)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def process_messages(self):
        """处理后台线程发送的消息"""
        while True:
            try:
                message = message_queue.get(timeout=0.1)
                self.log(message)
            except queue.Empty:
                if not self.processing:
                    # 如果没有消息且未在处理中，降低CPU使用率
                    self.after(100, lambda: None)
                continue

    def start_processing(self):
        if self.processing:
            messagebox.showinfo("提示", "已有账号正在处理中")
            return

        # 获取账号列表
        accounts_text = self.accounts_text.get(1.0, tk.END).strip()
        if not accounts_text:
            messagebox.showinfo("提示", "请先输入或导入账号")
            return

        accounts = [line.strip() for line in accounts_text.split("\n") if line.strip()]
        if not accounts:
            messagebox.showinfo("提示", "没有有效账号")
            return

        # 确保Chrome路径有效
        if not self.config.chrome_path or not os.path.exists(self.config.chrome_path):
            # 尝试自动检测
            detected_path = self.config.auto_detect_chrome()
            if not detected_path:
                result = messagebox.askyesno("提示", "未找到Chrome浏览器，是否选择Chrome路径？")
                if result:
                    self.select_chrome_path()
                    if not self.config.chrome_path or not os.path.exists(self.config.chrome_path):
                        messagebox.showinfo("提示", "未选择有效的Chrome路径，将使用Playwright内置浏览器")
                else:
                    self.log("将使用Playwright内置浏览器")
            else:
                self.chrome_path_var.set(detected_path)
                self.log(f"自动检测到Chrome路径: {detected_path}")

        # 过滤已处理的账号
        pending_accounts = [acc for acc in accounts if acc not in self.config.processed_accounts]
        if not pending_accounts:
            messagebox.showinfo("提示", "所有账号都已处理过")
            return

        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.status_var.set(f"处理中... (0/{len(pending_accounts)})")

        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # 启动处理线程
        threading.Thread(target=self.process_accounts, args=(pending_accounts,), daemon=True).start()

    def process_accounts(self, accounts):
        """处理账号的后台线程"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.log(f"开始处理 {len(accounts)} 个账号")

        async def run_processing():
            async with async_playwright() as playwright:
                for i, phone in enumerate(accounts):
                    # 更新状态栏
                    self.status_var.set(f"处理中... ({i + 1}/{len(accounts)})")

                    # 处理单个账号
                    await process_single_account(phone, self.config, playwright)

                    # 短暂暂停，避免过快处理下一个账号
                    await asyncio.sleep(2)

        try:
            loop.run_until_complete(run_processing())
        except Exception as e:
            message_queue.put(f"处理过程出错: {e}")
        finally:
            # 处理完成后恢复界面状态
            self.after(0, self.processing_completed, len(accounts))

    def processing_completed(self, count):
        self.processing = False
        self.start_button.config(state=tk.NORMAL)
        self.status_var.set("处理完成")
        messagebox.showinfo("处理完成", f"所有账号处理完成！\n共处理 {count} 个账号")


# 主程序入口
if __name__ == "__main__":
    # 设置默认错误处理
    if platform.system() == 'Darwin':
        # 重定向stderr以抑制macOS的IMK警告
        original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')

    try:
        app = Application()
        app.mainloop()
    finally:
        # 恢复stderr
        if platform.system() == 'Darwin':
            sys.stderr.close()
            sys.stderr = original_stderr 