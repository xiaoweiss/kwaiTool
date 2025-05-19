#!/usr/bin/env python3
"""
API请求工具 - 处理API请求和响应
"""

import os
import json
import requests
import time
from urllib.parse import urljoin

class CurlHelper:
    def __init__(self, config_file="curl_config.json"):
        """初始化API客户端"""
        self.config = self.load_config(config_file)
        self.base_url = self.config.get("base_url", "")
        self.default_headers = self.config.get("default_headers", {})
        self.timeout = self.config.get("timeout", 30)
        self.endpoints = self.config.get("endpoints", {})
        
        # 打印配置信息
        print("\n=== API客户端配置信息 ===")
        print(f"配置文件: {config_file}")
        print(f"基础URL: {self.base_url}")
        print(f"API端点: {self.endpoints}")
        print(f"超时设置: {self.timeout}秒")
        print(f"默认请求头: {self.default_headers}")
        print("=== SSL相关信息 ===")
        try:
            import ssl
            print(f"SSL模块可用: {ssl.OPENSSL_VERSION}")
        except ImportError:
            print("SSL模块不可用，请检查Python环境")
        print("=========================\n")
    
    def load_config(self, config_file):
        """加载配置文件"""
        if not os.path.exists(config_file):
            # 创建默认配置
            default_config = {
                "base_url": "https://kwaiTool.zhongle88.cn",
                "default_headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "KwaiTool/1.0"
                },
                "timeout": 30,
                "endpoints": {
                    "login": "/login",
                    "account": "/index.php/admin/Dashboard/account"
                }
            }
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            return default_config
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def get_endpoint_url(self, endpoint_name):
        """获取完整的API端点URL"""
        endpoint = self.endpoints.get(endpoint_name, "")
        if not endpoint:
            return None
        
        return urljoin(self.base_url, endpoint)
    
    def get(self, endpoint_name, params=None, headers=None):
        """发送GET请求"""
        url = self.get_endpoint_url(endpoint_name)
        if not url:
            return {"error": f"未找到端点: {endpoint_name}"}
        
        # 合并请求头
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=request_headers,
                timeout=self.timeout
            )
            
            return self.process_response(response)
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
    
    def post(self, endpoint_name, data=None, json_data=None, headers=None):
        """发送POST请求"""
        url = self.get_endpoint_url(endpoint_name)
        if not url:
            return {"error": f"未找到端点: {endpoint_name}"}
        
        # 合并请求头
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            response = requests.post(
                url,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=self.timeout
            )
            
            return self.process_response(response)
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
    
    def process_response(self, response):
        """处理API响应"""
        try:
            # 尝试解析JSON响应
            json_response = response.json()
            return {
                "status_code": response.status_code,
                "data": json_response,
                "headers": dict(response.headers)
            }
        except ValueError:
            # 非JSON响应
            return {
                "status_code": response.status_code,
                "text": response.text,
                "headers": dict(response.headers)
            }
    
    def upload_cookies(self, account, cookies):
        """上传账号Cookie到API"""
        timestamp = time.time()
        
        # 获取完整的API端点URL
        url = self.get_endpoint_url("account")
        print(f"正在发送请求到: {url}")
        
        # 准备发送的数据
        data = {
            "account": account,
            "cookies": cookies,
            "timestamp": timestamp
        }
        print(f"请求数据: {json.dumps(data, ensure_ascii=False)[:100]}...")  # 只打印前100个字符
        
        try:
            # 尝试发送请求
            return self.post(
                "account",
                json_data=data
            )
        except Exception as e:
            print(f"请求发送失败: {e}")
            return {"error": f"请求失败: {str(e)}"}

# 测试代码
if __name__ == "__main__":
    api = CurlHelper()
    print(f"已加载API配置: {api.base_url}")
    print(f"可用端点: {list(api.endpoints.keys())}") 
    
# 添加此行以触发GitHub重新打包，解决SSL模块问题 