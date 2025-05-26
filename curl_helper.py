#!/usr/bin/env python3
"""
API请求工具 - 处理API请求和响应
"""

import os
import json
import requests
import time
from urllib.parse import urljoin
import urllib.request
import urllib.error


class CurlHelper:
    def __init__(self, config_file="curl_config.json"):
        """初始化API客户端"""
        self.config = self.load_config(config_file)
        self.base_url = self.config.get("base_url", "")
        # 强制将HTTPS改为HTTP
        if self.base_url.startswith("https://"):
            self.base_url = "http://" + self.base_url[8:]
            print(f"已将基础URL转换为HTTP: {self.base_url}")
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
            print("SSL模块不可用，将使用纯HTTP请求")
        print("=========================\n")

    def load_config(self, config_file):
        """加载配置文件"""
        if not os.path.exists(config_file):
            # 创建默认配置
            default_config = {
                "base_url": "http://kwaiTool.zhongle88.cn",
                "default_headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "KwaiTool/1.0"
                },
                "timeout": 30,
                "endpoints": {
                    "login": "/login",
                    "account": "/index.php/admin/Dashboard/account",
                    "info": "/index.php/admin/Dashboard/OwnerInfo",
                }
            }

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            return default_config

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 强制将配置中的HTTPS改为HTTP
                if config.get("base_url", "").startswith("https://"):
                    config["base_url"] = "http://" + config["base_url"][8:]
                    print(f"已将配置文件中的URL转换为HTTP: {config['base_url']}")
                    # 保存更新后的配置
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                return config
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

        # 强制使用HTTP
        if url.startswith("https://"):
            url = "http://" + url[8:]
            print(f"已转换为HTTP URL: {url}")

        # 合并请求头
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            # 使用纯urllib实现，不依赖requests库
            import urllib.request
            import urllib.error
            import urllib.parse

            # 添加查询参数
            if params:
                query_string = urllib.parse.urlencode(params)
                if '?' in url:
                    url += '&' + query_string
                else:
                    url += '?' + query_string

            # 创建请求
            req = urllib.request.Request(
                url,
                headers=request_headers,
                method='GET'
            )

            # 禁止重定向
            opener = urllib.request.build_opener(NoRedirectHandler())
            urllib.request.install_opener(opener)

            # 发送请求
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    response_data = response.read().decode('utf-8')
                    status_code = response.status
                    response_headers = dict(response.headers)

                    # 解析响应
                    try:
                        json_response = json.loads(response_data)
                        return {
                            "status_code": status_code,
                            "data": json_response,
                            "headers": response_headers
                        }
                    except json.JSONDecodeError:
                        return {
                            "status_code": status_code,
                            "text": response_data,
                            "headers": response_headers
                        }
            except urllib.error.HTTPError as e:
                if e.code == 301 or e.code == 302:
                    print(f"检测到重定向（{e.code}），但我们不跟随重定向")
                    return {"error": f"服务器尝试重定向到HTTPS，但我们不允许重定向"}
                else:
                    print(f"HTTP错误: {e.code} - {e.reason}")
                    return {"error": f"HTTP错误: {e.code} - {e.reason}"}

        except Exception as e:
            print(f"请求发送失败: {e}")
            return {"error": f"请求失败: {str(e)}"}

    def post(self, endpoint_name, data=None, json_data=None, headers=None):
        """发送POST请求"""
        url = self.get_endpoint_url(endpoint_name)
        if not url:
            return {"error": f"未找到端点: {endpoint_name}"}

        # 强制使用HTTP
        if url.startswith("https://"):
            url = "http://" + url[8:]
            print(f"已转换为HTTP URL: {url}")

        # 合并请求头
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            # 使用纯urllib实现，不依赖requests库
            import urllib.request
            import urllib.error

            # 准备请求数据
            if json_data:
                post_data = json.dumps(json_data).encode('utf-8')
                request_headers['Content-Type'] = 'application/json'
            elif data:
                post_data = data.encode('utf-8') if isinstance(data, str) else urllib.parse.urlencode(data).encode(
                    'utf-8')
                if 'Content-Type' not in request_headers:
                    request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            else:
                post_data = None

            # 创建请求
            req = urllib.request.Request(
                url,
                data=post_data,
                headers=request_headers,
                method='POST'
            )

            # 禁止重定向
            opener = urllib.request.build_opener(NoRedirectHandler())
            urllib.request.install_opener(opener)

            # 发送请求
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    response_data = response.read().decode('utf-8')
                    status_code = response.status
                    response_headers = dict(response.headers)

                    # 解析响应
                    try:
                        json_response = json.loads(response_data)
                        return {
                            "status_code": status_code,
                            "data": json_response,
                            "headers": response_headers
                        }
                    except json.JSONDecodeError:
                        return {
                            "status_code": status_code,
                            "text": response_data,
                            "headers": response_headers
                        }
            except urllib.error.HTTPError as e:
                if e.code == 301 or e.code == 302:
                    print(f"检测到重定向（{e.code}），但我们不跟随重定向")
                    return {"error": f"服务器尝试重定向到HTTPS，但我们不允许重定向"}
                else:
                    print(f"HTTP错误: {e.code} - {e.reason}")
                    return {"error": f"HTTP错误: {e.code} - {e.reason}"}

        except Exception as e:
            print(f"请求发送失败: {e}")
            return {"error": f"请求失败: {str(e)}"}

    def upload_cookies(self, account, cookies, account_id):
        """上传账号Cookie到API"""
        timestamp = time.time()

        # 获取完整的API端点URL
        url = self.get_endpoint_url("account")
        print(f"正在发送请求到: {url}")

        # 准备发送的数据
        data = {
            "account": account,
            "cookies": cookies,
            "account_id": account_id,
            "timestamp": timestamp
        }
        print(f"请求数据: {json.dumps(data, ensure_ascii=False)[:100]}...")  # 只打印前100个字符

        # 直接使用urllib，完全绕过requests库
        import urllib.request
        import urllib.error

        # 确保URL是HTTP
        if url.startswith("https://"):
            url = "http://" + url[8:]
            print(f"已转换为HTTP URL: {url}")

        try:
            # 准备请求数据
            post_data = json.dumps(data).encode('utf-8')
            headers = self.default_headers.copy()
            headers['Content-Type'] = 'application/json'

            # 创建请求
            req = urllib.request.Request(
                url,
                data=post_data,
                headers=headers,
                method='POST'
            )

            # 设置不允许重定向
            opener = urllib.request.build_opener(NoRedirectHandler())
            urllib.request.install_opener(opener)

            # 发送请求
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    response_data = response.read().decode('utf-8')
                    status_code = response.status
                    response_headers = dict(response.headers)

                    print(f"请求成功，状态码: {status_code}")

                    # 解析响应
                    try:
                        json_response = json.loads(response_data)
                        return {
                            "status_code": status_code,
                            "data": json_response,
                            "headers": response_headers
                        }
                    except json.JSONDecodeError:
                        return {
                            "status_code": status_code,
                            "text": response_data,
                            "headers": response_headers
                        }
            except urllib.error.HTTPError as e:
                if e.code == 301 or e.code == 302:
                    print(f"检测到重定向（{e.code}），但我们不跟随重定向")
                    return {"error": f"服务器尝试重定向到HTTPS，但我们不允许重定向"}
                else:
                    print(f"HTTP错误: {e.code} - {e.reason}")
                    return {"error": f"HTTP错误: {e.code} - {e.reason}"}

        except Exception as e:
            print(f"请求发送失败: {e}")
            return {"error": f"请求失败: {str(e)}"}


# 自定义处理程序，禁止重定向
class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        print(f"禁止重定向: {code} - {headers.get('Location')}")
        return None

    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302


# 测试代码
if __name__ == "__main__":
    api = CurlHelper()
    print(f"已加载API配置: {api.base_url}")
    print(f"可用端点: {list(api.endpoints.keys())}")

    # 添加此行以触发GitHub重新打包，解决SSL模块问题