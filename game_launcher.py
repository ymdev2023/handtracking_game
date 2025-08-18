import pygame
import subprocess
import sys
import os

# PIL/Pillow import with fallback
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    print("⚠️ PIL/Pillow가 설치되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
    PIL_AVAILABLE = False

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

# 화면 설정 (전체화면)
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("게임 선택하기")

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

def run_game(script_name):
    """게임 실행"""
    try:
        # Python 가상환경 경로
        python_path = sys.executable
        if ".venv" not in python_path:
            # 가상환경이 아닌 경우 가상환경 Python 사용
            venv_python = "/Users/ym/projects/art_projects/afterschool_photobooth/handtracking_game/.venv/bin/python"
            if os.path.exists(venv_python):
                python_path = venv_python
        
        script_path = os.path.join(os.path.dirname(__file__), script_name)
        subprocess.Popen([python_path, script_path])
        print(f"게임 실행: {script_name}")
    except Exception as e:
        print(f"게임 실행 오류: {e}")

def main():
    clock = pygame.time.Clock()
    
    # 버튼 크기와 간격
    button_width = 300
    button_height = 200
    button_spacing = 50
    total_width = button_width * 2 + button_spacing
    start_x = (SCREEN_WIDTH - total_width) // 2
    button_y = (SCREEN_HEIGHT - button_height) // 2
    
    # 게임 버튼들 (화면 중앙 배치)
    buttons = [
        GameButton(
            start_x, button_y, button_width, button_height,
            "캐릭터 옮기기",
            "손으로 캐릭터를 잡아서\n목표 지점으로 옮기는 게임\n핀치 제스처로 드래그!",
            "student_moving_game.py",
            PASTEL_PINK
        ),
        GameButton(
            start_x + button_width + button_spacing, button_y, button_width, button_height,
            "음식 먹기",
            "입을 벌려서 떨어지는\n음식을 먹는 게임\n커비처럼 빨아들여요!",
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
                elif event.key == pygame.K_F11:
                    # 전체화면 토글
                    pygame.display.toggle_fullscreen()
            
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
                run_game(selected_game)
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
        
        # 제목
        title_text = font_title.render("🎮 Hand Tracking Games 🎮", True, DARK_GRAY)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 6))
        screen.blit(title_text, title_rect)
        
        # 부제목
        subtitle_text = font_medium.render("버튼을 클릭해서 게임을 시작하세요", True, GRAY)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 6 + 50))
        screen.blit(subtitle_text, subtitle_rect)
        
        # 하단 조작 안내
        control_y = SCREEN_HEIGHT - 80
        esc_text = font_small.render("ESC: 종료  |  F11: 전체화면 토글", True, GRAY)
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH // 2, control_y))
        screen.blit(esc_text, esc_rect)
        
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
