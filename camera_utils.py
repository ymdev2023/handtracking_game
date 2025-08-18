#!/usr/bin/env python3
"""
카메라 호환성 유틸리티
- 표준 USB 웹캠
- 라즈베리파이 카메라 모듈 (CSI)
- Arducam 모듈 지원
"""

import cv2
import os
import subprocess
import time

class CameraManager:
    def __init__(self):
        self.camera = None
        self.camera_index = 0
        self.width = 640
        self.height = 480
        self.fps = 30
        
    def detect_arducam(self):
        """Arducam 모듈 감지"""
        try:
            # Arducam 관련 장치 확인
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            if 'Arducam' in result.stdout or 'ArduCam' in result.stdout:
                print("📷 Arducam USB 모듈 감지됨")
                return True
                
            # dmesg에서 arducam 관련 메시지 확인
            result = subprocess.run(['dmesg'], capture_output=True, text=True)
            if 'arducam' in result.stdout.lower():
                print("📷 Arducam 모듈 감지됨 (dmesg)")
                return True
                
        except Exception as e:
            print(f"Arducam 감지 중 오류: {e}")
            
        return False
        
    def detect_raspberry_pi_camera(self):
        """라즈베리파이 CSI 카메라 감지"""
        try:
            # vcgencmd를 사용한 카메라 감지
            result = subprocess.run(['vcgencmd', 'get_camera'], capture_output=True, text=True)
            if 'detected=1' in result.stdout:
                print("📷 라즈베리파이 CSI 카메라 감지됨")
                return True
        except Exception:
            pass
            
        # /opt/vc/bin/vcgencmd 경로 시도
        try:
            result = subprocess.run(['/opt/vc/bin/vcgencmd', 'get_camera'], capture_output=True, text=True)
            if 'detected=1' in result.stdout:
                print("📷 라즈베리파이 CSI 카메라 감지됨")
                return True
        except Exception:
            pass
            
        return False
        
    def find_camera_devices(self):
        """사용 가능한 카메라 장치 찾기"""
        camera_devices = []
        
        # /dev/video* 장치 확인
        for i in range(10):
            if os.path.exists(f'/dev/video{i}'):
                camera_devices.append(i)
                
        print(f"📷 감지된 비디오 장치: {camera_devices}")
        return camera_devices
        
    def test_camera_device(self, device_index):
        """특정 카메라 장치 테스트"""
        try:
            cap = cv2.VideoCapture(device_index)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    print(f"✅ 카메라 장치 {device_index} 작동 확인")
                    return True
            else:
                print(f"❌ 카메라 장치 {device_index} 열기 실패")
        except Exception as e:
            print(f"❌ 카메라 장치 {device_index} 테스트 실패: {e}")
            
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
        print("📷 카메라 초기화 시작...")
        
        # 1. Arducam 감지 및 초기화 시도
        if self.detect_arducam():
            camera_devices = self.find_camera_devices()
            for device_index in camera_devices:
                print(f"🔧 Arducam 장치 {device_index} 초기화 시도...")
                self.camera = self.initialize_arducam(device_index)
                if self.camera is not None:
                    self.camera_index = device_index
                    return self.camera
                    
        # 2. 라즈베리파이 CSI 카메라 시도
        if self.detect_raspberry_pi_camera():
            print("🔧 라즈베리파이 CSI 카메라 초기화 시도...")
            self.camera = self.initialize_standard_camera(0)
            if self.camera is not None:
                self.camera_index = 0
                return self.camera
                
        # 3. 표준 USB 카메라들 순차 시도
        camera_devices = self.find_camera_devices()
        for device_index in camera_devices:
            if self.test_camera_device(device_index):
                print(f"🔧 표준 카메라 {device_index} 초기화 시도...")
                self.camera = self.initialize_standard_camera(device_index)
                if self.camera is not None:
                    self.camera_index = device_index
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
