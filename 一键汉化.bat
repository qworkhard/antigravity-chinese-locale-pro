@echo off
chcp 65001 >nul
echo ============================================================
echo   Google Antigravity 简体中文深度全量汉化 (v3.0 Pro)
echo ============================================================
echo.
echo [*] 正在检查 Python 运行环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请确保已安装 Python 3.8+ 并添加至环境变量 PATH。
    pause
    exit /b 1
)

echo [*] 正在执行汉化部署引擎...
python "%~dp0scripts\deploy_chinese.py"
echo.
pause
