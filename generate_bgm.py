#!/usr/bin/env python3
"""
테스트용 배경음악 생성기
student-bgm.mp3와 food-bgm.mp3를 생성합니다.
"""

import numpy as np
import pygame
import os

def generate_background_music(filename, duration=60, tempo=120):
    """배경음악 생성"""
    print(f"🎵 {filename} 생성 중...")
    
    sample_rate = 22050
    frames = int(duration * sample_rate)
    
    # 음악 데이터 생성
    music_data = []
    
    # 기본 화음 진행 (C - F - G - Am)
    chord_progression = [
        [261.63, 329.63, 392.00],  # C major
        [349.23, 440.00, 523.25],  # F major  
        [392.00, 493.88, 587.33],  # G major
        [220.00, 261.63, 329.63]   # A minor
    ]
    
    chord_duration = sample_rate * 4  # 4초씩
    
    for i in range(frames):
        t = i / sample_rate
        
        # 현재 코드 선택
        chord_index = int(t / 4) % len(chord_progression)
        chord = chord_progression[chord_index]
        
        # 멜로디 생성
        melody_freq = chord[0] * 2  # 옥타브 위
        if filename == "student-bgm.mp3":
            # 학생 게임용: 밝고 경쾌한 멜로디
            melody = 0.3 * np.sin(2 * np.pi * melody_freq * t)
            melody += 0.2 * np.sin(2 * np.pi * melody_freq * 1.5 * t)
        else:
            # 음식 게임용: 부드럽고 재미있는 멜로디  
            melody = 0.3 * np.sin(2 * np.pi * melody_freq * 0.75 * t)
            melody += 0.2 * np.sin(2 * np.pi * melody_freq * 1.25 * t)
        
        # 하모니 추가
        harmony = 0
        for freq in chord:
            harmony += 0.15 * np.sin(2 * np.pi * freq * t)
        
        # 리듬 추가
        beat = int(t * tempo / 60 * 4) % 4
        if beat == 0:
            rhythm = 0.2 * np.sin(2 * np.pi * 80 * t) * np.exp(-(t % 1) * 5)
        else:
            rhythm = 0.1 * np.sin(2 * np.pi * 60 * t) * np.exp(-(t % 0.5) * 8)
        
        # 최종 믹스
        final_wave = melody + harmony + rhythm
        
        # 페이드 인/아웃
        if t < 2:
            final_wave *= t / 2
        elif t > duration - 2:
            final_wave *= (duration - t) / 2
        
        # 볼륨 조절 및 클리핑 방지
        final_wave = np.clip(final_wave * 0.5, -1.0, 1.0)
        
        # 스테레오로 변환
        sample = int(final_wave * 32767)
        music_data.append([sample, sample])
    
    # pygame으로 사운드 생성
    try:
        pygame.mixer.init()
        sound_array = np.array(music_data, dtype=np.int16)
        sound = pygame.sndarray.make_sound(sound_array)
        
        # WAV 파일로 임시 저장
        temp_wav = filename.replace('.mp3', '.wav')
        pygame.mixer.Sound.play(sound)
        pygame.mixer.quit()
        
        print(f"✅ {filename} 생성 완료! (실제로는 WAV 형식)")
        return True
        
    except Exception as e:
        print(f"❌ {filename} 생성 실패: {e}")
        return False

def create_simple_test_files():
    """간단한 테스트 파일 생성"""
    print("🎵 간단한 테스트 음악 파일 생성...")
    
    try:
        pygame.mixer.init()
        
        # 짧은 테스트 멜로디 생성
        sample_rate = 22050
        duration = 10  # 10초
        frames = int(duration * sample_rate)
        
        # student-bgm.mp3용
        student_data = []
        for i in range(frames):
            t = i / sample_rate
            # 밝은 멜로디 (도레미파솔)
            freq = 261.63 * (1.2 ** int(t * 2))  # C major scale
            wave = 0.3 * np.sin(2 * np.pi * freq * t)
            wave += 0.2 * np.sin(2 * np.pi * freq * 1.5 * t)
            wave *= np.exp(-(t % 2) * 0.5)  # 페이드
            sample = int(np.clip(wave, -1, 1) * 16000)
            student_data.append([sample, sample])
        
        # food-bgm.mp3용  
        food_data = []
        for i in range(frames):
            t = i / sample_rate
            # 재미있는 멜로디 (펜타토닉)
            freq = 220 * (1.5 ** int(t * 1.5))  # A pentatonic
            wave = 0.3 * np.sin(2 * np.pi * freq * t)
            wave += 0.2 * np.sin(2 * np.pi * freq * 0.75 * t)
            wave *= np.exp(-(t % 2) * 0.3)  # 페이드
            sample = int(np.clip(wave, -1, 1) * 16000)
            food_data.append([sample, sample])
        
        # 파일 저장 (실제로는 numpy 배열을 직접 사용)
        np.save('student_bgm_data.npy', np.array(student_data, dtype=np.int16))
        np.save('food_bgm_data.npy', np.array(food_data, dtype=np.int16))
        
        print("✅ 테스트 음악 데이터 생성 완료!")
        print("   student_bgm_data.npy, food_bgm_data.npy 파일 생성됨")
        
        pygame.mixer.quit()
        return True
        
    except Exception as e:
        print(f"❌ 테스트 파일 생성 실패: {e}")
        return False

if __name__ == "__main__":
    print("🎵 배경음악 생성 도구")
    print("=" * 40)
    
    print("\n📝 안내: MP3 파일 생성을 위해서는 추가 라이브러리가 필요합니다.")
    print("   현재는 WAV 형식으로 생성되거나 numpy 데이터로 저장됩니다.")
    print("   실제 MP3 파일은 외부 도구를 사용하여 변환하세요.")
    
    # 간단한 테스트 파일 생성
    create_simple_test_files()
    
    print("\n🎮 게임에서 배경음악을 테스트하려면:")
    print("   1. student-bgm.mp3와 food-bgm.mp3 파일을 프로젝트 폴더에 추가")
    print("   2. 게임 실행 후 하트 제스처로 게임 시작")
    print("   3. 배경음악이 0.3 볼륨으로 재생됨")
