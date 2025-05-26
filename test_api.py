#!/usr/bin/env python3
# 测试快手接口返回值

import requests
import json

def test_kuaishou_api(cookie=None):
    """测试快手API返回值"""
    url = "https://niu.e.kuaishou.com/rest/esp/owner/info"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    
    if cookie:
        headers["Cookie"] = cookie
    
    try:
        # 发送请求
        response = requests.post(url, headers=headers)
        
        # 打印状态码
        print(f"HTTP状态码: {response.status_code}")
        
        # 尝试解析为JSON
        try:
            json_data = response.json()
            print("\n=== JSON格式响应 ===")
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            
            # 特别提取result字段
            if "result" in json_data:
                print(f"\n响应中的result值: {json_data['result']}")
                
            # 检查是否包含accountInfos字段
            if "accountInfos" in json_data:
                print(f"\n包含accountInfos字段，共有{len(json_data['accountInfos'])}个账号")
                for i, account in enumerate(json_data['accountInfos']):
                    print(f"\n账号 {i+1}:")
                    print(f"  账号ID: {account.get('accountId')}")
                    print(f"  账号名称: {account.get('accountName')}")
                    print(f"  账号类型: {account.get('accountTypeDescription')}")
        except ValueError:
            # 不是JSON格式，打印文本内容
            print("\n=== 文本格式响应 ===")
            print(response.text)
            
        # 打印响应头
        print("\n=== 响应头 ===")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"请求出错: {e}")

if __name__ == "__main__":
    # 使用示例:
    cookie = input("请输入您的Cookie (如果没有可直接回车): ")
    test_kuaishou_api(cookie) 