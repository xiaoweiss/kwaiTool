#!/usr/bin/env python3
"""
快手账号管理工具 - 主程序
"""

import os
import sys
import json
import time
import platform
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import traceback
import requests
from playwright.sync_api import sync_playwright
from curl_helper import CurlHelper

# 创建API客户端实例
api_client = CurlHelper()

# 全局变量
ACCOUNTS_DIR = "accounts"
PROCESSED_FILE = "processed_accounts.json"
running = False
stop_event = threading.Event()
log_queue = queue.Queue()

# 确保必要的目录存在
if not os.path.exists(ACCOUNTS_DIR):
    os.makedirs(ACCOUNTS_DIR)

# 加载已处理的账号
processed_accounts = {}
if os.path.exists(PROCESSED_FILE):
    try:
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            processed_accounts = json.load(f)
    except Exception as e:
        print(f"加载已处理账号失败: {e}")


class KwaiTool:
    def __init__(self, root):
        self.root = root
        self.root.title("快手账号管理工具")
        self.root.geometry("800x600")

        # 设置窗口图标
        if platform.system() == "Windows" and os.path.exists("app_icon.ico"):
            self.root.iconbitmap("app_icon.ico")

        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建菜单栏
        self.create_menu()

        # 创建工具栏
        self.create_toolbar()

        # 创建主界面
        self.create_main_ui()

        # 创建状态栏
        self.create_statusbar()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 启动日志更新线程
        self.log_update_thread = threading.Thread(target=self.update_log, daemon=True)
        self.log_update_thread.start()

        # 显示欢迎信息
        self.log("快手账号管理工具已启动")
        self.log(f"当前系统: {platform.system()} {platform.version()}")
        self.log(f"Python版本: {platform.python_version()}")
        self.log(f"账号目录: {os.path.abspath(ACCOUNTS_DIR)}")
        self.update_status("就绪")

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="导入账号", command=self.import_accounts)
        file_menu.add_command(label="添加账号", command=self.add_single_account)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 操作菜单
        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="开始处理", command=self.start_processing)
        action_menu.add_command(label="停止处理", command=self.stop_processing)
        action_menu.add_separator()
        action_menu.add_command(label="清除已处理记录", command=self.clear_processed)
        menubar.add_cascade(label="操作", menu=action_menu)

        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="浏览器设置", command=self.browser_settings)
        menubar.add_cascade(label="设置", menu=settings_menu)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="导入账号", command=self.import_accounts).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="添加账号", command=self.add_single_account).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="开始处理", command=self.start_processing).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="停止处理", command=self.stop_processing).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除账号", command=self.remove_account).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清除记录", command=self.clear_processed).pack(side=tk.LEFT, padx=2)

    def create_main_ui(self):
        """创建主界面"""
        # 创建上下分割的面板
        paned = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 上部分：账号列表
        accounts_frame = ttk.LabelFrame(paned, text="账号列表")
        paned.add(accounts_frame, weight=1)

        # 创建账号列表
        columns = ("账号", "密码", "状态", "更新时间")
        self.accounts_tree = ttk.Treeview(accounts_frame, columns=columns, show="headings")

        # 设置列标题
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=100)

        # 添加滚动条
        accounts_scrollbar = ttk.Scrollbar(accounts_frame, orient=tk.VERTICAL, command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=accounts_scrollbar.set)

        # 创建右键菜单
        self.context_menu = tk.Menu(self.accounts_tree, tearoff=0)
        self.context_menu.add_command(label="删除账号", command=self.remove_account)

        # 绑定右键点击事件
        self.accounts_tree.bind("<Button-3>", self.show_context_menu)

        # 布局
        accounts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.accounts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 下部分：日志区域
        log_frame = ttk.LabelFrame(paned, text="日志")
        paned.add(log_frame, weight=1)

        # 创建日志文本区域
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def create_statusbar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)

    def log(self, message):
        """添加日志消息到队列"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_queue.put(f"[{timestamp}] {message}")

    def update_log(self):
        """从队列更新日志显示"""
        while True:
            try:
                # 检查队列中是否有新日志
                try:
                    message = log_queue.get(block=False)
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, message + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)
                    log_queue.task_done()
                except queue.Empty:
                    pass

                time.sleep(0.1)
            except Exception as e:
                print(f"日志更新线程异常: {e}")

    def load_accounts(self):
        """加载账号列表"""
        # 清空现有列表
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)

        # 扫描账号目录
        if not os.path.exists(ACCOUNTS_DIR):
            os.makedirs(ACCOUNTS_DIR)
            self.log(f"创建账号目录: {ACCOUNTS_DIR}")
            return

        try:
            account_files = [f for f in os.listdir(ACCOUNTS_DIR) if f.endswith(".txt")]

            for file in account_files:
                try:
                    with open(os.path.join(ACCOUNTS_DIR, file), "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if lines:
                            username = lines[0].strip()

                            # 检查是否已处理
                            status = "未处理"
                            update_time = ""
                            if username in processed_accounts:
                                status = "已处理"
                                update_time = processed_accounts[username].get("time", "")

                            self.accounts_tree.insert("", tk.END, values=(username, "", status, update_time))
                except Exception as e:
                    self.log(f"加载账号文件 {file} 失败: {e}")

            self.log(f"已加载 {len(account_files)} 个账号文件")
        except Exception as e:
            self.log(f"加载账号列表失败: {e}")

    def import_accounts(self):
        """导入账号"""
        file_path = filedialog.askopenfilename(
            title="选择账号文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                # 每行一个账号
                accounts = [line.strip() for line in lines if line.strip()]
                imported = 0

                for account in accounts:
                    # 创建账号文件
                    account_file = os.path.join(ACCOUNTS_DIR, f"{account}.txt")
                    with open(account_file, "w", encoding="utf-8") as af:
                        af.write(account)
                    imported += 1

                self.log(f"成功导入 {imported} 个账号")
                self.load_accounts()
        except Exception as e:
            self.log(f"导入账号失败: {e}")
            messagebox.showerror("错误", f"导入账号失败: {e}")

    def start_processing(self):
        """开始处理账号"""
        global running

        if running:
            messagebox.showinfo("提示", "已有处理任务正在运行")
            return

        # 获取未处理的账号
        accounts_to_process = []
        for item in self.accounts_tree.get_children():
            values = self.accounts_tree.item(item, "values")
            if values[2] != "已处理":
                accounts_to_process.append((values[0], values[1]))

        if not accounts_to_process:
            messagebox.showinfo("提示", "没有需要处理的账号")
            return

        # 重置停止事件
        stop_event.clear()

        # 启动处理线程
        running = True
        self.update_status("正在处理账号...")
        processing_thread = threading.Thread(
            target=self.process_accounts,
            args=(accounts_to_process,),
            daemon=True
        )
        processing_thread.start()

    def process_accounts(self, accounts):
        """处理账号的线程函数"""
        global running

        try:
            total_accounts = len(accounts)
            self.log(f"开始处理 {total_accounts} 个账号")
            self.update_status(f"处理中... (0/{total_accounts})")

            for i, (username, _) in enumerate(accounts):
                if stop_event.is_set():
                    self.log("处理已停止")
                    break

                # 更新状态栏
                self.update_status(f"处理中... ({i + 1}/{total_accounts})")
                self.log(f"正在处理账号 ({i + 1}/{total_accounts}): {username}")

                try:
                    # 使用Playwright处理账号
                    result = self.process_account(username)

                    if result:
                        # 更新已处理记录
                        processed_accounts[username] = {
                            "time": time.strftime("%Y-%m-%d %H:%M:%S")
                        }

                        # 保存已处理记录
                        with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
                            json.dump(processed_accounts, f, indent=2, ensure_ascii=False)

                        self.log(f"账号 {username} 处理成功")
                    else:
                        self.log(f"账号 {username} 处理失败")

                except Exception as e:
                    self.log(f"处理账号 {username} 时出错: {e}")
                    traceback.print_exc()

            self.log("账号处理完成")
            self.update_status("处理完成")
            messagebox.showinfo("处理完成", f"所有账号处理完成！\n共处理 {total_accounts} 个账号")
        except Exception as e:
            self.log(f"处理过程出错: {e}")
            traceback.print_exc()
        finally:
            running = False
            self.update_status("就绪")

            # 刷新账号列表
            self.root.after(0, self.load_accounts)

    def process_account(self, username):
        """严格按照指定流程处理单个账号"""
        try:
            # 读取浏览器配置
            browser_path = None
            if os.path.exists("config.json"):
                try:
                    with open("config.json", "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        browser_path = config_data.get("chrome_path")
                except Exception as e:
                    self.log(f"加载浏览器配置失败: {e}")

            if not browser_path or not os.path.exists(browser_path):
                messagebox.showwarning("警告", "请先在设置中配置正确的浏览器路径")
                return False

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    executable_path=browser_path
                )
                context = browser.new_context()
                page = context.new_page()
                result = False
                try:
                    # 1. 打开快手牛平台
                    page.goto("https://niu.e.kuaishou.com/welcome")
                    self.log("已打开快手牛平台")
                    page.wait_for_load_state("networkidle")

                    # 2. 检测并点击"立即登录"按钮
                    self.log("检测是否存在'立即登录'按钮...")
                    login_button = None
                    try:
                        login_button = page.wait_for_selector("button:has-text('立即登录')", timeout=5000)
                    except:
                        pass
                    if not login_button:
                        try:
                            login_button_span = page.wait_for_selector("button.ant-btn span:has-text('立即登录')", timeout=5000)
                            if login_button_span:
                                login_button = page.evaluate("el => el.closest('button')", login_button_span)
                        except:
                            pass
                    if not login_button:
                        try:
                            login_button = page.wait_for_selector("//button[contains(@class, 'ant-btn')][.//span[text()='立即登录']]", timeout=5000)
                        except:
                            pass
                    if not login_button:
                        self.log("未找到'立即登录'按钮")
                        return False
                    self.log("找到'立即登录'按钮，点击中...")
                    login_button.click()
                    self.log("已点击'立即登录'按钮")
                    page.wait_for_timeout(2000)

                    # 3. 切换到验证码登录
                    self.log("查找'验证码登录'选项卡...")
                    try:
                        code_login_tab = page.wait_for_selector("div.tab.svelte-rlva34:has-text('验证码登录')", timeout=5000)
                        if code_login_tab:
                            self.log("找到'验证码登录'选项卡，点击中...")
                            code_login_tab.click()
                            self.log("已切换到验证码登录模式")
                        else:
                            self.log("未找到'验证码登录'选项卡")
                            return False
                    except Exception as e:
                        self.log(f"查找验证码登录选项卡出错: {e}")
                        return False

                    # 4. 输入手机号
                    self.log(f"正在输入手机号: {username}")
                    phone_input = page.wait_for_selector("input.component-input-real-value[placeholder='手机号']", timeout=5000)
                    phone_input.fill(username)
                    self.log(f"已输入手机号: {username}")

                    # 5. 发送验证码
                    send_code_button = page.wait_for_selector("span.svelte-9i4e5y:has-text('发送手机验证码')", timeout=5000)
                    send_code_button.click()
                    self.log("已点击发送验证码按钮")
                    self.log("等待用户输入验证码...")

                    # 6. 弹窗输入验证码
                    code_dialog = tk.Toplevel(self.root)
                    code_dialog.title("输入验证码")
                    code_dialog.geometry("300x150")
                    code_dialog.grab_set()
                    ttk.Label(code_dialog, text=f"请输入账号 {username} 收到的验证码:").pack(pady=(20, 10))
                    code_var = tk.StringVar()
                    code_entry = ttk.Entry(code_dialog, textvariable=code_var, width=10, justify="center")
                    code_entry.pack(pady=(0, 20))
                    code_entry.focus()
                    code_result = [None]
                    def on_submit():
                        code = code_var.get().strip()
                        if len(code) != 6 or not code.isdigit():
                            messagebox.showwarning("警告", "请输入6位数字验证码")
                            return
                        code_result[0] = code
                        code_dialog.destroy()
                    submit_button = ttk.Button(code_dialog, text="确定", command=on_submit)
                    submit_button.pack()
                    code_dialog.bind("<Return>", lambda event: on_submit())
                    self.root.wait_window(code_dialog)
                    verification_code = code_result[0]
                    if not verification_code:
                        self.log("未获取到验证码，取消登录")
                        return False
                    self.log(f"获取到验证码: {verification_code}")

                    # 7. 输入验证码并登录
                    code_input = page.wait_for_selector("input.component-input-real-value[placeholder='请输入验证码']", timeout=5000)
                    code_input.fill(verification_code)
                    checkbox = page.wait_for_selector("input.component-checkbox-input.svelte-1x8ouvx", timeout=5000)
                    if not checkbox.is_checked():
                        checkbox.check()
                        self.log("已勾选同意条款复选框")
                    submit_button = page.wait_for_selector("button.component-button.submit.component-button-primary", timeout=5000)
                    submit_button.click()
                    self.log("已点击登录按钮")
                    self.log("等待登录完成...")

                    # 登录成功，获取cookie
                    self.log("登录弹窗已消失，登录成功！")
                    self.log("等待页面跳转和cookie下发...")
                    page.wait_for_timeout(3000)  # 等待3秒
                    # 再获取cookie
                    cookies = context.cookies()
                    if not cookies:
                        self.log("无法获取Cookie，登录可能失败")
                        return False
                    cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                    self.log(f"登录后获取到的Cookie: {cookie_string}")

                    # 调试：打印 CurlHelper 加载到的 endpoints
                    self.log(f"当前 CurlHelper endpoints: {api_client.endpoints}")
                    if "info" not in api_client.endpoints:
                        self.log("endpoints 中未找到 'info' key，请检查 curl_config.json 配置！")
                    else:
                        self.log(f"endpoints['info']: {api_client.endpoints['info']}")
                    info_url = api_client.get_endpoint_url("info")
                    body = {
                        "cookies": cookie_string
                    }
                    self.log(f"实际请求的 info_url: {info_url}")
                    try:
                        resp = requests.post(info_url, json=body)
                        self.log(f"info接口响应状态码: {resp.status_code}")
                        self.log(f"info接口响应内容: {resp.text}")
                        resp_json = resp.json()
                    except Exception as e:
                        self.log(f"请求或解析 info 响应出错: {e}")
                        return False
                    if resp_json.get("code") != 1:
                        self.log(f"info接口返回失败: {resp_json}")
                        return False
                    data = resp_json.get("data", {})
                    account_infos = data.get('accountInfos', [])
                    if not isinstance(account_infos, list):
                        account_infos = []
                    self.log(f"accountInfos长度: {len(account_infos)}")
                    self.log(f"accountInfos内容: {account_infos}")
                    if len(account_infos) == 0:
                        self.log("检测到单一账号，直接上传cookie")
                        self.send_account_info(username, cookie_string)
                        result = True
                    else:
                        self.log(f"检测到多个账号，数量: {len(account_infos)}，等待用户选择登录账户")
                        select_dialog = tk.Toplevel(self.root)
                        select_dialog.title("选择登录账号")
                        select_dialog.geometry("400x300")
                        select_dialog.grab_set()
                        ttk.Label(select_dialog, text="请选择要登录的账号:").pack(pady=(20, 10))
                        account_frame = ttk.Frame(select_dialog)
                        account_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
                        account_listbox = tk.Listbox(account_frame, width=50, height=10)
                        account_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                        scrollbar = ttk.Scrollbar(account_frame, orient="vertical", command=account_listbox.yview)
                        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                        account_listbox.config(yscrollcommand=scrollbar.set)
                        account_map = {}
                        for account in account_infos:
                            account_name = account.get('accountName', '未命名账号')
                            account_id = account.get('accountId', 0)
                            account_type = account.get('accountTypeDescription', '')
                            display_text = f"{account_name} ({account_type})({account_id})"
                            account_listbox.insert(tk.END, display_text)
                            account_map[display_text] = account_id
                        if account_listbox.size() > 0:
                            account_listbox.select_set(0)
                        selected_result = [None]
                        def on_select(event=None):
                            selected_indices = account_listbox.curselection()
                            if not selected_indices:
                                messagebox.showwarning("警告", "请选择一个账号")
                                return
                            selected_item = account_listbox.get(selected_indices[0])
                            selected_id = account_map.get(selected_item)
                            if selected_id:
                                selected_result[0] = selected_id
                                select_dialog.destroy()
                            else:
                                messagebox.showwarning("警告", "无法获取所选账号ID")
                        ttk.Button(select_dialog, text="确定", command=on_select).pack(pady=10)
                        account_listbox.bind('<Double-1>', on_select)
                        self.root.wait_window(select_dialog)
                        if not selected_result[0]:
                            self.log("用户未选择账号，处理中止")
                            return False
                        selected_account_id = selected_result[0]
                        self.log(f"用户选择了账号ID: {selected_account_id}")
                        # 6. 跳转至对应账户页
                        account_url = f"https://niu.e.kuaishou.com/home?__accountId__={selected_account_id}&homeType=new"
                        self.log(f"跳转至对应账户页: {account_url}")
                        page.goto(account_url, wait_until="networkidle")
                        page.wait_for_timeout(2000)
                        # 7. 获取新页面cookie
                        cookies = context.cookies()
                        if not cookies:
                            self.log("跳转后未获取到Cookie")
                            return False
                        new_cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                        self.log(f"跳转后获取新页面Cookie: {new_cookie_string}")
                        # 8. 上传服务器(cookie+account_id+account)
                        self.send_account_info(username, new_cookie_string, selected_account_id)
                        result = True
                finally:
                    try:
                        browser.close()
                        self.log("浏览器已关闭")
                    except Exception as e:
                        self.log(f"关闭浏览器时出错: {e}")
                return result
        except Exception as e:
            self.log(f"处理过程出错: {e}")
            traceback.print_exc()
            return False

    def send_account_info(self, phone, cookie, account_id=None):
        """发送账号信息到API"""
        try:
            # 准备要发送的数据
            data = {
                "phone": phone,
                "cookie": cookie,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # 如果有account_id，添加到数据中
            if account_id:
                data["account_id"] = account_id
                self.log(f"将同时上传account_id: {account_id}")

            # 获取并打印API端点地址
            endpoint_url = api_client.get_endpoint_url("account")
            self.log(f"正在发送数据到API地址: {endpoint_url}")

            # 调用API发送数据
            result = api_client.upload_cookies(phone, cookie, account_id)

            if result and "error" not in result:
                self.log(f"账号 {phone} 的信息已成功发送到服务器")
                return True
            else:
                error_msg = result.get("error", "未知错误") if result else "请求失败"
                self.log(f"账号 {phone} 的信息发送失败: {error_msg}")
                return False
        except Exception as e:
            self.log(f"发送账号信息时出错: {e}")
            traceback.print_exc()
            return False

    def stop_processing(self):
        """停止处理账号"""
        if not running:
            messagebox.showinfo("提示", "没有正在运行的处理任务")
            return

        stop_event.set()
        self.log("正在停止处理...")

    def clear_processed(self):
        """清除已处理记录"""
        if messagebox.askyesno("确认", "确定要清除所有已处理的记录吗？\n这将允许重新处理所有账号。"):
            global processed_accounts
            processed_accounts = {}

            # 保存空的已处理记录
            with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
                json.dump(processed_accounts, f)

            self.log("已清除所有处理记录")
            self.load_accounts()

    def browser_settings(self):
        """浏览器设置"""
        # 创建配置窗口
        browser_window = tk.Toplevel(self.root)
        browser_window.title("浏览器设置")
        browser_window.geometry("600x150")
        browser_window.grab_set()  # 模态窗口

        # 创建表单
        form_frame = ttk.Frame(browser_window, padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 浏览器路径
        ttk.Label(form_frame, text="浏览器路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        browser_path_var = tk.StringVar()

        # 从配置文件中读取浏览器路径
        browser_config = {}
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    browser_config = json.load(f)
                    if "chrome_path" in browser_config:
                        browser_path_var.set(browser_config["chrome_path"])
            except Exception as e:
                self.log(f"加载浏览器配置失败: {e}")

        browser_entry = ttk.Entry(form_frame, textvariable=browser_path_var, width=50)
        browser_entry.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5)

        def browse_browser():
            path = filedialog.askopenfilename(
                title="选择浏览器可执行文件",
                filetypes=[
                    ("浏览器可执行文件", "*.exe") if platform.system() == "Windows"
                    else ("所有文件", "*.*")
                ]
            )
            if path:
                browser_path_var.set(path)

        browse_button = ttk.Button(form_frame, text="浏览...", command=browse_browser)
        browse_button.grid(row=0, column=2, padx=5, pady=5)

        # 保存按钮
        def save_browser_config():
            browser_path = browser_path_var.get().strip()

            if not browser_path:
                messagebox.showwarning("警告", "请选择浏览器路径")
                return

            if not os.path.exists(browser_path):
                if not messagebox.askyesno("警告", "指定的浏览器路径不存在，是否继续保存？"):
                    return

                # 保存到配置文件
            if os.path.exists("config.json"):
                try:
                    with open("config.json", "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                except Exception:
                    config_data = {}
            else:
                config_data = {}

            config_data["chrome_path"] = browser_path

            try:
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

                self.log("浏览器配置已更新")
                messagebox.showinfo("成功", "浏览器配置已保存")
                browser_window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {e}")

        button_frame = ttk.Frame(browser_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="保存", command=save_browser_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=browser_window.destroy).pack(side=tk.RIGHT, padx=5)

    def show_help(self):
        """显示使用说明"""
        help_text = """
使用说明：

1. 导入账号：
   - 点击"文件"→"导入账号"或工具栏上的"导入账号"按钮
   - 选择包含账号信息的文本文件（每行一个账号）

2. 处理账号：
   - 先在设置中配置浏览器路径
   - 点击"操作"→"开始处理"或工具栏上的"开始处理"按钮
   - 程序将自动打开浏览器，输入账号，等待验证码
   - 程序会弹出窗口让您输入验证码，登录成功后自动获取Cookie信息

3. 清除已处理记录：
   - 点击"操作"→"清除已处理记录"或工具栏上的"清除记录"按钮
   - 这将允许重新处理所有账号

4. 浏览器设置：
   - 点击"设置"→"浏览器设置"
   - 选择Chrome浏览器的可执行文件路径
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("600x400")

        help_text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)

    def show_about(self):
        """显示关于信息"""
        about_text = """
快手账号管理工具

版本: 2.0.0
作者: Ethan

本工具用于批量登录快手牛平台。
        """

        messagebox.showinfo("关于", about_text)

    def on_closing(self):
        """关闭窗口时的处理"""
        if running:
            if not messagebox.askyesno("确认", "有任务正在运行，确定要退出吗？"):
                return
            stop_event.set()

        self.root.destroy()

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 先选中点击的项
        item = self.accounts_tree.identify_row(event.y)
        if item:
            self.accounts_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def remove_account(self):
        """从账号列表中删除选中的账号"""
        selected_item = self.accounts_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选择要删除的账号")
            return
        # 获取选中的账号信息
        values = self.accounts_tree.item(selected_item[0], "values")
        username = values[0]
        # 确认是否删除
        if messagebox.askyesno("确认删除", f"确定要从处理列表中移除账号 {username} 吗？"):
            try:
                # 从TreeView中删除
                self.accounts_tree.delete(selected_item[0])
                # 删除账号文件
                account_file = os.path.join(ACCOUNTS_DIR, f"{username}.txt")
                if os.path.exists(account_file):
                    os.remove(account_file)
                self.log(f"已从处理列表中移除账号: {username}")
            except Exception as e:
                self.log(f"删除账号失败: {e}")
                messagebox.showerror("错误", f"删除账号失败: {e}")

    def add_single_account(self):
        """添加单个账号"""
        # 创建对话框
        add_dialog = tk.Toplevel(self.root)
        add_dialog.title("添加账号")
        add_dialog.geometry("350x150")
        add_dialog.grab_set()  # 模态窗口

        # 创建表单
        form_frame = ttk.Frame(add_dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 账号输入框
        ttk.Label(form_frame, text="账号:").grid(row=0, column=0, sticky=tk.W, pady=10)
        account_var = tk.StringVar()
        account_entry = ttk.Entry(form_frame, textvariable=account_var, width=30)
        account_entry.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=10)
        account_entry.focus()  # 设置焦点

        # 确定和取消按钮
        button_frame = ttk.Frame(add_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        def on_submit():
            account = account_var.get().strip()
            if not account:
                messagebox.showwarning("警告", "请输入账号")
                return

            try:
                # 创建账号文件
                account_file = os.path.join(ACCOUNTS_DIR, f"{account}.txt")
                with open(account_file, "w", encoding="utf-8") as f:
                    f.write(account)

                self.log(f"成功添加账号: {account}")
                self.load_accounts()  # 刷新账号列表
                add_dialog.destroy()
            except Exception as e:
                self.log(f"添加账号失败: {e}")
                messagebox.showerror("错误", f"添加账号失败: {e}")

        ttk.Button(button_frame, text="确定", command=on_submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=add_dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # 绑定回车键
        add_dialog.bind("<Return>", lambda event: on_submit())


# 检查是否在macOS上运行，如果是则尝试修复IMK警告
if platform.system() == "Darwin":
    try:
        import mac_fix

        mac_fix.fix_imk_warning()
    except ImportError:
        print("未找到mac_fix模块，跳过macOS IMK修复")

# 主程序入口
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = KwaiTool(root)
        app.load_accounts()  # 加载账号列表
        root.mainloop()
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()

        # 在控制台模式下显示错误
        if not hasattr(sys, "frozen"):
            input("按Enter键退出...") 