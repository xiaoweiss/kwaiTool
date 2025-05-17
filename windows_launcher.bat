@echo off
echo ======================================
echo 快手账号管理工具启动器
echo ======================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查exe文件是否存在
if not exist "快手账号管理工具.exe" (
    echo 错误: 未找到快手账号管理工具.exe文件！
    echo 请确保此批处理文件与快手账号管理工具.exe在同一目录。
    goto end
)

:: 检查accounts目录是否存在，不存在则创建
if not exist "accounts" (
    echo 创建accounts目录...
    mkdir accounts
)

echo 启动快手账号管理工具...
echo.
echo 如果程序首次运行，可能需要安装Playwright浏览器。
echo 请在命令行中运行: playwright install
echo.
echo 正在启动程序，请稍候...

:: 运行主程序
"快手账号管理工具.exe"

:end
echo.
echo 程序已退出。
pause 