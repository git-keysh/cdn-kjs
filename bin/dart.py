import cv2
import mediapipe as mp
import pygame
import random
import math
import sys
import numpy as np

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dart Machine by WSS")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 50)
PURPLE = (255, 50, 255)
BULLSEYE = (255, 200, 50)
CURSOR_COLOR = (0, 255, 255)
GOLD = (255, 215, 0)

# Game settings
BASE_TARGET_SIZE = 60
target_size = BASE_TARGET_SIZE
target_growing = True
target_size_speed = 1.2

SCORE_ZONES = {
    'bullseye': {'radius_factor': 0.2, 'points': 100, 'color': BULLSEYE},
    'inner': {'radius_factor': 0.42, 'points': 50, 'color': RED},
    'outer': {'radius_factor': 0.67, 'points': 25, 'color': BLUE},
    'edge': {'radius_factor': 1.0, 'points': 10, 'color': WHITE}
}

# Game variables
DART_TRAIL_LENGTH = 30
MAX_DARTS = 30  # More darts for longer gameplay
darts_thrown = 0
score = 0
high_score = 0
combo = 0
last_was_bullseye = False
game_state = "playing"

# Target movement
target_x = SCREEN_WIDTH // 2
target_y = SCREEN_HEIGHT // 2
target_dx = random.choice([-5, -4, 4, 5])
target_dy = random.choice([-5, -4, 4, 5])

# Dart trail
dart_trail = []

# Camera setup - Higher resolution for better tracking
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)

# MediaPipe with performance settings for good computer
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, 
    max_num_hands=1, 
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1  # Use full model for better tracking
)
mp_draw = mp.solutions.drawing_utils

# Fonts
font_huge = pygame.font.Font(None, 140)
font_large = pygame.font.Font(None, 80)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)
font_tiny = pygame.font.Font(None, 24)

# Smooth cursor movement
cursor_smooth_x = SCREEN_WIDTH // 2
cursor_smooth_y = SCREEN_HEIGHT // 2
cursor_speed = 0.3  # Smoothing factor

def get_current_radii():
    current_radius = target_size
    return {
        'bullseye': current_radius * SCORE_ZONES['bullseye']['radius_factor'],
        'inner': current_radius * SCORE_ZONES['inner']['radius_factor'],
        'outer': current_radius * SCORE_ZONES['outer']['radius_factor'],
        'edge': current_radius * SCORE_ZONES['edge']['radius_factor']
    }

def check_score(tip_x, tip_y):
    global combo, last_was_bullseye
    
    distance = math.sqrt((tip_x - target_x)**2 + (tip_y - target_y)**2)
    radii = get_current_radii()
    
    points = 0
    is_bullseye = False
    
    if distance <= radii['bullseye']:
        points = SCORE_ZONES['bullseye']['points']
        is_bullseye = True
    elif distance <= radii['inner']:
        points = SCORE_ZONES['inner']['points']
    elif distance <= radii['outer']:
        points = SCORE_ZONES['outer']['points']
    elif distance <= radii['edge']:
        points = SCORE_ZONES['edge']['points']
    
    if points > 0:
        if is_bullseye and last_was_bullseye:
            combo += 1
            points += combo * 15
        elif is_bullseye:
            combo = 1
        else:
            combo = 0
        last_was_bullseye = is_bullseye
    else:
        combo = 0
        last_was_bullseye = False
    
    return points

def update_target_size():
    global target_size, target_growing, target_size_speed
    
    if target_growing:
        target_size += target_size_speed
        if target_size >= BASE_TARGET_SIZE + 40:
            target_growing = False
            target_size_speed = random.uniform(1.0, 1.8)
    else:
        target_size -= target_size_speed
        if target_size <= BASE_TARGET_SIZE - 30:
            target_growing = True
            target_size_speed = random.uniform(1.0, 1.8)

def reset_game():
    global score, darts_thrown, game_state, dart_trail, target_x, target_y, target_dx, target_dy, combo, last_was_bullseye, target_size, target_growing
    score = 0
    darts_thrown = 0
    dart_trail = []
    combo = 0
    last_was_bullseye = False
    target_size = BASE_TARGET_SIZE
    target_growing = True
    game_state = "playing"
    target_x = SCREEN_WIDTH // 2
    target_y = SCREEN_HEIGHT // 2
    target_dx = random.choice([-5, -4, 4, 5])
    target_dy = random.choice([-5, -4, 4, 5])

def draw_target():
    radii = get_current_radii()
    
    # Draw with glow effect
    if target_growing:
        glow_radius = radii['edge'] + 8
        for i in range(3):
            alpha = 50 - i * 15
            glow_color = (255, 255, 100, alpha)
            pygame.draw.circle(screen, (255, 255, 100), (target_x, target_y), glow_radius - i * 2, 2)
    
    pygame.draw.circle(screen, SCORE_ZONES['edge']['color'], (target_x, target_y), radii['edge'])
    pygame.draw.circle(screen, SCORE_ZONES['outer']['color'], (target_x, target_y), radii['outer'])
    pygame.draw.circle(screen, SCORE_ZONES['inner']['color'], (target_x, target_y), radii['inner'])
    pygame.draw.circle(screen, SCORE_ZONES['bullseye']['color'], (target_x, target_y), radii['bullseye'])
    
    cross_size = int(target_size * 0.25)
    pygame.draw.line(screen, BLACK, (target_x - cross_size, target_y), (target_x + cross_size, target_y), 2)
    pygame.draw.line(screen, BLACK, (target_x, target_y - cross_size), (target_x, target_y + cross_size), 2)

def draw_dart_trail():
    for i, (x, y, points, combo_bonus) in enumerate(dart_trail):
        alpha = i / len(dart_trail)
        size = int(12 * alpha)
        if size > 0:
            color = (255, int(200 * alpha), int(200 * alpha))
            pygame.draw.circle(screen, color, (int(x), int(y)), size)
            if i >= len(dart_trail) - 5 and points > 0:
                if combo_bonus > 0:
                    point_text = font_tiny.render(f"+{points}!", True, GOLD)
                else:
                    point_text = font_tiny.render(f"+{points}", True, YELLOW)
                screen.blit(point_text, (int(x) + 12, int(y) - 18))

def draw_hand_cursor(x, y):
    # Smooth cursor with trail
    pygame.draw.circle(screen, CURSOR_COLOR, (int(x), int(y)), 20, 3)
    pygame.draw.circle(screen, CURSOR_COLOR, (int(x), int(y)), 12, 2)
    pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 5)
    
    # Crosshair
    pygame.draw.line(screen, CURSOR_COLOR, (int(x) - 30, int(y)), (int(x) - 15, int(y)), 2)
    pygame.draw.line(screen, CURSOR_COLOR, (int(x) + 15, int(y)), (int(x) + 30, int(y)), 2)
    pygame.draw.line(screen, CURSOR_COLOR, (int(x), int(y) - 30), (int(x), int(y) - 15), 2)
    pygame.draw.line(screen, CURSOR_COLOR, (int(x), int(y) + 15), (int(x), int(y) + 30), 2)

def draw_ui():
    # Big score with shadow
    score_text = font_huge.render(f"{score}", True, GOLD if combo > 0 else WHITE)
    score_shadow = font_huge.render(f"{score}", True, (50, 50, 50))
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2 + 3, 83))
    screen.blit(score_shadow, score_rect)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
    screen.blit(score_text, score_rect)
    
    # Combo system
    if combo > 0:
        combo_text = font_medium.render(f"COMBO x{combo}!", True, GOLD)
        combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 165))
        screen.blit(combo_text, combo_rect)
        
        # Animated combo bar
        bar_width = min(400, combo * 25)
        bar_x = SCREEN_WIDTH // 2 - 200
        for i in range(3):
            pygame.draw.rect(screen, (100, 100, 100), (bar_x - i, 200 - i, 400 + i*2, 12 + i*2), 2)
        pygame.draw.rect(screen, GOLD, (bar_x, 200, bar_width, 8))
    
    # Stats panel
    darts_left = MAX_DARTS - darts_thrown
    darts_text = font_small.render(f"Darts Left: {darts_left}", True, WHITE)
    screen.blit(darts_text, (SCREEN_WIDTH - 220, 30))
    
    high_text = font_small.render(f"High Score: {high_score}", True, YELLOW)
    screen.blit(high_text, (SCREEN_WIDTH - 220, 75))
    
    # Target info
    size_percent = int(((target_size - (BASE_TARGET_SIZE - 30)) / 70) * 100)
    size_percent = max(0, min(100, size_percent))
    size_text = font_tiny.render(f"Target Size: {size_percent}%", True, WHITE)
    screen.blit(size_text, (SCREEN_WIDTH - 220, 120))
    
    # Instructions
    if game_state == "playing":
        inst_text = font_tiny.render("PINCH THUMB & INDEX FINGER TO THROW", True, WHITE)
        screen.blit(inst_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 35))
        
        if combo == 0 and darts_thrown > 0:
            hint_text = font_tiny.render("🔥 HIT BULLSEYES FOR COMBO BONUS! 🔥", True, GOLD)
            screen.blit(hint_text, (SCREEN_WIDTH // 2 - 170, SCREEN_HEIGHT - 65))
    
    # Game over screen
    if game_state == "game_over":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        game_over_text = font_huge.render("GAME OVER", True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 120))
        
        final_score_text = font_large.render(f"Score: {score}", True, GOLD)
        screen.blit(final_score_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 40))
        
        if score == high_score and score > 0:
            new_record_text = font_medium.render("★ NEW RECORD! ★", True, YELLOW)
            screen.blit(new_record_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 20))
        
        restart_text = font_medium.render("Press SPACE to play again", True, GREEN)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 100))
    
    # Copyright
    copyright_text = font_tiny.render("© Keyshaun Sookdar | President of Robotics Club, CTO of IT club", True, (80, 80, 80))
    screen.blit(copyright_text, (SCREEN_WIDTH - 470, SCREEN_HEIGHT - 25))

def update_target():
    global target_x, target_y, target_dx, target_dy
    
    target_x += target_dx
    target_y += target_dy
    
    radii = get_current_radii()
    
    if target_x - radii['edge'] <= 0:
        target_x = radii['edge']
        target_dx = -target_dx
    if target_x + radii['edge'] >= SCREEN_WIDTH:
        target_x = SCREEN_WIDTH - radii['edge']
        target_dx = -target_dx
    if target_y - radii['edge'] <= 0:
        target_y = radii['edge']
        target_dy = -target_dy
    if target_y + radii['edge'] >= SCREEN_HEIGHT:
        target_y = SCREEN_HEIGHT - radii['edge']
        target_dy = -target_dy

def throw_dart(x, y):
    global score, darts_thrown, high_score, game_state
    
    points = check_score(x, y)
    score += points
    darts_thrown += 1
    
    combo_bonus = (combo * 15) if last_was_bullseye and combo > 1 else 0
    
    dart_trail.append((x, y, points, combo_bonus))
    if len(dart_trail) > DART_TRAIL_LENGTH:
        dart_trail.pop(0)
    
    if score > high_score:
        high_score = score
    
    if darts_thrown >= MAX_DARTS:
        game_state = "game_over"

def main():
    global game_state, cursor_smooth_x, cursor_smooth_y
    
    pinch_detected = False
    last_pinch_state = False
    
    print("=" * 50)
    print("DART MACHINE by WSS - PERFORMANCE MODE")
    print("=" * 50)
    print("Controls: Pinch thumb & index finger to throw!")
    print("🎯 Target grows & shrinks randomly!")
    print("🔥 Consecutive bullseyes = COMBO BONUS!")
    print("Press Q to quit | SPACE to restart")
    print("=" * 50)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_SPACE and game_state == "game_over":
                    reset_game()
        
        # Camera capture
        ret, frame = cap.read()
        if not ret:
            continue
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw game elements
        if game_state == "playing":
            update_target()
            update_target_size()
        draw_target()
        draw_dart_trail()
        draw_ui()
        
        # Hand tracking and cursor
        cursor_raw_x = SCREEN_WIDTH // 2
        cursor_raw_y = SCREEN_HEIGHT // 2
        pinch = False
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                
                h, w = SCREEN_HEIGHT, SCREEN_WIDTH
                cursor_raw_x = int(index_tip.x * w)
                cursor_raw_y = int(index_tip.y * h)
                
                thumb_x = int(thumb_tip.x * w)
                thumb_y = int(thumb_tip.y * h)
                
                distance = math.sqrt((cursor_raw_x - thumb_x)**2 + (cursor_raw_y - thumb_y)**2)
                pinch = distance < 40
                
                # Draw hand landmarks (optional)
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                      landmark_drawing_spec=mp_draw.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=2),
                                      connection_drawing_spec=mp_draw.DrawingSpec(color=(255,255,255), thickness=1))
        
        # Smooth cursor movement
        cursor_smooth_x = cursor_smooth_x * (1 - cursor_speed) + cursor_raw_x * cursor_speed
        cursor_smooth_y = cursor_smooth_y * (1 - cursor_speed) + cursor_raw_y * cursor_speed
        
        draw_hand_cursor(cursor_smooth_x, cursor_smooth_y)
        
        # Handle dart throw
        if game_state == "playing":
            if pinch and not last_pinch_state:
                throw_dart(int(cursor_smooth_x), int(cursor_smooth_y))
                # Visual feedback
                pygame.draw.circle(screen, (255, 255, 255), (int(cursor_smooth_x), int(cursor_smooth_y)), 35, 5)
                pygame.draw.circle(screen, GOLD, (int(cursor_smooth_x), int(cursor_smooth_y)), 25, 3)
            
            # Aiming line
            pygame.draw.line(screen, (100, 100, 100), (cursor_smooth_x, cursor_smooth_y), (target_x, target_y), 2)
            
            # Distance indicator
            distance = math.sqrt((cursor_smooth_x - target_x)**2 + (cursor_smooth_y - target_y)**2)
            if distance < 80:
                color = GREEN if distance < 40 else YELLOW
                pygame.draw.circle(screen, color, (target_x, target_y), 12, 3)
        
        last_pinch_state = pinch
        
        # Show camera feed (smaller for better performance)
        frame_small = cv2.resize(frame, (300, 225))
        frame_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.surfarray.make_surface(frame_small.swapaxes(0, 1))
        screen.blit(frame_surface, (SCREEN_WIDTH - 310, SCREEN_HEIGHT - 235))
        
        # Draw border around camera feed
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 312, SCREEN_HEIGHT - 237, 304, 229), 2)
        
        pygame.display.flip()
        clock.tick(60)  # Lock at 60 FPS
    
    cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()