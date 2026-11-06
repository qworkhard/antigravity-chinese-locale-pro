@echo off
chcp 65001 >nul
echo ============================================================
echo   Google Antigravity 官方原版一键无损还原
echo ============================================================
echo.
echo [*] 正在还原官方纯净 app.asar...
python "%~dp0scripts\restore_original.py"
echo.
pause
