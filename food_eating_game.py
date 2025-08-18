import cv2
import mediapipe as mp
import pygame
import random
import json
import os
import math
import numpy as np
from math import sqrt

# MediaPipe 로그 레벨 설정 (경고 메시지 숨기기)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import logging
logging.getLogger('mediapipe').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

# PIL/Pillow import with fallback
try:
    from PIL import Image, ImageFont, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    print("⚠️ PIL/Pillow가 설치되지 않았습니다. 폰트 기능이 제한될 수 있습니다.")
    PIL_AVAILABLE = False

# 카메라 유틸리티 import
try:
    from camera_utils import CameraManager
    CAMERA_UTILS_AVAILABLE = True
except ImportError:
    print("⚠️ camera_utils를 찾을 수 없습니다. 기본 카메라 초기화를 사용합니다.")
    CAMERA_UTILS_AVAILABLE = False

# Pygame 초기화
pygame.init()
pygame.mixer.init()

# 효과음 생성 (coin-sfx 스타일)
def create_coin_sound():
    """coin-sfx 스타일의 효과음 생성"""
    sample_rate = 22050
    duration = 0.4
    
    frames = int(duration * sample_rate)
    arr = []
    for i in range(frames):
        t = i / sample_rate
        
        # 클래식한 coin 효과음: 높은 주파수에서 시작해서 낮아지는 소리
        frequency = 1200 * (1 - t * 0.7)  # 1200Hz에서 360Hz로 감소
        
        # 여러 하모닉으로 금속성 소리 만들기
        wave1 = math.sin(2 * math.pi * frequency * t)
        wave2 = 0.5 * math.sin(2 * math.pi * frequency * 2 * t)
        wave3 = 0.3 * math.sin(2 * math.pi * frequency * 3 * t)
        
        # 빠른 감쇠로 coin 효과
        envelope = math.exp(-t * 8) * (1 - t * 0.5)
        
        # 최종 파형
        wave = int(3000 * (wave1 + wave2 + wave3) * envelope)
        wave = max(-32767, min(32767, wave))  # 클리핑 방지
        arr.append([wave, wave])
    
    sound = pygame.sndarray.make_sound(np.array(arr, dtype=np.int16))
    return sound

# 효과음 로드
try:
    # coin-sfx.mp3 파일 로드 시도
    if os.path.exists("coin-sfx.mp3"):
        coin_sound = pygame.mixer.Sound("coin-sfx.mp3")
    else:
        # 파일이 없으면 생성된 사운드 사용
        coin_sound = create_coin_sound()
except:
    coin_sound = None

# 화면 설정 (전체화면)
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("🍔 음식 먹기 게임 (ESC: 종료, F11: 전체화면 토글)")

# 색상 정의 (파스텔 컬러 추가)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 파스텔 컬러들
PASTEL_PINK = (255, 200, 220)
PASTEL_BLUE = (173, 216, 230)
PASTEL_GREEN = (200, 255, 200)
PASTEL_PURPLE = (221, 160, 221)
PASTEL_MINT = (175, 238, 238)

# 폰트 설정
try:
    font_large = pygame.font.Font("neodgm.ttf", 48)
    font_medium = pygame.font.Font("neodgm.ttf", 36)
    font_small = pygame.font.Font("neodgm.ttf", 24)
except:
    font_large = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)

# MediaPipe 초기화
mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# 입술 랜드마크 인덱스 (위쪽 입술과 아래쪽 입술)
UPPER_LIP = [13, 14, 15, 16, 17, 18, 19, 20]
LOWER_LIP = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# 음식 클래스
class Food:
    def __init__(self, x, y, food_type):
        self.x = x
        self.y = y
        self.food_type = food_type
        
        # 원본 이미지 로드
        original_image = pygame.image.load(f"food/snack{food_type}.png")
        original_width, original_height = original_image.get_size()
        
        # 원본 비율을 유지하면서 5배 크게 스케일링
        scale_factor = 5.0
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        self.image = pygame.transform.scale(original_image, (new_width, new_height))
        self.rect = pygame.Rect(x, y, new_width, new_height)
        self.width = new_width
        self.height = new_height
        self.speed = random.uniform(3.6, 9.6)  # 속도를 1.2배로 증가 (3-8에서 3.6-9.6으로)
        self.eaten = False
        
    def update(self):
        # 스폰 위치에 따른 다양한 움직임
        if self.x < 0:  # 왼쪽에서 스폰된 경우
            self.x += self.speed
            self.y += self.speed * 0.5
        elif self.x > SCREEN_WIDTH - self.width:  # 오른쪽에서 스폰된 경우
            self.x -= self.speed
            self.y += self.speed * 0.5
        else:  # 위쪽에서 스폰된 경우
            self.y += self.speed
            
        self.rect.x = self.x
        self.rect.y = self.y
        
    def draw(self, screen):
        if not self.eaten:
            screen.blit(self.image, (self.x, self.y))

# 게임 상태 관리
class GameState:
    def __init__(self):
        self.score = 0
        self.time_left = 60  # 60초 게임
        self.game_over = False
        self.game_started = False
        self.waiting_for_heart = True  # 하트 감지 대기 상태
        self.foods = []
        self.mouth_open = False
        self.mouth_threshold = 15  # 입이 열렸다고 판단하는 거리 임계값
        self.food_spawn_timer = 0
        self.food_spawn_interval = 25  # 25프레임마다 음식 생성 (더 빠르게, 45에서 25로)
        self.start_time = None  # 게임 시작 시간
        
        # 하트 제스처 관련
        self.is_heart_gesture = False
        self.last_heart_time = 0
        self.heart_cooldown = 2.0
        
        # 파티클 효과
        self.heart_particles = []
        self.sparkle_particles = []
        
        # 폰트 설정
        try:
            self.font_large = pygame.font.Font("neodgm.ttf", 48)
            self.font_medium = pygame.font.Font("neodgm.ttf", 36)
            self.font_small = pygame.font.Font("neodgm.ttf", 24)
        except:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)
        
    def spawn_food(self):
        # 더 다양한 스폰 위치 (작은 화면에 맞게 조정)
        spawn_side = random.choice(['top', 'left', 'right'])
        
        # 5배 큰 음식 크기를 고려한 스폰 위치 (640x480 화면용)
        if spawn_side == 'top':
            x = random.randint(50, SCREEN_WIDTH - 300)  # 더 큰 음식을 위한 여유 공간
            y = -250  # 더 위에서 시작
        elif spawn_side == 'left':
            x = -250  # 더 왼쪽에서 시작
            y = random.randint(50, SCREEN_HEIGHT // 2)
        else:  # right
            x = SCREEN_WIDTH + 100
            y = random.randint(50, SCREEN_HEIGHT // 2)
            
        food_type = random.randint(1, 7)
        self.foods.append(Food(x, y, food_type))
        
    def update_foods(self):
        for food in self.foods[:]:
            food.update()
            # 화면을 벗어난 음식 제거 (5배 큰 크기와 작은 화면 고려)
            if (food.y > SCREEN_HEIGHT or 
                food.x < -300 or 
                food.x > SCREEN_WIDTH + 200):
                self.foods.remove(food)
                
    def check_food_collision(self, mouth_center):
        if not self.mouth_open:
            return
            
        mouth_x, mouth_y = mouth_center
        attraction_radius = 300  # 반경을 0.8배로 조정 (600 → 480)
        eat_radius = 50
        attraction_strength = 300  # 속도를 0.8배로 조정 (750 → 600)
        
        for food in self.foods[:]:
            if not food.eaten:
                # 음식 중심점 계산 (5배 큰 크기 고려)
                food_center_x = food.x + food.width // 2
                food_center_y = food.y + food.height // 2
                distance = sqrt((food_center_x - mouth_x)**2 + (food_center_y - mouth_y)**2)
                
                # 커비처럼 강력하게 빨아들이는 효과
                if distance < attraction_radius and distance > 0:
                    # 거리에 따른 강력한 끌어당기는 힘
                    force_multiplier = (attraction_radius - distance) / attraction_radius
                    attraction_force = attraction_strength * force_multiplier * force_multiplier  # 제곱으로 더 강하게
                    
                    # 입 방향 벡터 계산
                    dx = mouth_x - food_center_x
                    dy = mouth_y - food_center_y
                    
                    # 정규화하고 힘 적용
                    dx = (dx / distance) * attraction_force
                    dy = (dy / distance) * attraction_force
                    
                    # 음식 위치 업데이트
                    food.x += dx
                    food.y += dy
                    food.rect.x = food.x
                    food.rect.y = food.y
                
                # 실제로 먹기
                if distance < eat_radius:
                    food.eaten = True
                    self.foods.remove(food)
                    self.score += 10
                    # 먹을 때 파티클 효과
                    self.create_eat_particles(mouth_x, mouth_y)
                    # 효과음 재생
                    if coin_sound:
                        try:
                            coin_sound.play()
                        except:
                            pass
                    
    def create_heart_particles(self, x, y):
        """하트 제스처 성공 시 파티클 생성"""
        for _ in range(10):
            self.heart_particles.append({
                'x': x + random.randint(-50, 50),
                'y': y + random.randint(-30, 30),
                'speed': random.uniform(2, 5),
                'size': random.randint(8, 15),
                'color': (255, random.randint(100, 255), random.randint(150, 255)),
                'life': 80
            })
        
        for _ in range(15):
            self.sparkle_particles.append({
                'x': x + random.randint(-80, 80),
                'y': y + random.randint(-50, 50),
                'speed': random.uniform(1, 3),
                'size': random.randint(3, 8),
                'color': (random.randint(200, 255), random.randint(200, 255), random.randint(100, 255)),
                'life': 60
            })
    
    def create_eat_particles(self, x, y):
        """음식을 먹을 때 파티클 생성"""
        for _ in range(8):
            self.sparkle_particles.append({
                'x': x + random.randint(-30, 30),
                'y': y + random.randint(-20, 20),
                'speed': random.uniform(2, 5),
                'size': random.randint(5, 12),
                'color': (255, 255, random.randint(100, 255)),
                'life': 30
            })
    
    def update_particles(self):
        """파티클 업데이트"""
        # 하트 파티클 업데이트
        for particle in self.heart_particles[:]:
            particle['y'] -= particle['speed']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.heart_particles.remove(particle)
        
        # 스파클 파티클 업데이트
        for particle in self.sparkle_particles[:]:
            particle['y'] -= particle['speed']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.sparkle_particles.remove(particle)
    
    def draw_particles(self, screen):
        """파티클 그리기"""
        # 하트 파티클
        for particle in self.heart_particles:
            x, y = int(particle['x']), int(particle['y'])
            size = particle['size']
            color = particle['color']
            
            # 하트 모양 그리기
            # 왼쪽 원
            pygame.draw.circle(screen, color, (x - size//3, y - size//3), size//2)
            # 오른쪽 원
            pygame.draw.circle(screen, color, (x + size//3, y - size//3), size//2)
            # 하단 삼각형
            points = [(x, y + size//2), (x - size//2, y), (x + size//2, y)]
            pygame.draw.polygon(screen, color, points)
        
        # 스파클 파티클
        for particle in self.sparkle_particles:
            x, y = int(particle['x']), int(particle['y'])
            size = particle['size']
            color = particle['color']
            
            # 별 모양 그리기
            pygame.draw.line(screen, color, (x - size, y), (x + size, y), 2)
            pygame.draw.line(screen, color, (x, y - size), (x, y + size), 2)
            pygame.draw.line(screen, color, (x - size//2, y - size//2), (x + size//2, y + size//2), 1)
            pygame.draw.line(screen, color, (x + size//2, y - size//2), (x - size//2, y + size//2), 1)
                    
    def draw_ui(self, screen):
        """아기자기한 UI 그리기"""
        # 반투명 배경 오버레이 (상단)
        overlay = pygame.Surface((SCREEN_WIDTH, 150))
        overlay.set_alpha(180)
        overlay.fill((250, 230, 255))  # 파스텔 보라
        screen.blit(overlay, (0, 0))
        
        # 게임 제목 (폰트 크기 줄임)
        title_text = self.font_medium.render("음식 먹기 게임", True, (150, 100, 200))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 30))
        screen.blit(title_text, title_rect)
        
        # 점수 표시 (파스텔 핑크 배경)
        score_bg = pygame.Surface((200, 40))
        score_bg.set_alpha(200)
        score_bg.fill(PASTEL_PINK)
        screen.blit(score_bg, (20, 70))
        score_text = self.font_medium.render(f"점수: {self.score}", True, (255, 100, 150))
        screen.blit(score_text, (30, 80))
        
        # 시간 표시 (파스텔 블루 배경)
        time_bg = pygame.Surface((200, 40))
        time_bg.set_alpha(200)
        time_bg.fill(PASTEL_BLUE)
        screen.blit(time_bg, (SCREEN_WIDTH - 220, 70))
        time_text = self.font_medium.render(f"시간: {int(self.time_left)}", True, (100, 150, 255))
        screen.blit(time_text, (SCREEN_WIDTH - 210, 80))
        
        # 입 상태 표시 (귀여운 아이콘)
        mouth_status = "냠냠!" if self.mouth_open else "입을 동그랗게 벌려주세요"
        mouth_color = PASTEL_GREEN if self.mouth_open else PASTEL_PINK
        mouth_bg = pygame.Surface((280, 30))  # 텍스트가 길어져서 박스 크기 증가
        mouth_bg.set_alpha(200)
        mouth_bg.fill(mouth_color)
        screen.blit(mouth_bg, (20, 120))
        mouth_text = self.font_small.render(mouth_status, True, (100, 100, 100))
        screen.blit(mouth_text, (30, 125))

def draw_hand_skeleton(screen, landmarks):
    """손 골격을 그리는 함수"""
    # 손가락 연결선 정의 (MediaPipe 랜드마크 인덱스)
    connections = [
        # 엄지
        [0, 1, 2, 3, 4],
        # 검지
        [0, 5, 6, 7, 8],
        # 중지
        [0, 9, 10, 11, 12],
        # 약지
        [0, 13, 14, 15, 16],
        # 새끼손가락
        [0, 17, 18, 19, 20]
    ]
    
    # 손가락 끝점들을 화면에 그리기
    for i, landmark in enumerate(landmarks):
        x = int(landmark.x * SCREEN_WIDTH)
        y = int(landmark.y * SCREEN_HEIGHT)
        
        # 중요한 랜드마크만 그리기 (손가락 끝과 손목)
        if i in [0, 4, 8, 12, 16, 20]:  # 손목과 손가락 끝
            color = (255, 100, 100) if i == 0 else (100, 255, 100)  # 손목은 빨강, 손가락 끝은 초록
            pygame.draw.circle(screen, color, (x, y), 8)
            # 번호 표시
            number_text = font_small.render(str(i), True, (255, 255, 255))
            screen.blit(number_text, (x + 10, y - 10))
        else:
            # 다른 관절들은 작은 점으로
            pygame.draw.circle(screen, (255, 255, 100), (x, y), 4)
    
    # 손가락 연결선 그리기
    for connection in connections:
        for i in range(len(connection) - 1):
            start_idx = connection[i]
            end_idx = connection[i + 1]
            
            start_landmark = landmarks[start_idx]
            end_landmark = landmarks[end_idx]
            
            start_x = int(start_landmark.x * SCREEN_WIDTH)
            start_y = int(start_landmark.y * SCREEN_HEIGHT)
            end_x = int(end_landmark.x * SCREEN_WIDTH)
            end_y = int(end_landmark.y * SCREEN_HEIGHT)
            
            pygame.draw.line(screen, (255, 255, 0), (start_x, start_y), (end_x, end_y), 2)

def calculate_mouth_distance(landmarks, image_width, image_height):
    """입술 사이의 거리를 계산"""
    # 위쪽 입술과 아래쪽 입술의 중심점 계산
    upper_lip_y = landmarks[13].y * image_height  # 위쪽 입술 중심
    lower_lip_y = landmarks[14].y * image_height  # 아래쪽 입술 중심
    
    return abs(upper_lip_y - lower_lip_y)

def get_mouth_center(landmarks, image_width, image_height):
    """입의 중심점 계산"""
    mouth_x = landmarks[13].x * image_width
    mouth_y = (landmarks[13].y + landmarks[14].y) / 2 * image_height
    return (int(mouth_x), int(mouth_y))

def detect_heart_gesture(left_hand, right_hand):
    """두 손으로 하트 모양 만들기 감지 (더 관대한 조건)"""
    try:
        # 왼손 주요 포인트
        left_thumb = left_hand[4]  # 왼손 엄지 끝
        left_index = left_hand[8]  # 왼손 검지 끝
        
        # 오른손 주요 포인트
        right_thumb = right_hand[4]  # 오른손 엄지 끝
        right_index = right_hand[8]  # 오른손 검지 끝
        
        # 하트의 상단 두 점 사이의 거리 (엄지들)
        thumb_distance = math.sqrt(
            (left_thumb.x - right_thumb.x) ** 2 +
            (left_thumb.y - right_thumb.y) ** 2
        )
        
        # 하트의 하단 점 (검지들이 만나는 지점)
        index_distance = math.sqrt(
            (left_index.x - right_index.x) ** 2 +
            (left_index.y - right_index.y) ** 2
        )
        
        # 디버깅 정보 출력
        print(f"엄지 거리: {thumb_distance:.3f}, 검지 거리: {index_distance:.3f}")
        print(f"왼손 엄지Y: {left_thumb.y:.3f}, 왼손 검지Y: {left_index.y:.3f}")
        print(f"오른손 엄지Y: {right_thumb.y:.3f}, 오른손 검지Y: {right_index.y:.3f}")
        
        # 간단한 하트 모양 조건들 (더 관대하게)
        heart_conditions = [
            0.05 < thumb_distance < 0.30,  # 엄지들 사이 거리 (더 관대)
            index_distance < 0.10,  # 검지들 만남 (더 관대)
            left_thumb.y < left_index.y + 0.08,  # 왼손 구조 (더 관대)
            right_thumb.y < right_index.y + 0.08,  # 오른손 구조 (더 관대)
            abs(left_thumb.y - right_thumb.y) < 0.10,  # 엄지 높이 맞춤 (더 관대)
        ]
        
        satisfied_conditions = sum(heart_conditions)
        print(f"만족한 조건: {satisfied_conditions}/5")
        
        return satisfied_conditions >= 3  # 5개 중 3개 이상 만족하면 하트로 인식 (더 관대)
        
    except Exception as e:
        print(f"하트 감지 오류: {e}")
        return False

def load_high_score():
    """최고 점수 로드"""
    try:
        if os.path.exists("high_score.json"):
            with open("high_score.json", "r") as f:
                data = json.load(f)
                return data.get("food_eating_high_score", 0)
    except:
        pass
    return 0

def save_high_score(score):
    """최고 점수 저장"""
    try:
        data = {}
        if os.path.exists("high_score.json"):
            with open("high_score.json", "r") as f:
                data = json.load(f)
        
        if score > data.get("food_eating_high_score", 0):
            data["food_eating_high_score"] = score
            with open("high_score.json", "w") as f:
                json.dump(data, f)
            return True
    except:
        pass
    return False

def apply_beautify_filter(frame):
    """beautify 필터 적용 (피부 보정 효과)"""
    # 가우시안 블러로 부드럽게 만들기
    blurred = cv2.GaussianBlur(frame, (15, 15), 0)
    
    # 원본과 블러된 이미지를 적당히 섞어서 자연스러운 보정 효과
    beautified = cv2.addWeighted(frame, 0.7, blurred, 0.3, 0)
    
    # 밝기와 대비 조정으로 화사하게
    alpha = 1.1  # 대비
    beta = 15    # 밝기
    beautified = cv2.convertScaleAbs(beautified, alpha=alpha, beta=beta)
    
    # 색상 보정 (살짝 따뜻한 톤)
    beautified[:, :, 0] = np.clip(beautified[:, :, 0] * 1.05, 0, 255)  # 파란색 채널 약간 증가
    beautified[:, :, 2] = np.clip(beautified[:, :, 2] * 1.1, 0, 255)   # 빨간색 채널 증가
    
    return beautified

def main():
    # 고급 카메라 초기화 (Arducam 지원)
    if CAMERA_UTILS_AVAILABLE:
        camera_manager = CameraManager()
        cap = camera_manager.initialize_camera()
        if cap is None:
            print("[X] 카메라를 초기화할 수 없습니다!")
            return
    else:
        # 기본 카메라 초기화
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    clock = pygame.time.Clock()
    game_state = GameState()
    high_score = load_high_score()
    new_record = False
    
    # 게임 시작 화면
    waiting_for_start = True
    
    try:
        while True:
            if CAMERA_UTILS_AVAILABLE:
                frame = camera_manager.read_frame()
                if frame is None:
                    continue
            else:
                ret, frame = cap.read()
                if not ret:
                    continue
                
            # 프레임 좌우 반전
            frame = cv2.flip(frame, 1)
        
        # beautify 필터 적용
        frame = apply_beautify_filter(frame)
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 얼굴 및 손 인식
        face_results = face_mesh.process(rgb_frame)
        hand_results = hands.process(rgb_frame)
        
        # 하트 제스처 감지 (시작 또는 재시작 시에만)
        heart_detected = False
        hands_landmarks = []
        
        if hand_results.multi_hand_landmarks and (waiting_for_start or game_state.game_over):
            for hand_landmarks in hand_results.multi_hand_landmarks:
                hands_landmarks.append(hand_landmarks.landmark)
                
                # 손 골격 그리기
                draw_hand_skeleton(screen, hand_landmarks.landmark)
            
            # 하트 제스처 감지 (2개 손이 있을 때)
            if len(hands_landmarks) >= 2:
                heart_detected = detect_heart_gesture(hands_landmarks[0], hands_landmarks[1])
                if heart_detected:
                    # 하트 위치 계산 (첫 번째 손과 두 번째 손의 중점)
                    heart_x = int((hands_landmarks[0][4].x + hands_landmarks[1][4].x) / 2 * SCREEN_WIDTH)
                    heart_y = int((hands_landmarks[0][4].y + hands_landmarks[1][4].y) / 2 * SCREEN_HEIGHT)
                    game_state.create_heart_particles(heart_x, heart_y)
                    
                    # 하트 형태 시각화
                    left_thumb_x = int(hands_landmarks[0][4].x * SCREEN_WIDTH)
                    left_thumb_y = int(hands_landmarks[0][4].y * SCREEN_HEIGHT)
                    right_thumb_x = int(hands_landmarks[1][4].x * SCREEN_WIDTH)
                    right_thumb_y = int(hands_landmarks[1][4].y * SCREEN_HEIGHT)
                    left_index_x = int(hands_landmarks[0][8].x * SCREEN_WIDTH)
                    left_index_y = int(hands_landmarks[0][8].y * SCREEN_HEIGHT)
                    right_index_x = int(hands_landmarks[1][8].x * SCREEN_WIDTH)
                    right_index_y = int(hands_landmarks[1][8].y * SCREEN_HEIGHT)
                    
                    # 하트 모양 연결선 그리기 (더 굵고 핑크색으로)
                    pygame.draw.line(screen, (255, 100, 150), (left_thumb_x, left_thumb_y), (left_index_x, left_index_y), 6)
                    pygame.draw.line(screen, (255, 100, 150), (right_thumb_x, right_thumb_y), (right_index_x, right_index_y), 6)
                    pygame.draw.line(screen, (255, 100, 150), (left_index_x, left_index_y), (right_index_x, right_index_y), 6)
        
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    cap.release()
                    pygame.quit()
                    return
                elif event.key == pygame.K_F11:
                    # 전체화면 토글
                    pygame.display.toggle_fullscreen()
        
        # 하트 제스처로 게임 상태 제어
        current_time = pygame.time.get_ticks() / 1000.0
        if heart_detected and current_time - game_state.last_heart_time > game_state.heart_cooldown:
            game_state.last_heart_time = current_time
            if waiting_for_start:
                waiting_for_start = False
                game_state.game_started = True
                print("🎮 하트 제스처로 게임 시작!")
            elif game_state.game_over:
                # 게임 재시작
                game_state = GameState()
                game_state.game_started = True
                new_record = False
                print("🎮 하트 제스처로 게임 재시작!")
        
        screen.fill(BLACK)
        
        # 카메라 프레임을 pygame 표면으로 변환
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        frame_surface = pygame.transform.scale(frame_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(frame_surface, (0, 0))
        
        # 파티클 업데이트 및 그리기
        game_state.update_particles()
        game_state.draw_particles(screen)
        
        # 시작 화면
        if waiting_for_start:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(120)  # 투명도를 더 낮춤 (180에서 120으로)
            overlay.fill((250, 230, 255))  # 파스텔 보라 배경
            screen.blit(overlay, (0, 0))
            
            # 제목 (폰트 크기 줄임)
            title_text = game_state.font_medium.render("음식 먹기 게임", True, (150, 100, 200))
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150))
            screen.blit(title_text, title_rect)
            
            # 설명
            instruction1 = game_state.font_medium.render("입을 벌리고 떨어지는 음식을 먹으세요!", True, (120, 80, 160))
            instruction1_rect = instruction1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
            screen.blit(instruction1, instruction1_rect)
            
            instruction2 = game_state.font_medium.render("제한시간: 60초", True, (120, 80, 160))
            instruction2_rect = instruction2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
            screen.blit(instruction2, instruction2_rect)
            
            # 하트 제스처 안내
            heart_text = game_state.font_medium.render("손으로 하트를 그려서 시작하세요!", True, (255, 100, 150))
            heart_rect = heart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
            screen.blit(heart_text, heart_rect)
            
            # 하트 제스처 감지 표시
            if heart_detected:
                detected_text = game_state.font_small.render("하트 감지!", True, (255, 200, 200))
                detected_rect = detected_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
                screen.blit(detected_text, detected_rect)
            else:
                # 손 감지 상태 표시
                hand_count = len(hands_landmarks) if hands_landmarks else 0
                if hand_count >= 2:
                    guide_text = game_state.font_small.render("엄지끼리 가깝게, 검지끼리 아래서 만나게", True, (255, 255, 100))
                elif hand_count == 1:
                    guide_text = game_state.font_small.render("양손을 화면에 보여주세요", True, (255, 255, 100))
                else:
                    guide_text = game_state.font_small.render("손을 화면에 보여주세요", True, (255, 255, 100))
                guide_rect = guide_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
                screen.blit(guide_text, guide_rect)
            
            # 최고 점수
            high_score_text = game_state.font_small.render(f"최고 점수: {high_score}", True, (150, 100, 200))
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
            screen.blit(high_score_text, high_score_rect)
            
        # 게임 진행 중
        elif game_state.game_started and not game_state.game_over:
            # 얼굴 인식 및 입 상태 감지
            mouth_center = None
            forehead_pos = None
            if face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    # 입 거리 계산
                    mouth_distance = calculate_mouth_distance(face_landmarks.landmark, frame.shape[1], frame.shape[0])
                    game_state.mouth_open = mouth_distance > game_state.mouth_threshold
                    
                    # 입의 중심점 계산 (화면 좌표로 변환)
                    mouth_center = get_mouth_center(face_landmarks.landmark, SCREEN_WIDTH, SCREEN_HEIGHT)
                    
                    # 이마 위치 계산 (왕관을 위해)
                    forehead_landmark = face_landmarks.landmark[10]  # 이마 중앙 부분
                    forehead_x = int(forehead_landmark.x * SCREEN_WIDTH)
                    forehead_y = int(forehead_landmark.y * SCREEN_HEIGHT)
                    forehead_pos = (forehead_x, forehead_y)
                    
                    # 입 표시 (큰 동그라미)
                    mouth_color = PASTEL_GREEN if game_state.mouth_open else PASTEL_PINK
                    pygame.draw.circle(screen, mouth_color, mouth_center, 25, 5)  # 크기 15→25, 두께 3→5로 증가
            
            # 음식 생성
            game_state.food_spawn_timer += 1
            if game_state.food_spawn_timer >= game_state.food_spawn_interval:
                game_state.spawn_food()
                game_state.food_spawn_timer = 0
            
            # 음식 업데이트
            game_state.update_foods()
            
            # 음식과의 충돌 체크
            if mouth_center:
                game_state.check_food_collision(mouth_center)
            
            # 음식 그리기
            for food in game_state.foods:
                food.draw(screen)
            
            # 시간 업데이트 (실제 경과 시간 기준)
            if game_state.start_time is None:
                game_state.start_time = pygame.time.get_ticks()
            
            elapsed_time = (pygame.time.get_ticks() - game_state.start_time) / 1000.0  # 초 단위
            game_state.time_left = max(0, 60 - elapsed_time)  # 60초에서 경과 시간 빼기
            
            if game_state.time_left <= 0:
                game_state.game_over = True
                new_record = save_high_score(game_state.score)
                if new_record:
                    high_score = game_state.score
            
            # UI 그리기
            game_state.draw_ui(screen)
            
        # 게임 오버 화면
        elif game_state.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((240, 230, 255))  # 파스텔 라벤더
            screen.blit(overlay, (0, 0))
            
            # 게임 오버 배경 박스
            result_box = pygame.Surface((600, 400))
            result_box.set_alpha(220)
            result_box.fill((250, 240, 255))
            result_box_rect = result_box.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(result_box, result_box_rect)
            
            # 테두리
            pygame.draw.rect(screen, PASTEL_PURPLE, result_box_rect, 5)
            
            game_over_text = game_state.font_large.render("게임 종료!", True, (150, 100, 200))
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 120))
            screen.blit(game_over_text, game_over_rect)
            
            score_text = game_state.font_medium.render(f"최종 점수: {game_state.score}점", True, (255, 150, 200))
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
            screen.blit(score_text, score_rect)
            
            if new_record:
                record_text = game_state.font_medium.render("새로운 기록!", True, (255, 200, 100))
                record_rect = record_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
                screen.blit(record_text, record_rect)
            
            high_score_text = game_state.font_small.render(f"최고 점수: {high_score}점", True, (150, 100, 200))
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            screen.blit(high_score_text, high_score_rect)
            
            # 하트 제스처 재시작 안내
            restart_text = game_state.font_medium.render("하트를 그려서 다시 시작하세요!", True, (255, 100, 150))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
            screen.blit(restart_text, restart_rect)
            
            # 하트 제스처 감지 표시
            if heart_detected:
                detected_text = game_state.font_small.render("하트 감지! 재시작 중...", True, (255, 200, 200))
                detected_rect = detected_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
                screen.blit(detected_text, detected_rect)
            
            exit_text = game_state.font_small.render("ESC: 종료", True, (150, 150, 150))
            exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 160))
            screen.blit(exit_text, exit_rect)
        pygame.display.flip()
        clock.tick(60)
        
    except KeyboardInterrupt:
        print("\n게임이 중단되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if CAMERA_UTILS_AVAILABLE and 'camera_manager' in locals():
            camera_manager.release()
        elif 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        pygame.quit()
        print("게임 종료")

if __name__ == "__main__":
    main()
