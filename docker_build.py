#!/usr/bin/env python3
"""
Docker打包脚本 - 在macOS上打包Windows exe文件
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
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"错误输出: {result.stderr}")
    return result.returncode == 0

def check_docker():
    """检查Docker是否已安装"""
    print_step("检查Docker是否已安装")
    if not run_command("docker --version"):
        print("错误: 未检测到Docker! 请先安装Docker: https://docs.docker.com/desktop/install/mac-install/")
        return False
    return True

def create_dockerfile():
    """创建Dockerfile"""
    print_step("创建Dockerfile")
    
    dockerfile_content = """FROM python:3.9-windowsservercore-ltsc2022

WORKDIR /app

# 安装依赖
RUN pip install pyinstaller requests playwright
RUN playwright install

# 复制项目文件
COPY . /app/

# 打包应用
CMD pyinstaller --onedir --name "快手账号管理工具" main.py && \
    echo @echo off > dist/快手账号管理工具/启动.bat && \
    echo cd /d "%~dp0" >> dist/快手账号管理工具/启动.bat && \
    echo echo 正在启动快手账号管理工具... >> dist/快手账号管理工具/启动.bat && \
    echo 快手账号管理工具.exe >> dist/快手账号管理工具/启动.bat && \
    echo pause >> dist/快手账号管理工具/启动.bat && \
    powershell -command "Compress-Archive -Path 'dist/快手账号管理工具/*' -DestinationPath '快手账号管理工具.zip'"
"""
    
    with open("Dockerfile.windows", "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    
    print("Dockerfile.windows 已创建")
    return True

def build_docker_image():
    """构建Docker镜像"""
    print_step("构建Docker镜像")
    
    if not run_command("docker build -f Dockerfile.windows -t kwai-tool-builder ."):
        print("构建Docker镜像失败!")
        return False
    
    print("Docker镜像构建成功")
    return True

def run_docker_container():
    """运行Docker容器进行打包"""
    print_step("运行Docker容器进行打包")
    
    # 创建输出目录
    os.makedirs("docker_output", exist_ok=True)
    
    # 运行容器
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    container_name = f"kwai-tool-builder-{timestamp}"
    
    if not run_command(f"docker run --name {container_name} kwai-tool-builder"):
        print("运行Docker容器失败!")
        return False
    
    # 从容器复制打包结果
    if not run_command(f"docker cp {container_name}:/app/快手账号管理工具.zip ./docker_output/快手账号管理工具_{timestamp}.zip"):
        print("从容器复制文件失败!")
        return False
    
    # 清理容器
    run_command(f"docker rm {container_name}")
    
    print(f"打包完成! 输出文件: docker_output/快手账号管理工具_{timestamp}.zip")
    return True

def check_system():
    """检查是否在macOS系统上运行"""
    if platform.system() != "Darwin":
        print("错误: 此脚本需要在macOS系统上运行!")
        return False
    return True

def main():
    """主函数"""
    print_header("快手账号管理工具 - Docker Windows打包脚本")
    
    # 检查系统环境
    if not check_system():
        return
    
    # 检查Docker
    if not check_docker():
        return
    
    # 创建Dockerfile
    if not create_dockerfile():
        return
    
    # 构建Docker镜像
    if not build_docker_image():
        return
    
    # 运行Docker容器进行打包
    if not run_docker_container():
        return
    
    print_header("打包完成!")
    print("您可以在docker_output目录找到Windows版本的ZIP压缩包。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"错误: {e}")
    finally:
        print("\n按Enter键退出...")
        input() 