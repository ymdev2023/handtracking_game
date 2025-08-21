@echo off
REM 학생 이동 게임 실행 스크립트
REM 더블클릭으로 가상환경 활성화 + 게임 실행

echo.
echo ==========================================
echo      학생 이동 게임 (Student Moving Game)
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
echo 🎮 학생 이동 게임을 시작합니다...
echo.

REM 게임 실행
python student_moving_game.py

echo.
echo 🎯 게임이 종료되었습니다.
pause
