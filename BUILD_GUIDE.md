# 빌드 방법 가이드

## PyInstaller 사용 (추천)

### 1. PyInstaller 설치
```bash
pip install pyinstaller
```

### 2. 단일 실행 파일 생성
```bash
# 게임 런처만 실행 파일로 만들기
pyinstaller --onefile --windowed game_launcher.py

# 개별 게임들도 실행 파일로 만들기
pyinstaller --onefile --windowed handtracking_interactive.py
pyinstaller --onefile --windowed food_eating_game.py
```

### 3. 데이터 파일 포함해서 빌드
```bash
# 폰트 파일과 이미지 파일들을 포함해서 빌드
pyinstaller --onefile --windowed --add-data "neodgm.ttf:." --add-data "cha:cha" --add-data "food:food" game_launcher.py
```

### 4. spec 파일로 상세 설정
```python
# game_launcher.spec 파일 생성 후 수정
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['game_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('neodgm.ttf', '.'),
        ('cha', 'cha'),
        ('food', 'food'),
        ('handtracking_interactive.py', '.'),
        ('food_eating_game.py', '.'),
        ('high_score.json', '.')
    ],
    hiddenimports=[
        'cv2',
        'mediapipe',
        'pygame',
        'PIL',
        'numpy'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HandTracking_Games',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
```

## cx_Freeze 사용 (대안)

### 1. cx_Freeze 설치
```bash
pip install cx-freeze
```

### 2. setup.py 생성
```python
from cx_Freeze import setup, Executable
import sys

# 의존성 패키지
packages = ["pygame", "cv2", "mediapipe", "PIL", "numpy"]

# 포함할 파일들
include_files = [
    "neodgm.ttf",
    "cha/",
    "food/",
    "handtracking_interactive.py",
    "food_eating_game.py",
    "high_score.json"
]

# 빌드 옵션
build_exe_options = {
    "packages": packages,
    "include_files": include_files,
    "excludes": []
}

# Mac에서 앱 번들 생성
bdist_mac_options = {
    "bundle_name": "HandTracking Games"
}

# 실행 파일 설정
executables = [
    Executable(
        "game_launcher.py",
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="HandTracking_Games"
    )
]

setup(
    name="HandTracking Games",
    version="1.0",
    description="Hand tracking interactive games",
    options={
        "build_exe": build_exe_options,
        "bdist_mac": bdist_mac_options
    },
    executables=executables
)
```

### 3. 빌드 실행
```bash
python setup.py build
# 또는 Mac 앱 번들 생성
python setup.py bdist_mac
```

## 배포 고려사항

### 1. 웹캠 권한
- macOS: 앱에서 카메라 접근 권한 필요
- 처음 실행 시 권한 요청 팝업 표시

### 2. 파일 크기
- MediaPipe, OpenCV 포함 시 약 200-500MB
- --exclude-module로 불필요한 모듈 제외 가능

### 3. 성능
- 첫 실행 시 압축 해제로 시간 소요
- --onedir 옵션으로 폴더 형태 배포 시 빠른 실행

### 4. 크로스 플랫폼
- Windows: .exe 파일
- macOS: .app 번들
- Linux: 실행 파일

## 추천 빌드 명령어
```bash
# 간단한 실행 파일 생성
pyinstaller --onefile --windowed game_launcher.py

# 모든 리소스 포함한 완전한 빌드
pyinstaller --onefile --windowed \
  --add-data "neodgm.ttf:." \
  --add-data "cha:cha" \
  --add-data "food:food" \
  --add-data "handtracking_interactive.py:." \
  --add-data "food_eating_game.py:." \
  --add-data "high_score.json:." \
  --name "HandTracking_Games" \
  game_launcher.py
```
