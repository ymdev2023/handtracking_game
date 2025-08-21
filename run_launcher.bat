@echo off
REM 게임 런처 실행 스크립트 (GUI)
REM 더블클릭으로 가상환경 활성화 + GUI 런처 실행

echo.
echo ==========================================
echo         게임 런처 (Game Launcher)
echo ==========================================
echo.

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"

REM .venv 폴더 존재 확인
if not exist ".venv\" (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo 📁 .venv 폴더가 없습니다.
    echo.
    echo 💡 activate_venv.bat를 먼저 실행하여 가상환경을 설정하세요.
    echo.
    pause
    exit /b 1
)

echo 🔍 가상환경 활성화 중...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패!
    pause
    exit /b 1
)

echo ✅ 가상환경 활성화 완료!
echo 🚀 GUI 게임 런처를 시작합니다...
echo.

REM GUI 런처 실행
python game_launcher.py

echo.
echo 🎯 게임 런처가 종료되었습니다.
pause
