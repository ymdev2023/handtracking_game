#!/bin/bash
# 라즈베리파이4 최적화 스크립트

echo "🚀 라즈베리파이4 Hand Tracking Game 최적화 시작..."

# GPU 메모리 분할 설정
echo "⚙️ GPU 메모리 설정..."
if ! grep -q "gpu_mem=128" /boot/config.txt; then
    echo "gpu_mem=128" | sudo tee -a /boot/config.txt
fi

# CPU 성능 최적화
echo "🔧 CPU 성능 최적화..."
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 스왑 메모리 최적화
echo "💾 스왑 메모리 최적화..."
sudo sysctl vm.swappiness=10

# 카메라 활성화
echo "📷 카메라 모듈 활성화..."
sudo raspi-config nonint do_camera 0

# 오디오 설정
echo "🔊 오디오 설정..."
sudo usermod -a -G audio $USER

# 권한 설정
echo "🔐 권한 설정..."
sudo usermod -a -G video $USER
sudo usermod -a -G input $USER

# 불필요한 서비스 비활성화 (선택사항)
echo "🚫 불필요한 서비스 비활성화..."
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# 완료 메시지
echo "✅ 최적화 완료! 재부팅 후 게임을 실행하세요."
echo "📝 재부팅: sudo reboot"
echo "🎮 게임 실행: cd ~/handtracking_game && source .venv/bin/activate && python game_launcher.py"
