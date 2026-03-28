import pygame
import math
import random
import sys
import cv2
import mediapipe as mp
import numpy as np
from pygame.locals import *

# Initialize Pygame and OpenGL
pygame.init()
pygame.display.set_mode((1200, 800), DOUBLEBUF | OPENGL)
pygame.display.set_caption("PC Builder Simulator by WSS - Ultimate Edition")
clock = pygame.time.Clock()

# Import OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *

# Colors (RGB for OpenGL)
WHITE = (1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0)
RED = (0.9, 0.2, 0.2)
GREEN = (0.2, 0.8, 0.2)
BLUE = (0.2, 0.3, 0.8)
YELLOW = (0.9, 0.9, 0.2)
ORANGE = (0.9, 0.5, 0.2)
PURPLE = (0.6, 0.2, 0.8)
CYAN = (0.2, 0.7, 0.9)
GOLD = (0.9, 0.7, 0.2)

class Component3D:
    def __init__(self, name, x, y, z, width, height, depth, color):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.depth = depth
        self.color = color
        self.installed = False
        self.hover_offset = random.uniform(0, math.pi * 2)
        
    def update_hover(self):
        self.hover_offset += 0.05
        if self.hover_offset > math.pi * 2:
            self.hover_offset -= math.pi * 2
    
    def draw(self, is_held=False, installed_pos=None):
        glPushMatrix()
        
        if is_held:
            y_offset = math.sin(pygame.time.get_ticks() * 0.008) * 0.08
            glTranslatef(self.x, self.y + y_offset, self.z)
            glRotatef(pygame.time.get_ticks() * 0.8, 0, 1, 0)
        elif installed_pos:
            glTranslatef(installed_pos[0], installed_pos[1], installed_pos[2])
        else:
            # Hover animation for available components
            y_offset = math.sin(self.hover_offset) * 0.05
            glTranslatef(self.x, self.y + y_offset, self.z)
        
        w2 = self.width / 2
        h2 = self.height / 2
        d2 = self.depth / 2
        
        # Glow effect for held component
        if is_held:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(self.color[0], self.color[1], self.color[2], 0.5)
            for i in range(3):
                glow_size = 0.05 + i * 0.03
                glBegin(GL_QUADS)
                glVertex3f(-w2-glow_size, -h2-glow_size, d2+glow_size)
                glVertex3f(w2+glow_size, -h2-glow_size, d2+glow_size)
                glVertex3f(w2+glow_size, h2+glow_size, d2+glow_size)
                glVertex3f(-w2-glow_size, h2+glow_size, d2+glow_size)
                glEnd()
            glDisable(GL_BLEND)
        
        glBegin(GL_QUADS)
        
        # Front face
        glColor3f(*self.color)
        glVertex3f(-w2, -h2, d2)
        glVertex3f(w2, -h2, d2)
        glVertex3f(w2, h2, d2)
        glVertex3f(-w2, h2, d2)
        
        # Back face
        glColor3f(self.color[0]*0.6, self.color[1]*0.6, self.color[2]*0.6)
        glVertex3f(-w2, -h2, -d2)
        glVertex3f(-w2, h2, -d2)
        glVertex3f(w2, h2, -d2)
        glVertex3f(w2, -h2, -d2)
        
        # Top face
        glColor3f(self.color[0]*1.2, self.color[1]*1.2, self.color[2]*1.2)
        glVertex3f(-w2, h2, -d2)
        glVertex3f(-w2, h2, d2)
        glVertex3f(w2, h2, d2)
        glVertex3f(w2, h2, -d2)
        
        # Bottom face
        glColor3f(self.color[0]*0.8, self.color[1]*0.8, self.color[2]*0.8)
        glVertex3f(-w2, -h2, -d2)
        glVertex3f(w2, -h2, -d2)
        glVertex3f(w2, -h2, d2)
        glVertex3f(-w2, -h2, d2)
        
        # Right face
        glColor3f(self.color[0]*0.9, self.color[1]*0.9, self.color[2]*0.9)
        glVertex3f(w2, -h2, -d2)
        glVertex3f(w2, h2, -d2)
        glVertex3f(w2, h2, d2)
        glVertex3f(w2, -h2, d2)
        
        # Left face
        glColor3f(self.color[0]*0.7, self.color[1]*0.7, self.color[2]*0.7)
        glVertex3f(-w2, -h2, -d2)
        glVertex3f(-w2, -h2, d2)
        glVertex3f(-w2, h2, d2)
        glVertex3f(-w2, h2, -d2)
        
        glEnd()
        
        # Add detail lines
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(2)
        glBegin(GL_LINES)
        
        if "CPU" in self.name:
            glVertex3f(-w2+0.05, -h2+0.05, d2+0.01)
            glVertex3f(w2-0.05, -h2+0.05, d2+0.01)
            glVertex3f(-w2+0.05, h2-0.05, d2+0.01)
            glVertex3f(w2-0.05, h2-0.05, d2+0.01)
        elif "GPU" in self.name:
            for i in range(3):
                offset = -0.3 + i * 0.3
                glVertex3f(offset, -h2+0.05, d2+0.01)
                glVertex3f(offset, h2-0.05, d2+0.01)
        elif "RAM" in self.name:
            for i in range(4):
                offset = -0.1 + i * 0.067
                glVertex3f(offset, -h2+0.05, d2+0.01)
                glVertex3f(offset, h2-0.05, d2+0.01)
        elif "Cooler" in self.name:
            for i in range(5):
                offset = -0.35 + i * 0.175
                glVertex3f(offset, -h2+0.1, d2+0.01)
                glVertex3f(offset, h2-0.1, d2+0.01)
        
        glEnd()
        
        glPopMatrix()

class Motherboard:
    def __init__(self):
        self.x = 0
        self.y = -0.3
        self.z = 0
        self.components = {
            'cpu': None,
            'cpu_cooler': None,
            'gpu': None,
            'ram': [],
            'psu': None,
            'storage': None
        }
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Main PCB
        glBegin(GL_QUADS)
        glColor3f(0.08, 0.1, 0.12)
        glVertex3f(-2.0, -1.2, 0)
        glVertex3f(2.0, -1.2, 0)
        glVertex3f(2.0, 1.2, 0)
        glVertex3f(-2.0, 1.2, 0)
        glEnd()
        
        # PCB traces (detail)
        glColor3f(0.2, 0.25, 0.3)
        glLineWidth(1)
        glBegin(GL_LINES)
        for i in range(20):
            glVertex3f(-1.8 + i*0.2, -1.0, 0.01)
            glVertex3f(-1.8 + i*0.2, 1.0, 0.01)
        glEnd()
        
        # CPU Socket Area
        glColor3f(0.25, 0.28, 0.35)
        glBegin(GL_QUADS)
        glVertex3f(-0.6, 0.2, 0.02)
        glVertex3f(0.6, 0.2, 0.02)
        glVertex3f(0.6, 1.0, 0.02)
        glVertex3f(-0.6, 1.0, 0.02)
        glEnd()
        
        # RAM Slots
        glColor3f(0.3, 0.33, 0.4)
        for i in range(2):
            ram_x = 1.0 + i * 0.5
            # Slot 1
            glBegin(GL_QUADS)
            glVertex3f(ram_x-0.15, -0.5, 0.02)
            glVertex3f(ram_x+0.15, -0.5, 0.02)
            glVertex3f(ram_x+0.15, -0.1, 0.02)
            glVertex3f(ram_x-0.15, -0.1, 0.02)
            glEnd()
            # Slot 2
            glBegin(GL_QUADS)
            glVertex3f(ram_x-0.15, 0.1, 0.02)
            glVertex3f(ram_x+0.15, 0.1, 0.02)
            glVertex3f(ram_x+0.15, 0.5, 0.02)
            glVertex3f(ram_x-0.15, 0.5, 0.02)
            glEnd()
        
        # PCIe Slot
        glColor3f(0.3, 0.33, 0.4)
        glBegin(GL_QUADS)
        glVertex3f(-1.2, -0.9, 0.02)
        glVertex3f(1.2, -0.9, 0.02)
        glVertex3f(1.2, -0.6, 0.02)
        glVertex3f(-1.2, -0.6, 0.02)
        glEnd()
        
        # PSU Area
        glColor3f(0.2, 0.22, 0.25)
        glBegin(GL_QUADS)
        glVertex3f(1.5, -1.1, 0.01)
        glVertex3f(1.9, -1.1, 0.01)
        glVertex3f(1.9, -0.3, 0.01)
        glVertex3f(1.5, -0.3, 0.01)
        glEnd()
        
        glPopMatrix()
    
    def check_build(self):
        if self.components['cpu'] is None:
            return "no_cpu"
        if self.components['cpu_cooler'] is None:
            return "overheat"
        if len(self.components['ram']) < 2:
            return "no_ram"
        if self.components['gpu'] is None:
            return "no_gpu"
        if self.components['psu'] is None:
            return "no_psu"
        if self.components['storage'] is None:
            return "no_storage"
        return "complete"

class PCBuilderGame:
    def __init__(self):
        self.game_state = "building"
        self.build_status = "incomplete"
        self.setup_3d()
        
        # Create motherboard
        self.motherboard = Motherboard()
        
        # Create components on side
        self.available_components = []
        self.create_components()
        
        # Held component
        self.held_component = None
        
        # Hand tracking
        self.hand_x = 0
        self.hand_y = 0
        self.hand_z = 0
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
        
        # Camera preview surface
        self.cam_surface = pygame.Surface((280, 210))
        
        # UI elements
        self.warning_timer = 0
        self.current_warning = ""
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
    def setup_3d(self):
        glClearColor(0.05, 0.05, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Main light
        glLightfv(GL_LIGHT0, GL_POSITION, [3, 5, 4, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.4, 0.4, 0.4, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        
        # Fill light
        glLightfv(GL_LIGHT1, GL_POSITION, [-2, 3, 3, 1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.5, 0.5, 0.5, 1])
        
        # Setup projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, 1200/800, 0.1, 100)
        glMatrixMode(GL_MODELVIEW)
    
    def create_components(self):
        # Components arranged on the right side (x = 3.5 to 4.5)
        components_data = [
            ("Intel i9 CPU", 3.5, 1.2, 0, 0.8, 0.8, 0.1, (0.55, 0.55, 0.65)),
            ("RGB Cooler", 3.5, 0.4, 0, 1.0, 1.0, 1.0, (0.35, 0.35, 0.45)),
            ("RTX 4090 GPU", 3.5, -0.4, 0, 1.3, 0.4, 0.5, (0.25, 0.25, 0.35)),
            ("DDR5 RAM 1", 3.5, -1.0, 0, 0.25, 0.7, 0.08, (0.15, 0.45, 0.75)),
            ("DDR5 RAM 2", 4.0, -1.0, 0, 0.25, 0.7, 0.08, (0.15, 0.45, 0.75)),
            ("850W PSU", 3.5, -1.7, 0, 0.9, 0.5, 0.6, (0.35, 0.35, 0.35)),
            ("NVMe SSD", 3.5, -2.3, 0, 0.6, 0.25, 0.12, (0.25, 0.55, 0.25))
        ]
        
        for name, x, y, z, w, h, d, color in components_data:
            self.available_components.append(Component3D(name, x, y, z, w, h, d, color))
    
    def detect_fist(self, hand_landmarks):
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
        
        curled = 0
        for i, (tip_idx, pip_idx) in enumerate(zip(finger_tips, finger_pips)):
            tip = hand_landmarks.landmark[tip_idx]
            pip = hand_landmarks.landmark[pip_idx]
            
            if i == 0:  # Thumb
                index_base = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
                dist = math.sqrt((tip.x - index_base.x)**2 + (tip.y - index_base.y)**2)
                if dist < 0.1:
                    curled += 1
            else:
                if tip.y > pip.y:
                    curled += 1
        
        return curled >= 4
    
    def get_hand_3d_position(self, hand_landmarks):
        # Get palm center for smooth tracking
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
        
        # Map to world coordinates (x: -3 to 4, y: -2 to 2)
        world_x = (x - 0.5) * 7
        world_y = (0.5 - y) * 4
        world_z = 0
        
        return world_x, world_y, world_z
    
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
                self.hand_x, self.hand_y, self.hand_z = self.get_hand_3d_position(hand_landmarks)
                self.is_fist = self.detect_fist(hand_landmarks)
        
        # Handle grab/release
        if self.game_state == "building":
            if self.fist_cooldown > 0:
                self.fist_cooldown -= 1
            
            # GRAB: Make fist over component
            if self.is_fist and not self.was_fist and self.fist_cooldown == 0:
                if self.held_component is None:
                    for comp in self.available_components:
                        dx = abs(self.hand_x - comp.x)
                        dy = abs(self.hand_y - comp.y)
                        if dx < 0.7 and dy < 0.7:
                            self.held_component = comp
                            self.available_components.remove(comp)
                            self.fist_cooldown = 10
                            break
            
            # RELEASE: Open hand
            elif not self.is_fist and self.was_fist and self.held_component is not None:
                # Check if over motherboard
                mb = self.motherboard
                if abs(self.hand_x - mb.x) < 2.0 and abs(self.hand_y - mb.y) < 1.2:
                    installed = self.install_component(self.held_component)
                    if installed:
                        self.held_component = None
                        self.fist_cooldown = 10
                        self.current_warning = f"✓ {self.held_component.name if self.held_component else 'Component'} INSTALLED!"
                        self.warning_timer = 30
                    else:
                        self.available_components.append(self.held_component)
                        self.held_component = None
                        self.current_warning = "❌ Wrong placement location!"
                        self.warning_timer = 60
                else:
                    self.available_components.append(self.held_component)
                    self.held_component = None
            
            # Update held component position
            if self.held_component:
                self.held_component.x = self.hand_x
                self.held_component.y = self.hand_y
                self.held_component.z = self.hand_z
        
        self.was_fist = self.is_fist
        
        if self.warning_timer > 0:
            self.warning_timer -= 1
    
    def install_component(self, component):
        if "CPU" in component.name and self.motherboard.components['cpu'] is None:
            self.motherboard.components['cpu'] = component
            return True
        elif "Cooler" in component.name and self.motherboard.components['cpu_cooler'] is None and self.motherboard.components['cpu']:
            self.motherboard.components['cpu_cooler'] = component
            return True
        elif "GPU" in component.name and self.motherboard.components['gpu'] is None:
            self.motherboard.components['gpu'] = component
            return True
        elif "RAM" in component.name and len(self.motherboard.components['ram']) < 4:
            self.motherboard.components['ram'].append(component)
            return True
        elif "PSU" in component.name and self.motherboard.components['psu'] is None:
            self.motherboard.components['psu'] = component
            return True
        elif "SSD" in component.name and self.motherboard.components['storage'] is None:
            self.motherboard.components['storage'] = component
            return True
        return False
    
    def update_build_status(self):
        result = self.motherboard.check_build()
        
        if result == "complete":
            self.game_state = "complete"
        elif result == "overheat":
            self.game_state = "fail"
            self.current_warning = "💥 CPU OVERHEATED! You forgot the cooler! 💥"
            self.warning_timer = 180
    
    def draw_3d_scene(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Static camera - fixed position for easy grabbing
        gluLookAt(4, 0.5, 5,  # Camera position (right, center, front)
                  0, 0, 0,     # Look at center
                  0, 1, 0)     # Up vector
        
        # Floor grid
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        glColor3f(0.2, 0.2, 0.3)
        for i in range(-5, 6):
            glVertex3f(i, -1.5, -3)
            glVertex3f(i, -1.5, 3)
            glVertex3f(-3, -1.5, i)
            glVertex3f(3, -1.5, i)
        glEnd()
        glEnable(GL_LIGHTING)
        
        # Draw motherboard
        self.motherboard.draw()
        
        # Draw installed components
        if self.motherboard.components['cpu']:
            self.motherboard.components['cpu'].draw(installed_pos=(0, 0.05, 0.08))
        if self.motherboard.components['cpu_cooler']:
            self.motherboard.components['cpu_cooler'].draw(installed_pos=(0, 0.05, 0.15))
        if self.motherboard.components['gpu']:
            self.motherboard.components['gpu'].draw(installed_pos=(0, -0.68, 0.05))
        if self.motherboard.components['psu']:
            self.motherboard.components['psu'].draw(installed_pos=(1.65, -0.6, 0.05))
        if self.motherboard.components['storage']:
            self.motherboard.components['storage'].draw(installed_pos=(0.5, 0.4, 0.08))
        
        # RAM sticks
        ram_positions = [(-0.5, -0.3), (0, -0.3), (-0.5, 0.3), (0, 0.3)]
        for i, ram in enumerate(self.motherboard.components['ram']):
            if i < len(ram_positions):
                ram.draw(installed_pos=(ram_positions[i][0], ram_positions[i][1], 0.08))
        
        # Draw available components (right side)
        for comp in self.available_components:
            comp.update_hover()
            comp.draw()
        
        # Draw held component
        if self.held_component:
            self.held_component.draw(is_held=True)
        
        # Draw hand cursor
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(self.hand_x, self.hand_y, self.hand_z)
        if self.is_fist:
            glColor3f(0.9, 0.2, 0.2)  # Red for fist
        else:
            glColor3f(0.2, 0.7, 0.9)  # Blue for open hand
        
        quad = gluNewQuadric()
        gluSphere(quad, 0.15, 12, 12)
        gluDeleteQuadric(quad)
        
        # Add glow effect
        if self.is_fist:
            glColor4f(0.9, 0.2, 0.2, 0.3)
            gluSphere(quad, 0.22, 8, 8)
        
        glPopMatrix()
        glEnable(GL_LIGHTING)
    
    def draw_2d_ui(self):
        # Switch to 2D projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1200, 800, 0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Create temporary surface
        temp_surf = pygame.Surface((1200, 800), pygame.SRCALPHA)
        temp_surf.fill((0, 0, 0, 0))
        
        # Title
        title = self.font_large.render("PC BUILDER SIMULATOR", True, (255, 215, 0))
        temp_surf.blit(title, (400, 15))
        
        # Build status and needed components
        if self.game_state == "building":
            # Status
            status_color = (0, 255, 255) if self.build_status != "incomplete" else (255, 200, 100)
            status_text = self.font_medium.render(f"BUILD STATUS: {self.build_status.upper()}", True, status_color)
            temp_surf.blit(status_text, (20, 85))
            
            # Needed components list
            needed = []
            if self.motherboard.components['cpu'] is None: needed.append("CPU")
            if self.motherboard.components['cpu_cooler'] is None and self.motherboard.components['cpu']: needed.append("CPU Cooler")
            if len(self.motherboard.components['ram']) < 2: needed.append(f"RAM ({2-len(self.motherboard.components['ram'])} more)")
            if self.motherboard.components['gpu'] is None: needed.append("GPU")
            if self.motherboard.components['psu'] is None: needed.append("PSU")
            if self.motherboard.components['storage'] is None: needed.append("Storage")
            
            if needed:
                needed_text = self.font_small.render(f"NEEDED: {', '.join(needed)}", True, (255, 255, 100))
                temp_surf.blit(needed_text, (20, 125))
            
            # Installed components count
            installed_count = 0
            if self.motherboard.components['cpu']: installed_count += 1
            if self.motherboard.components['cpu_cooler']: installed_count += 1
            if self.motherboard.components['gpu']: installed_count += 1
            installed_count += len(self.motherboard.components['ram'])
            if self.motherboard.components['psu']: installed_count += 1
            if self.motherboard.components['storage']: installed_count += 1
            
            total_components = 7  # CPU, Cooler, GPU, 2xRAM, PSU, SSD
            progress_text = self.font_small.render(f"PROGRESS: {installed_count}/{total_components}", True, (100, 255, 100))
            temp_surf.blit(progress_text, (20, 165))
            
            # Progress bar
            bar_width = 300
            fill_width = int(bar_width * (installed_count / total_components))
            pygame.draw.rect(temp_surf, (50, 50, 50), (20, 195, bar_width, 15))
            pygame.draw.rect(temp_surf, (0, 200, 0), (20, 195, fill_width, 15))
        
        # Warning/Info messages
        if self.warning_timer > 0 and self.current_warning:
            warning_text = self.font_medium.render(self.current_warning, True, (255, 80, 80) if "❌" in self.current_warning or "💥" in self.current_warning else (80, 255, 80))
            temp_surf.blit(warning_text, (400, 700))
        
        # Instructions
        inst1 = self.font_small.render("✊ MAKE A FIST over a component to GRAB it", True, (80, 200, 255))
        inst2 = self.font_small.render("🖐️ OPEN HAND over the MOTHERBOARD to PLACE it", True, (80, 200, 255))
        inst3 = self.font_small.render("⚠️ Install CPU FIRST, then COOLER, then others!", True, (255, 200, 100))
        temp_surf.blit(inst1, (20, 720))
        temp_surf.blit(inst2, (20, 745))
        temp_surf.blit(inst3, (20, 770))
        
        # Camera preview
        temp_surf.blit(self.cam_surface, (910, 560))
        pygame.draw.rect(temp_surf, (255, 255, 255), (910, 560, 280, 210), 2)
        
        # Copyright
        copy_text = self.font_small.render("© Keyshaun Sookdar | President of Robotics Club, CTO of IT club", True, (100, 100, 100))
        temp_surf.blit(copy_text, (380, 780))
        
        # Game over screens
        if self.game_state == "complete":
            overlay = pygame.Surface((1200, 800))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            temp_surf.blit(overlay, (0, 0))
            win_text = self.font_large.render("BUILD COMPLETE!", True, (255, 215, 0))
            temp_surf.blit(win_text, (450, 350))
            win_sub = self.font_medium.render("Your PC is ready! Press R to restart", True, (255, 255, 255))
            temp_surf.blit(win_sub, (450, 420))
        
        elif self.game_state == "fail":
            overlay = pygame.Surface((1200, 800))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            temp_surf.blit(overlay, (0, 0))
            fail_text = self.font_large.render("SYSTEM FAILURE!", True, (255, 80, 80))
            temp_surf.blit(fail_text, (480, 350))
            fail_sub = self.font_medium.render("CPU overheated! Always install a cooler! Press R to restart", True, (255, 255, 255))
            temp_surf.blit(fail_sub, (380, 420))
        
        # Draw temp surface
        temp_data = pygame.image.tostring(temp_surf, "RGBA", True)
        glRasterPos2d(0, 0)
        glDrawPixels(1200, 800, GL_RGBA, GL_UNSIGNED_BYTE, temp_data)
        
        # Restore 3D
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def run(self):
        print("=" * 60)
        print("PC BUILDER SIMULATOR by WSS - ULTIMATE EDITION")
        print("=" * 60)
        print("✊ MAKE A FIST over a component to GRAB it!")
        print("🖐️ OPEN HAND over the MOTHERBOARD to PLACE it!")
        print("⚠️ IMPORTANT: Install CPU FIRST, then COOLER!")
        print("💥 Forgot CPU Cooler? SYSTEM OVERHEATS!")
        print("🔧 Build the complete PC to WIN!")
        print("Press Q to quit | R to restart")
        print("=" * 60)
        
        self.game_state = "building"
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_r:
                        self.__init__()
                        self.game_state = "building"
            
            self.update_hand_tracking()
            self.update_build_status()
            
            self.draw_3d_scene()
            self.draw_2d_ui()
            
            pygame.display.flip()
            clock.tick(60)
        
        self.cap.release()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PCBuilderGame()
    game.run()