#!/bin/bash
echo "🚀 Hand Tracking Game 오프라인 설치 시작..."

# 시스템 패키지 확인
echo "📋 시스템 요구사항 확인..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    echo "다음 명령어로 설치하세요: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# 가상환경 생성
echo "🔧 가상환경 생성 중..."
python3 -m venv .venv
source .venv/bin/activate

# 오프라인 패키지 설치
echo "📦 패키지 설치 중..."
if [ -d "wheels" ]; then
    pip install --no-index --find-links wheels/ -r requirements_raspi.txt
else
    echo "⚠️ wheels 폴더가 없습니다. 온라인 설치를 시도합니다..."
    pip install -r requirements_raspi.txt
fi

# 권한 설정
echo "🔐 실행 권한 설정..."
chmod +x run_game.sh
chmod +x optimize_raspi.sh

echo "✅ 설치 완료!"
echo "🎮 게임 실행: ./run_game.sh"
echo "⚙️ 시스템 최적화: ./optimize_raspi.sh"
