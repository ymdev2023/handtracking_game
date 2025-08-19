#!/usr/bin/env python3
"""
카메라 호환성 유틸리티
- 표준 USB 웹캠
- 라즈베리파이 카메라 모듈 (CSI)
- Arducam 모듈 지원
"""

import cv2
import                
        if not devices:
            devices = [0]  # 기본값 사용
            
        return devicesort subprocess
import time
import platform

class CameraManager:
    def __init__(self):
        self.camera = None
        self.camera_index = 0
        self.width = 640
        self.height = 480
        self.fps = 30
        self.is_mac = platform.system() == "Darwin"
        self.is_raspberry_pi = os.path.exists('/proc/device-tree/model')
        
    def detect_arducam(self):
        """Arducam 모듈 감지 (Linux/라즈베리파이만)"""
        if self.is_mac:
            # 맥에서는 Arducam 특별 감지 건너뛰기
            return False
            
        try:
            # Arducam 관련 장치 확인 (Linux만)
            if os.path.exists('/usr/bin/lsusb'):
                result = subprocess.run(['lsusb'], capture_output=True, text=True)
                if 'Arducam' in result.stdout or 'ArduCam' in result.stdout:
                    print("📷 Arducam USB 모듈 감지됨")
                    return True
                    
            # dmesg에서 arducam 관련 메시지 확인
            if os.path.exists('/bin/dmesg'):
                result = subprocess.run(['dmesg'], capture_output=True, text=True)
                if 'arducam' in result.stdout.lower():
                    print("📷 Arducam 모듈 감지됨 (dmesg)")
                    return True
                    
        except Exception as e:
            print(f"Arducam 감지 중 오류: {e}")
            
        return False
        
    def detect_raspberry_pi_camera(self):
        """라즈베리파이 CSI 카메라 감지 (라즈베리파이만)"""
        if self.is_mac:
            # 맥에서는 라즈베리파이 카메라 감지 건너뛰기
            return False
            
        if not self.is_raspberry_pi:
            return False
            
        try:
            # vcgencmd를 사용한 카메라 감지
            if os.path.exists('/usr/bin/vcgencmd'):
                result = subprocess.run(['vcgencmd', 'get_camera'], capture_output=True, text=True)
                if 'detected=1' in result.stdout:
                    print("📷 라즈베리파이 CSI 카메라 감지됨")
                    return True
        except Exception:
            pass
            
        # /opt/vc/bin/vcgencmd 경로 시도
        try:
            if os.path.exists('/opt/vc/bin/vcgencmd'):
                result = subprocess.run(['/opt/vc/bin/vcgencmd', 'get_camera'], capture_output=True, text=True)
                if 'detected=1' in result.stdout:
                    print("📷 라즈베리파이 CSI 카메라 감지됨")
                    return True
        except Exception:
            pass
            
        return False
        
    def find_camera_devices(self):
        """모든 플랫폼에서 사용 가능한 카메라 장치 찾기"""
        devices = []
        
        if self.is_mac:
            # macOS에서는 기본 카메라부터 테스트
            print("🍎 macOS 카메라 장치 검색...")
            for i in range(5):  # 0-4까지 테스트
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    cap.release()
                    if ret:
                        devices.append(i)
        else:
            # Linux/라즈베리파이에서는 더 세밀한 검색
            
            # /dev/video* 파일 확인
            for i in range(10):
                video_path = f"/dev/video{i}"
                if os.path.exists(video_path):
                    devices.append(i)
                    
            # lsusb 명령으로 USB 카메라 확인 (Linux만)
            try:
                result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
                usb_devices = result.stdout.lower()
                if 'camera' in usb_devices or 'webcam' in usb_devices or 'video' in usb_devices:
                    pass  # USB 카메라 감지됨
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
                
        if not devices:
            print("⚠️ 카메라 장치를 찾을 수 없음 - 기본값 [0] 사용")
            devices = [0]
            
        print(f"� 총 {len(devices)}개 카메라 장치 발견: {devices}")
        return devices
        
    def test_camera_device(self, device_index):
        """카메라 장치가 실제로 작동하는지 테스트"""
        try:
            cap = cv2.VideoCapture(device_index)
            if not cap.isOpened():
                cap.release()
                return False
                
            # 해상도 설정 시도
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # 몇 프레임 읽어보기
            for _ in range(3):
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    cap.release()
                    print(f"✅ 카메라 {device_index} 테스트 성공")
                    return True
                    
            cap.release()
            return False
            
        except Exception as e:
            print(f"⚠️ 카메라 {device_index} 테스트 중 오류: {e}")
            return False

    def initialize_arducam(self, device_index=0):
        """Arducam 특별 초기화"""
        try:
            # Arducam을 위한 특별 설정
            cap = cv2.VideoCapture(device_index)
            
            if not cap.isOpened():
                # V4L2 백엔드로 재시도
                cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
                
            if cap.isOpened():
                # Arducam 최적화 설정
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                cap.set(cv2.CAP_PROP_FPS, self.fps)
                
                # 버퍼 크기 최소화 (지연 감소)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # 자동 노출 및 화이트 밸런스 설정
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 수동 모드
                cap.set(cv2.CAP_PROP_EXPOSURE, -6)  # 노출 값 조정
                
                print("📷 Arducam 초기화 완료")
                return cap
                
        except Exception as e:
            print(f"❌ Arducam 초기화 실패: {e}")
            
        return None
        
    def initialize_standard_camera(self, device_index=0):
        """표준 카메라 초기화"""
        try:
            cap = cv2.VideoCapture(device_index)
            
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                cap.set(cv2.CAP_PROP_FPS, self.fps)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                print(f"📷 표준 카메라 {device_index} 초기화 완료")
                return cap
                
        except Exception as e:
            print(f"❌ 표준 카메라 초기화 실패: {e}")
            
        return None
        
    def initialize_camera(self):
        """최적의 카메라 초기화"""
        print(f"📷 카메라 초기화 중...")
        
        # 맥에서는 간단한 순서로 시도
        if self.is_mac:
            camera_devices = self.find_camera_devices()
            for device_index in camera_devices:
                if self.test_camera_device(device_index):
                    self.camera = self.initialize_standard_camera(device_index)
                    if self.camera is not None:
                        self.camera_index = device_index
                        print(f"✅ 카메라 {device_index} 초기화 완료!")
                        return self.camera
        else:
            # Linux/라즈베리파이에서는 고급 감지 사용
            
            # 1. Arducam 감지 및 초기화 시도
            if self.detect_arducam():
                camera_devices = self.find_camera_devices()
                for device_index in camera_devices:
                    self.camera = self.initialize_arducam(device_index)
                    if self.camera is not None:
                        self.camera_index = device_index
                        print(f"✅ Arducam {device_index} 초기화 완료!")
                        return self.camera
                        
            # 2. 라즈베리파이 CSI 카메라 시도
            if self.detect_raspberry_pi_camera():
                self.camera = self.initialize_standard_camera(0)
                if self.camera is not None:
                    self.camera_index = 0
                    print(f"✅ 라즈베리파이 CSI 카메라 초기화 완료!")
                    return self.camera
                    
            # 3. 표준 USB 카메라들 순차 시도
            camera_devices = self.find_camera_devices()
            for device_index in camera_devices:
                if self.test_camera_device(device_index):
                    self.camera = self.initialize_standard_camera(device_index)
                    if self.camera is not None:
                        self.camera_index = device_index
                        print(f"✅ 표준 카메라 {device_index} 초기화 완료!")
                        return self.camera
                        
        print("❌ 사용 가능한 카메라를 찾을 수 없습니다.")
        return None
        
    def read_frame(self):
        """프레임 읽기"""
        if self.camera is not None:
            ret, frame = self.camera.read()
            if ret:
                return frame
        return None
        
    def release(self):
        """카메라 해제"""
        if self.camera is not None:
            self.camera.release()
            print("📷 카메라 해제됨")

# 테스트 함수
def test_camera():
    """카메라 테스트"""
    cm = CameraManager()
    camera = cm.initialize_camera()
    
    if camera is None:
        print("❌ 카메라 초기화 실패")
        return False
        
    print("📷 카메라 테스트 시작 (ESC로 종료)")
    
    while True:
        frame = cm.read_frame()
        if frame is not None:
            cv2.imshow('Camera Test', frame)
            
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
            
    cm.release()
    cv2.destroyAllWindows()
    print("✅ 카메라 테스트 완료")
    return True

if __name__ == "__main__":
    test_camera()
