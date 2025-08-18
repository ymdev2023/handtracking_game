#!/bin/bash
# 라즈베리파이에서 Hand Tracking Game 실행 스크립트

echo "🎮 Hand Tracking Game 시작 중..."

# 현재 디렉토리 확인
if [[ ! -f "game_launcher.py" ]]; then
    echo "❌ 게임 파일을 찾을 수 없습니다. handtracking_game 폴더에서 실행하세요."
    exit 1
fi

# 가상환경 활성화
if [[ -d ".venv" ]]; then
    echo "🔧 가상환경 활성화 중..."
    source .venv/bin/activate
else
    echo "❌ 가상환경을 찾을 수 없습니다. 설치를 먼저 완료하세요."
    exit 1
fi

# 카메라 권한 확인
if [[ ! -r "/dev/video0" ]]; then
    echo "⚠️ 카메라 접근 권한이 없습니다. 카메라를 연결하고 권한을 확인하세요."
fi

# 성능 최적화 설정 (임시)
export MEDIAPIPE_DISABLE_GPU=1
export OPENCV_LOG_LEVEL=ERROR

# 게임 실행
echo "🚀 게임 런처 실행..."
python game_launcher.py

echo "🎮 게임이 종료되었습니다."
