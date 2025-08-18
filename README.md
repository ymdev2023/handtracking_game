# 🎮 Hand Tracking Games

MediaPipe와 OpenCV를 사용한 핸드 트래킹 게임 모음입니다.

## 🎯 게임 목록

1. **학생 이동 게임** (`student_moving_game.py`)
   - 하트 제스처로 시작
   - 핀치 제스처로 캐릭터 드래그
   - 30초 안에 최대한 많은 캐릭터를 목표 구역으로 이동

2. **음식 먹기 게임** (`food_eating_game.py`)
   - 입을 벌려서 음식 먹기
   - 점수 시스템
   - 파티클 효과

3. **게임 런처** (`game_launcher.py`)
   - 게임 선택 GUI
   - 전체화면 지원

## 🖥️ 지원 플랫폼

- ✅ **macOS** (Intel/Apple Silicon)
- ✅ **라즈베리파이** (CSI 카메라, USB 웹캠, **Arducam CSI 모듈**)
- ✅ **Linux** (일반 배포판)

### 🎯 지원 카메라 모듈

**라즈베리파이:**
- 📷 **Arducam CSI 카메라** (OV5647, IMX219, IMX477, IMX708)
- 📷 공식 라즈베리파이 카메라 (v1, v2, HQ)
- 🔌 USB 웹캠 (UVC 호환)

**기타 플랫폼:**
- 🔌 표준 USB 웹캠

## 📦 설치 방법

### 기본 설치

```bash
# 저장소 클론
git clone https://github.com/ymdev2023/handtracking_game.git
cd handtracking_game

# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 라즈베리파이 특별 설치

라즈베리파이에서는 추가 설정이 필요합니다 (Arducam CSI 포함):

```bash
# 1. 자동 설정 스크립트 실행 (권장) - Arducam CSI 지원 포함
sudo bash setup_raspberry_pi_camera.sh

# 2. 재부팅
sudo reboot

# 3. 카메라 테스트 (Arducam 감지 포함)
python3 raspberry_pi_camera_test.py
```

#### 수동 설정 (필요시)

```bash
# 필수 패키지 설치 (Arducam CSI 지원)
sudo apt update
sudo apt install -y v4l-utils python3-opencv i2c-tools
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good
sudo apt install -y libcamera-apps libcamera-dev  # 최신 OS용

# 사용자를 video 그룹에 추가
sudo usermod -a -G video $USER

# 카메라 활성화
sudo raspi-config
# -> Interface Options -> Camera -> Enable
# -> Interface Options -> I2C -> Enable (Arducam용)

# GPU 메모리 설정 (/boot/config.txt 또는 /boot/firmware/config.txt)
echo "gpu_mem=128" | sudo tee -a /boot/config.txt
echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt  # Arducam I2C 통신

# Arducam 센서 오버레이 추가
echo "dtoverlay=ov5647" | sudo tee -a /boot/config.txt   # Arducam OV5647
echo "dtoverlay=imx219" | sudo tee -a /boot/config.txt   # Arducam IMX219
echo "dtoverlay=imx477" | sudo tee -a /boot/config.txt   # Arducam IMX477
echo "dtoverlay=imx708" | sudo tee -a /boot/config.txt   # Arducam IMX708

# 재부팅
sudo reboot
```

## 🚀 실행 방법

### 게임 런처 실행

```bash
python game_launcher.py
```

### 개별 게임 실행

```bash
# 학생 이동 게임
python student_moving_game.py

# 음식 먹기 게임
python food_eating_game.py
```

## 🎮 게임 조작법

### 학생 이동 게임
- **하트 제스처**: 게임 시작/재시작
  - 엄지와 검지를 하트 모양으로 만들기
- **핀치 제스처**: 캐릭터 잡기/놓기
  - 엄지와 검지를 가까이 모으기
- **드래그**: 캐릭터를 목표 구역으로 이동
- **S키**: 스크린샷 저장
- **F11**: 전체화면 토글
- **ESC**: 게임 종료

### 음식 먹기 게임
- **입 벌리기**: 음식 먹기
- **F11**: 전체화면 토글
- **ESC**: 게임 종료

## 🔧 문제 해결

### 카메라 인식 안됨

**macOS:**
```bash
# 카메라 권한 확인
# 시스템 환경설정 -> 보안 및 개인정보 보호 -> 카메라
```

**라즈베리파이:**
```bash
# 진단 도구 실행
python3 raspberry_pi_camera_test.py

# 자동 설정 실행
sudo bash setup_raspberry_pi_camera.sh
sudo reboot
```

### 일반적인 문제들

1. **ModuleNotFoundError: No module named 'cv2'**
   ```bash
   pip install opencv-python
   ```

2. **MediaPipe 설치 오류**
   ```bash
   pip install mediapipe --upgrade
   ```

3. **라즈베리파이 카메라 "cannot open camera"**
   ```bash
   # 카메라 모듈 활성화 확인
   vcgencmd get_camera
   
   # Arducam 센서 I2C 확인
   i2cdetect -y 1
   
   # video 그룹 확인
   groups $USER
   
   # 권한 문제시
   sudo chmod 666 /dev/video*
   
   # libcamera 테스트 (최신 OS)
   libcamera-hello --list-cameras
   ```

4. **Arducam CSI 카메라 특별 문제**
   ```bash
   # Device Tree 확인
   ls -la /proc/device-tree/soc/i2c@7e804000/
   
   # 커널 모듈 확인
   lsmod | grep bcm2835
   
   # GStreamer 테스트
   gst-launch-1.0 libcamerasrc ! autovideosink
   ```

4. **성능 저하 (라즈베리파이)**
   - GPU 메모리를 128MB 이상으로 설정
   - 해상도를 640x480으로 제한
   - 불필요한 프로세스 종료

## 📁 파일 구조

```
handtracking_game/
├── game_launcher.py           # 게임 선택 런처
├── student_moving_game.py     # 학생 이동 게임
├── food_eating_game.py        # 음식 먹기 게임
├── camera_utils.py            # 카메라 호환성 유틸리티
├── raspberry_pi_camera_test.py # 라즈베리파이 카메라 진단
├── setup_raspberry_pi_camera.sh # 라즈베리파이 자동 설정
├── requirements.txt           # Python 패키지 목록
├── cha/                      # 캐릭터 이미지들
├── neodgm.ttf               # 한글 폰트
└── high_score.json          # 최고 점수 저장
```

## 🎨 커스터마이징

### 캐릭터 교체
`cha/` 폴더의 이미지 파일들을 교체하면 됩니다.
- 권장 크기: 24x16 픽셀
- 형식: PNG (투명도 지원)

### 게임 설정 변경
각 게임 파일의 상단에 있는 설정 변수들을 수정할 수 있습니다:

```python
# student_moving_game.py
GAME_TIME = 30  # 게임 시간 (초)
SPAWN_INTERVAL = 2.0  # 캐릭터 생성 간격 (초)
CHARACTER_SCALE = 3.0  # 캐릭터 크기 배율
```

## 🐛 버그 리포트

문제가 발생하면 다음 정보와 함께 이슈를 등록해주세요:
- 운영체제 및 버전
- Python 버전
- 카메라 모델
- 오류 메시지
- `raspberry_pi_camera_test.py` 실행 결과 (라즈베리파이의 경우)

## 📄 라이선스

MIT License

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

- 이슈: https://github.com/ymdev2023/handtracking_game/issues
- 이메일: [연락처]

---

**즐거운 게임하세요! 🎮✨**
