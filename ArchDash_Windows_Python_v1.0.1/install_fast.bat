@echo off
echo ============================================
echo     ArchDash 快速安装脚本 (国内镜像)
echo ============================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo [信息] 使用清华大学镜像加速安装
python -m venv venv
call venv\Scripts\activate.bat
pip install -r src\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo [完成] 创建启动脚本
(
echo @echo off
echo call venv\Scripts\activate.bat
echo cd src
echo python app.py
echo pause
) > start_ArchDash.bat

echo.
echo 安装完成！双击 start_ArchDash.bat 启动应用
pause
