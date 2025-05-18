#!/usr/bin/env python3
"""
GitHub Actions构建脚本 - 用于CI环境中打包应用程序
"""

import os
import sys
import subprocess
import platform
import shutil

def print_header(message):
    """打印带格式的标题"""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)

def print_step(message):
    """打印步骤信息"""
    print(f"\n>> {message}")

def run_command(command):
    """运行命令并打印输出"""
    print(f"执行命令: {command}")
    subprocess.check_call(command, shell=True)
    return True

def build_app():
    """打包应用程序"""
    print_step("打包应用程序")
    
    # 使用spec文件打包
    if os.path.exists("kwai_tool.spec"):
        print("使用spec文件打包...")
        run_command(f"{sys.executable} -m PyInstaller kwai_tool.spec")
    else:
        # 直接使用PyInstaller命令行参数打包
        print("使用PyInstaller命令行参数打包...")
        if platform.system() == "Windows":
            run_command(f"{sys.executable} -m PyInstaller --name \"快手账号管理工具\" --onedir main.py")
        else:  # macOS
            run_command(f"{sys.executable} -m PyInstaller --name \"快手账号管理工具\" --onedir main.py")
    
    # 创建启动文件
    app_name = "快手账号管理工具"
    if platform.system() == "Windows":
        print("创建Windows启动批处理文件...")
        with open(f"dist/{app_name}/启动.bat", "w", encoding="utf-8") as f:
            f.write('@echo off\n')
            f.write('cd /d "%~dp0"\n')
            f.write(f'echo 正在启动{app_name}...\n')
            f.write(f'{app_name}.exe\n')
            f.write('pause\n')
    else:  # macOS
        print("创建macOS启动脚本...")
        with open(f"dist/{app_name}/启动.sh", "w", encoding="utf-8") as f:
            f.write('#!/bin/bash\n')
            f.write('cd "$(dirname "$0")"\n')
            f.write(f'echo "正在启动{app_name}..."\n')
            f.write(f'./{app_name}\n')
        # 设置可执行权限
        os.chmod(f"dist/{app_name}/启动.sh", 0o755)
    
    # 复制配置文件
    if os.path.exists("curl_config.json"):
        print("复制配置文件...")
        shutil.copy("curl_config.json", f"dist/{app_name}/")
    
    # 创建accounts目录
    print("创建accounts目录...")
    os.makedirs(f"dist/{app_name}/accounts", exist_ok=True)
    
    print("应用程序打包完成")
    return True

def main():
    """主函数"""
    print_header("快手账号管理工具 - GitHub Actions构建脚本")
    
    # 打包应用程序
    build_app()
    
    print_header("构建完成!")

if __name__ == "__main__":
    main() 