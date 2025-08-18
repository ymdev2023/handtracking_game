#!/usr/bin/env python3
"""
라즈베리파이 카메라 진단 도구
카메라 문제를 찾고 해결하는 스크립트
"""

import os
import sys
import subprocess
import time
import cv2
from camera_utils import CameraManager

def run_command(cmd, description=""):
    """명령어 실행 및 결과 표시"""
    print(f"\n🔧 {description}")
    print(f"명령어: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
        if result.returncode == 0:
            print("✅ 성공")
            if result.stdout.strip():
                print(f"출력:\n{result.stdout}")
        else:
            print("❌ 실패")
            if result.stderr.strip():
                print(f"오류:\n{result.stderr}")
                
        return result.returncode == 0, result.stdout
        
    except subprocess.TimeoutExpired:
        print("⏰ 시간 초과")
        return False, ""
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return False, ""

def check_hardware():
    """하드웨어 확인"""
    print("\n" + "="*60)
    print("🔍 하드웨어 확인")
    print("="*60)
    
    # 라즈베리파이 모델 확인
    if os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            if "Raspberry Pi" in cpuinfo:
                print("✅ 라즈베리파이 감지됨")
                # 모델 정보 추출
                for line in cpuinfo.split('\n'):
                    if 'Model' in line:
                        print(f"  {line.strip()}")
            else:
                print("⚠️ 라즈베리파이가 아닐 수 있음")
    
    # GPU 메모리 확인
    run_command(["vcgencmd", "get_mem", "gpu"], "GPU 메모리 확인")
    
    # 카메라 하드웨어 감지
    run_command(["vcgencmd", "get_camera"], "카메라 하드웨어 감지")
    
    # I2C 장치 확인 (Arducam 센서 감지)
    print("\n🔍 I2C 장치 확인 (Arducam 센서 감지):")
    success, output = run_command(["i2cdetect", "-y", "1"], "I2C 버스 1 스캔")
    if success and output:
        # 일반적인 카메라 센서 I2C 주소들
        camera_addresses = {
            '36': 'OV5647 (라즈베리파이 카메라 v1 / Arducam OV5647)',
            '10': 'IMX219 (라즈베리파이 카메라 v2 / Arducam IMX219)', 
            '1a': 'IMX477/IMX708 (HQ 카메라 / Arducam IMX477/IMX708)'
        }
        
        for addr, description in camera_addresses.items():
            if addr in output.lower():
                print(f"  ✅ {description} 감지됨 (주소: 0x{addr})")
    
    # Device Tree 확인
    print("\n🌳 Device Tree 카메라 정보:")
    dt_paths = [
        "/proc/device-tree/soc/i2c@7e804000/ov5647@36",
        "/proc/device-tree/soc/i2c@7e804000/imx219@10", 
        "/proc/device-tree/soc/i2c@7e804000/imx477@1a",
        "/proc/device-tree/soc/i2c@7e804000/imx708@1a"
    ]
    
    for path in dt_paths:
        if os.path.exists(path):
            sensor_name = path.split('/')[-1]
            print(f"  ✅ {sensor_name} Device Tree 엔트리 발견")
    
    # 커널 모듈 확인
    print("\n🔧 커널 모듈 확인:")
    run_command("lsmod | grep -E '(bcm2835|ov5647|imx219|imx477|imx708|v4l2|unicam)'", "카메라 관련 커널 모듈")
    
    # dmesg에서 카메라 관련 로그 확인
    print("\n📋 시스템 로그 확인:")
    run_command("dmesg | grep -i -E '(camera|ov5647|imx219|imx477|imx708|bcm2835|mmal|unicam)' | tail -10", "카메라 관련 최근 로그")

def check_permissions():
    """권한 확인"""
    print("\n" + "="*60)
    print("🔐 권한 확인")
    print("="*60)
    
    # 현재 사용자
    import getpass
    username = getpass.getuser()
    print(f"현재 사용자: {username}")
    
    # video 그룹 확인
    run_command(["groups"], "사용자 그룹")
    
    # /dev/video* 권한 확인
    video_devices = []
    for i in range(10):
        video_path = f"/dev/video{i}"
        if os.path.exists(video_path):
            video_devices.append(video_path)
            
    if video_devices:
        print(f"\n발견된 비디오 장치: {video_devices}")
        for device in video_devices:
            try:
                stat = os.stat(device)
                readable = os.access(device, os.R_OK)
                writable = os.access(device, os.W_OK)
                print(f"{device}: 읽기={readable}, 쓰기={writable}")
            except Exception as e:
                print(f"{device}: 확인 실패 - {e}")
    else:
        print("❌ /dev/video* 장치를 찾을 수 없음")

def check_config():
    """설정 파일 확인"""
    print("\n" + "="*60)
    print("📝 설정 파일 확인")
    print("="*60)
    
    config_files = ['/boot/config.txt', '/boot/firmware/config.txt']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"\n📄 {config_file} 확인:")
            try:
                with open(config_file, 'r') as f:
                    lines = f.readlines()
                    
                camera_lines = []
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if any(keyword in line.lower() for keyword in 
                          ['camera', 'start_x', 'gpu_mem', 'dtoverlay']):
                        camera_lines.append(f"{line_num}: {line}")
                        
                if camera_lines:
                    for line in camera_lines:
                        print(f"  {line}")
                else:
                    print("  카메라 관련 설정 없음")
                    
            except Exception as e:
                print(f"  읽기 실패: {e}")

def test_v4l2():
    """V4L2 도구 테스트"""
    print("\n" + "="*60)
    print("📹 V4L2 테스트")
    print("="*60)
    
    # v4l2-ctl 설치 확인
    success, _ = run_command(["which", "v4l2-ctl"], "v4l2-ctl 설치 확인")
    
    if success:
        run_command(["v4l2-ctl", "--list-devices"], "V4L2 장치 목록")
        run_command(["v4l2-ctl", "--all"], "V4L2 상세 정보")
    else:
        print("⚠️ v4l2-utils가 설치되지 않음")
        print("설치하려면: sudo apt install v4l-utils")

def test_opencv_camera():
    """OpenCV 카메라 테스트"""
    print("\n" + "="*60)
    print("🎥 OpenCV 카메라 테스트")
    print("="*60)
    
    # CameraManager로 테스트
    print("CameraManager를 사용한 테스트:")
    manager = CameraManager()
    camera = manager.initialize_camera()
    
    if camera:
        print("✅ CameraManager 카메라 초기화 성공!")
        
        # 몇 프레임 읽어보기
        for i in range(5):
            ret, frame = camera.read()
            if ret and frame is not None:
                print(f"  프레임 {i+1}: 크기 {frame.shape}, 타입 {frame.dtype}")
            else:
                print(f"  프레임 {i+1}: 읽기 실패")
                
        camera.release()
    else:
        print("❌ CameraManager 카메라 초기화 실패")
        
    # 직접 OpenCV 테스트
    print("\n직접 OpenCV 테스트:")
    backends = [
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_GSTREAMER, "GStreamer"), 
        (cv2.CAP_ANY, "자동")
    ]
    
    for backend_id, backend_name in backends:
        print(f"\n🔧 {backend_name} 백엔드 테스트:")
        try:
            cap = cv2.VideoCapture(0, backend_id)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"  ✅ {backend_name} 성공! 프레임 크기: {frame.shape}")
                else:
                    print(f"  ❌ {backend_name} 프레임 읽기 실패")
                cap.release()
            else:
                print(f"  ❌ {backend_name} 열기 실패")
        except Exception as e:
            print(f"  ❌ {backend_name} 예외: {e}")

def suggest_fixes():
    """해결 방안 제시"""
    print("\n" + "="*60)
    print("🔧 문제 해결 방안")
    print("="*60)
    
    print("""
1. 카메라 모듈 활성화:
   sudo raspi-config
   -> Interface Options -> Camera -> Enable

2. 사용자를 video 그룹에 추가:
   sudo usermod -a -G video $USER
   (재로그인 필요)

3. GPU 메모리 증가 (/boot/config.txt):
   gpu_mem=128

4. 카메라 자동 감지 활성화 (/boot/config.txt):
   camera_auto_detect=1

5. V4L2 도구 설치:
   sudo apt update
   sudo apt install v4l-utils

6. 재부팅:
   sudo reboot

7. 하드웨어 연결 확인:
   - CSI 케이블이 제대로 연결되었는지 확인
   - 케이블이 손상되지 않았는지 확인
   - 카메라 모듈이 올바른 방향으로 연결되었는지 확인
""")

def main():
    print("🚀 라즈베리파이 카메라 진단 도구")
    print("="*60)
    
    try:
        check_hardware()
        check_permissions() 
        check_config()
        test_v4l2()
        test_opencv_camera()
        suggest_fixes()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류: {e}")
        
    print("\n✅ 진단 완료!")

if __name__ == "__main__":
    main()
