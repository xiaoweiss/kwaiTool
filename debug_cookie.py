#!/usr/bin/env python3
"""
调试Cookie截断问题的工具脚本
"""

import os
import json
import time
import platform
from playwright.sync_api import sync_playwright
from curl_helper import CurlHelper

# 创建API客户端实例
api_client = CurlHelper()

def test_cookie(phone, url="https://niu.e.kuaishou.com/welcome"):
    """测试cookie获取和上传"""
    print(f"开始测试cookie获取和上传流程，账号: {phone}")
    
    # 读取浏览器配置
    browser_path = None
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)
                browser_path = config_data.get("chrome_path")
        except Exception as e:
            print(f"加载浏览器配置失败: {e}")
    
    if not browser_path or not os.path.exists(browser_path):
        print("请先在config.json中配置正确的chrome_path")
        return False
    
    with sync_playwright() as p:
        # 使用配置的浏览器路径
        browser = p.chromium.launch(
            headless=False,  # 非无头模式，方便用户手动操作
            executable_path=browser_path
        )
        context = browser.new_context()
        page = context.new_page()
        
        # 访问网站
        page.goto(url)
        print("已打开网站，请手动登录...")
        
        # 等待用户手动操作
        input("登录成功后，按Enter键继续...")
        
        # 获取所有cookie
        print("开始获取cookie...")
        cookies = context.cookies()
        
        # 打印cookie信息
        if cookies:
            print(f"获取到 {len(cookies)} 个cookie")
            
            # 详细打印每个cookie
            for i, cookie in enumerate(cookies):
                print(f"Cookie {i+1}: {cookie['name']}={cookie['value'][:20]}... (总长度: {len(cookie['value'])}字符)")
            
            # 构建cookie字符串
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            print(f"完整Cookie字符串长度: {len(cookie_string)} 字符")
            print(f"Cookie字符串前100字符: {cookie_string[:100]}...")
            print(f"Cookie字符串最后50字符: ...{cookie_string[-50:]}")
            
            # 保存完整cookie到文件
            with open(f"cookie_{phone}.txt", "w", encoding="utf-8") as f:
                f.write(cookie_string)
            print(f"已保存完整cookie到 cookie_{phone}.txt")
            
            # 测试上传到API
            print("测试上传cookie到API...")
            result = api_client.upload_cookies(phone, cookie_string)
            print(f"上传结果: {result}")
            
            return True
        else:
            print("未获取到任何cookie")
            return False

if __name__ == "__main__":
    phone = input("请输入要测试的手机号: ")
    test_cookie(phone) 