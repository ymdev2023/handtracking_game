#!/bin/bash
# 오프라인 설치용 패키지 생성 스크립트

echo "📦 오프라인 설치 패키지 생성 중..."

# 디렉토리 생성
mkdir -p offline_package
cd offline_package

# 프로젝트 파일 복사
echo "📂 프로젝트 파일 복사 중..."
cp -r ../* . 2>/dev/null || true
rm -f create_offline_package.sh  # 이 스크립트는 제외

# Python 패키지 다운로드 (휠 파일)
echo "🐍 Python 패키지 다운로드 중..."
mkdir -p wheels

# 라즈베리파이용 패키지 다운로드
pip download -r requirements_raspi.txt -d wheels/ --platform linux_aarch64 --only-binary=:all: 2>/dev/null || \
pip download -r requirements_raspi.txt -d wheels/ --platform linux_armv7l --only-binary=:all: 2>/dev/null || \
pip download -r requirements_raspi.txt -d wheels/

# 설치 스크립트 생성
cat > install_offline.sh << 'EOF'
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
EOF

chmod +x install_offline.sh

# 압축 파일 생성
cd ..
echo "🗜️ 압축 파일 생성 중..."
tar -czf handtracking_game_offline.tar.gz offline_package/

echo "✅ 오프라인 패키지 생성 완료!"
echo "📁 파일: handtracking_game_offline.tar.gz"
echo ""
echo "📋 라즈베리파이에서 설치 방법:"
echo "1. tar -xzf handtracking_game_offline.tar.gz"
echo "2. cd offline_package"
echo "3. ./install_offline.sh"
echo "4. ./run_game.sh"
