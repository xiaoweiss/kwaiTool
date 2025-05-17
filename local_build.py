#!/usr/bin/env python3
"""
本地打包脚本 - 在Windows和macOS上直接运行，不依赖GitHub Actions
"""

import os
import sys
import subprocess
import platform
import shutil
import time
from datetime import datetime

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
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"错误输出: {result.stderr}")
    return result.returncode == 0

def check_system():
    """检查系统类型"""
    system = platform.system()
    print_step(f"检测到系统类型: {system}")
    if system not in ["Windows", "Darwin"]:
        print("错误: 此脚本仅支持Windows和macOS系统!")
        return False
    return True

def check_python():
    """检查Python版本"""
    print_step("检查Python版本")
    print(f"Python版本: {platform.python_version()}")
    return True

def install_dependencies():
    """安装必要的依赖"""
    print_step("安装必要的依赖")
    
    dependencies = ["pyinstaller", "requests", "playwright"]
    for dep in dependencies:
        print(f"安装 {dep}...")
        if not run_command(f"{sys.executable} -m pip install {dep}"):
            print(f"安装 {dep} 失败!")
            return False
    
    print("安装Playwright浏览器...")
    if not run_command(f"{sys.executable} -m playwright install"):
        print("安装Playwright浏览器失败!")
        return False
    
    return True

def build_app():
    """打包应用程序"""
    print_step("打包应用程序")
    
    # 创建dist目录（如果不存在）
    if not os.path.exists("dist"):
        os.makedirs("dist")
    
    # 清理旧的构建文件
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # 应用程序名称
    app_name = "快手账号管理工具"
    
    # 使用PyInstaller打包应用程序
    print("使用PyInstaller打包应用程序...")
    if not run_command(f"{sys.executable} -m PyInstaller --onedir --name \"{app_name}\" main.py"):
        print("打包应用程序失败!")
        return False
    
    # 根据系统类型创建启动文件
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
    
    # 创建ZIP压缩包
    print("创建ZIP压缩包...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{app_name}_{timestamp}.zip"
    
    if platform.system() == "Windows":
        # 使用PowerShell的Compress-Archive
        command = f'powershell -command "Compress-Archive -Path \\"dist/{app_name}/*\\" -DestinationPath \\"{zip_filename}\\""'
        if not run_command(command):
            print("创建ZIP压缩包失败!")
            return False
    else:  # macOS
        # 切换到dist目录
        current_dir = os.getcwd()
        os.chdir(f"dist/{app_name}")
        
        # 使用zip命令
        if not run_command(f"zip -r ../../{zip_filename} ."):
            os.chdir(current_dir)
            print("创建ZIP压缩包失败!")
            return False
        
        # 切回原目录
        os.chdir(current_dir)
    
    print(f"ZIP压缩包已创建: {zip_filename}")
    return True

def show_file_info():
    """显示文件信息"""
    print_step("显示文件信息")
    
    # 查找最新的ZIP文件
    zip_files = [f for f in os.listdir(".") if f.startswith("快手账号管理工具_") and f.endswith(".zip")]
    if not zip_files:
        print("未找到ZIP文件!")
        return
    
    latest_zip = max(zip_files)
    print(f"最新ZIP文件: {latest_zip}")
    
    # 显示文件大小
    size_bytes = os.path.getsize(latest_zip)
    size_mb = size_bytes / (1024 * 1024)
    print(f"文件大小: {size_mb:.2f} MB ({size_bytes:,} 字节)")
    
    # 显示文件路径
    abs_path = os.path.abspath(latest_zip)
    print(f"文件路径: {abs_path}")
    
    # 显示dist目录内容
    app_name = "快手账号管理工具"
    print(f"\ndist/{app_name} 目录内容:")
    for root, dirs, files in os.walk(f"dist/{app_name}"):
        level = root.replace(f"dist/{app_name}", "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = " " * 4 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")

def main():
    """主函数"""
    print_header("快手账号管理工具 - 本地打包脚本")
    
    # 检查系统环境
    if not check_system():
        return
    
    if not check_python():
        return
    
    # 安装依赖
    if not install_dependencies():
        return
    
    # 打包应用程序
    if not build_app():
        return
    
    # 显示文件信息
    show_file_info()
    
    print_header("打包完成!")
    print("您可以在当前目录找到ZIP压缩包，或在dist/快手账号管理工具目录中找到可执行文件。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"错误: {e}")
    finally:
        print("\n按Enter键退出...")
        input() 