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
import platform

class CameraManager:
    def __init__(self):
        self.camera = None
        self.camera_index = 0
        self.width = 640
        self.height = 480
        self.fps = 30
        self.is_mac = platform.system() == "Darwin"
        
    def detect_arducam(self):
        """Arducam 모듈 감지"""
        if self.is_mac:
            return False  # macOS에서는 Arducam 지원 안함
            
        # Linux에서만 실행
        try:
            # lsusb로 Arducam 장치 확인
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
            devices = result.stdout.lower()
            
            arducam_keywords = [
                'arducam', 'ov5647', 'imx219', 'imx477', 'imx708',
                'camera module', 'csi camera'
            ]
            
            for keyword in arducam_keywords:
                if keyword in devices:
                    return True
                    
            # /proc/device-tree에서 카메라 확인
            dt_path = "/proc/device-tree/soc/csi@7e800000/port/endpoint"
            if os.path.exists(dt_path):
                return True
                
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
            
        return False
        
    def detect_raspberry_pi_camera(self):
        """라즈베리파이 CSI 카메라 감지"""
        if self.is_mac:
            return False  # macOS에서는 라즈베리파이 CSI 카메라 지원 안함
            
        try:
            # vcgencmd로 카메라 상태 확인
            result = subprocess.run(['vcgencmd', 'get_camera'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout.strip()
                if 'detected=1' in output:
                    return True
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
            
        return False
        
    def find_camera_devices(self):
        """모든 플랫폼에서 사용 가능한 카메라 장치 찾기"""
        devices = []
        
        if self.is_mac:
            # macOS에서는 기본 카메라부터 테스트
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
            devices = [0]  # 기본값 사용
            
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
                    return True
                    
            cap.release()
            return False
            
        except Exception as e:
            return False

    def initialize_arducam(self, device_index=0):
        """Arducam 특별 초기화"""
        try:
            # V4L2 백엔드 강제 사용
            cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
            
            if cap.isOpened():
                # Arducam 특화 설정
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                cap.set(cv2.CAP_PROP_FPS, self.fps)
                
                # 자동 조정 비활성화
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 수동 모드
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # 자동 포커스 비활성화
                
                return cap
                
        except Exception:
            pass
            
        return None
        
    def initialize_standard_camera(self, device_index=0):
        """표준 카메라 초기화"""
        try:
            cap = cv2.VideoCapture(device_index)
            
            if cap.isOpened():
                # 기본 설정
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                cap.set(cv2.CAP_PROP_FPS, self.fps)
                
                return cap
                
        except Exception:
            pass
            
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
        if self.camera is None:
            return False, None
            
        ret, frame = self.camera.read()
        return ret, frame
        
    def release(self):
        """카메라 해제"""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
            
    def get_camera_info(self):
        """카메라 정보 반환"""
        if self.camera is None:
            return None
            
        return {
            'index': self.camera_index,
            'width': int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.camera.get(cv2.CAP_PROP_FPS))
        }

# 편의 함수들
def get_available_cameras():
    """사용 가능한 모든 카메라 반환"""
    manager = CameraManager()
    return manager.find_camera_devices()

def test_camera(device_index):
    """특정 카메라 테스트"""
    manager = CameraManager()
    return manager.test_camera_device(device_index)

if __name__ == "__main__":
    print("=== 카메라 감지 및 테스트 ===")
    
    manager = CameraManager()
    print(f"플랫폼: {platform.system()}")
    print(f"Arducam 감지: {manager.detect_arducam()}")
    print(f"라즈베리파이 CSI 감지: {manager.detect_raspberry_pi_camera()}")
    
    devices = manager.find_camera_devices()
    print(f"감지된 카메라 장치: {devices}")
    
    camera = manager.initialize_camera()
    if camera:
        print("카메라 초기화 성공!")
        info = manager.get_camera_info()
        print(f"카메라 정보: {info}")
        manager.release()
    else:
        print("카메라 초기화 실패")
