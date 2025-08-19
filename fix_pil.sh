#!/bin/bash
# PIL/Pillow 설치 문제 해결 스크립트

echo "🔧 PIL/Pillow 설치 문제 해결 중..."

# Python 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️ 가상환경이 활성화되지 않았습니다."
    if [[ -d ".venv" ]]; then
        echo "🔧 가상환경 활성화 중..."
        source .venv/bin/activate
    else
        echo "🔧 가상환경 생성 중..."
        python3 -m venv .venv
        source .venv/bin/activate
    fi
fi

# Pillow 설치
echo "📦 Pillow 설치 중..."
pip install --upgrade pip
pip install Pillow

# OpenCV와 MediaPipe 설치
echo "📦 기본 패키지 설치 중..."
pip install opencv-python mediapipe pygame numpy

# 라즈베리파이 특별 처리
if [[ $(uname -m) == "armv7l" ]] || [[ $(uname -m) == "aarch64" ]]; then
    echo "🍓 라즈베리파이 감지 - 특별 설치 중..."
    
    # 시스템 패키지 설치
    sudo apt update
    sudo apt install -y python3-pil python3-pil.imagetk
    sudo apt install -y python3-opencv python3-numpy
    
    # pip으로 추가 설치
    pip install --upgrade pillow
fi

# 설치 확인
echo "✅ 설치 확인 중..."
python3 -c "
try:
    from PIL import Image, ImageDraw, ImageFont
    print('✅ PIL/Pillow 설치 성공!')
except ImportError as e:
    print(f'❌ PIL 설치 실패: {e}')
    
try:
    import cv2
    print('✅ OpenCV 설치 성공!')
except ImportError as e:
    print(f'❌ OpenCV 설치 실패: {e}')
    
try:
    import mediapipe
    print('✅ MediaPipe 설치 성공!')
except ImportError as e:
    print(f'❌ MediaPipe 설치 실패: {e}')
    
try:
    import pygame
    print('✅ Pygame 설치 성공!')
except ImportError as e:
    print(f'❌ Pygame 설치 실패: {e}')
"

echo "🎮 이제 게임을 실행해보세요: ./run_game.sh"
