@echo off
REM 패키지 설치 스크립트
REM 더블클릭으로 가상환경 활성화 + requirements.txt 설치

echo.
echo ==========================================
echo       패키지 설치 (Install Packages)
echo ==========================================
echo.

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"

REM .venv 폴더 존재 확인
if not exist ".venv\" (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo 📁 .venv 폴더가 없습니다.
    echo.
    echo 💡 먼저 가상환경을 생성하세요:
    echo    python -m venv .venv
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
echo.

REM requirements.txt 파일 존재 확인
if not exist "requirements.txt" (
    echo ❌ requirements.txt 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)

echo 📦 패키지 설치를 시작합니다...
echo 🔄 pip를 최신 버전으로 업그레이드...
python -m pip install --upgrade pip

echo.
echo 📋 requirements.txt에서 패키지 설치 중...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 패키지 설치 중 오류가 발생했습니다!
    pause
    exit /b 1
)

echo.
echo ✅ 모든 패키지가 성공적으로 설치되었습니다!
echo 🎮 이제 게임을 실행할 수 있습니다.
echo.
echo 💡 게임 실행 방법:
echo    - run_student_game.bat (학생 이동 게임)
echo    - run_food_game.bat (음식 먹기 게임)  
echo    - run_launcher.bat (GUI 런처)
echo.
pause
