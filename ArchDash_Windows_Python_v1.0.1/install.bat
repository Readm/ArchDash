@echo off
echo ============================================
echo     ArchDash Windows 安装脚本 v1.0.1
echo ============================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8或更高版本
    echo.
    echo 请访问 https://www.python.org/downloads/ 下载并安装Python
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [信息] 检测到Python环境
python --version

echo.
echo [步骤1] 创建虚拟环境...
python -m venv venv
if %errorlevel% neq 0 (
    echo [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

echo [步骤2] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
pip install -r src\requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

echo [步骤3] 创建启动脚本...
(
echo @echo off
echo call venv\Scripts\activate.bat
echo cd src
echo echo 正在启动ArchDash...
echo echo 请等待应用加载完成后，在浏览器中访问 http://127.0.0.1:8050
echo echo 按 Ctrl+C 停止应用程序
echo echo.
echo python app.py
echo pause
) > start_ArchDash.bat

echo.
echo ============================================
echo          安装完成！
echo ============================================
echo.
echo 使用方法：
echo 1. 双击 start_ArchDash.bat 启动应用
echo 2. 在浏览器中访问 http://127.0.0.1:8050
echo.
echo 注意：首次启动可能需要较长时间加载
echo.
pause
