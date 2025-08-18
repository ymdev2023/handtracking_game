#!/bin/bash
# Arducam 카메라 모듈 설정 스크립트

echo "📷 Arducam 카메라 모듈 설정 시작..."

# 시스템 정보 확인
echo "🔍 시스템 정보 확인..."
uname -a
cat /etc/os-release | grep PRETTY_NAME

# 카메라 모듈 활성화
echo "⚙️ 카메라 모듈 활성화..."
sudo raspi-config nonint do_camera 0

# I2C 활성화 (일부 Arducam 모듈에 필요)
echo "⚙️ I2C 활성화..."
sudo raspi-config nonint do_i2c 0

# SPI 활성화 (일부 Arducam 모듈에 필요)
echo "⚙️ SPI 활성화..."
sudo raspi-config nonint do_spi 0

# 필수 패키지 설치
echo "📦 Arducam 관련 패키지 설치..."
sudo apt update
sudo apt install -y v4l-utils
sudo apt install -y python3-opencv
sudo apt install -y libcamera-tools  # 라즈베리파이 OS Bullseye 이상

# Arducam 드라이버 설치 (선택사항)
echo "🔧 Arducam 지원 확인..."

# USB 장치 확인
echo "📋 USB 장치 목록:"
lsusb | grep -i cam
lsusb | grep -i ardu

# 비디오 장치 확인
echo "📋 비디오 장치 목록:"
ls -la /dev/video*

# V4L2 정보 확인
if command -v v4l2-ctl &> /dev/null; then
    echo "📋 V4L2 장치 정보:"
    for device in /dev/video*; do
        if [ -c "$device" ]; then
            echo "=== $device ==="
            v4l2-ctl --device="$device" --info
            echo ""
        fi
    done
fi

# 카메라 테스트
echo "🧪 카메라 테스트..."
python3 - << 'EOF'
import cv2
import sys

print("OpenCV 버전:", cv2.__version__)

# 카메라 장치 찾기
cameras_found = []
for i in range(5):
    try:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                cameras_found.append(i)
                print(f"✅ 카메라 {i}: 작동 확인")
            else:
                print(f"❌ 카메라 {i}: 프레임 읽기 실패")
            cap.release()
        else:
            print(f"❌ 카메라 {i}: 열기 실패")
    except Exception as e:
        print(f"❌ 카메라 {i}: 오류 - {e}")

if cameras_found:
    print(f"🎉 사용 가능한 카메라: {cameras_found}")
else:
    print("⚠️ 사용 가능한 카메라를 찾을 수 없습니다.")
EOF

# 권한 설정
echo "🔐 카메라 권한 설정..."
sudo usermod -a -G video $USER

# GPU 메모리 설정 확인
echo "💾 GPU 메모리 설정 확인..."
if ! grep -q "gpu_mem" /boot/config.txt; then
    echo "gpu_mem=128" | sudo tee -a /boot/config.txt
    echo "✅ GPU 메모리 128MB로 설정됨"
else
    echo "ℹ️ GPU 메모리 설정이 이미 존재합니다."
fi

# Arducam 특별 설정 (필요시)
echo "🔧 Arducam 특별 설정..."

# USB 카메라를 위한 udev 규칙
sudo tee /etc/udev/rules.d/99-arducam.rules > /dev/null << 'EOF'
# Arducam USB 카메라 규칙
SUBSYSTEM=="video4linux", ATTRS{idVendor}=="52cb", MODE="0666", GROUP="video"
SUBSYSTEM=="usb", ATTRS{idVendor}=="52cb", MODE="0666", GROUP="plugdev"
EOF

# udev 규칙 재로드
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "✅ Arducam 설정 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 재부팅: sudo reboot"
echo "2. 카메라 테스트: python3 camera_utils.py"
echo "3. 게임 실행: ./run_game.sh"
echo ""
echo "⚠️ 일부 설정은 재부팅 후 적용됩니다."
