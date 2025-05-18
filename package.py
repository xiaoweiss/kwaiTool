#!/usr/bin/env python3
"""
简化版打包脚本 - 直接使用PyInstaller打包
"""

import os
import sys
import subprocess
import platform
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
    result = subprocess.run(command, shell=True)
    return result.returncode == 0

def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    print_step("检查PyInstaller是否已安装")
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        if not run_command(f"{sys.executable} -m pip install pyinstaller"):
            print("安装PyInstaller失败!")
            return False
        return True

def install_dependencies():
    """安装必要的依赖"""
    print_step("安装必要的依赖")
    
    dependencies = ["requests", "playwright"]
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
    
    # 使用spec文件打包
    if os.path.exists("kwai_tool.spec"):
        print("使用spec文件打包...")
        if not run_command(f"{sys.executable} -m PyInstaller kwai_tool.spec"):
            print("打包应用程序失败!")
            return False
    else:
        # 直接使用PyInstaller命令行参数打包
        print("使用PyInstaller命令行参数打包...")
        if platform.system() == "Windows":
            if not run_command(f"{sys.executable} -m PyInstaller --name \"快手账号管理工具\" --onedir main.py"):
                print("打包应用程序失败!")
                return False
        else:  # macOS
            if not run_command(f"{sys.executable} -m PyInstaller --name \"快手账号管理工具\" --onedir main.py"):
                print("打包应用程序失败!")
                return False
    
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
        import shutil
        shutil.copy("curl_config.json", f"dist/{app_name}/")
    
    # 创建accounts目录
    print("创建accounts目录...")
    os.makedirs(f"dist/{app_name}/accounts", exist_ok=True)
    
    return True

def create_zip():
    """创建ZIP压缩包"""
    print_step("创建ZIP压缩包")
    
    app_name = "快手账号管理工具"
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

def main():
    """主函数"""
    print_header("快手账号管理工具 - 打包脚本")
    
    # 检查PyInstaller
    if not check_pyinstaller():
        return
    
    # 安装依赖
    if not install_dependencies():
        return
    
    # 打包应用程序
    if not build_app():
        return
    
    # 创建ZIP压缩包
    if not create_zip():
        return
    
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