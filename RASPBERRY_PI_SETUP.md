# 라즈베리파이4에서 Hand Tracking Game 실행하기

## 시스템 요구사항
- 라즈베리파이 4 (4GB RAM 이상 권장)
- Raspberry Pi OS (Bullseye 64-bit 권장)
- USB 웹캠 또는 라즈베리파이 카메라 모듈
- 인터넷 연결

## 1. 시스템 업데이트
```bash
sudo apt update
sudo apt upgrade -y
```

## 2. 필수 패키지 설치
```bash
# Python 개발 도구
sudo apt install -y python3-pip python3-venv python3-dev

# OpenCV 의존성
sudo apt install -y libopencv-dev python3-opencv

# 오디오 지원
sudo apt install -y pulseaudio pulseaudio-utils

# 기타 필수 라이브러리
sudo apt install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt install -y libjasper-dev libfontconfig1-dev libcairo2-dev
sudo apt install -y libgdk-pixbuf2.0-dev libpango1.0-dev
sudo apt install -y libgtk2.0-dev libgtk-3-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
sudo apt install -y libpng-dev libjpeg-dev libtiff-dev
```

## 3. 프로젝트 클론
```bash
cd ~
git clone https://github.com/ymdev2023/handtracking_game.git
cd handtracking_game
```

## 4. 가상환경 생성 및 활성화
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 5. Python 패키지 설치
```bash
# 기본 패키지 설치
pip install --upgrade pip
pip install wheel setuptools

# 게임 의존성 설치
pip install -r requirements_raspi.txt
```

## 6. 카메라 권한 설정
```bash
# 카메라 그룹에 사용자 추가
sudo usermod -a -G video $USER

# 재부팅 후 적용됨
sudo reboot
```

## 7. 게임 실행
```bash
cd ~/handtracking_game
source .venv/bin/activate
python game_launcher.py
```

## 성능 최적화 설정

### GPU 메모리 할당 증가
```bash
sudo raspi-config
# Advanced Options → Memory Split → 128 또는 256으로 설정
```

### CPU 성능 모드 설정
```bash
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## 문제 해결

### 카메라가 인식되지 않는 경우
```bash
# USB 카메라 확인
lsusb | grep -i camera

# 비디오 장치 확인
ls /dev/video*

# 카메라 테스트
ffmpeg -f v4l2 -list_formats all -i /dev/video0
```

### 오디오가 나오지 않는 경우
```bash
# 오디오 장치 확인
aplay -l

# PulseAudio 재시작
pulseaudio --kill
pulseaudio --start
```

### 성능이 느린 경우
- 해상도를 낮춤 (640x480 권장)
- FPS 제한 (15-20 FPS)
- 불필요한 백그라운드 프로세스 종료

## 자동 실행 설정 (선택사항)
```bash
# 데스크톱 파일 생성
cat > ~/Desktop/HandTrackingGame.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Hand Tracking Game
Comment=Hand tracking games using MediaPipe
Exec=/home/pi/handtracking_game/.venv/bin/python /home/pi/handtracking_game/game_launcher.py
Icon=/home/pi/handtracking_game/game_icon.png
Terminal=true
StartupNotify=true
EOF

chmod +x ~/Desktop/HandTrackingGame.desktop
```
