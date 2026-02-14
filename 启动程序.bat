@echo off
title BananaSplit-AI 启动器
echo ==========================================
echo 🚀 正在启动 BananaSplit-AI Web 界面...
echo ==========================================
echo.

:: 检查是否安装了 streamlit
streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 streamlit。请先安装依赖：
    echo pip install -r requirements.txt
    pause
    exit /b
)

:: 启动程序
streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 程序运行出错，请检查控制台报错信息。
    pause
)
