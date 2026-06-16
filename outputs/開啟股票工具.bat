@echo off
chcp 65001 >nul
echo 正在啟動股票估價工具...
echo.

:: 找 Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON=python
    goto :start
)
py --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON=py
    goto :start
)
echo 找不到 Python，請先安裝 Python 3
pause
exit /b 1

:start
:: 切到 outputs 資料夾
cd /d "%~dp0"

:: 開啟瀏覽器（等 1 秒讓伺服器先啟動）
start "" cmd /c "timeout /t 1 >nul && start http://localhost:8765/stock-valuation.html"

:: 啟動伺服器（關閉此視窗即停止）
echo 伺服器已啟動：http://localhost:8765/stock-valuation.html
echo 關閉此視窗即停止伺服器
echo.
%PYTHON% -m http.server 8765

pause
