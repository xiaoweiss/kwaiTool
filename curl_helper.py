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
    
    def load_config(self, config_file):
        """加载配置文件"""
        if not os.path.exists(config_file):
            # 创建默认配置
            default_config = {
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
        return self.post(
            "account",
            json_data={
                "account": account,
                "cookies": cookies,
                "timestamp": timestamp
            }
        )

# 测试代码
if __name__ == "__main__":
    api = CurlHelper()
    print(f"已加载API配置: {api.base_url}")
    print(f"可用端点: {list(api.endpoints.keys())}") 