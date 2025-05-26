#!/usr/bin/env python3
"""
测试多账户选择流程
"""

import os
import sys
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
from playwright.sync_api import sync_playwright
from curl_helper import CurlHelper
import requests

# 创建API客户端实例
api_client = CurlHelper()

def test_multi_account(phone):
    """命令行交互版多账户选择流程，流程与 main.py 一致"""
    print(f"开始测试多账户选择流程，账号: {phone}")
    
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
    
    try:
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
                print("已打开快手牛平台，请手动完成登录流程（手机号、验证码等）")
                input("请在浏览器中手动完成登录后，按回车继续...")

                # 2. 登录后获取cookie
                cookies = context.cookies()
                if not cookies:
                    print("无法获取Cookie，登录可能失败")
                    return False
                cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                print(f"登录后获取到的Cookie: {cookie_string}")

                # 3. 携带cookie请求owner/info
                headers = {
                    "Cookie": cookie_string,
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/json"
                }
                print("使用Python requests发送owner/info请求...")
                resp = requests.post(
                    "https://niu.e.kuaishou.com/rest/esp/owner/info",
                    headers=headers,
                    json={}
                )
                print(f"owner/info响应状态码: {resp.status_code}")
                print(f"owner/info响应内容: {resp.text}")

                # 4. 解析owner/info响应内容
                try:
                    resp_json = resp.json()
                except Exception as e:
                    print(f"解析owner/info响应出错: {e}")
                    return False

                # 5. 判断accountInfos长度
                account_infos = resp_json.get('accountInfos', [])
                if not isinstance(account_infos, list):
                    account_infos = []
                print(f"accountInfos长度: {len(account_infos)}")
                print(f"accountInfos内容: {account_infos}")

                if len(account_infos) == 0:
                    # 单账户逻辑
                    print("检测到单一账号，直接上传cookie")
                    send_account_info(phone, cookie_string)
                    result = True
                else:
                    # 多账户逻辑
                    print(f"检测到多个账号，数量: {len(account_infos)}，请在下方选择要登录的账号：")
                    account_map = {}
                    for idx, account in enumerate(account_infos):
                        account_name = account.get('accountName', '未命名账号')
                        account_id = account.get('accountId', 0)
                        account_type = account.get('accountTypeDescription', '')
                        print(f"[{idx+1}] {account_name} ({account_type}) (ID: {account_id})")
                        account_map[str(idx+1)] = account_id
                    selected = None
                    while True:
                        selected = input(f"请输入要登录的账号序号(1-{len(account_infos)}): ").strip()
                        if selected in account_map:
                            break
                        print("输入有误，请重新输入。")
                    selected_account_id = account_map[selected]
                    print(f"你选择了账号ID: {selected_account_id}")
                    # 6. 跳转至对应账户页
                    account_url = f"https://niu.e.kuaishou.com/home?__accountId__={selected_account_id}&homeType=new"
                    print(f"跳转至对应账户页: {account_url}")
                    page.goto(account_url, wait_until="networkidle")
                    page.wait_for_timeout(2000)
                    # 7. 获取新页面cookie
                    cookies = context.cookies()
                    if not cookies:
                        print("跳转后未获取到Cookie")
                        return False
                    new_cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                    print(f"跳转后获取新页面Cookie: {new_cookie_string}")
                    # 8. 上传服务器(cookie+account_id+account)
                    send_account_info(phone, new_cookie_string, selected_account_id)
                    result = True
            finally:
                try:
                    browser.close()
                    print("浏览器已关闭")
                except Exception as e:
                    print(f"关闭浏览器时出错: {e}")
            return result
    except Exception as e:
        print(f"处理过程出错: {e}")
        traceback.print_exc()
        return False

def send_account_info(phone, cookie, account_id=None):
    """发送账号信息到API"""
    try:
        # 打印cookie信息用于调试
        if cookie:
            cookie_length = len(cookie)
            print(f"准备上传的Cookie长度: {cookie_length} 字符")
            print(f"Cookie前50字符: {cookie[:50]}...")
            if cookie_length > 100:
                print(f"Cookie末尾50字符: ...{cookie[-50:]}")
        
        # 准备要发送的数据 - 注意这里使用phone作为account
        data = {
            "account": phone,  # 确保使用手机号作为account
            "cookies": cookie,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # 如果有account_id，添加到数据中
        if account_id:
            data["account_id"] = account_id
            print(f"将同时上传account_id: {account_id}")

        # 获取并打印API端点地址
        endpoint_url = api_client.get_endpoint_url("account")
        print(f"正在发送数据到API地址: {endpoint_url}")
        print(f"上传数据: account={phone}, cookie长度={len(cookie)}, account_id={account_id}")

        # 调用API发送数据
        if account_id:
            result = api_client.upload_cookies(phone, cookie, account_id)
        else:
            result = api_client.upload_cookies(phone, cookie)

        if result and "error" not in result:
            print(f"账号 {phone} 的信息已成功发送到服务器")
            print(f"服务器响应: {result}")
            return True
        else:
            error_msg = result.get("error", "未知错误") if result else "请求失败"
            print(f"账号 {phone} 的信息发送失败: {error_msg}")
            return False
    except Exception as e:
        print(f"发送账号信息时出错: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    phone = input("请输入要测试的手机号: ")
    test_multi_account(phone)