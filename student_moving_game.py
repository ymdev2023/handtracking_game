import cv2
import numpy as np
import mediapipe as mp
import time
import os
import random
import math
import json
import pygame

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

class HandTrackingPixelPhotobooth:
    def __init__(self):
        """핸드 트래킹 픽셀 캐릭터 포토부스"""
        print("< 3 Hand Tracking Pixel Photobooth 초기화!")
        
        # Pygame 초기화 (효과음용)
        try:
            pygame.mixer.init()
            # confirmbeep-sfx.wav 로드
            if os.path.exists("confirmbeep-sfx.wav"):
                self.confirm_sound = pygame.mixer.Sound("confirmbeep-sfx.wav")
            else:
                self.confirm_sound = None
            print("✓ Pygame mixer 초기화 완료!")
        except Exception as e:
            print(f"[!] Pygame 초기화 실패: {e}")
            self.confirm_sound = None
        
        # MediaPipe Hands 초기화
        try:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            self.mp_draw = mp.solutions.drawing_utils
            print("✓ MediaPipe Hands 초기화 완료!")
        except Exception as e:
            print(f"[!] MediaPipe 초기화 실패: {e}")
            self.hands = None
        
        # 픽셀 캐릭터 로드
        self.load_pixel_characters()
        
        # 캐릭터 객체들
        self.characters = []
        self.spawn_timer = 0
        self.spawn_interval = 1.5  # 1.5초마다 캐릭터 스폰
        
        # 게임 상태
        self.game_state = "waiting"  # waiting, playing, finished
        self.game_start_time = time.time()
        self.game_duration = 30.0  # 30초 게임으로 변경
        self.score = 0
        self.target_zone_x = 0.7  # 화면 우측 70% 지점이 목표 구역
        self.moved_characters = set()  # 이미 점수가 계산된 캐릭터들
        
        # 최고 점수 시스템
        self.high_score_file = "high_score.json"
        self.high_score = self.load_high_score()
        
        # 폰트 설정
        self.font_path = "neodgm.ttf"
        self.load_font()
        
        # 캐릭터 중복 방지를 위한 리스트
        self.available_characters = []
        self.used_characters = []
        
        # 핸드 트래킹 상태
        self.pinch_distance = 0
        self.is_pinching = False
        self.selected_character = None
        self.pinch_threshold = 0.05
        self.drag_mode = False
        self.initial_pinch_scale = 1.0
        
        # 하트 제스처 상태 (게임 제어용)
        self.is_heart_gesture = False
        self.last_heart_time = 0
        self.heart_cooldown = 2.0  # 2초 쿨다운
        self.heart_debug_info = ""  # 화면 표시용 디버그 정보
        
        # 파티클 효과
        self.heart_particles = []
        self.sparkle_particles = []
        
        print("✓ 초기화 완료!")
    
    def load_pixel_characters(self):
        """픽셀 캐릭터 이미지 로드 (cha 폴더의 모든 캐릭터)"""
        self.character_images = []
        
        # cha 폴더의 모든 캐릭터 로드 (cha1.png ~ cha7.png)
        cha_folder = "cha"
        if not os.path.exists(cha_folder):
            print(f"[!] {cha_folder} 폴더를 찾을 수 없습니다. 현재 경로에서 캐릭터를 찾습니다.")
            cha_folder = "."
        
        # cha1.png부터 cha10.png까지 로드
        for i in range(1, 11):  # 1부터 10까지
            char_path = os.path.join(cha_folder, f"cha{i}.png")
            if os.path.exists(char_path):
                try:
                    # PIL로 이미지 로드 (알파 채널 포함)
                    pil_img = Image.open(char_path).convert("RGBA")
                    # OpenCV 형식으로 변환
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGRA)
                    self.character_images.append({
                        'image': cv_img,
                        'name': f"cha{i}",
                        'id': i
                    })
                    print(f"✓ cha{i}.png 로드 완료! 크기: {cv_img.shape}")
                except Exception as e:
                    print(f"[!] cha{i}.png 로드 실패: {e}")
            else:
                print(f"[!] cha{i}.png를 찾을 수 없습니다.")
        
        # 캐릭터가 하나도 로드되지 않은 경우 기본 캐릭터 생성
        if not self.character_images:
            print("[!] 캐릭터를 찾을 수 없어 기본 캐릭터를 생성합니다.")
            for i in range(1, 4):  # 기본 3개 캐릭터
                default_char = self.create_default_character(i)
                self.character_images.append({
                    'image': default_char,
                    'name': f"default{i}",
                    'id': i
                })
        
        print(f"✓ 총 {len(self.character_images)}개의 캐릭터 로드 완료!")
        
        # 캐릭터 풀 초기화 (중복 방지)
        self.reset_character_pool()
    
    def load_font(self):
        """neodgm.ttf 폰트 로드"""
        try:
            if os.path.exists(self.font_path):
                self.font_small = ImageFont.truetype(self.font_path, 16)
                self.font_medium = ImageFont.truetype(self.font_path, 24)
                self.font_large = ImageFont.truetype(self.font_path, 32)
                print(f"✓ {self.font_path} 폰트 로드 완료!")
            else:
                print(f"[!] {self.font_path}를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
                self.font_small = ImageFont.load_default()
                self.font_medium = ImageFont.load_default()
                self.font_large = ImageFont.load_default()
        except Exception as e:
            print(f"[!] 폰트 로드 실패: {e}. 기본 폰트를 사용합니다.")
            self.font_small = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
    
    def load_high_score(self):
        """최고 점수 로드"""
        try:
            if os.path.exists(self.high_score_file):
                with open(self.high_score_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    score = data.get('high_score', 0)
                    print(f"✓ 최고 점수 로드: {score}점")
                    return score
        except Exception as e:
            print(f"[!] 최고 점수 로드 실패: {e}")
        return 0
    
    def save_high_score(self):
        """최고 점수 저장"""
        try:
            data = {'high_score': self.high_score}
            with open(self.high_score_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ 최고 점수 저장: {self.high_score}점")
        except Exception as e:
            print(f"[!] 최고 점수 저장 실패: {e}")
    
    def update_high_score(self):
        """최고 점수 업데이트"""
        if self.score > self.high_score:
            old_score = self.high_score
            self.high_score = self.score
            self.save_high_score()
            print(f"🎉 새로운 최고 점수! {old_score} → {self.high_score}")
            return True
        return False
    
    def reset_character_pool(self):
        """캐릭터 풀 초기화 (중복 방지)"""
        self.available_characters = list(range(len(self.character_images)))
        self.used_characters = []
        random.shuffle(self.available_characters)
        print(f"✓ 캐릭터 풀 초기화: {len(self.available_characters)}개 캐릭터 준비")
    
    def create_default_character(self, char_type):
        """기본 픽셀 캐릭터 생성 (18x24)"""
        char = np.zeros((24, 18, 4), dtype=np.uint8)
        
        if char_type == 1:
            # 파란색 캐릭터
            # 머리
            char[6:18, 4:14] = [100, 150, 255, 255]  # 파란색 몸 (18 너비에 맞게 조정)
            # 눈
            char[10:12, 7:9] = [255, 255, 255, 255]  # 왼쪽 눈
            char[10:12, 10:12] = [255, 255, 255, 255]  # 오른쪽 눈
            # 입
            char[14:16, 8:11] = [255, 100, 100, 255]  # 빨간 입
        else:
            # 핑크색 캐릭터
            # 머리
            char[6:18, 4:14] = [255, 150, 200, 255]  # 핑크색 몸 (18 너비에 맞게 조정)
            # 눈
            char[10:12, 7:9] = [50, 50, 50, 255]   # 왼쪽 눈
            char[10:12, 10:12] = [50, 50, 50, 255]   # 오른쪽 눈
            # 입
            char[14:16, 8:11] = [255, 255, 255, 255] # 흰색 입
        
        return char
    
    def spawn_character(self, frame_width, frame_height):
        """왼쪽에서 새로운 캐릭터 스폰 (게임용, 중복 없이)"""
        if len(self.characters) < 8 and self.game_state == "playing":  # 최대 8개 캐릭터
            # 사용 가능한 캐릭터가 없으면 풀 리셋
            if not self.available_characters:
                self.reset_character_pool()
                print("🔄 모든 캐릭터 사용됨! 캐릭터 풀 리셋")
            
            # 다음 캐릭터 선택 (중복 없이)
            char_index = self.available_characters.pop(0)
            char_data = self.character_images[char_index]
            self.used_characters.append(char_index)
            
            char_width = int(18 * 3.0)  # 기본 너비 (18 * 3 = 54)
            char_height = int(24 * 3.0)  # 기본 높이 (24 * 3 = 72)
            
            # 왼쪽 30% 영역에서만 스폰 (UI 영역 피하기)
            spawn_area_width = int(frame_width * 0.3)
            safe_x = max(0, spawn_area_width - char_width)
            
            # Y 좌표: UI 영역(150픽셀) 아래부터 화면 하단까지
            spawn_area_top = 180  # UI 영역 + 여유공간
            spawn_area_bottom = frame_height - char_height - 20  # 하단 여유공간
            safe_y_min = spawn_area_top
            safe_y_max = max(spawn_area_top + 20, spawn_area_bottom)
            
            character = {
                'image': char_data['image'],
                'name': char_data['name'],
                'char_id': char_data['id'],
                'x': random.randint(0, max(1, safe_x)),
                'y': random.randint(safe_y_min, safe_y_max),
                'vel_x': 0,  # 게임에서는 자동 이동 없음
                'vel_y': 0,
                'scale': 3.0,
                'alpha': 255,
                'rotation': 0,
                'birth_time': time.time(),
                'life': 255.0,
                'is_dragging': False,
                'id': len(self.characters),  # 고유 ID 추가
                'scored': False  # 점수 획득 여부
            }
            self.characters.append(character)
            print(f"🎨 {char_data['name']} 캐릭터 스폰! (남은: {len(self.available_characters)}개)")
    
    def update_characters(self, frame_width, frame_height):
        """캐릭터 업데이트 (게임 로직)"""
        current_time = time.time()
        
        # 게임 시간 체크
        elapsed_time = current_time - self.game_start_time
        if elapsed_time >= self.game_duration and self.game_state == "playing":
            self.game_state = "finished"
            self._is_new_record = self.update_high_score()
            if self._is_new_record:
                print(f"🎉 게임 종료! 새로운 최고 점수: {self.score}점!")
            else:
                print(f"게임 종료! 최종 점수: {self.score}점 (최고: {self.high_score}점)")
        
        # 스폰 타이머 (게임 중일 때만)
        if (current_time - self.spawn_timer > self.spawn_interval and 
            self.game_state == "playing"):
            self.spawn_character(frame_width, frame_height)
            self.spawn_timer = current_time
        
        # 캐릭터 점수 체크
        target_x_position = frame_width * self.target_zone_x
        
        i = 0
        while i < len(self.characters):
            char = self.characters[i]
            
            # 목표 구역에 도달한 캐릭터 점수 계산
            if (char['x'] >= target_x_position and 
                char['id'] not in self.moved_characters and
                not char.get('is_dragging', False)):
                self.score += 1
                self.moved_characters.add(char['id'])
                
                # 점수 획득 시 귀여운 파티클 효과 생성
                char_center_x = char['x'] + (18 * char['scale']) // 2
                char_center_y = char['y'] + (24 * char['scale']) // 2
                self.create_score_particles(char_center_x, char_center_y)
                
                # 효과음 재생
                if self.confirm_sound:
                    try:
                        self.confirm_sound.play()
                    except:
                        pass
                
                print(f"🎉 점수! {char.get('name', '캐릭터')} - 현재 점수: {self.score}")
                
                # 10명 모두 옮겼을 때 특별 메시지
                if self.score >= 10:
                    print("🎊 축하해!! 모두를 다 옮겼구나!! 🎊")
                    # 특별 파티클 효과 추가
                    self.create_completion_celebration(frame_width, frame_height)
            
            # 드래그 중인 캐릭터는 물리 업데이트 스킵
            if char.get('is_dragging', False):
                i += 1
                continue
            
            # 경계 체크 (캐릭터가 화면을 벗어나지 않도록)
            char_width = int(18 * char['scale'])
            char_height = int(24 * char['scale'])
            
            char['x'] = max(-10, min(char['x'], frame_width - char_width + 10))
            char['y'] = max(-10, min(char['y'], frame_height - char_height + 10))
            
            i += 1
    
    def draw_character(self, frame, character):
        """캐릭터를 프레임에 그리기"""
        char_img = character['image']
        scale = character['scale']
        x, y = int(character['x']), int(character['y'])
        
        # 스케일링 (18x24 크기 기준)
        new_width = int(18 * scale)
        new_height = int(24 * scale)
        if new_width > 0 and new_height > 0:
            try:
                # 이미지 리사이즈 (18x24 비율 유지)
                resized = cv2.resize(char_img, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
                
                # 회전 (선택적) - 18x24 크기 기준
                if character.get('rotation', 0) != 0:
                    center = (new_width // 2, new_height // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, character['rotation'], 1.0)
                    resized = cv2.warpAffine(resized, rotation_matrix, (new_width, new_height))
                
                # 프레임에 합성 (알파 블렌딩)
                self.blend_character(frame, resized, x, y)
                
            except Exception as e:
                print(f"캐릭터 그리기 오류: {e}")
    
    def blend_character(self, frame, char_img, x, y):
        """알파 블렌딩으로 캐릭터 합성 (경계 처리 개선)"""
        h, w = char_img.shape[:2]
        frame_h, frame_w = frame.shape[:2]
        
        # 캐릭터와 프레임의 겹치는 영역 계산
        # 캐릭터 영역
        char_start_x = max(0, -x)
        char_start_y = max(0, -y)
        char_end_x = min(w, frame_w - x)
        char_end_y = min(h, frame_h - y)
        
        # 프레임 영역
        frame_start_x = max(0, x)
        frame_start_y = max(0, y)
        frame_end_x = min(frame_w, x + w)
        frame_end_y = min(frame_h, y + h)
        
        # 유효한 영역이 있는지 확인
        if (char_end_x <= char_start_x or char_end_y <= char_start_y or
            frame_end_x <= frame_start_x or frame_end_y <= frame_start_y):
            return
        
        # 겹치는 부분만 추출
        char_region = char_img[char_start_y:char_end_y, char_start_x:char_end_x]
        frame_region = frame[frame_start_y:frame_end_y, frame_start_x:frame_end_x]
        
        # 알파 채널이 있는 경우
        if char_img.shape[2] == 4:
            # BGR과 알파 분리
            char_bgr = char_region[:, :, :3]
            alpha = char_region[:, :, 3:4] / 255.0
            
            # 알파 블렌딩 (벡터화된 연산)
            blended = alpha * char_bgr + (1 - alpha) * frame_region
            frame[frame_start_y:frame_end_y, frame_start_x:frame_end_x] = blended.astype(np.uint8)
        else:
            # 알파 채널이 없는 경우 그냥 복사
            frame[frame_start_y:frame_end_y, frame_start_x:frame_end_x] = char_region
    
    def calculate_pinch_distance(self, landmarks):
        """엄지와 검지 사이의 거리 계산"""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        distance = math.sqrt(
            (thumb_tip.x - index_tip.x) ** 2 + 
            (thumb_tip.y - index_tip.y) ** 2
        )
        return distance
    
    def detect_heart_gesture(self, left_hand, right_hand):
        """두 손으로 하트 모양 만들기 감지 (더 관대한 조건)"""
        try:
            # 양손의 주요 지점들
            left_thumb = left_hand[4]
            left_index = left_hand[8]
            right_thumb = right_hand[4]
            right_index = right_hand[8]
            
            # 더 관대한 하트 제스처 조건들
            heart_conditions = [
                # 엄지들이 가까이 있어야 함 (하트의 상단 만남점) - 더 관대하게
                abs(left_thumb.x - right_thumb.x) < 0.15,  # 0.1에서 0.15로 증가
                abs(left_thumb.y - right_thumb.y) < 0.08,  # 0.05에서 0.08로 증가
                
                # 검지들이 가까이 있어야 함 (하트의 하단 만남점) - 더 관대하게
                abs(left_index.x - right_index.x) < 0.15,  # 0.1에서 0.15로 증가
                abs(left_index.y - right_index.y) < 0.08,  # 0.05에서 0.08로 증가
                
                # 검지가 엄지보다 아래쪽에 있어야 함 (하트의 아래쪽 모양)
                left_index.y > left_thumb.y - 0.02,   # 약간의 여유 추가
                right_index.y > right_thumb.y - 0.02, # 약간의 여유 추가
                
                # 좌우 대칭성 확인 - 더 관대하게
                left_thumb.x <= right_thumb.x + 0.05,  # 약간의 여유 추가
                left_index.x <= right_index.x + 0.05   # 약간의 여유 추가
            ]
            
            satisfied_conditions = sum(heart_conditions)
            
            # 디버그 정보 출력
            if satisfied_conditions >= 3:  # 어느 정도 조건을 만족할 때만 출력
                print(f"하트 조건 만족: {satisfied_conditions}/8")
                print(f"엄지 거리: x={abs(left_thumb.x - right_thumb.x):.3f}, y={abs(left_thumb.y - right_thumb.y):.3f}")
                print(f"검지 거리: x={abs(left_index.x - right_index.x):.3f}, y={abs(left_index.y - right_index.y):.3f}")
            
            # 디버그 정보 저장 (화면 표시용)
            if satisfied_conditions >= 5:
                self.heart_debug_info = f"하트 감지됨! ({satisfied_conditions}/8)"
            elif satisfied_conditions >= 3:
                self.heart_debug_info = f"하트 근사 ({satisfied_conditions}/8)"
            else:
                self.heart_debug_info = f"하트: {satisfied_conditions}/8"
            
            return satisfied_conditions >= 5  # 8개 중 5개 이상 만족하면 하트로 인식 (6에서 5로 완화)
            
        except Exception as e:
            print(f"하트 제스처 감지 오류: {e}")
            return False
    
    def find_nearest_character(self, hand_x, hand_y, frame_width, frame_height):
        """손에 가장 가까운 캐릭터 찾기"""
        # 정규화된 좌표를 픽셀 좌표로 변환
        pixel_x = int(hand_x * frame_width)
        pixel_y = int(hand_y * frame_height)
        
        nearest_char = None
        min_distance = float('inf')
        
        for char in self.characters:
            char_center_x = char['x'] + (18 * char['scale']) // 2
            char_center_y = char['y'] + (24 * char['scale']) // 2
            
            distance = math.sqrt(
                (pixel_x - char_center_x) ** 2 + 
                (pixel_y - char_center_y) ** 2
            )
            
            if distance < min_distance and distance < 100:  # 100픽셀 이내
                min_distance = distance
                nearest_char = char
        
        return nearest_char
    
    def process_hand_tracking(self, frame, results):
        """핸드 트래킹 처리 (하트=게임제어, 핀치=캐릭터조작)"""
        frame_height, frame_width = frame.shape[:2]
        current_time = time.time()
        
        if results.multi_hand_landmarks:
            # 양손 감지 확인
            left_hand = None
            right_hand = None
            
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # 손 랜드마크 그리기
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(255, 192, 203), thickness=2),
                    self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=1)
                )
                
                # 손의 위치로 좌우 구분 (간단한 방법)
                hand_center_x = sum([lm.x for lm in hand_landmarks.landmark]) / len(hand_landmarks.landmark)
                if hand_center_x < 0.5:  # 화면 기준 왼쪽에 있는 손
                    left_hand = hand_landmarks.landmark
                else:  # 화면 기준 오른쪽에 있는 손
                    right_hand = hand_landmarks.landmark
            
            # 하트 제스처 감지 (게임 제어용)
            if left_hand and right_hand:
                heart_detected = self.detect_heart_gesture(left_hand, right_hand)
                
                if heart_detected and not self.is_heart_gesture:
                    if current_time - self.last_heart_time > self.heart_cooldown:
                        self.is_heart_gesture = True
                        self.last_heart_time = current_time
                        
                        # 게임 상태에 따른 처리
                        if self.game_state == "waiting":
                            self.start_game()
                            print("💖 하트 제스처로 게임 시작!")
                        elif self.game_state == "finished":
                            self.restart_game()
                            print("💖 하트 제스처로 게임 재시작!")
                elif not heart_detected:
                    self.is_heart_gesture = False
                
                elif not heart_detected:
                    self.is_heart_gesture = False
            else:
                # 양손이 감지되지 않았을 때
                self.heart_debug_info = "양손이 필요합니다"
                
            # 하트 제스처 시각화
            if left_hand and right_hand and heart_detected:
                cv2.putText(frame, "💖 HEART DETECTED! 💖", (frame_width//2 - 100, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 150), 2)
            
            # 핀치 제스처 감지 (캐릭터 조작용 - 게임 중일 때만)
            if self.game_state == "playing":
                for hand_landmarks in results.multi_hand_landmarks:
                    landmarks = hand_landmarks.landmark
                    pinch_dist = self.calculate_pinch_distance(landmarks)
                    
                    # 손바닥 중심 계산 (검지 MCP 사용)
                    palm_x = landmarks[5].x  # 검지 MCP
                    palm_y = landmarks[5].y
                    
                    # 핀치 제스처 감지
                    if pinch_dist < self.pinch_threshold:
                        if not self.is_pinching:
                            # 핀치 시작 - 가장 가까운 캐릭터 선택
                            self.selected_character = self.find_nearest_character(
                                palm_x, palm_y, frame_width, frame_height
                            )
                            self.is_pinching = True
                            self.drag_mode = True
                            if self.selected_character:
                                # 초기 스케일 저장 (배율 변화 방지)
                                self.initial_pinch_scale = self.selected_character['scale']
                                self.selected_character['is_dragging'] = True
                                # 드래그 중 속도 초기화
                                self.selected_character['vel_x'] = 0
                                self.selected_character['vel_y'] = 0
                                print(f"캐릭터 선택됨! 드래그 모드 (크기: {self.selected_character['scale']:.1f})")
                        
                        # 핀치 중 - 캐릭터를 손 위치로 이동 (크기는 고정)
                        if self.selected_character and self.drag_mode:
                            # 캐릭터를 손 위치로 이동 (18x24 크기 기준)
                            char_width = int(18 * self.selected_character['scale'])
                            char_height = int(24 * self.selected_character['scale'])
                            
                            # 손 위치 계산 (캐릭터 중심을 손 위치에 맞춤)
                            hand_x = int(palm_x * frame_width)
                            hand_y = int(palm_y * frame_height)
                            
                            # 캐릭터가 화면을 벗어나지 않도록 제한 (여유 공간 고려)
                            margin = 10  # 경계에서 10픽셀 여유
                            target_x = max(-margin, min(
                                hand_x - char_width // 2,
                                frame_width - char_width + margin
                            ))
                            target_y = max(-margin, min(
                                hand_y - char_height // 2,
                                frame_height - char_height + margin
                            ))
                            
                            # 부드러운 이동을 위한 직접 할당
                            self.selected_character['x'] = target_x
                            self.selected_character['y'] = target_y
                            
                            # 드래그 중에는 속도 초기화
                            self.selected_character['vel_x'] = 0
                            self.selected_character['vel_y'] = 0
                    else:
                        if self.is_pinching and self.drag_mode:
                            # 핀치 종료 - 캐릭터 놓기
                            if self.selected_character:
                                # 놓을 때 현재 위치에 고정하고 약간의 랜덤 속도 부여
                                self.selected_character['vel_x'] = random.uniform(-0.5, 0.5)
                                self.selected_character['vel_y'] = random.uniform(-0.5, 0.5)
                                self.selected_character['is_dragging'] = False
                                print(f"캐릭터 해제됨! 위치: ({self.selected_character['x']}, {self.selected_character['y']})")
                            self.is_pinching = False
                            self.drag_mode = False
                            self.selected_character = None
                    
                    # 핀치 거리 시각화 (게임 중일 때만)
                    thumb_pos = (int(landmarks[4].x * frame_width), int(landmarks[4].y * frame_height))
                    index_pos = (int(landmarks[8].x * frame_width), int(landmarks[8].y * frame_height))
                    
                    # 핀치 라인 그리기
                    if self.is_pinching and self.drag_mode:
                        color = (0, 255, 0)  # 초록색 - 드래그 중
                    else:
                        color = (255, 255, 255)  # 흰색 - 일반 상태
                    
                    cv2.line(frame, thumb_pos, index_pos, color, 2)
                    
                    # 핀치 거리 텍스트
                    cv2.putText(frame, f"Pinch: {pinch_dist:.3f}", 
                               (10, frame_height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            # 손이 감지되지 않으면 모든 제스처 해제
            if self.is_pinching and self.selected_character:
                self.selected_character['vel_x'] = random.uniform(-0.5, 0.5)
                self.selected_character['vel_y'] = random.uniform(-0.5, 0.5)
                self.selected_character['is_dragging'] = False
                print("손 감지 안됨 - 캐릭터 해제!")
            self.is_pinching = False
            self.drag_mode = False
            self.selected_character = None
            self.is_heart_gesture = False

    def create_completion_celebration(self, frame_width, frame_height):
        """10명 완주 시 특별 축하 파티클 효과"""
        # 화면 전체에 더 많은 하트 파티클
        for _ in range(20):
            self.heart_particles.append({
                'x': random.randint(0, frame_width),
                'y': random.randint(0, frame_height),
                'speed': random.uniform(1, 3),
                'size': random.randint(15, 25),
                'color': (255, random.randint(100, 255), random.randint(150, 255)),
                'life': 120  # 더 오래 지속
            })
        
        # 화면 전체에 더 많은 반짝이 파티클
        for _ in range(30):
            self.sparkle_particles.append({
                'x': random.randint(0, frame_width),
                'y': random.randint(0, frame_height),
                'speed': random.uniform(0.5, 2),
                'size': random.randint(3, 8),
                'color': (random.randint(200, 255), random.randint(200, 255), random.randint(100, 255)),
                'life': 100
            })

    def create_score_particles(self, x, y):
        """점수 획득 시 귀여운 파티클 효과 생성"""
        # 하트 파티클 생성
        for _ in range(5):
            self.heart_particles.append({
                'x': x + random.randint(-20, 20),
                'y': y + random.randint(-10, 10),
                'speed': random.uniform(2, 4),
                'size': random.randint(8, 15),
                'color': (random.randint(200, 255), random.randint(100, 200), 255),
                'life': 60  # 더 오래 지속
            })
        
        # 반짝이 파티클 생성
        for _ in range(8):
            self.sparkle_particles.append({
                'x': x + random.randint(-30, 30),
                'y': y + random.randint(-20, 20),
                'life': 40,
                'size': random.randint(3, 8),
                'color': (255, 255, random.randint(100, 255)),
                'vel_x': random.uniform(-2, 2),
                'vel_y': random.uniform(-3, -1)
            })
    
    def update_particles(self, frame):
        """파티클 업데이트"""
        h, w = frame.shape[:2]
        
        # 하트 파티클 생성
        if len(self.heart_particles) < 10:
            self.heart_particles.append({
                'x': np.random.randint(0, w),
                'y': h,
                'speed': np.random.uniform(1, 3),
                'size': np.random.randint(3, 8),
                'color': (np.random.randint(100, 255), np.random.randint(100, 255), 255)
            })
        
        # 반짝이 파티클 생성
        if len(self.sparkle_particles) < 15:
            self.sparkle_particles.append({
                'x': np.random.randint(0, w),
                'y': np.random.randint(0, h),
                'life': 30,
                'size': np.random.randint(2, 5),
                'color': (255, 255, np.random.randint(150, 255))
            })
    
    def draw_particles(self, frame):
        """귀여운 파티클 그리기"""
        # 하트 파티클
        for particle in self.heart_particles[:]:
            # 위치 업데이트
            particle['y'] -= particle['speed']
            if hasattr(particle, 'life'):
                particle['life'] -= 1
                if particle['life'] <= 0:
                    self.heart_particles.remove(particle)
                    continue
            elif particle['y'] < -10:
                self.heart_particles.remove(particle)
                continue
            
            # 하트 모양 그리기 (귀여운 효과)
            x, y = int(particle['x']), int(particle['y'])
            size = particle['size']
            color = particle['color']
            
            # 하트의 두 원
            cv2.circle(frame, (x - size//3, y - size//3), size//2, color, -1)
            cv2.circle(frame, (x + size//3, y - size//3), size//2, color, -1)
            # 하트의 삼각형 부분
            triangle = np.array([[x, y + size//2], 
                               [x - size//2, y], 
                               [x + size//2, y]], np.int32)
            cv2.fillPoly(frame, [triangle], color)
        
        # 반짝이 파티클 (별 모양)
        for particle in self.sparkle_particles[:]:
            if 'vel_x' in particle and 'vel_y' in particle:
                particle['x'] += particle['vel_x']
                particle['y'] += particle['vel_y']
            
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.sparkle_particles.remove(particle)
                continue
            
            # 별 모양 그리기
            x, y = int(particle['x']), int(particle['y'])
            size = particle['size']
            color = particle['color']
            
            # 십자 모양의 별
            cv2.line(frame, (x - size, y), (x + size, y), color, 2)
            cv2.line(frame, (x, y - size), (x, y + size), color, 2)
            cv2.line(frame, (x - size//2, y - size//2), (x + size//2, y + size//2), color, 1)
            cv2.line(frame, (x + size//2, y - size//2), (x - size//2, y + size//2), color, 1)
    
    def draw_ui(self, frame):
        """UI 그리기 (PIL + neodgm 폰트 사용)"""
        h, w = frame.shape[:2]
        
        # OpenCV frame을 PIL Image로 변환 (RGBA 모드 사용)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb).convert('RGBA')
        
        # 반투명 오버레이 생성
        overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # 파스텔 배경 오버레이 (상단)
        draw.rectangle([(0, 0), (w, 140)], fill=(250, 230, 255, 180))
        
        # 게임 제목 (neodgm 폰트)
        title_text = "친구들을 옮겨줘!"
        try:
            title_bbox = draw.textbbox((0, 0), title_text, font=self.font_large)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text(((w - title_width) // 2, 10), title_text, 
                     fill=(150, 100, 200, 255), font=self.font_large)
        except Exception as e:
            print(f"[!] 제목 텍스트 렌더링 오류: {e}")
            # 대체 텍스트 (영어)
            draw.text((w//2 - 100, 10), "Move Friends!", 
                     fill=(150, 100, 200, 255), font=self.font_large)
        
        # 오버레이를 원본 이미지에 합성
        pil_image = Image.alpha_composite(pil_image, overlay)
        
        # 게임 UI 표시
        self.draw_game_ui_pil(ImageDraw.Draw(pil_image), w, h)
        
        # PIL에서 OpenCV로 다시 변환 (RGB로 변환 후)
        pil_image = pil_image.convert('RGB')
        frame_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        frame[:] = frame_bgr[:]
        
        # OpenCV로 구역 표시 (PIL로는 복잡한 도형 그리기가 어려움)
        self.draw_zones_opencv(frame, w, h)
    
    def draw_zones_opencv(self, frame, w, h):
        """구역 표시 (OpenCV 사용)"""
        # 목표 구역 표시 (파스텔 민트)
        target_x = int(w * self.target_zone_x)
        cv2.rectangle(frame, (target_x, 180), (w, h), (180, 255, 200), 3)
        
        # 스폰 구역 표시 (파스텔 피치) - 실제 스폰 영역과 일치
        spawn_x = int(w * 0.3)
        cv2.rectangle(frame, (0, 180), (spawn_x, h), (200, 180, 255), 3)
    
    def safe_draw_text(self, draw, position, text, color, font):
        """안전한 텍스트 렌더링 (한글 지원)"""
        try:
            draw.text(position, text, fill=color, font=font)
        except Exception as e:
            print(f"[!] 텍스트 렌더링 오류: {e}")
            # 영어 대체 텍스트 또는 기본 폰트 사용
            try:
                draw.text(position, text, fill=color, font=ImageFont.load_default())
            except:
                # 최종 대체안: 간단한 ASCII 문자
                draw.text(position, "TEXT", fill=color, font=ImageFont.load_default())
    
    def safe_draw_text(self, draw, position, text, color, font):
        """한국어 텍스트를 안전하게 그리는 함수"""
        try:
            # RGBA 이미지에서 한국어 텍스트 렌더링
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 텍스트 이미지 생성
            text_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((10, 10), text, fill=color, font=font)
            
            # 원본 이미지에 합성
            draw._image.paste(text_img, position, text_img)
        except Exception as e:
            # 한국어 렌더링 실패 시 영어로 대체
            english_text = "Game UI"
            if "하트" in text or "Heart" in text:
                english_text = "Make Heart to Start!"
            elif "시작" in text:
                english_text = "START"
            elif "종료" in text:
                english_text = "END"
            elif "점수" in text or "Score" in text:
                english_text = f"Score: {self.score}"
            elif "시간" in text:
                english_text = text.replace("시간:", "Time:").replace("초", "s")
            elif "최고점" in text:
                english_text = f"Best: {self.high_score}"
                
            draw.text(position, english_text, fill=color, font=font)

    def draw_game_ui_pil(self, draw, w, h):
        """게임 UI 표시 (PIL 버전)"""
        current_time = time.time()
        elapsed_time = current_time - self.game_start_time
        remaining_time = max(0, self.game_duration - elapsed_time)
        
        # 시간 표시 (파스텔 컬러)
        if self.game_state == "waiting":
            time_color = (200, 150, 255, 255)  # 파스텔 퍼플
            time_text = "시작 준비!"
        elif remaining_time > 10:
            time_color = (150, 255, 150, 255)  # 파스텔 그린
            time_text = f"시간: {remaining_time:.1f}초"
        elif remaining_time > 5:
            time_color = (150, 220, 255, 255)  # 파스텔 블루
            time_text = f"시간: {remaining_time:.1f}초"
        else:
            time_color = (255, 180, 180, 255)  # 파스텔 핑크
            time_text = f"시간: {remaining_time:.1f}초"
        
        # 안전한 텍스트 렌더링
        self.safe_draw_text(draw, (20, 50), time_text, time_color, self.font_medium)
        
        # 점수 표시 (핑크색)
        score_text = f"점수: {self.score}"
        self.safe_draw_text(draw, (20, 80), score_text, (255, 150, 200, 255), self.font_medium)
        
        # 하트 디버그 정보 표시 (작은 글씨, 상단 좌측)
        if hasattr(self, 'heart_debug_info') and self.heart_debug_info:
            self.safe_draw_text(draw, (20, 110), self.heart_debug_info, (200, 200, 200, 180), self.font_small)
        
        # 최고 점수 표시 (핑크색)
        high_score_text = f"최고점: {self.high_score}"
        try:
            high_score_bbox = draw.textbbox((0, 0), high_score_text, font=self.font_medium)
            high_score_width = high_score_bbox[2] - high_score_bbox[0]
            self.safe_draw_text(draw, (w - high_score_width - 20, 50), high_score_text, 
                               (255, 150, 200, 255), self.font_medium)
        except:
            # 대체 표시
            self.safe_draw_text(draw, (w - 150, 50), f"Best: {self.high_score}", 
                               (255, 150, 200, 255), self.font_medium)
        
        # 게임 상태별 메시지
        if self.game_state == "waiting":
            # 시작 대기 메시지
            start_text = "손으로 하트를 그려 게임 시작!"
            try:
                start_bbox = draw.textbbox((0, 0), start_text, font=self.font_large)
                start_width = start_bbox[2] - start_bbox[0]
                self.safe_draw_text(draw, ((w - start_width) // 2, h // 2), start_text, 
                                   (255, 200, 220, 255), self.font_large)
            except:
                # 대체 메시지
                self.safe_draw_text(draw, (w//2 - 100, h//2), "Make Heart to Start!", 
                                   (255, 200, 220, 255), self.font_large)
            
            desc_text = "30초 안에 캐릭터들을 오른쪽으로 옮겨주세요!"
            try:
                self.safe_draw_text(draw, ((w - 400) // 2, h // 2 + 50), desc_text, 
                                   (200, 180, 255, 255), self.font_medium)
            except:
                self.safe_draw_text(draw, ((w - 300) // 2, h // 2 + 50), "Move characters to the right!", 
                                   (200, 180, 255, 255), self.font_medium)
        
        elif self.game_state == "playing":
            # 10명 달성 시 특별 메시지
            if self.score >= 10:
                celebration_text = "축하해!! 모두를 다 옮겼구나!!"
                self.safe_draw_text(draw, ((w - 400) // 2, h // 2 - 50), celebration_text, 
                                   (255, 100, 200, 255), self.font_large)
                
                perfect_text = "PERFECT!"
                self.safe_draw_text(draw, ((w - 200) // 2, h // 2), perfect_text, 
                                   (255, 200, 100, 255), self.font_large)
            else:
                instruction_text = "캐릭터를 목표 구역으로 드래그하세요!"
                self.safe_draw_text(draw, ((w - 400) // 2, h - 60), instruction_text, 
                                   (180, 255, 200, 255), self.font_medium)
        
        else:
            # 게임 종료 메시지
            # 반투명 배경
            draw.rectangle([(w//2 - 250, h//2 - 100), (w//2 + 250, h//2 + 120)], 
                          fill=(240, 230, 255, 220))
            draw.rectangle([(w//2 - 250, h//2 - 100), (w//2 + 250, h//2 + 120)], 
                          outline=(200, 150, 255), width=3)
            
            # 게임 오버 텍스트
            game_over_text = "게임 종료!"
            self.safe_draw_text(draw, ((w - 150) // 2, h//2 - 60), game_over_text, 
                               (255, 100, 150, 255), self.font_large)
            
            # 최종 점수 (핑크색)
            final_score_text = f"최종 점수: {self.score}점"
            self.safe_draw_text(draw, ((w - 200) // 2, h//2 - 10), final_score_text, 
                               (255, 150, 200, 255), self.font_medium)
            
            # 새 기록 표시
            if hasattr(self, '_is_new_record') and self._is_new_record:
                new_record_text = "🎉 새로운 최고 기록! 🎉"
                self.safe_draw_text(draw, ((w - 300) // 2, h//2 + 20), new_record_text, 
                                   (255, 200, 100, 255), self.font_medium)
            
            # 재시작 안내
            restart_text = "하트를 그려 다시 시작!"
            self.safe_draw_text(draw, ((w - 250) // 2, h//2 + 60), restart_text, 
                               (200, 200, 255, 255), self.font_medium)
    
    def start_game(self):
        """게임 시작"""
        self.game_state = "playing"
        self.game_start_time = time.time()
        self.score = 0
        self.characters.clear()
        self.moved_characters.clear()
        self.spawn_timer = 0
        self.is_pinching = False
        self.selected_character = None
        self.drag_mode = False
        self._is_new_record = False
        
        # 캐릭터 풀 리셋 (새 게임에서 모든 캐릭터 다시 사용 가능)
        self.reset_character_pool()
        print("30초 친구들 옮기기 게임 시작!")
    
    def restart_game(self):
        """게임 재시작"""
        self.start_game()  # start_game과 동일한 로직
        print("🎮 게임 재시작! 새로운 캐릭터들과 함께!")
    
    def run(self):
        """메인 실행"""
        print("\n🎮 🎮 친구들을 옮겨줘! 🎮 🎮")
        print("=" * 60)
        print("*** 30초 안에 왼쪽 캐릭터들을 오른쪽으로 옮기세요!")
        print("*** � 손으로 하트를 그려주세요 (게임 시작 및 재시작)!")
        print("*** ✋ 엄지와 검지를 모아서 캐릭터를 잡고 드래그!")
        print("*** 🎯 목표: 오른쪽 파스텔 목표 구역에 최대한 많은 캐릭터 이동!")
        print("*** 📊 최고 점수가 자동으로 저장됩니다!")
        print("*** 🎨 neodgm 폰트와 파스텔 UI로 업그레이드!")
        print("*** 📸 S키: 스크린샷 저장, ESC: 종료")
        print("=" * 60)
        
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
            if not cap.isOpened():
                print("[X] 웹캠을 열 수 없습니다!")
                return
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
        print("✓ 웹캠 초기화 완료!")
        
        # OpenCV 창 전체화면 설정
        window_name = '🎮 친구들을 옮겨줘! (ESC: 종료, F11: 전체화면 토글)'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        particles_enabled = True
        
        try:
            while True:
                if CAMERA_UTILS_AVAILABLE:
                    ret, frame = camera_manager.read_frame()
                    if not ret or frame is None:
                        break
                else:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        break
                
                frame = cv2.flip(frame, 1)
                frame_height, frame_width = frame.shape[:2]
                
                # 핸드 트래킹
                if self.hands:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.hands.process(rgb_frame)
                    self.process_hand_tracking(frame, results)
                
                # 캐릭터 업데이트 및 그리기
                self.update_characters(frame_width, frame_height)
                for character in self.characters:
                    self.draw_character(frame, character)
                
                # 파티클 효과
                if particles_enabled:
                    self.update_particles(frame)
                    self.draw_particles(frame)
                
                # UI 그리기
                self.draw_ui(frame)
                
                cv2.imshow(window_name, frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC - 종료
                    break
                elif key == ord('s'):  # S - 스크린샷 저장
                    filename = f"pixel_game_{int(time.time())}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"\n📸 게임 스크린샷 저장: {filename}")
                elif key == 255:  # F11 - 전체화면 토글 (일부 시스템에서)
                    # 전체화면 상태 토글
                    fullscreen = cv2.getWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN)
                    if fullscreen == cv2.WINDOW_FULLSCREEN:
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                    else:
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                elif key == ord('c'):  # C - 캐릭터 전체 삭제 (디버그용)
                    self.characters.clear()
                    self.moved_characters.clear()
                    print("\n🗑️ 모든 캐릭터 삭제!")
                    
                # 핀치 제스처 안내 메시지
                if self.game_state == "waiting":
                    # 첫 게임 대기 중에는 추가 안내 없음 (UI에 표시됨)
                    pass
                elif self.game_state == "finished":
                    # 게임 끝난 후에는 추가 안내 없음 (UI에 표시됨)
                    pass
                    
        except KeyboardInterrupt:
            print("\n[X] 프로그램을 종료합니다.")
        except Exception as e:
            print(f"[X] 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if CAMERA_UTILS_AVAILABLE and 'camera_manager' in locals():
                camera_manager.release()
            elif 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()
            print("\n< 3 Hand Tracking Pixel Photobooth 종료!")


def main():
    try:
        print("< 3 Hand Tracking Pixel Photobooth 시작!")
        photobooth = HandTrackingPixelPhotobooth()
        photobooth.run()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
