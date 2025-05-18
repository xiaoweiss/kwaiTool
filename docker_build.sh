#!/bin/bash
echo "======================================"
echo "快手账号管理工具 - Docker Windows打包脚本"
echo "======================================"
echo ""

echo "正在启动Docker打包脚本..."
python3 docker_build.py

echo ""
echo "如果脚本已经结束，请按Enter键退出..."
read 