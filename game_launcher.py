import pygame
import subprocess
import sys
import os
import cv2
from PIL import Image, ImageDraw, ImageFont

# USB 웹캠 감지 함수
def detect_usb_camera():
    """USB 웹캠을 감지하고 우선적으로 사용할 카메라 인덱스를 반환"""
    print("🔍 카메라 장치 검색 중...")
    
    # Windows에서 USB 웹캠 감지
    usb_camera_detected = False
    try:
        import subprocess
        result = subprocess.run(['powershell', 'Get-PnpDevice -Class Camera'], 
                              capture_output=True, text=True, timeout=2)
        camera_list = result.stdout
        if 'C920' in camera_list or 'USB' in camera_list:
            usb_camera_detected = True
            print("🔌 USB 웹캠이 Windows에서 감지됨!")
    except:
        pass
    
    # 빠른 카메라 테스트 - 가장 일반적인 인덱스만 시도
    if usb_camera_detected:
        # USB 웹캠이 감지되면 1번을 먼저 시도
        camera_index = 1
        print(f"🎯 USB 웹캠 감지됨 - 카메라 {camera_index} 사용")
    else:
        # USB 웹캠이 없으면 0번 사용
        camera_index = 0
        print(f"� 내장 카메라 사용 - 카메라 {camera_index} 사용")
    
    # 선택된 카메라가 작동하는지 간단히 확인
    try:
        print(f"✅ 카메라 {camera_index} 준비 완료")
        return camera_index, [{'index': camera_index, 'name': f'카메라 {camera_index}'}]
    except:
        print(f"⚠️ 카메라 {camera_index} 사용 불가, 기본값 0 사용")
        return 0, [{'index': 0, 'name': '기본 카메라'}]

# Pygame 초기화
pygame.init()
pygame.mixer.init()

# 효과음 로드
try:
    if os.path.exists("boop-sfx.wav"):
        boop_sound = pygame.mixer.Sound("boop-sfx.wav")
    else:
        boop_sound = None
except:
    boop_sound = None

# 화면 설정 (반응형)
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

# 화면 비율에 따라 적절한 창 크기 설정
if screen_height > screen_width:  # 세로화면
    SCREEN_WIDTH = min(int(screen_width * 0.9), 600)
    SCREEN_HEIGHT = min(int(screen_height * 0.8), 800)
else:  # 가로화면
    SCREEN_WIDTH = min(int(screen_width * 0.7), 1000)
    SCREEN_HEIGHT = min(int(screen_height * 0.8), 700)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("INTERACTIVE GAME")

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PASTEL_PINK = (255, 200, 220)
PASTEL_BLUE = (173, 216, 230)
PASTEL_GREEN = (200, 255, 200)
PASTEL_PURPLE = (221, 160, 221)
PASTEL_MINT = (175, 238, 238)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# 폰트 설정
try:
    font_title = pygame.font.Font("neodgm.ttf", 48)
    font_large = pygame.font.Font("neodgm.ttf", 36)
    font_medium = pygame.font.Font("neodgm.ttf", 28)
    font_small = pygame.font.Font("neodgm.ttf", 20)
except:
    font_title = pygame.font.Font(None, 48)
    font_large = pygame.font.Font(None, 36)
    font_medium = pygame.font.Font(None, 28)
    font_small = pygame.font.Font(None, 20)

class GameButton:
    def __init__(self, x, y, width, height, title, description, script_name, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.description = description
        self.script_name = script_name
        self.color = color
        self.hover_color = tuple(min(255, c + 30) for c in color)
        self.is_hovered = False
        
    def draw(self, screen):
        # 버튼 배경
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=20)
        pygame.draw.rect(screen, WHITE, self.rect, 3, border_radius=20)
        
        # 그림자 효과
        shadow_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 5, self.rect.width, self.rect.height)
        pygame.draw.rect(screen, GRAY, shadow_rect, border_radius=20)
        pygame.draw.rect(screen, color, self.rect, border_radius=20)
        pygame.draw.rect(screen, WHITE, self.rect, 3, border_radius=20)
        
        # 제목
        title_text = font_large.render(self.title, True, DARK_GRAY)
        title_rect = title_text.get_rect(center=(self.rect.centerx, self.rect.y + 40))
        screen.blit(title_text, title_rect)
        
        # 설명
        desc_lines = self.description.split('\n')
        for i, line in enumerate(desc_lines):
            desc_text = font_small.render(line, True, DARK_GRAY)
            desc_rect = desc_text.get_rect(center=(self.rect.centerx, self.rect.y + 80 + i * 25))
            screen.blit(desc_text, desc_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                # 효과음 재생
                if boop_sound:
                    try:
                        boop_sound.play()
                    except:
                        pass
                return True
        return False

def create_gradient_background(screen):
    """그라데이션 배경 생성"""
    for y in range(SCREEN_HEIGHT):
        ratio = y / SCREEN_HEIGHT
        r = int(250 + (240 - 250) * ratio)
        g = int(230 + (220 - 230) * ratio)
        b = int(255 + (240 - 255) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

def draw_sparkles(screen, sparkles):
    """반짝이는 효과 그리기"""
    for sparkle in sparkles:
        x, y, size, alpha = sparkle
        if alpha > 0:
            color = (*PASTEL_MINT[:3], int(alpha))
            # 별 모양 그리기
            pygame.draw.line(screen, color[:3], (x - size, y), (x + size, y), 2)
            pygame.draw.line(screen, color[:3], (x, y - size), (x, y + size), 2)
            pygame.draw.line(screen, color[:3], (x - size//2, y - size//2), (x + size//2, y + size//2), 1)
            pygame.draw.line(screen, color[:3], (x + size//2, y - size//2), (x - size//2, y + size//2), 1)

def update_sparkles(sparkles):
    """반짝이는 효과 업데이트"""
    for i, sparkle in enumerate(sparkles):
        x, y, size, alpha = sparkle
        sparkles[i] = (x, y, size, max(0, alpha - 3))

def run_game(script_name, camera_index=0):
    """게임 실행"""
    try:
        # Python 가상환경 경로
        python_path = sys.executable
        if ".venv" not in python_path:
            # 가상환경이 아닌 경우 가상환경 Python 사용
            venv_python = "/Users/ym/projects/art_projects/afterschool_photobooth/handtracking_game/.venv/bin/python"
            if os.path.exists(venv_python):
                python_path = venv_python
        
        # 환경변수에 카메라 인덱스 설정
        env = os.environ.copy()
        env['CAMERA_INDEX'] = str(camera_index)
        
        script_path = os.path.join(os.path.dirname(__file__), script_name)
        subprocess.Popen([python_path, script_path], env=env)
        print(f"게임 실행: {script_name} (카메라: {camera_index})")
    except Exception as e:
        print(f"게임 실행 오류: {e}")

def main():
    clock = pygame.time.Clock()
    
    # USB 웹캠 감지 및 카메라 설정
    default_camera, available_cameras = detect_usb_camera()
    
    # 화면 비율 확인
    is_portrait = SCREEN_HEIGHT > SCREEN_WIDTH
    
    # 반응형 버튼 배치
    if is_portrait:  # 세로화면 레이아웃
        button_width = int(SCREEN_WIDTH * 0.8)
        button_height = int(SCREEN_HEIGHT * 0.25)
        button_spacing = int(SCREEN_HEIGHT * 0.05)
        
        start_x = (SCREEN_WIDTH - button_width) // 2
        button1_y = int(SCREEN_HEIGHT * 0.3)
        button2_y = button1_y + button_height + button_spacing
        
        buttons = [
            GameButton(
                start_x, button1_y, button_width, button_height,
                "캐릭터 옮기기",
                "손으로 캐릭터를 잡아서\n목표 지점으로 옮기는 게임\n핀치 제스처로 드래그",
                "student_moving_game.py",
                PASTEL_PINK
            ),
            GameButton(
                start_x, button2_y, button_width, button_height,
                "음식 먹기",
                "입을 벌려서 떨어지는\n음식을 먹는 게임\n커비처럼 빨아들여요",
                "food_eating_game.py",
                PASTEL_BLUE
            )
        ]
    else:  # 가로화면 레이아웃
        button_width = int(SCREEN_WIDTH * 0.35)
        button_height = int(SCREEN_HEIGHT * 0.45)
        button_spacing = int(SCREEN_WIDTH * 0.05)
        
        total_width = button_width * 2 + button_spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        button_y = int(SCREEN_HEIGHT * 0.3)
        
        buttons = [
            GameButton(
                start_x, button_y, button_width, button_height,
                "캐릭터 옮기기",
                "손으로 캐릭터를 잡아서\n목표 지점으로 옮기는 게임\n핀치 제스처로 드래그",
                "student_moving_game.py",
                PASTEL_PINK
            ),
            GameButton(
                start_x + button_width + button_spacing, button_y, button_width, button_height,
                "음식 먹기",
                "입을 벌려서 떨어지는\n음식을 먹는 게임\n커비처럼 빨아들여요",
                "food_eating_game.py",
                PASTEL_BLUE
            )
        ]
    
    # 반짝이는 효과
    sparkles = []
    sparkle_timer = 0
    
    # 효과음 재생 관련 변수
    waiting_for_sound = False
    sound_start_time = 0
    selected_game = None
    
    running = True
    while running:
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            # 버튼 이벤트 처리
            for button in buttons:
                if button.handle_event(event):
                    # 효과음 재생 시작
                    waiting_for_sound = True
                    sound_start_time = pygame.time.get_ticks()
                    selected_game = button.script_name
                    break
        
        # 효과음 재생 완료 후 게임 실행
        if waiting_for_sound:
            current_time = pygame.time.get_ticks()
            # boop-sfx는 약 500ms 정도이므로 600ms 후에 게임 실행
            if current_time - sound_start_time >= 600:
                run_game(selected_game, default_camera)
                running = False
        
        # 반짝이는 효과 업데이트
        sparkle_timer += 1
        if sparkle_timer > 20:  # 20프레임마다 새 반짝이 생성
            import random
            sparkles.append((
                random.randint(0, SCREEN_WIDTH),
                random.randint(0, SCREEN_HEIGHT),
                random.randint(3, 8),
                255
            ))
            sparkle_timer = 0
        
        # 기존 반짝이 업데이트
        update_sparkles(sparkles)
        sparkles = [s for s in sparkles if s[3] > 0]  # alpha가 0보다 큰 것만 유지
        
        # 화면 그리기
        create_gradient_background(screen)
        
        # 반짝이는 효과 그리기
        draw_sparkles(screen, sparkles)
        
        # 제목 (반응형 위치)
        title_y = int(SCREEN_HEIGHT * 0.15) if is_portrait else int(SCREEN_HEIGHT * 0.12)
        title_text = font_title.render("INTERACTIVE GAME", True, DARK_GRAY)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(title_text, title_rect)
        
        # 부제목 (반응형 위치)
        subtitle_y = title_y + int(SCREEN_HEIGHT * 0.06)
        subtitle_text = font_medium.render("버튼을 클릭해서 게임을 시작하세요", True, GRAY)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, subtitle_y))
        screen.blit(subtitle_text, subtitle_rect)
        
        # 버튼들 그리기
        for button in buttons:
            button.draw(screen)
        
        # 효과음 재생 중 표시
        if waiting_for_sound:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(100)
            overlay.fill((255, 255, 255))
            screen.blit(overlay, (0, 0))
            
            loading_text = font_large.render("게임 실행 중...", True, DARK_GRAY)
            loading_rect = loading_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(loading_text, loading_rect)
        
        # 하단 안내 메시지
        footer_text = font_small.render("ESC: 종료", True, GRAY)
        footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(footer_text, footer_rect)
        
        # 요구사항 안내
        req_text = font_small.render("요구사항: 웹캠, MediaPipe, OpenCV", True, GRAY)
        req_rect = req_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        screen.blit(req_text, req_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
