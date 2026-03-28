import pygame
import math
import random
import sys
import cv2
import mediapipe as mp
import numpy as np
from pygame.locals import *

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((1200, 800))
pygame.display.set_caption("Hand Puzzle Master by WSS - Fist Grab Control")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 80, 80)
GREEN = (80, 255, 80)
BLUE = (80, 80, 255)
YELLOW = (255, 255, 80)
ORANGE = (255, 165, 80)
PURPLE = (200, 80, 255)
CYAN = (80, 255, 255)
GOLD = (255, 215, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
PINK = (255, 192, 203)

class PuzzlePiece:
    def __init__(self, x, y, shape_type, color, size=40):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.shape_type = shape_type
        self.color = color
        self.size = size
        self.correct_placement = False
        self.hover_offset = random.uniform(0, math.pi * 2)
        
    def update_hover(self):
        self.hover_offset += 0.03
        if self.hover_offset > math.pi * 2:
            self.hover_offset -= math.pi * 2
    
    def draw(self, screen, is_held=False):
        x = self.x + (math.sin(self.hover_offset) * 2 if not is_held else 0)
        y = self.y + (math.cos(self.hover_offset) * 1.5 if not is_held else 0)
        
        # Glow effect for held piece
        if is_held:
            for i in range(2):
                glow_size = self.size + 8 - i * 3
                alpha = 80 - i * 20
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color, alpha), (glow_size, glow_size), glow_size)
                screen.blit(glow_surf, (x - glow_size, y - glow_size))
        
        # Draw shape
        if self.shape_type == 'circle':
            pygame.draw.circle(screen, self.color, (int(x), int(y)), self.size // 2)
            pygame.draw.circle(screen, WHITE, (int(x), int(y)), self.size // 2, 2)
        elif self.shape_type == 'square':
            rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
            pygame.draw.rect(screen, self.color, rect)
            pygame.draw.rect(screen, WHITE, rect, 2)
        elif self.shape_type == 'triangle':
            points = [(x, y - self.size//2), (x - self.size//2, y + self.size//2), (x + self.size//2, y + self.size//2)]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
        elif self.shape_type == 'star':
            points = []
            for i in range(10):
                angle = i * math.pi * 2 / 10 - math.pi/2
                radius = self.size//2 if i % 2 == 0 else self.size//4
                points.append((x + math.cos(angle) * radius, y + math.sin(angle) * radius))
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
        
        # Checkmark
        if self.correct_placement:
            pygame.draw.circle(screen, GREEN, (int(x + self.size//3), int(y - self.size//3)), 10)
            pygame.draw.line(screen, WHITE, (x + self.size//3 - 4, y - self.size//3), (x + self.size//3, y - self.size//3 + 4), 2)
            pygame.draw.line(screen, WHITE, (x + self.size//3, y - self.size//3 + 4), (x + self.size//3 + 6, y - self.size//3 - 2), 2)

class PuzzleGame:
    def __init__(self):
        # Game state
        self.puzzles = self.create_puzzles()
        self.current_puzzle_index = 0
        self.current_puzzle = None
        self.puzzle_pieces = []
        self.slots = []
        self.game_state = "menu"
        self.score = 0
        self.total_score = 0
        self.time_remaining = 0
        self.start_time = 0
        
        # Hand tracking
        self.hand_x = 600
        self.hand_y = 400
        self.hand_radius = 40
        self.held_piece = None
        self.is_fist = False
        self.was_fist = False
        self.fist_cooldown = 0
        
        # Camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        # MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0
        )
        
        # Camera preview
        self.cam_surface = pygame.Surface((280, 210))
        
        self.load_puzzle(0)
    
    def detect_fist(self, hand_landmarks):
        """Detect if hand is making a fist (all fingers curled)"""
        # Get fingertip and pip joint positions
        finger_tips = [
            self.mp_hands.HandLandmark.THUMB_TIP,
            self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
            self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
            self.mp_hands.HandLandmark.RING_FINGER_TIP,
            self.mp_hands.HandLandmark.PINKY_TIP
        ]
        
        finger_pips = [
            self.mp_hands.HandLandmark.THUMB_IP,
            self.mp_hands.HandLandmark.INDEX_FINGER_PIP,
            self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
            self.mp_hands.HandLandmark.RING_FINGER_PIP,
            self.mp_hands.HandLandmark.PINKY_PIP
        ]
        
        curled_fingers = 0
        
        for i, (tip_idx, pip_idx) in enumerate(zip(finger_tips, finger_pips)):
            tip = hand_landmarks.landmark[tip_idx]
            pip = hand_landmarks.landmark[pip_idx]
            
            # For thumb, check if it's curled inward
            if i == 0:  # Thumb
                # Thumb tip should be close to index finger base for fist
                index_base = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
                thumb_tip = tip
                distance_to_index = math.sqrt((thumb_tip.x - index_base.x)**2 + (thumb_tip.y - index_base.y)**2)
                if distance_to_index < 0.1:  # Thumb tucked in
                    curled_fingers += 1
            else:
                # For other fingers, tip should be below pip (y coordinate)
                if tip.y > pip.y:  # Finger is curled
                    curled_fingers += 1
        
        # Fist if at least 4 fingers are curled
        return curled_fingers >= 4
    
    def get_hand_center(self, hand_landmarks):
        """Get center of palm for smooth tracking"""
        palm_points = [
            self.mp_hands.HandLandmark.WRIST,
            self.mp_hands.HandLandmark.INDEX_FINGER_MCP,
            self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
            self.mp_hands.HandLandmark.RING_FINGER_MCP,
            self.mp_hands.HandLandmark.PINKY_MCP
        ]
        
        x = 0
        y = 0
        for point in palm_points:
            lm = hand_landmarks.landmark[point]
            x += lm.x
            y += lm.y
        
        x /= len(palm_points)
        y /= len(palm_points)
        
        return x, y
    
    def update_hand_tracking(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        # Update camera preview
        frame_small = cv2.resize(frame, (280, 210))
        frame_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        self.cam_surface = pygame.surfarray.make_surface(frame_small.swapaxes(0, 1))
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get hand center
                palm_x, palm_y = self.get_hand_center(hand_landmarks)
                
                # Map to screen coordinates
                self.hand_x = int(palm_x * 1200)
                self.hand_y = int(palm_y * 800)
                
                # Detect if hand is making a fist
                self.is_fist = self.detect_fist(hand_landmarks)
                
                # Draw hand landmarks on camera preview (for debugging)
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_utils.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=2),
                    mp.solutions.drawing_utils.DrawingSpec(color=(255,255,255), thickness=1)
                )
                self.cam_surface = pygame.surfarray.make_surface(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).swapaxes(0, 1))
                self.cam_surface = pygame.transform.scale(self.cam_surface, (280, 210))
        
        # Handle grab/release logic with fist detection
        if self.game_state == "playing":
            # Fist cooldown to prevent rapid grabbing
            if self.fist_cooldown > 0:
                self.fist_cooldown -= 1
            
            # On fist CLENCH (transition from open to fist) = GRAB
            if self.is_fist and not self.was_fist and self.fist_cooldown == 0:
                if self.held_piece is None:
                    # Try to grab piece
                    for piece in self.puzzle_pieces:
                        if not piece.correct_placement:
                            dx = abs(self.hand_x - piece.x)
                            dy = abs(self.hand_y - piece.y)
                            if dx < self.hand_radius and dy < self.hand_radius:
                                self.held_piece = piece
                                self.fist_cooldown = 10  # Cooldown to prevent multiple grabs
                                break
            
            # On fist RELEASE (transition from fist to open) = PLACE
            elif not self.is_fist and self.was_fist and self.held_piece is not None:
                # Try to place piece
                placed = False
                for slot_x, slot_y, shape, color in self.slots:
                    dx = abs(self.hand_x - slot_x)
                    dy = abs(self.hand_y - slot_y)
                    if dx < 45 and dy < 45:
                        if self.held_piece.shape_type == shape and self.held_piece.color == color:
                            self.held_piece.x = slot_x
                            self.held_piece.y = slot_y
                            self.held_piece.correct_placement = True
                            self.held_piece = None
                            self.score += 100
                            placed = True
                            self.fist_cooldown = 10
                            break
                
                if not placed:
                    # Drop piece if not placed correctly
                    self.held_piece = None
                    self.fist_cooldown = 10
            
            # Update held piece position
            if self.held_piece:
                self.held_piece.x = self.hand_x
                self.held_piece.y = self.hand_y
        
        self.was_fist = self.is_fist
    
    def update(self):
        if self.game_state == "playing":
            # Update time
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
            self.time_remaining = max(0, self.current_puzzle.time_limit - elapsed)
            
            if self.time_remaining <= 0:
                self.game_state = "failed"
            
            # Update hover animations
            for piece in self.puzzle_pieces:
                if piece != self.held_piece:
                    piece.update_hover()
            
            # Check completion
            if all(piece.correct_placement for piece in self.puzzle_pieces):
                time_percentage = self.time_remaining / self.current_puzzle.time_limit
                if time_percentage > 0.7:
                    stars = 3
                elif time_percentage > 0.4:
                    stars = 2
                else:
                    stars = 1
                self.current_puzzle.stars_earned = stars
                self.total_score += self.score * stars
                self.game_state = "completed"
    
    def create_puzzles(self):
        puzzles = []
        
        puzzle_data = [
            ("Shape Sorter", 1, "Match shapes to outlines", 60),
            ("Color Match", 1, "Match colors correctly", 60),
            ("Star Pattern", 2, "Arrange stars in constellation", 75),
            ("Rainbow Order", 2, "Arrange colors in rainbow order", 75),
            ("Mirror Image", 2, "Create mirror pattern", 80),
            ("Number Sequence", 3, "Arrange numbers 1-5", 90),
            ("Geometric Garden", 3, "Place shapes in garden", 100),
            ("Color Wheel", 3, "Complete the color wheel", 90),
            ("Ancient Pyramid", 3, "Build the pyramid", 100),
            ("Sacred Mandala", 4, "Create symmetrical pattern", 120),
            ("Animal Friends", 2, "Complete animal faces", 80),
            ("Clock Master", 3, "Place numbers on clock", 100),
            ("Flower Power", 2, "Arrange flower petals", 90),
            ("Chess Pattern", 4, "Place chess pieces", 150),
            ("Golden Spiral", 4, "Follow spiral pattern", 120),
            ("Crystal Cave", 3, "Arrange crystals by size", 90),
            ("Space Station", 4, "Build station modules", 120),
            ("Dragon's Lair", 5, "Arrange dragon gems", 150),
            ("Infinity Mirror", 5, "Create infinite pattern", 140),
            ("Master's Trial", 5, "Ultimate challenge", 180)
        ]
        
        for name, diff, desc, time in puzzle_data:
            puzzles.append(Puzzle(name, diff, desc, {}, time))
        
        return puzzles
    
    def load_puzzle(self, index):
        self.current_puzzle = self.puzzles[index]
        self.puzzle_pieces = []
        self.slots = []
        self.score = 0
        self.time_remaining = self.current_puzzle.time_limit
        self.start_time = pygame.time.get_ticks()
        
        # Generate puzzle pieces
        num_pieces = 5 + self.current_puzzle.difficulty
        
        shapes = ['circle', 'square', 'triangle', 'star']
        colors = [RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, CYAN, PINK]
        
        # Random positions for pieces (top area)
        piece_positions = []
        for i in range(num_pieces):
            while True:
                x = random.randint(100, 1100)
                y = random.randint(180, 480)
                overlap = False
                for px, py in piece_positions:
                    if abs(x - px) < 70 and abs(y - py) < 70:
                        overlap = True
                        break
                if not overlap:
                    piece_positions.append((x, y))
                    break
        
        # Target positions (bottom area)
        target_positions = []
        for i in range(num_pieces):
            while True:
                x = random.randint(150, 1050)
                y = random.randint(560, 760)
                overlap = False
                for tx, ty in target_positions:
                    if abs(x - tx) < 80 and abs(y - ty) < 80:
                        overlap = True
                        break
                if not overlap:
                    target_positions.append((x, y))
                    break
        
        # Create pieces
        for i in range(num_pieces):
            shape = shapes[i % len(shapes)]
            color = colors[i % len(colors)]
            piece = PuzzlePiece(piece_positions[i][0], piece_positions[i][1], shape, color, 38)
            piece.target_x, piece.target_y = target_positions[i]
            self.puzzle_pieces.append(piece)
            self.slots.append((target_positions[i][0], target_positions[i][1], shape, color))
    
    def draw(self):
        screen.fill((20, 20, 30))
        
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "playing":
            self.draw_game()
        elif self.game_state == "completed":
            self.draw_completed()
        elif self.game_state == "failed":
            self.draw_failed()
    
    def draw_menu(self):
        # Title
        title_font = pygame.font.Font(None, 68)
        title = title_font.render("HAND PUZZLE MASTER", True, GOLD)
        screen.blit(title, (300, 50))
        
        sub_font = pygame.font.Font(None, 28)
        subtitle = sub_font.render("by WSS", True, WHITE)
        screen.blit(subtitle, (540, 110))
        
        # Puzzle grid
        start_x, start_y = 80, 180
        for i, puzzle in enumerate(self.puzzles):
            row = i // 5
            col = i % 5
            x = start_x + col * 210
            y = start_y + row * 130
            
            if i == self.current_puzzle_index:
                pygame.draw.rect(screen, GOLD, (x-3, y-3, 186, 106), 3)
            pygame.draw.rect(screen, DARK_GRAY, (x, y, 180, 100))
            pygame.draw.rect(screen, GRAY, (x, y, 180, 100), 2)
            
            name_font = pygame.font.Font(None, 20)
            name_text = name_font.render(puzzle.name[:14], True, WHITE)
            screen.blit(name_text, (x+8, y+8))
            
            for s in range(puzzle.difficulty):
                star_color = GOLD if s < puzzle.stars_earned else GRAY
                pygame.draw.polygon(screen, star_color, [(x+12 + s*15, y+38), (x+9 + s*15, y+43), (x+12 + s*15, y+48), (x+15 + s*15, y+43)])
        
        # Instructions
        inst_font = pygame.font.Font(None, 24)
        inst1 = inst_font.render("✊ CLOSE YOUR HAND (FIST) to GRAB pieces", True, CYAN)
        inst2 = inst_font.render("🖐️ OPEN YOUR HAND to RELEASE pieces", True, CYAN)
        screen.blit(inst1, (50, 720))
        screen.blit(inst2, (50, 755))
        
        # Start button
        start_rect = pygame.Rect(500, 710, 200, 50)
        pygame.draw.rect(screen, GREEN, start_rect)
        pygame.draw.rect(screen, WHITE, start_rect, 3)
        start_text = pygame.font.Font(None, 32).render("START", True, BLACK)
        screen.blit(start_text, (575, 722))
        
        # Navigation
        nav_font = pygame.font.Font(None, 24)
        prev_text = nav_font.render("← PREV", True, WHITE)
        next_text = nav_font.render("NEXT →", True, WHITE)
        screen.blit(prev_text, (180, 760))
        screen.blit(next_text, (980, 760))
        
        # Copyright
        copy_font = pygame.font.Font(None, 18)
        copy_text = copy_font.render("© Keyshaun Sookdar | President of Robotics Club, CTO of IT club", True, GRAY)
        screen.blit(copy_text, (380, 780))
    
    def draw_game(self):
        # Background
        for y in range(800):
            color = 20 + int(y / 800 * 40)
            pygame.draw.line(screen, (color, color, color+10), (0, y), (1200, y))
        
        # Title and info
        title_font = pygame.font.Font(None, 32)
        title = title_font.render(self.current_puzzle.name, True, GOLD)
        screen.blit(title, (20, 15))
        
        desc_font = pygame.font.Font(None, 20)
        desc = desc_font.render(self.current_puzzle.description, True, WHITE)
        screen.blit(desc, (20, 50))
        
        # Time
        time_font = pygame.font.Font(None, 48)
        minutes = int(self.time_remaining // 60)
        seconds = int(self.time_remaining % 60)
        time_color = RED if self.time_remaining < 10 else WHITE
        time_text = time_font.render(f"{minutes:02d}:{seconds:02d}", True, time_color)
        screen.blit(time_text, (1080, 20))
        
        # Score
        score_font = pygame.font.Font(None, 32)
        score_text = score_font.render(f"Score: {self.score}", True, GOLD)
        screen.blit(score_text, (1080, 75))
        
        # Areas
        pygame.draw.rect(screen, (40, 40, 50), (0, 120, 1200, 380))
        pygame.draw.rect(screen, GRAY, (0, 120, 1200, 380), 2)
        pygame.draw.rect(screen, (40, 40, 50), (0, 520, 1200, 280))
        pygame.draw.rect(screen, GRAY, (0, 520, 1200, 280), 2)
        
        # Draw slots
        for slot_x, slot_y, shape, color in self.slots:
            if shape == 'circle':
                pygame.draw.circle(screen, color, (slot_x, slot_y), 22, 2)
            elif shape == 'square':
                pygame.draw.rect(screen, color, (slot_x-22, slot_y-22, 44, 44), 2)
            elif shape == 'triangle':
                points = [(slot_x, slot_y-22), (slot_x-22, slot_y+22), (slot_x+22, slot_y+22)]
                pygame.draw.polygon(screen, color, points, 2)
            elif shape == 'star':
                points = []
                for i in range(10):
                    angle = i * math.pi * 2 / 10 - math.pi/2
                    radius = 22 if i % 2 == 0 else 11
                    points.append((slot_x + math.cos(angle) * radius, slot_y + math.sin(angle) * radius))
                pygame.draw.polygon(screen, color, points, 2)
        
        # Draw pieces
        for piece in self.puzzle_pieces:
            if piece != self.held_piece:
                piece.draw(screen)
        
        # Draw held piece
        if self.held_piece:
            self.held_piece.draw(screen, is_held=True)
        
        # Draw hand cursor with FIST vs OPEN hand visualization
        if self.is_fist:
            # FIST - Closed hand (grabbing mode)
            pygame.draw.circle(screen, RED, (self.hand_x, self.hand_y), self.hand_radius)
            pygame.draw.circle(screen, YELLOW, (self.hand_x, self.hand_y), self.hand_radius, 3)
            # Draw fist icon
            pygame.draw.circle(screen, WHITE, (self.hand_x, self.hand_y), 15)
            for i in range(4):
                angle = i * 90 - 45
                rad = math.radians(angle)
                fx = self.hand_x + math.cos(rad) * 12
                fy = self.hand_y + math.sin(rad) * 12
                pygame.draw.circle(screen, WHITE, (int(fx), int(fy)), 4)
            # Text indicator
            fist_text = pygame.font.Font(None, 24).render("GRABBING", True, RED)
            screen.blit(fist_text, (self.hand_x - 40, self.hand_y - 50))
        else:
            # OPEN HAND
            pygame.draw.circle(screen, CYAN, (self.hand_x, self.hand_y), self.hand_radius, 4)
            pygame.draw.circle(screen, WHITE, (self.hand_x, self.hand_y), 12)
            # Draw fingers
            for angle in [-30, 0, 30, 60, 90]:
                rad = math.radians(angle)
                fx = self.hand_x + math.cos(rad) * 28
                fy = self.hand_y + math.sin(rad) * 28
                pygame.draw.line(screen, CYAN, (self.hand_x, self.hand_y), (fx, fy), 4)
            # Text indicator
            if self.held_piece:
                release_text = pygame.font.Font(None, 24).render("RELEASE TO PLACE", True, GREEN)
                screen.blit(release_text, (self.hand_x - 70, self.hand_y - 50))
            else:
                open_text = pygame.font.Font(None, 24).render("OPEN HAND", True, CYAN)
                screen.blit(open_text, (self.hand_x - 45, self.hand_y - 50))
        
        # Instructions
        inst_font = pygame.font.Font(None, 20)
        if self.held_piece:
            inst = inst_font.render("✊ OPEN HAND over matching slot to PLACE", True, GREEN)
        else:
            inst = inst_font.render("✊ MAKE A FIST over a piece to GRAB it", True, YELLOW)
        screen.blit(inst, (450, 770))
        
        # Camera preview
        screen.blit(self.cam_surface, (910, 560))
        pygame.draw.rect(screen, WHITE, (910, 560, 280, 210), 2)
    
    def draw_completed(self):
        overlay = pygame.Surface((1200, 800))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        complete_font = pygame.font.Font(None, 64)
        complete_text = complete_font.render("PUZZLE COMPLETE!", True, GOLD)
        screen.blit(complete_text, (380, 280))
        
        # Stars
        for i in range(3):
            star_color = GOLD if i < self.current_puzzle.stars_earned else GRAY
            points = []
            cx, cy = 600 + (i-1) * 80, 380
            for s in range(10):
                angle = s * math.pi * 2 / 10 - math.pi/2
                radius = 28 if s % 2 == 0 else 14
                points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
            pygame.draw.polygon(screen, star_color, points)
        
        score_font = pygame.font.Font(None, 36)
        score_text = score_font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (540, 460))
        
        # Buttons
        next_rect = pygame.Rect(450, 540, 300, 50)
        pygame.draw.rect(screen, GREEN, next_rect)
        pygame.draw.rect(screen, WHITE, next_rect, 2)
        next_text = pygame.font.Font(None, 32).render("NEXT PUZZLE", True, BLACK)
        screen.blit(next_text, (540, 552))
        
        menu_rect = pygame.Rect(450, 610, 300, 45)
        pygame.draw.rect(screen, BLUE, menu_rect)
        pygame.draw.rect(screen, WHITE, menu_rect, 2)
        menu_text = pygame.font.Font(None, 28).render("BACK TO MENU", True, WHITE)
        screen.blit(menu_text, (550, 620))
    
    def draw_failed(self):
        overlay = pygame.Surface((1200, 800))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        fail_font = pygame.font.Font(None, 64)
        fail_text = fail_font.render("TIME'S UP!", True, RED)
        screen.blit(fail_text, (480, 320))
        
        retry_rect = pygame.Rect(450, 450, 300, 50)
        pygame.draw.rect(screen, ORANGE, retry_rect)
        pygame.draw.rect(screen, WHITE, retry_rect, 2)
        retry_text = pygame.font.Font(None, 32).render("RETRY", True, BLACK)
        screen.blit(retry_text, (590, 462))
        
        menu_rect = pygame.Rect(450, 520, 300, 45)
        pygame.draw.rect(screen, BLUE, menu_rect)
        pygame.draw.rect(screen, WHITE, menu_rect, 2)
        menu_text = pygame.font.Font(None, 28).render("BACK TO MENU", True, WHITE)
        screen.blit(menu_text, (550, 530))
    
    def handle_click(self, pos):
        if self.game_state == "menu":
            if 500 < pos[0] < 700 and 710 < pos[1] < 760:
                self.game_state = "playing"
                self.load_puzzle(self.current_puzzle_index)
            if 180 < pos[0] < 250 and 760 < pos[1] < 790:
                self.current_puzzle_index = (self.current_puzzle_index - 1) % len(self.puzzles)
            if 980 < pos[0] < 1050 and 760 < pos[1] < 790:
                self.current_puzzle_index = (self.current_puzzle_index + 1) % len(self.puzzles)
            
            start_x, start_y = 80, 180
            for i in range(len(self.puzzles)):
                row = i // 5
                col = i % 5
                x = start_x + col * 210
                y = start_y + row * 130
                if x < pos[0] < x+180 and y < pos[1] < y+100:
                    self.current_puzzle_index = i
        
        elif self.game_state == "completed":
            if 450 < pos[0] < 750 and 540 < pos[1] < 590:
                self.current_puzzle_index = (self.current_puzzle_index + 1) % len(self.puzzles)
                self.load_puzzle(self.current_puzzle_index)
                self.game_state = "playing"
            elif 450 < pos[0] < 750 and 610 < pos[1] < 655:
                self.game_state = "menu"
        
        elif self.game_state == "failed":
            if 450 < pos[0] < 750 and 450 < pos[1] < 500:
                self.load_puzzle(self.current_puzzle_index)
                self.game_state = "playing"
            elif 450 < pos[0] < 750 and 520 < pos[1] < 565:
                self.game_state = "menu"

class Puzzle:
    def __init__(self, name, difficulty, description, solution_pattern, time_limit):
        self.name = name
        self.difficulty = difficulty
        self.description = description
        self.solution_pattern = solution_pattern
        self.time_limit = time_limit
        self.stars_earned = 0

def main():
    game = PuzzleGame()
    
    print("=" * 60)
    print("HAND PUZZLE MASTER by WSS - FIST GRAB CONTROL")
    print("=" * 60)
    print("✊ MAKE A FIST over a piece to GRAB it!")
    print("🖐️ OPEN YOUR HAND over a matching slot to PLACE it!")
    print("🎯 Complete puzzles faster for more stars!")
    print("🧩 20 puzzles with increasing difficulty!")
    print("Press Q to quit | Click buttons to navigate")
    print("=" * 60)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(event.pos)
        
        game.update_hand_tracking()
        game.update()
        game.draw()
        
        pygame.display.flip()
        clock.tick(60)
    
    game.cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()