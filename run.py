@echo off
REM WMIS 运行脚本

echo 微信市场情报自动化系统 (WMIS)
echo =================================

REM 激活虚拟环境（如果有的话）
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM 运行主程序
python main.py

pause
