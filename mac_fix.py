#!/usr/bin/env python3
"""
这是一个用于在macOS上运行快手账号管理工具的启动脚本
它会自动抑制macOS上的IMK警告
"""

import os
import sys
import platform
import subprocess
import importlib.util

def check_dependencies():
    """检查必要的依赖是否已安装"""
    required_packages = ['playwright', 'requests', 'tkinter']
    missing_packages = []
    
    for package in required_packages:
        if package == 'tkinter':
            # tkinter是Python标准库，特殊检查
            try:
                import tkinter
                print(f"✓ {package} 已安装")
            except ImportError:
                missing_packages.append(package)
                print(f"✗ {package} 未安装")
        else:
            # 检查其他包
            if importlib.util.find_spec(package) is None:
                missing_packages.append(package)
                print(f"✗ {package} 未安装")
            else:
                print(f"✓ {package} 已安装")
    
    if missing_packages:
        print("\n缺少必要的依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        
        print("\n请使用以下命令安装依赖:")
        if 'tkinter' in missing_packages:
            print("  tkinter是Python标准库的一部分，请确保您的Python安装包含tkinter")
            missing_packages.remove('tkinter')
        
        if missing_packages:
            packages_str = ' '.join(missing_packages)
            print(f"  pip install {packages_str}")
            
            # 询问是否自动安装依赖
            try:
                response = input("\n是否自动安装缺少的依赖? (y/n): ")
                if response.lower() == 'y':
                    print("正在安装依赖...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                    print("依赖安装完成")
                    
                    # 检查playwright是否需要安装浏览器
                    if 'playwright' in missing_packages:
                        print("正在安装Playwright浏览器...")
                        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
                        print("Playwright浏览器安装完成")
                    
                    return True
            except Exception as e:
                print(f"安装依赖时出错: {e}")
        
        return False
    
    return True

def main():
    print("快手账号管理工具 - macOS启动器")
    
    # 检查是否为macOS
    if platform.system() != "Darwin":
        print("这个脚本只需要在macOS上使用。")
        run_main_app()
        return
    
    print("检测到macOS系统，应用修复...")
    
    # 检查依赖
    if not check_dependencies():
        print("请安装缺少的依赖后重试")
        return
    
    # 使用环境变量禁用IMK警告
    env = os.environ.copy()
    env["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    
    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.realpath(__file__))
    
    # 构建main.py的完整路径
    main_script = os.path.join(script_dir, "main.py")
    
    # 检查main.py是否存在
    if not os.path.exists(main_script):
        print("错误: 无法找到main.py，请确保此脚本与main.py在同一目录。")
        return
    
    # 使用subprocess运行main.py，并重定向stderr
    try:
        print("启动主程序...")
        with open(os.devnull, 'w') as devnull:
            # 直接执行Python解释器运行main.py
            process = subprocess.Popen(
                [sys.executable, main_script],
                env=env,
                stderr=devnull
            )
            # 等待进程结束
            return_code = process.wait()
            
            if return_code != 0:
                print(f"主程序异常退出，退出码: {return_code}")
                print("尝试直接导入运行...")
                run_main_app()
    except Exception as e:
        print(f"运行主程序时出错: {e}")
        run_main_app()  # 如果失败，尝试直接运行

def run_main_app():
    """直接运行主应用程序"""
    try:
        # 设置环境变量
        os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
        
        # 导入main模块
        import main
        if hasattr(main, 'Application'):
            print("直接启动Application类...")
            app = main.Application()
            app.mainloop()
        else:
            print("主模块结构不正确，无法直接运行")
            print("请尝试直接运行: python main.py")
    except Exception as e:
        print(f"直接运行主程序失败: {e}")
        print("错误详情:", str(e))
        print("请尝试直接运行: python main.py")

if __name__ == "__main__":
    main()
    # 程序结束时暂停
    input("按Enter键退出...") 