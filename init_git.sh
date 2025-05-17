#!/bin/bash

# 初始化Git仓库
echo "初始化Git仓库..."
git init

# 添加所有文件
echo "添加文件到Git..."
git add .

# 提交初始代码
echo "提交初始代码..."
git commit -m "初始提交：快手账号管理工具"

# 创建main分支
echo "创建main分支..."
git branch -M main

# 设置远程仓库
echo "请输入GitHub仓库URL (例如: https://github.com/username/repo.git):"
read repo_url

if [ -z "$repo_url" ]; then
  echo "未提供仓库URL，跳过远程仓库设置。"
  echo "请手动设置远程仓库并推送代码："
  echo "git remote add origin 您的仓库URL"
  echo "git push -u origin main"
else
  echo "设置远程仓库..."
  git remote add origin $repo_url
  
  echo "推送代码到GitHub..."
  git push -u origin main
  
  echo "完成！代码已推送到GitHub仓库。"
  echo "请访问GitHub仓库页面，点击'Actions'选项卡，手动触发打包工作流。"
fi 