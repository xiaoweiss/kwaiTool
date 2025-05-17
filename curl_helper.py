"""
HTTP请求工具核心功能
功能：
1. 获取认证令牌
2. 上报消费数据
3. 上报账号信息
"""

import json
import os
import sys
import requests
import urllib.parse

# 关闭模拟认证模式，使用内置默认配置进行实际请求
MOCK_AUTH = False

class APIClient:
    def __init__(self):
        self.config = {}
        self.session = requests.Session()
        # 直接使用内置默认配置，不尝试加载外部配置文件
        self._use_default_config()

    def _load_config(self, config_file='curl_config.json'):
        """此方法现在不会被调用"""
        # 直接使用内置默认配置
        self._use_default_config()
        return

    def _use_default_config(self):
        """使用内置默认配置"""
        self.config = {
            "base_url": "https://kwaiTool.zhongle88.cn/",
            "default_headers": {
                "Content-Type": "application/json",
                "X-Client": "FacebookAdsManager/1.0"
            },
            "timeout": 30,
            "endpoints": {
                "get_auth": "index.php/api/finance.Callback/getAuth",
                "report_spend": "index.php/api/finance.Callback/index",
                "account": "index.php/admin/Dashboard/account"  # 添加账号信息上报接口
            }
        }
        print("直接使用内置默认配置，不尝试加载外部配置")
        # 检查并修复base_url
        if 'base_url' in self.config:
            self.config['base_url'] = self._normalize_base_url(self.config['base_url'])

    def _normalize_base_url(self, url):
        """标准化处理base_url"""
        if not url:
            print("警告: base_url为空")
            return "https://kwaiTool.zhongle88.cn/"
            
        # 确保URL有协议前缀
        if not url.startswith(('http://', 'https://')):
            url = f'http://{url}' if any(local in url for local in ['localhost', '192.168', '127.0.0.1']) else f'https://{url}'
        
        # 确保URL以/结尾
        if not url.endswith('/'):
            url += '/'
            
        return url

    def _build_url(self, endpoint):
        """构建完整API URL"""
        base = self.config.get('base_url', '')
        if not base:
            print("错误: base_url未配置")
            # 使用默认值而不是返回空字符串
            base = "https://kwaiTool.zhongle88.cn/"
            
        # 去除endpoint开头的斜杠
        endpoint = endpoint.lstrip('/')
        
        # 使用urllib.parse确保URL正确拼接
        full_url = urllib.parse.urljoin(base, endpoint)
        
        print(f"调试: 构建URL: {full_url}")
        return full_url

    def account(self, data):
        """上报账号信息"""
        endpoint = self.config.get('endpoints', {}).get('account', 'index.php/admin/Dashboard/account')
        try:
            url = self._build_url(endpoint)
            if not url:
                raise ValueError("无法构建有效的上报URL")
                
            print(f"上报账号信息请求URL: {url}")
            print(f"上报数据: {json.dumps(data, ensure_ascii=False)}")
            
            response = self.session.post(
                url=url,
                json=data,
                headers=self.config.get('default_headers', {}),
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            result = response.json()
            print(f"上报账号信息响应: {json.dumps(result, ensure_ascii=False)}")
            return result
        except Exception as e:
            print(f"上报账号信息失败: {str(e)}")
            return {"code": -1, "msg": f"请求失败: {str(e)}"}
            
    def report_spend(self, data):
        """上报消费数据"""
        endpoint = self.config.get('endpoints', {}).get('report_spend', 'index.php/api/finance.Callback/index')
        try:
            url = self._build_url(endpoint)
            if not url:
                raise ValueError("无法构建有效的上报URL")
                
            print(f"上报消费数据请求URL: {url}")
            response = self.session.post(
                url=url,
                json=data,
                headers=self.config.get('default_headers', {}),
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"上报消费数据失败: {str(e)}")
            return None 