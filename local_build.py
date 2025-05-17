#!/usr/bin/env python3
"""
本地打包脚本 - 在Windows上直接运行，不依赖GitHub Actions
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

def check_windows():
    """检查是否在Windows系统上运行"""
    if platform.system() != "Windows":
        print("错误: 此脚本需要在Windows系统上运行!")
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
    
    # 使用PyInstaller打包应用程序
    print("使用PyInstaller打包应用程序...")
    if not run_command(f"{sys.executable} -m PyInstaller --onedir --name \"快手账号管理工具\" main.py"):
        print("打包应用程序失败!")
        return False
    
    # 创建启动批处理文件
    print("创建启动批处理文件...")
    with open("dist/快手账号管理工具/启动.bat", "w", encoding="utf-8") as f:
        f.write('@echo off\n')
        f.write('cd /d "%~dp0"\n')
        f.write('echo 正在启动快手账号管理工具...\n')
        f.write('快手账号管理工具.exe\n')
        f.write('pause\n')
    
    # 复制配置文件
    if os.path.exists("curl_config.json"):
        print("复制配置文件...")
        shutil.copy("curl_config.json", "dist/快手账号管理工具/")
    
    # 创建accounts目录
    print("创建accounts目录...")
    os.makedirs("dist/快手账号管理工具/accounts", exist_ok=True)
    
    # 创建ZIP压缩包
    print("创建ZIP压缩包...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"快手账号管理工具_{timestamp}.zip"
    
    if platform.system() == "Windows":
        # 使用PowerShell的Compress-Archive
        command = f'powershell -command "Compress-Archive -Path \\"dist/快手账号管理工具/*\\" -DestinationPath \\"{zip_filename}\\""'
        if not run_command(command):
            print("创建ZIP压缩包失败!")
            return False
    else:
        # 使用Python的shutil.make_archive
        shutil.make_archive(f"快手账号管理工具_{timestamp}", 'zip', "dist/快手账号管理工具")
    
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
    print("\ndist/快手账号管理工具 目录内容:")
    for root, dirs, files in os.walk("dist/快手账号管理工具"):
        level = root.replace("dist/快手账号管理工具", "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = " " * 4 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")

def main():
    """主函数"""
    print_header("快手账号管理工具 - 本地打包脚本")
    
    # 检查系统环境
    if not check_windows():
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