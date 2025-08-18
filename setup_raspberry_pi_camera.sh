#!/bin/bash

# 라즈베리파이 카메라 자동 설정 스크립트

echo "🚀 라즈베리파이 카메라 자동 설정 시작"
echo "============================================"

# 루트 권한 확인
if [ "$EUID" -ne 0 ]; then
    echo "❌ 이 스크립트는 root 권한이 필요합니다."
    echo "sudo bash setup_raspberry_pi_camera.sh 로 실행하세요"
    exit 1
fi

# 라즈베리파이 확인
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️ 라즈베리파이가 아닌 것 같습니다. 계속 진행하시겠습니까? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 필수 패키지 설치..."
apt update
apt install -y v4l-utils python3-opencv python3-pip i2c-tools

# GStreamer 관련 패키지 설치 (Arducam CSI 지원)
echo "📦 GStreamer 패키지 설치 (Arducam CSI 지원)..."
apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libav

# libcamera 설치 (최신 라즈베리파이 OS)
echo "📦 libcamera 설치 (최신 카메라 지원)..."
apt install -y libcamera-apps libcamera-dev || echo "⚠️ libcamera 설치 실패 (구버전 OS일 수 있음)"

echo "👤 사용자를 video 그룹에 추가..."
# 현재 sudo를 실행한 실제 사용자 찾기
REAL_USER=${SUDO_USER:-$USER}
if [ "$REAL_USER" != "root" ]; then
    usermod -a -G video "$REAL_USER"
    echo "✅ 사용자 '$REAL_USER'를 video 그룹에 추가했습니다"
else
    echo "⚠️ 실제 사용자를 찾을 수 없습니다. 수동으로 추가하세요: usermod -a -G video [사용자명]"
fi

echo "⚙️ 카메라 설정 확인 및 수정..."

# config.txt 파일 찾기
CONFIG_FILE=""
if [ -f "/boot/firmware/config.txt" ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f "/boot/config.txt" ]; then
    CONFIG_FILE="/boot/config.txt"
else
    echo "❌ config.txt 파일을 찾을 수 없습니다"
    exit 1
fi

echo "📝 $CONFIG_FILE 수정 중..."

# 백업 생성
cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ 설정 파일 백업 완료: $CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"

# GPU 메모리 설정
if ! grep -q "^gpu_mem=" "$CONFIG_FILE"; then
    echo "gpu_mem=128" >> "$CONFIG_FILE"
    echo "✅ GPU 메모리를 128MB로 설정"
else
    # 기존 gpu_mem 값 업데이트
    sed -i 's/^gpu_mem=.*/gpu_mem=128/' "$CONFIG_FILE"
    echo "✅ GPU 메모리를 128MB로 업데이트"
fi

# 카메라 자동 감지 활성화
if ! grep -q "^camera_auto_detect=" "$CONFIG_FILE"; then
    echo "camera_auto_detect=1" >> "$CONFIG_FILE"
    echo "✅ 카메라 자동 감지 활성화"
else
    sed -i 's/^camera_auto_detect=.*/camera_auto_detect=1/' "$CONFIG_FILE"
    echo "✅ 카메라 자동 감지 업데이트"
fi

# 레거시 카메라 지원 (필요한 경우)
if ! grep -q "^start_x=" "$CONFIG_FILE"; then
    echo "start_x=1" >> "$CONFIG_FILE"
    echo "✅ 레거시 카메라 지원 활성화"
fi

# dtoverlay 설정 확인 및 Arducam 지원 추가
if ! grep -q "dtoverlay.*camera" "$CONFIG_FILE"; then
    echo "# CSI 카메라 모듈 지원" >> "$CONFIG_FILE"
    echo "dtoverlay=ov5647" >> "$CONFIG_FILE"
    echo "dtoverlay=imx219" >> "$CONFIG_FILE" 
    echo "dtoverlay=imx477" >> "$CONFIG_FILE"
    echo "dtoverlay=imx708" >> "$CONFIG_FILE"
    echo "✅ 카메라 오버레이 설정 추가 (OV5647, IMX219, IMX477, IMX708)"
fi

# I2C 활성화 (Arducam 센서 통신용)
if ! grep -q "^dtparam=i2c_arm=on" "$CONFIG_FILE"; then
    echo "dtparam=i2c_arm=on" >> "$CONFIG_FILE"
    echo "✅ I2C 활성화 (Arducam 센서 통신용)"
else
    sed -i 's/^dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' "$CONFIG_FILE"
fi

# Arducam 특화 설정
echo "# Arducam 특화 설정" >> "$CONFIG_FILE"
echo "disable_camera_led=1" >> "$CONFIG_FILE"  # 카메라 LED 비활성화 (선택사항)
echo "✅ Arducam 특화 설정 추가"

echo "🔧 권한 설정..."
# /dev/video* 권한 설정
if [ -e /dev/video0 ]; then
    chmod 666 /dev/video*
    echo "✅ 비디오 장치 권한 설정 완료"
fi

echo "📋 현재 설정 확인..."
echo "--- GPU 메모리 ---"
vcgencmd get_mem gpu 2>/dev/null || echo "vcgencmd 명령어 없음"

echo "--- 카메라 감지 ---"
vcgencmd get_camera 2>/dev/null || echo "vcgencmd 명령어 없음"

echo "--- I2C 장치 스캔 (Arducam 센서 확인) ---"
i2cdetect -y 1 2>/dev/null || echo "I2C 스캔 실패"

echo "--- 비디오 장치 ---"
ls -la /dev/video* 2>/dev/null || echo "비디오 장치 없음"

echo "--- V4L2 장치 ---"
v4l2-ctl --list-devices 2>/dev/null || echo "v4l2-ctl 실행 불가"

echo "--- libcamera 확인 ---"
libcamera-hello --list-cameras --timeout 1 2>/dev/null || echo "libcamera 명령어 없음"

echo ""
echo "✅ 라즈베리파이 카메라 설정 완료!"
echo ""
echo "🔄 설정을 적용하려면 재부팅이 필요합니다:"
echo "   sudo reboot"
echo ""
echo "🧪 재부팅 후 테스트:"
echo "   python3 raspberry_pi_camera_test.py"
echo ""
echo "📁 백업된 원본 설정:"
echo "   $CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
