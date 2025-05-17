import os
import subprocess
import sys
import platform
import shutil

def is_ci_environment():
    """检查是否在CI环境中运行"""
    return os.environ.get('CI', 'false').lower() == 'true' or os.environ.get('GITHUB_ACTIONS', 'false').lower() == 'true'

def package_application():
    """使用PyInstaller将应用程序打包成EXE"""
    
    print("快手账号管理工具打包程序")
    print("=" * 50)
    print("准备打包应用程序...")
    
    # 检查是否在CI环境中运行
    ci_mode = is_ci_environment()
    if ci_mode:
        print("检测到CI环境，将以非交互模式运行")
    
    # 确保安装了PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
    except ImportError:
        print("✗ 未检测到PyInstaller，尝试安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller安装成功")
        except Exception as e:
            print(f"✗ 安装PyInstaller失败: {e}")
            print("请手动安装PyInstaller: pip install pyinstaller")
            if not ci_mode:
                input("\n按Enter键退出...")
            return
    
    # 检查其他必要的依赖
    required_packages = ['playwright', 'requests']
    missing_packages = []
    
    print("\n检查必要的依赖...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"✗ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n缺少必要的依赖包，尝试安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✓ 所有依赖安装完成")
        except Exception as e:
            print(f"✗ 安装依赖失败: {e}")
            print("请手动安装以下依赖:")
            for package in missing_packages:
                print(f"  pip install {package}")
            if not ci_mode:
                input("\n按Enter键退出...")
            return
    
    # 确保配置文件存在
    print("\n检查配置文件...")
    config_files = ['curl_config.json']
    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"✗ 未找到配置文件 {config_file}，将创建默认配置")
            if config_file == 'curl_config.json':
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write('''{
  "base_url": "http://192.168.1.34:8082",
  "default_headers": {
    "Content-Type": "application/json",
    "X-Client": "FacebookAdsManager/1.0"
  },
  "timeout": 30,
  "endpoints": {
    "account": "index.php/admin/Dashboard/account"
  }
}''')
                print(f"✓ 已创建默认 {config_file}")
        else:
            print(f"✓ 配置文件 {config_file} 已存在")
    
    # 创建accounts目录（如果不存在）
    if not os.path.exists("accounts"):
        os.makedirs("accounts")
        print("✓ 已创建accounts目录")
    
    # 创建requirements.txt（如果不存在）
    if not os.path.exists("requirements.txt"):
        with open("requirements.txt", 'w', encoding='utf-8') as f:
            f.write("playwright>=1.30.0\nrequests>=2.28.0")
        print("✓ 已创建requirements.txt")
    
    # 创建spec文件内容
    print("\n创建打包配置...")
    if platform.system() == "Darwin":  # macOS
        # macOS版本，包含修复脚本
        spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('mac_fix.py', '.'),
        ('curl_config.json', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'playwright', 
        'requests', 
        'tkinter', 
        'tkinter.ttk', 
        'tkinter.scrolledtext', 
        'tkinter.filedialog', 
        'tkinter.messagebox',
        'urllib.parse',
        'json',
        'datetime',
        'threading',
        'queue',
        'platform',
        'asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='快手账号管理工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
        """
    else:
        # Windows/Linux版本
        spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('curl_config.json', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'playwright', 
        'requests', 
        'tkinter', 
        'tkinter.ttk', 
        'tkinter.scrolledtext', 
        'tkinter.filedialog', 
        'tkinter.messagebox',
        'urllib.parse',
        'json',
        'datetime',
        'threading',
        'queue',
        'platform',
        'asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='快手账号管理工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
        """
    
    # 写入spec文件
    with open("kuaishou.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    print("✓ 已创建打包配置文件")
    
    print("\n开始打包应用程序...")
    print("=" * 50)
    
    # 执行打包命令
    try:
        subprocess.check_call([sys.executable, "-m", "PyInstaller", "kuaishou.spec", "--clean"])
        print("\n✓ 打包完成！")
        
        # 创建dist/accounts目录
        dist_accounts_dir = os.path.join("dist", "accounts")
        if not os.path.exists(dist_accounts_dir):
            os.makedirs(dist_accounts_dir)
            print("✓ 已创建dist/accounts目录")
        
        # 添加特定于平台的提示
        if platform.system() == "Darwin":
            print("\n可执行文件位于: dist/快手账号管理工具")
            print("\nMacOS用户注意:")
            print("为了避免IMK警告，请使用终端运行打包后的应用程序:")
            print("./dist/快手账号管理工具")
            print("或者使用mac_fix.py启动脚本，它已被包含在打包文件中")
        else:
            print("\n可执行文件位于: dist/快手账号管理工具.exe")
            
            # 创建启动批处理文件
            with open("dist/启动快手账号管理工具.bat", "w", encoding="utf-8") as f:
                f.write('@echo off\necho 正在启动快手账号管理工具...\ncd /d "%~dp0"\n快手账号管理工具.exe\npause')
            print("✓ 已创建启动批处理文件: dist/启动快手账号管理工具.bat")
        
        # 提醒用户安装Playwright浏览器
        print("\n重要提示：首次运行前，请确保已安装Playwright浏览器")
        print("请在命令行中运行: playwright install")
        
        print("\n打包后的文件说明:")
        print("- 主程序: 快手账号管理工具.exe")
        print("- 配置文件: curl_config.json (可根据需要修改API地址)")
        print("- 账号数据目录: accounts/ (用于存储账号相关数据)")
        
        if not ci_mode:
            input("\n按Enter键退出...")
    except Exception as e:
        print(f"\n✗ 打包过程出错: {e}")
        if not ci_mode:
            input("\n按Enter键退出...")

if __name__ == "__main__":
    package_application() 