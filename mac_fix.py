#!/usr/bin/env python3
"""
macOS修复脚本 - 用于修复macOS上的IMK警告
"""

import os
import sys
import platform
import subprocess
import traceback

def check_dependency(dependency):
    """检查依赖是否已安装"""
    try:
        subprocess.run(
            ["which", dependency],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def fix_imk_warning():
    """修复macOS上的IMK警告"""
    if platform.system() != "Darwin":
        print("此脚本仅适用于macOS系统")
        return False
    
    print("正在应用macOS IMK修复...")
    
    # 检查依赖
    if not check_dependency("defaults"):
        print("错误: 未找到'defaults'命令，无法应用修复")
        return False
    
    try:
        # 设置环境变量
        os.environ["LANG"] = "en_US.UTF-8"
        
        # 使用defaults命令禁用IMK警告
        subprocess.run(
            ["defaults", "write", "-g", "ApplePressAndHoldEnabled", "-bool", "false"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        print("已成功应用IMK修复")
        return True
    except Exception as e:
        print(f"应用IMK修复时出错: {e}")
        traceback.print_exc()
        return False

def launch_app(app_path=None):
    """启动应用程序，应用IMK修复"""
    # 应用IMK修复
    fix_imk_warning()
    
    # 如果指定了应用程序路径，则启动它
    if app_path:
        if os.path.exists(app_path) and os.path.isfile(app_path) and os.access(app_path, os.X_OK):
            try:
                print(f"正在启动应用程序: {app_path}")
                subprocess.run([app_path])
            except Exception as e:
                print(f"启动应用程序时出错: {e}")
                traceback.print_exc()
        else:
            print(f"错误: 无法找到可执行文件 {app_path}")
    else:
        # 如果是打包后的应用程序，尝试找到主程序
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
            main_app = os.path.join(app_dir, "快手账号管理工具")
            
            if os.path.exists(main_app) and os.access(main_app, os.X_OK):
                try:
                    print(f"正在启动主程序: {main_app}")
                    subprocess.run([main_app])
                except Exception as e:
                    print(f"启动主程序时出错: {e}")
                    traceback.print_exc()

# 主程序入口
if __name__ == "__main__":
    # 如果有命令行参数，则作为应用程序路径
    if len(sys.argv) > 1:
        launch_app(sys.argv[1])
    else:
        # 否则尝试修复IMK警告并启动主程序
        launch_app() 