@echo off
REM 핸드 트래킹 게임 가상환경 활성화 스크립트
REM 더블클릭으로 가상환경 활성화 + 명령 프롬프트 열기

echo.
echo ============================================
echo    핸드 트래킹 게임 가상환경 활성화
echo ============================================
echo.

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"

REM .venv 폴더 존재 확인
if not exist ".venv\" (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo 📁 .venv 폴더가 없습니다.
    echo.
    echo 💡 다음 명령어로 가상환경을 생성하세요:
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

echo ✅ 가상환경이 활성화되었습니다!
echo.
echo 🎮 사용 가능한 명령어:
echo    python student_moving_game.py  - 학생 이동 게임
echo    python food_eating_game.py     - 음식 먹기 게임
echo    python game_launcher.py        - 게임 런처 (GUI)
echo    pip install -r requirements.txt - 패키지 설치
echo    deactivate                      - 가상환경 종료
echo.

REM 새로운 명령 프롬프트 창을 열어서 가상환경 유지
cmd /k "echo 🎯 가상환경이 활성화된 상태입니다. 게임을 실행하세요!"
