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

# 全局变量
ACCOUNTS_DIR = "accounts"
CONFIG_FILE = "curl_config.json"
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

# 加载配置
config = {}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"加载配置失败: {e}")
else:
    # 创建默认配置
    config = {
        "base_url": "https://api.example.com",
        "default_headers": {
            "Content-Type": "application/json",
            "User-Agent": "KwaiTool/1.0"
        },
        "timeout": 30,
        "endpoints": {
            "login": "/login",
            "account": "/account"
        }
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

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
        file_menu.add_command(label="导出Cookies", command=self.export_cookies)
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
        settings_menu.add_command(label="API配置", command=self.edit_config)
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
        ttk.Button(toolbar, text="开始处理", command=self.start_processing).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="停止处理", command=self.stop_processing).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清除记录", command=self.clear_processed).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出Cookies", command=self.export_cookies).pack(side=tk.LEFT, padx=2)
    
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
                        if len(lines) >= 2:
                            username = lines[0].strip()
                            password = lines[1].strip()
                            
                            # 检查是否已处理
                            status = "未处理"
                            update_time = ""
                            if username in processed_accounts:
                                status = "已处理"
                                update_time = processed_accounts[username].get("time", "")
                            
                            self.accounts_tree.insert("", tk.END, values=(username, password, status, update_time))
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
                
                imported = 0
                for i in range(0, len(lines), 2):
                    if i + 1 < len(lines):
                        username = lines[i].strip()
                        password = lines[i + 1].strip()
                        
                        if username and password:
                            # 创建账号文件
                            account_file = os.path.join(ACCOUNTS_DIR, f"{username}.txt")
                            with open(account_file, "w", encoding="utf-8") as af:
                                af.write(f"{username}\n{password}")
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
            self.log(f"开始处理 {len(accounts)} 个账号")
            
            for i, (username, password) in enumerate(accounts):
                if stop_event.is_set():
                    self.log("处理已停止")
                    break
                
                self.log(f"正在处理账号 ({i+1}/{len(accounts)}): {username}")
                
                try:
                    # 使用Playwright登录并获取Cookie
                    cookies = self.login_and_get_cookies(username, password)
                    
                    if cookies:
                        # 保存Cookie
                        cookie_file = os.path.join(ACCOUNTS_DIR, f"{username}_cookies.json")
                        with open(cookie_file, "w", encoding="utf-8") as f:
                            json.dump(cookies, f, indent=2, ensure_ascii=False)
                        
                        # 更新已处理记录
                        processed_accounts[username] = {
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "cookie_file": cookie_file
                        }
                        
                        # 保存已处理记录
                        with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
                            json.dump(processed_accounts, f, indent=2, ensure_ascii=False)
                        
                        self.log(f"账号 {username} 处理成功")
                    else:
                        self.log(f"账号 {username} 登录失败")
                
                except Exception as e:
                    self.log(f"处理账号 {username} 时出错: {e}")
                    traceback.print_exc()
            
            self.log("账号处理完成")
        except Exception as e:
            self.log(f"处理过程出错: {e}")
            traceback.print_exc()
        finally:
            running = False
            self.update_status("就绪")
            
            # 刷新账号列表
            self.root.after(0, self.load_accounts)
    
    def login_and_get_cookies(self, username, password):
        """使用Playwright登录并获取Cookie"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # 访问快手电商牛平台
                page.goto("https://s.kwaixiaodian.com/")
                self.log("已打开快手电商牛平台")
                
                # 等待登录页面加载
                page.wait_for_selector("input[name='username']", timeout=30000)
                
                # 输入用户名和密码
                page.fill("input[name='username']", username)
                page.fill("input[name='password']", password)
                
                # 点击登录按钮
                page.click("button[type='submit']")
                
                # 等待登录成功
                page.wait_for_url("**/dashboard*", timeout=60000)
                
                # 获取所有Cookie
                cookies = context.cookies()
                
                # 关闭浏览器
                browser.close()
                
                return cookies
        except Exception as e:
            self.log(f"登录过程出错: {e}")
            return None
    
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
    
    def export_cookies(self):
        """导出所有Cookies"""
        if not processed_accounts:
            messagebox.showinfo("提示", "没有已处理的账号")
            return
        
        export_dir = filedialog.askdirectory(title="选择导出目录")
        if not export_dir:
            return
        
        try:
            exported = 0
            for username, data in processed_accounts.items():
                cookie_file = data.get("cookie_file")
                if cookie_file and os.path.exists(cookie_file):
                    # 读取Cookie文件
                    with open(cookie_file, "r", encoding="utf-8") as f:
                        cookies = json.load(f)
                    
                    # 导出到目标目录
                    export_file = os.path.join(export_dir, f"{username}_cookies.json")
                    with open(export_file, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, indent=2, ensure_ascii=False)
                    
                    exported += 1
            
            self.log(f"成功导出 {exported} 个账号的Cookies")
            messagebox.showinfo("导出完成", f"成功导出 {exported} 个账号的Cookies")
        except Exception as e:
            self.log(f"导出Cookies失败: {e}")
            messagebox.showerror("错误", f"导出Cookies失败: {e}")
    
    def edit_config(self):
        """编辑API配置"""
        # 创建配置编辑窗口
        config_window = tk.Toplevel(self.root)
        config_window.title("API配置")
        config_window.geometry("600x400")
        config_window.grab_set()  # 模态窗口
        
        # 创建文本编辑区
        config_text = scrolledtext.ScrolledText(config_window, wrap=tk.WORD)
        config_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 加载当前配置
        config_text.insert(tk.END, json.dumps(config, indent=2, ensure_ascii=False))
        
        # 创建按钮区域
        button_frame = ttk.Frame(config_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def save_config():
            try:
                # 获取文本内容并解析JSON
                new_config = json.loads(config_text.get("1.0", tk.END))
                
                # 保存到配置文件
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_config, f, indent=2, ensure_ascii=False)
                
                # 更新全局配置
                global config
                config = new_config
                
                self.log("API配置已更新")
                config_window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=config_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def browser_settings(self):
        """浏览器设置"""
        messagebox.showinfo("浏览器设置", "此功能尚未实现")
    
    def show_help(self):
        """显示使用说明"""
        help_text = """
使用说明：

1. 导入账号：
   - 点击"文件"→"导入账号"或工具栏上的"导入账号"按钮
   - 选择包含账号信息的文本文件（每行一个账号，每两行为一组）

2. 处理账号：
   - 点击"操作"→"开始处理"或工具栏上的"开始处理"按钮
   - 程序将自动登录并获取Cookie

3. 导出Cookies：
   - 点击"文件"→"导出Cookies"或工具栏上的"导出Cookies"按钮
   - 选择导出目录

4. 清除已处理记录：
   - 点击"操作"→"清除已处理记录"或工具栏上的"清除记录"按钮
   - 这将允许重新处理所有账号

5. API配置：
   - 点击"设置"→"API配置"
   - 编辑API相关设置
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

版本: 1.0.0
作者: 快手账号管理团队

本工具用于批量登录快手电商牛平台并提取Cookie。
        """
        
        messagebox.showinfo("关于", about_text)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        if running:
            if not messagebox.askyesno("确认", "有任务正在运行，确定要退出吗？"):
                return
            stop_event.set()
        
        self.root.destroy()

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