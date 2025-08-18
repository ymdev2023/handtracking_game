# Git "could not resolve host" 오류 해결 가이드

## 문제 상황
```
fatal: unable to access 'https://github.com/...': Could not resolve host: github.com
```

## 1. 네트워크 연결 확인
```bash
# 인터넷 연결 테스트
ping google.com

# GitHub 연결 테스트
ping github.com

# DNS 확인
nslookup github.com
```

## 2. DNS 설정 변경
```bash
# DNS 설정 파일 편집
sudo nano /etc/resolv.conf

# 아래 내용 추가 (Google DNS)
nameserver 8.8.8.8
nameserver 8.8.4.4

# 또는 Cloudflare DNS
nameserver 1.1.1.1
nameserver 1.0.0.1
```

## 3. 네트워크 재시작
```bash
# WiFi 재연결
sudo iwconfig wlan0 down
sudo iwconfig wlan0 up

# 또는 네트워크 서비스 재시작
sudo systemctl restart networking
```

## 4. Git 설정 변경
```bash
# HTTP 대신 HTTPS 사용
git config --global url."https://".insteadOf git://

# 프록시 설정 해제 (있다면)
git config --global --unset http.proxy
git config --global --unset https.proxy
```

## 5. SSH 대신 HTTPS 사용
```bash
# 현재 원격 저장소 확인
git remote -v

# HTTPS로 변경
git remote set-url origin https://github.com/ymdev2023/handtracking_game.git
```

## 6. 방화벽/라우터 확인
- 방화벽에서 포트 443 (HTTPS) 차단 여부 확인
- 라우터 설정에서 외부 접속 허용 확인
- 학교/회사 네트워크의 경우 프록시 설정 필요할 수 있음

## 7. 임시 해결책 (오프라인 전송)
```bash
# 현재 프로젝트를 압축
tar -czf handtracking_game.tar.gz handtracking_game/

# USB나 다른 방법으로 라즈베리파이에 전송
# 라즈베리파이에서 압축 해제
tar -xzf handtracking_game.tar.gz
```

## 8. 라즈베리파이에서 직접 다운로드
```bash
# wget으로 직접 다운로드
wget https://github.com/ymdev2023/handtracking_game/archive/refs/heads/main.zip

# 압축 해제
unzip main.zip
mv handtracking_game-main handtracking_game
```
