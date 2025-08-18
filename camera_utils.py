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
        
        # 라즈베리파이 특화 초기화
        if not self.is_mac:
            self.check_raspberry_pi_setup()
    
    def create_gstreamer_pipeline(self, device_index=0, width=640, height=480, fps=30):
        """Arducam CSI 카메라용 GStreamer 파이프라인 생성"""
        # 라즈베리파이 CSI 카메라용 최적화된 GStreamer 파이프라인들
        pipelines = [
            # libcamera 기반 파이프라인 (최신 라즈베리파이 OS)
            f"libcamerasrc ! video/x-raw,width={width},height={height},framerate={fps}/1 ! videoconvert ! appsink",
            
            # v4l2src 파이프라인 (일반적인 V4L2)
            f"v4l2src device=/dev/video{device_index} ! video/x-raw,width={width},height={height},framerate={fps}/1 ! videoconvert ! appsink",
            
            # MJPEG 파이프라인 (Arducam MJPEG 지원시)
            f"v4l2src device=/dev/video{device_index} ! image/jpeg,width={width},height={height},framerate={fps}/1 ! jpegdec ! videoconvert ! appsink",
            
            # 기본 자동 파이프라인
            f"v4l2src device=/dev/video{device_index} ! videoconvert ! video/x-raw,width={width},height={height} ! appsink"
        ]
        
        return pipelines
    
    def initialize_gstreamer_camera(self, device_index=0):
        """GStreamer를 사용한 Arducam CSI 카메라 초기화"""
        print(f"🔧 GStreamer로 Arducam 초기화 시도 (장치: {device_index})")
        
        pipelines = self.create_gstreamer_pipeline(device_index, self.width, self.height, self.fps)
        
        for i, pipeline in enumerate(pipelines):
            try:
                print(f"  🔧 GStreamer 파이프라인 {i+1} 시도...")
                print(f"    {pipeline}")
                
                cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
                
                if cap.isOpened():
                    # 테스트 프레임 읽기
                    for attempt in range(3):
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            print(f"  ✅ GStreamer 파이프라인 {i+1} 성공!")
                            print(f"    프레임 크기: {frame.shape}")
                            return cap
                        time.sleep(0.2)
                    
                    print(f"  ❌ GStreamer 파이프라인 {i+1} 프레임 읽기 실패")
                    cap.release()
                else:
                    print(f"  ❌ GStreamer 파이프라인 {i+1} 열기 실패")
                    
            except Exception as e:
                print(f"  ❌ GStreamer 파이프라인 {i+1} 오류: {e}")
                continue
                
        print("❌ 모든 GStreamer 파이프라인 실패")
        return None
        
    def check_raspberry_pi_setup(self):
        """라즈베리파이 카메라 설정 확인"""
        print("🔍 라즈베리파이 카메라 설정 확인 중...")
        
        # 1. video 그룹 권한 확인
        try:
            import grp
            import getpass
            
            username = getpass.getuser()
            video_group = grp.getgrnam('video')
            
            if username in video_group.gr_mem:
                print(f"✅ 사용자 '{username}'이 video 그룹에 속해 있음")
            else:
                print(f"⚠️ 사용자 '{username}'이 video 그룹에 속해 있지 않음")
                print("   sudo usermod -a -G video $USER 명령어로 추가 후 재로그인하세요")
                
        except Exception as e:
            print(f"⚠️ video 그룹 확인 실패: {e}")
            
        # 2. 카메라 모듈 활성화 확인
        config_files = ['/boot/config.txt', '/boot/firmware/config.txt']
        camera_enabled = False
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if 'camera_auto_detect=1' in content or 'start_x=1' in content:
                            camera_enabled = True
                            print(f"✅ 카메라 모듈이 {config_file}에서 활성화됨")
                            break
                except Exception:
                    pass
                    
        if not camera_enabled:
            print("⚠️ 카메라 모듈이 비활성화된 것 같습니다.")
            print("   sudo raspi-config에서 카메라를 활성화하고 재부팅하세요")
            
        # 3. 모듈 로드 확인
        try:
            result = subprocess.run(['lsmod'], capture_output=True, text=True, timeout=5)
            modules = result.stdout
            camera_modules = ['bcm2835_v4l2', 'ov5647', 'imx219', 'imx477']
            
            for module in camera_modules:
                if module in modules:
                    print(f"✅ 카메라 모듈 '{module}' 로드됨")
                    
        except Exception:
            pass
        
    def detect_arducam(self):
        """Arducam CSI 모듈 감지 (USB가 아닌 CSI 포트 연결)"""
        if self.is_mac:
            return False  # macOS에서는 Arducam CSI 지원 안함
            
        # Linux에서만 실행
        try:
            # 1. Device Tree에서 Arducam 감지
            dt_paths = [
                "/proc/device-tree/soc/i2c@7e804000/arducam",
                "/proc/device-tree/soc/i2c@7e804000/ov5647@36",  # Arducam OV5647
                "/proc/device-tree/soc/i2c@7e804000/imx219@10",  # Arducam IMX219
                "/proc/device-tree/soc/i2c@7e804000/imx477@1a",  # Arducam IMX477
                "/proc/device-tree/soc/i2c@7e804000/imx708@1a",  # Arducam IMX708
            ]
            
            for path in dt_paths:
                if os.path.exists(path):
                    print(f"📷 Arducam CSI 모듈 감지됨: {path}")
                    return True
            
            # 2. i2cdetect로 Arducam 센서 확인
            try:
                result = subprocess.run(['i2cdetect', '-y', '1'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    i2c_output = result.stdout.lower()
                    arducam_addresses = ['36', '10', '1a']  # 일반적인 Arducam I2C 주소들
                    for addr in arducam_addresses:
                        if addr in i2c_output:
                            print(f"📷 Arducam 센서 감지됨 (I2C 주소: 0x{addr})")
                            return True
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
            
            # 3. dmesg에서 Arducam 관련 로그 확인
            try:
                result = subprocess.run(['dmesg'], capture_output=True, text=True, timeout=10)
                dmesg_output = result.stdout.lower()
                arducam_keywords = [
                    'arducam', 'ov5647', 'imx219', 'imx477', 'imx708',
                    'bcm2835-v4l2', 'mmal service'
                ]
                for keyword in arducam_keywords:
                    if keyword in dmesg_output:
                        print(f"📷 Arducam/CSI 카메라 감지됨 (dmesg): {keyword}")
                        return True
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
                
            # 4. /sys/class/video4linux에서 CSI 카메라 확인
            v4l_paths = [
                "/sys/class/video4linux/video0/name",
                "/sys/class/video4linux/video1/name"
            ]
            
            for v4l_path in v4l_paths:
                if os.path.exists(v4l_path):
                    try:
                        with open(v4l_path, 'r') as f:
                            camera_name = f.read().strip().lower()
                            csi_keywords = ['mmal', 'bcm2835', 'unicam', 'arducam']
                            for keyword in csi_keywords:
                                if keyword in camera_name:
                                    print(f"📷 CSI/Arducam 카메라 감지됨: {camera_name}")
                                    return True
                    except Exception:
                        pass
                        
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
            
        return False
        
    def detect_raspberry_pi_camera(self):
        """라즈베리파이 CSI 카메라 감지"""
        if self.is_mac:
            return False  # macOS에서는 라즈베리파이 CSI 카메라 지원 안함
            
        try:
            # 1. vcgencmd로 카메라 상태 확인
            result = subprocess.run(['vcgencmd', 'get_camera'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout.strip()
                if 'detected=1' in output:
                    print("📷 라즈베리파이 CSI 카메라 감지됨 (vcgencmd)")
                    return True
                    
            # 2. /proc/device-tree 확인
            dt_paths = [
                "/proc/device-tree/soc/csi@7e800000",
                "/proc/device-tree/soc/i2c@7e804000/ov5647@36",
                "/proc/device-tree/soc/i2c@7e804000/imx219@10"
            ]
            for path in dt_paths:
                if os.path.exists(path):
                    print(f"📷 라즈베리파이 카메라 하드웨어 감지됨: {path}")
                    return True
                    
            # 3. dmesg에서 카메라 관련 로그 확인
            try:
                result = subprocess.run(['dmesg'], capture_output=True, text=True, timeout=10)
                dmesg_output = result.stdout.lower()
                camera_keywords = ['ov5647', 'imx219', 'imx477', 'imx708', 'csi', 'camera']
                for keyword in camera_keywords:
                    if keyword in dmesg_output:
                        print(f"📷 라즈베리파이 카메라 감지됨 (dmesg): {keyword}")
                        return True
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
                        
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
            print("🐧 Linux/라즈베리파이 카메라 장치 검색...")
            
            # 1. /dev/video* 파일 확인
            video_devices = []
            for i in range(20):  # 0-19까지 확장 검색
                video_path = f"/dev/video{i}"
                if os.path.exists(video_path):
                    # 장치 권한 확인
                    if os.access(video_path, os.R_OK | os.W_OK):
                        video_devices.append(i)
                        print(f"✅ 비디오 장치 {video_path} 발견 (권한 OK)")
                    else:
                        print(f"⚠️ 비디오 장치 {video_path} 발견했지만 권한 없음")
                        
            devices.extend(video_devices)
            
            # 2. v4l2-ctl로 상세 정보 확인 (있는 경우)
            try:
                result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("📹 v4l2 장치 목록:")
                    print(result.stdout)
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                print("⚠️ v4l2-ctl 명령어 없음 (선택사항)")
                
            # 3. lsusb 명령으로 USB 카메라 확인
            try:
                result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
                usb_devices = result.stdout.lower()
                camera_keywords = ['camera', 'webcam', 'video', 'uvc', 'capture']
                found_usb_camera = False
                for keyword in camera_keywords:
                    if keyword in usb_devices:
                        found_usb_camera = True
                        break
                        
                if found_usb_camera:
                    print("🔍 USB 카메라 장치 감지됨")
                else:
                    print("⚠️ USB 카메라 미감지")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                print("⚠️ lsusb 명령어 실행 실패")
                
            # 4. 라즈베리파이 특화 감지
            if self.detect_raspberry_pi_camera():
                # CSI 카메라가 감지되면 device 0을 최우선으로
                if 0 not in devices:
                    devices.insert(0, 0)
                    print("📷 라즈베리파이 CSI 카메라 우선 설정")
                    
        if not devices:
            print("⚠️ 카메라 장치를 찾을 수 없음 - 기본값 [0] 사용")
            devices = [0]
            
        print(f"📱 총 {len(devices)}개 카메라 장치 발견: {devices}")
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
        """Arducam CSI 모듈 특별 초기화"""
        print(f"🔧 Arducam CSI 카메라 초기화 시도 (장치: {device_index})")
        
        # Arducam CSI 카메라를 위한 다양한 백엔드 시도
        backends = [
            (cv2.CAP_V4L2, "V4L2"),
            (cv2.CAP_GSTREAMER, "GStreamer"),
            (cv2.CAP_ANY, "자동")
        ]
        
        for backend_id, backend_name in backends:
            try:
                print(f"  🔧 {backend_name} 백엔드로 Arducam 초기화 시도...")
                cap = cv2.VideoCapture(device_index, backend_id)
                
                if cap.isOpened():
                    # Arducam CSI 카메라 특화 설정
                    
                    # 기본 해상도 설정
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    cap.set(cv2.CAP_PROP_FPS, self.fps)
                    
                    # CSI 카메라 특화 설정
                    if backend_id == cv2.CAP_V4L2:
                        # V4L2 백엔드용 설정
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기 최소화 (지연 감소)
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                        
                        # Arducam 특화 설정 (가능한 경우)
                        try:
                            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 수동 노출
                            cap.set(cv2.CAP_PROP_EXPOSURE, -6)  # 노출 시간 조정
                            cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # 자동 포커스 비활성화
                            cap.set(cv2.CAP_PROP_BRIGHTNESS, 0)  # 밝기 기본값
                            cap.set(cv2.CAP_PROP_CONTRAST, 32)  # 대비 조정
                            cap.set(cv2.CAP_PROP_SATURATION, 32)  # 채도 조정
                        except Exception:
                            print("    ⚠️ 일부 Arducam 고급 설정 적용 실패 (무시)")
                    
                    elif backend_id == cv2.CAP_GSTREAMER:
                        # GStreamer 백엔드용 설정 (라즈베리파이 CSI 최적화)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    # 테스트 프레임 읽기
                    for attempt in range(5):
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
                            
                            print(f"  ✅ Arducam {backend_name} 초기화 성공!")
                            print(f"    해상도: {actual_width}x{actual_height}, FPS: {actual_fps}")
                            return cap
                        time.sleep(0.1)  # 잠시 대기 후 재시도
                    
                    print(f"  ❌ {backend_name} 프레임 읽기 실패")
                    cap.release()
                else:
                    print(f"  ❌ {backend_name} 백엔드 열기 실패")
                    
            except Exception as e:
                print(f"  ❌ {backend_name} 백엔드 오류: {e}")
                continue
                
        print("❌ 모든 Arducam 초기화 방법 실패")
        return None
        
    def initialize_standard_camera(self, device_index=0):
        """표준 카메라 초기화"""
        try:
            # 라즈베리파이에서는 다양한 백엔드 시도
            if not self.is_mac:
                backends = [
                    cv2.CAP_V4L2,     # Video4Linux2 (라즈베리파이 기본)
                    cv2.CAP_GSTREAMER, # GStreamer (라즈베리파이 CSI 카메라)
                    cv2.CAP_ANY        # 자동 선택
                ]
                
                for backend in backends:
                    try:
                        print(f"🔧 백엔드 {backend} 시도 중...")
                        cap = cv2.VideoCapture(device_index, backend)
                        
                        if cap.isOpened():
                            # 기본 설정 적용
                            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                            cap.set(cv2.CAP_PROP_FPS, self.fps)
                            
                            # 라즈베리파이 특화 설정
                            if backend == cv2.CAP_V4L2:
                                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기 최소화
                                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                            
                            # 테스트 프레임 읽기
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                print(f"✅ 백엔드 {backend} 성공!")
                                return cap
                            else:
                                cap.release()
                                print(f"❌ 백엔드 {backend} 프레임 읽기 실패")
                        else:
                            print(f"❌ 백엔드 {backend} 열기 실패")
                            
                    except Exception as e:
                        print(f"❌ 백엔드 {backend} 오류: {e}")
                        continue
            else:
                # macOS에서는 기본 방식
                cap = cv2.VideoCapture(device_index)
                
                if cap.isOpened():
                    # 기본 설정
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    cap.set(cv2.CAP_PROP_FPS, self.fps)
                    
                    return cap
                
        except Exception as e:
            print(f"❌ 카메라 초기화 오류: {e}")
            
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
            print("🐧 Linux/라즈베리파이 카메라 감지 시작...")
            
            # 1. Arducam CSI 모듈 우선 감지 및 초기화
            if self.detect_arducam():
                print("🎯 Arducam CSI 모듈 감지됨 - 특화 초기화 시도")
                camera_devices = self.find_camera_devices()
                
                for device_index in camera_devices:
                    # 1-1. GStreamer로 Arducam CSI 초기화 시도 (최우선)
                    print(f"🔧 Arducam CSI GStreamer 초기화 시도 (장치 {device_index})")
                    self.camera = self.initialize_gstreamer_camera(device_index)
                    if self.camera is not None:
                        self.camera_index = device_index
                        print(f"✅ Arducam CSI GStreamer {device_index} 초기화 완료!")
                        return self.camera
                    
                    # 1-2. V4L2로 Arducam CSI 초기화 시도 (차선책)
                    print(f"🔧 Arducam CSI V4L2 초기화 시도 (장치 {device_index})")
                    self.camera = self.initialize_arducam(device_index)
                    if self.camera is not None:
                        self.camera_index = device_index
                        print(f"✅ Arducam CSI V4L2 {device_index} 초기화 완료!")
                        return self.camera
                        
            # 2. 일반 라즈베리파이 CSI 카메라 시도
            if self.detect_raspberry_pi_camera():
                print("📷 일반 라즈베리파이 CSI 카메라 초기화 시도")
                
                # 2-1. GStreamer로 CSI 카메라 초기화 시도
                self.camera = self.initialize_gstreamer_camera(0)
                if self.camera is not None:
                    self.camera_index = 0
                    print(f"✅ 라즈베리파이 CSI GStreamer 초기화 완료!")
                    return self.camera
                
                # 2-2. 표준 방식으로 CSI 카메라 초기화 시도
                self.camera = self.initialize_standard_camera(0)
                if self.camera is not None:
                    self.camera_index = 0
                    print(f"✅ 라즈베리파이 CSI 표준 초기화 완료!")
                    return self.camera
                    
            # 3. 표준 USB 카메라들 순차 시도
            print("🔌 USB 카메라 감지 및 초기화 시도")
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
