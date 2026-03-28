import pygame
import math
import random
import sys
import cv2
import mediapipe as mp
import numpy as np
import pygame.gfxdraw

# Initialize Pygame
pygame.init()
pygame.font.init()

# Setup Display with hardware acceleration flags
flags = pygame.DOUBLEBUF | pygame.HWSURFACE
screen = pygame.display.set_mode((1400, 900), flags)
pygame.display.set_caption("PC Builder Simulator by WSS - Ultra Edition")
clock = pygame.time.Clock()

# --- Advanced Color Palette (Gothic / Tech Aesthetic) ---
BG_COLOR = (12, 12, 18)
WHITE = (255, 255, 255)  
GLASS_BG = (25, 25, 35, 180)
GLASS_BORDER = (80, 80, 100, 150)
MOBO_BASE = (15, 18, 22)
MOBO_ACCENT = (40, 45, 55)
TRACE_COLOR = (50, 150, 255, 60)
GOLD_PIN = (255, 215, 0)
SILVER_METAL = (200, 205, 210)
DARK_METAL = (45, 48, 52)
CARBON = (25, 25, 25)
NEON_CYAN = (0, 255, 255)
NEON_PURPLE = (180, 50, 255)
WARNING_RED = (255, 50, 50)
SUCCESS_GREEN = (50, 255, 100)

# Pre-create fonts for performance
FONT_SMALL = pygame.font.Font(None, 18)
FONT_MEDIUM = pygame.font.Font(None, 24)
FONT_LARGE = pygame.font.Font(None, 36)
FONT_TITLE = pygame.font.Font(None, 64)

# --- Helper Functions for Advanced Graphics ---
def create_gradient_surface(width, height, color1, color2, vertical=True):
    """Creates a smooth gradient surface for metallic effects."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    if vertical:
        step_r = (color2[0] - color1[0]) / height
        step_g = (color2[1] - color1[1]) / height
        step_b = (color2[2] - color1[2]) / height
        step_a = (color2[3] - color1[3]) / height if len(color1) == 4 else 0
        
        for i in range(height):
            r = int(color1[0] + step_r * i)
            g = int(color1[1] + step_g * i)
            b = int(color1[2] + step_b * i)
            a = int(color1[3] + step_a * i) if len(color1) == 4 else 255
            pygame.draw.line(surface, (r, g, b, a), (0, i), (width, i))
    else:
        step_r = (color2[0] - color1[0]) / width
        step_g = (color2[1] - color1[1]) / width
        step_b = (color2[2] - color1[2]) / width
        step_a = (color2[3] - color1[3]) / width if len(color1) == 4 else 0
        
        for i in range(width):
            r = int(color1[0] + step_r * i)
            g = int(color1[1] + step_g * i)
            b = int(color1[2] + step_b * i)
            a = int(color1[3] + step_a * i) if len(color1) == 4 else 255
            pygame.draw.line(surface, (r, g, b, a), (i, 0), (i, height))
    return surface

def draw_glass_panel(surface, x, y, width, height, radius=15):
    """Draws a glassy, frosted UI panel."""
    glass = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(glass, GLASS_BG, (0, 0, width, height), border_radius=radius)
    pygame.draw.rect(glass, GLASS_BORDER, (0, 0, width, height), 2, border_radius=radius)
    # Add subtle highlight
    pygame.draw.line(glass, (255, 255, 255, 50), (radius, 1), (width-radius, 1), 2)
    surface.blit(glass, (x, y))

class RealisticComponent:
    def __init__(self, name, x, y, width, height, image_type, slot_name):
        self.name = name
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image_type = image_type
        self.slot_name = slot_name
        self.installed = False
        self.hover = False
        self.selected = False
        self.anim_offset = random.uniform(0, math.pi * 2)
        
        # Pre-render component base to save frame time
        self.cache = self.generate_cache()

    def generate_cache(self):
        surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
        # Drop shadow
        pygame.draw.rect(surf, (0, 0, 0, 100), (12, 12, self.width, self.height), border_radius=8)
        return surf
        
    def update(self, mouse_x, mouse_y):
        # Only update hover if not installed and not selected
        if not self.installed and not self.selected:
            # Expanded hover area for easier grabbing
            hover_expand = 15
            self.hover = (mouse_x > self.x - hover_expand and 
                         mouse_x < self.x + self.width + hover_expand and 
                         mouse_y > self.y - hover_expand and 
                         mouse_y < self.y + self.height + hover_expand)
        else:
            self.hover = False
        self.anim_offset += 0.08
        
    def draw(self, screen, is_held=False):
        # Use original position
        x = self.x
        y = self.y
        
        # Smooth floating effect when uninstalled and not selected
        if not self.installed and not self.selected and not is_held:
            y += math.sin(self.anim_offset * 0.5) * 3

        # Draw cached shadow
        screen.blit(self.cache, (x - 10, y - 10))

        # Draw specific component
        if self.image_type == "cpu": self.draw_cpu(screen, x, y)
        elif self.image_type == "cooler": self.draw_cooler(screen, x, y)
        elif self.image_type == "gpu": self.draw_gpu(screen, x, y)
        elif self.image_type == "ram": self.draw_ram(screen, x, y)
        elif self.image_type == "psu": self.draw_psu(screen, x, y)
        elif self.image_type == "ssd": self.draw_ssd(screen, x, y)
        
        # Selected/Hover glow
        if (self.hover or self.selected) and not self.installed:
            glow = pygame.Surface((self.width+20, self.height+20), pygame.SRCALPHA)
            glow_color = (255, 100, 0, 80) if self.selected else (0, 255, 255, 60)
            border_color = (255, 150, 0) if self.selected else NEON_CYAN
            pygame.draw.rect(glow, glow_color, (0, 0, self.width+20, self.height+20), border_radius=8)
            pygame.draw.rect(glow, border_color, (0, 0, self.width+20, self.height+20), 2, border_radius=8)
            screen.blit(glow, (x-10, y-10))
            
            # Add pulsing effect for selected component
            if self.selected:
                pulse = abs(math.sin(pygame.time.get_ticks() / 200))
                alpha = int(100 + 100 * pulse)
                selection_ring = pygame.Surface((self.width+30, self.height+30), pygame.SRCALPHA)
                pygame.draw.rect(selection_ring, (255, 100, 0, alpha), (0, 0, self.width+30, self.height+30), 3, border_radius=8)
                screen.blit(selection_ring, (x-15, y-15))
    
    def draw_cpu(self, screen, x, y):
        # Base PCB
        pygame.draw.rect(screen, (30, 80, 50), (x, y, self.width, self.height), border_radius=4)
        # Gold contacts edge
        pygame.draw.rect(screen, GOLD_PIN, (x, y, self.width, self.height), 2, border_radius=4)
        # IHS (Heat Spreader) - Metallic Gradient
        ihs = create_gradient_surface(self.width-16, self.height-16, (220, 225, 230), (150, 155, 160))
        screen.blit(ihs, (x+8, y+8))
        pygame.draw.rect(screen, (100, 105, 110), (x+8, y+8, self.width-16, self.height-16), 1)
        
        # Laser etching
        screen.blit(FONT_SMALL.render("INTEL CORE", True, (80, 85, 90)), (x + 20, y + 25))
        screen.blit(pygame.font.Font(None, 24).render("i9 14900K", True, (60, 65, 70)), (x + 20, y + 40))
        
        # Orientation triangle
        pygame.draw.polygon(screen, GOLD_PIN, [(x+4, y+4), (x+12, y+4), (x+4, y+12)])
    
    def draw_cooler(self, screen, x, y):
        # Radiator Block
        rad = create_gradient_surface(self.width, self.height, (40, 40, 40), (10, 10, 10))
        screen.blit(rad, (x, y))
        
        # Metallic Fins
        for i in range(0, self.height, 4):
            pygame.draw.line(screen, (80, 85, 90), (x+2, y+i), (x+self.width-2, y+i), 1)
            
        # Copper Heatpipes
        for i in range(4):
            pygame.draw.rect(screen, (184, 115, 51), (x + 15 + i*25, y-5, 12, self.height+10), border_radius=6)
            pygame.draw.rect(screen, (220, 150, 80), (x + 15 + i*25 + 2, y-5, 3, self.height+10))

        # Volumetric Fan
        fan_center = (x + self.width // 2, y + self.height // 2)
        pygame.draw.circle(screen, (15, 15, 18), fan_center, self.width//2 - 5)
        
        # Spinning Blades
        blade_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        spin_angle = self.anim_offset * 15
        for angle in range(0, 360, 45):
            rad_angle = math.radians(angle + spin_angle)
            end_x = self.width//2 + math.cos(rad_angle) * (self.width//2 - 10)
            end_y = self.height//2 + math.sin(rad_angle) * (self.width//2 - 10)
            pygame.draw.line(blade_surf, (80, 80, 85, 150), (self.width//2, self.height//2), (end_x, end_y), 15)
        screen.blit(blade_surf, (x, y))
        
        # RGB Ring
        rgb = [int(128 + 127 * math.sin(self.anim_offset + offset)) for offset in (0, 2, 4)]
        pygame.draw.circle(screen, rgb, fan_center, self.width//2 - 2, 3)
        pygame.draw.circle(screen, (30, 30, 35), fan_center, 15)
    
    def draw_gpu(self, screen, x, y):
        # Stealth Shroud
        pygame.draw.rect(screen, CARBON, (x, y, self.width, self.height), border_radius=8)
        pygame.draw.rect(screen, DARK_METAL, (x+2, y+2, self.width-4, self.height-4), 2, border_radius=8)
        
        # Angular Geometry Design
        pygame.draw.polygon(screen, (40, 40, 45), [(x, y+20), (x+40, y), (x+self.width, y), (x+self.width, y+30)])
        
        # Animated RGB Strip
        rgb = [int(128 + 127 * math.sin(self.anim_offset * 2 + o)) for o in (0, 1, 2)]
        pygame.draw.rect(screen, rgb, (x, y+8, self.width, 4))
        
        # Fans
        fan_spin = self.anim_offset * 12
        for fan in range(3):
            fan_x = x + 25 + fan * 45
            fan_y = y + 45
            pygame.draw.circle(screen, (10, 10, 12), (fan_x, fan_y), 20)
            # Spinning blades
            for angle in range(0, 360, 60):
                rad = math.radians(angle + fan_spin)
                end_x = fan_x + math.cos(rad) * 18
                end_y = fan_y + math.sin(rad) * 18
                pygame.draw.line(screen, (60, 60, 65), (fan_x, fan_y), (end_x, end_y), 4)
            pygame.draw.circle(screen, (30, 30, 30), (fan_x, fan_y), 6)
        
        # Text
        screen.blit(FONT_SMALL.render("RTX 4090", True, (255, 255, 255)), (x + 10, y + 85))
        screen.blit(FONT_SMALL.render("SUPRIM X", True, (150, 150, 150)), (x + 10, y + 95))
    
    def draw_ram(self, screen, x, y):
        # Heatsink
        pygame.draw.rect(screen, (20, 20, 25), (x, y, self.width, self.height), border_radius=3)
        # Metallic accents
        pygame.draw.polygon(screen, (60, 60, 65), [(x, y+10), (x+20, y+10), (x+30, y+30), (x, y+30)])
        pygame.draw.polygon(screen, (60, 60, 65), [(x+self.width, y+10), (x+self.width-20, y+10), (x+self.width-30, y+30), (x+self.width, y+30)])
        
        # Pulsing RGB Top Line
        rgb = [int(128 + 127 * math.sin(self.anim_offset + o)) for o in (0, 1, 2)]
        pygame.draw.rect(screen, rgb, (x, y, self.width, 6), border_radius=2)
        
        # Label
        screen.blit(FONT_SMALL.render("TRIDENT Z5", True, SILVER_METAL), (x + 15, y + 35))
        screen.blit(pygame.font.Font(None, 12).render("DDR5 7200", True, (150, 150, 150)), (x + 20, y + 50))
    
    def draw_psu(self, screen, x, y):
        # Casing
        pygame.draw.rect(screen, (25, 25, 28), (x, y, self.width, self.height), border_radius=4)
        # Fan Grill Texture
        fan_x, fan_y = x + self.width - 45, y + 15
        pygame.draw.circle(screen, (15, 15, 15), (fan_x + 20, fan_y + 20), 22)
        for i in range(1, 22, 4):
            pygame.draw.circle(screen, (50, 50, 55), (fan_x + 20, fan_y + 20), i, 1)
        
        # Label & Branding
        pygame.draw.rect(screen, (40, 40, 45), (x + 5, y + 15, 45, 60), border_radius=2)
        screen.blit(pygame.font.Font(None, 16).render("1200W", True, GOLD_PIN), (x + 8, y + 25))
        screen.blit(FONT_SMALL.render("80+ PLATINUM", True, (200, 200, 200)), (x + 8, y + 45))
        
        # Modular Ports
        for i in range(2):
            for j in range(3):
                pygame.draw.rect(screen, (10, 10, 10), (x + 55 + j*18, y + 15 + i*15, 12, 10), border_radius=1)
    
    def draw_ssd(self, screen, x, y):
        # M.2 PCB
        pygame.draw.rect(screen, (10, 15, 12), (x, y, self.width, self.height), border_radius=2)
        # Gold Pins
        for i in range(0, int(self.height), 4):
            pygame.draw.rect(screen, GOLD_PIN, (x + self.width - 6, y + i, 6, 2))
            
        # Graphene Heatsink Sticker
        pygame.draw.rect(screen, (30, 30, 35), (x+5, y+2, self.width-15, self.height-4), border_radius=1)
        pygame.draw.line(screen, WARNING_RED, (x+10, y+10), (x+self.width-20, y+10), 2)
        
        screen.blit(FONT_SMALL.render("990 PRO", True, (255, 255, 255)), (x + 10, y + 15))
        screen.blit(pygame.font.Font(None, 12).render("2TB NVMe", True, (150, 150, 150)), (x + 10, y + 25))

class RealisticSlot:
    def __init__(self, name, x, y, width, height, slot_type):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.slot_type = slot_type
        self.occupied = False
        self.occupied_by = None
        self.hover = False
        
    def update(self, mouse_x, mouse_y):
        # Expanded hover area for slots
        hover_expand = 10
        self.hover = (mouse_x > self.x - hover_expand and 
                     mouse_x < self.x + self.width + hover_expand and 
                     mouse_y > self.y - hover_expand and 
                     mouse_y < self.y + self.height + hover_expand)
        
    def draw(self, screen):
        # Draw Slot Base Hardware
        if not self.occupied:
            if self.slot_type == "cpu_socket":
                # Detailed LGA Socket with shield mechanism
                pygame.draw.rect(screen, (40, 42, 45), (self.x, self.y, self.width, self.height), border_radius=5)
                pygame.draw.rect(screen, (20, 20, 22), (self.x+10, self.y+10, self.width-20, self.height-20))
                # Pin grid illusion
                for i in range(12, self.width-12, 8):
                    for j in range(12, self.height-12, 8):
                        screen.set_at((self.x+i, self.y+j), GOLD_PIN)
                
                # Draw shield mechanism (open or closed)
                if hasattr(self, 'shield_open') and self.shield_open:
                    # Open shield - show the socket
                    pygame.draw.rect(screen, (100, 100, 110), (self.x+5, self.y-10, self.width-10, 15), border_radius=2)
                    pygame.draw.rect(screen, SILVER_METAL, (self.x+self.width//2-15, self.y-8, 30, 8))
                    # Draw "OPEN" text
                    screen.blit(FONT_SMALL.render("SHIELD OPEN", True, NEON_CYAN), (self.x+20, self.y-25))
                else:
                    # Closed shield - cover the socket
                    pygame.draw.rect(screen, DARK_METAL, (self.x-5, self.y-5, self.width+10, self.height+10), border_radius=5)
                    pygame.draw.rect(screen, SILVER_METAL, (self.x, self.y, self.width, self.height), 2, border_radius=5)
                    screen.blit(FONT_SMALL.render("CPU SHIELD", True, SILVER_METAL), (self.x+25, self.y+40))
                    screen.blit(FONT_SMALL.render("LOCKED", True, WARNING_RED), (self.x+30, self.y+60))
                
                # Retention Arm
                pygame.draw.line(screen, SILVER_METAL, (self.x+self.width, self.y+10), (self.x+self.width+10, self.y+10), 4)
                pygame.draw.line(screen, SILVER_METAL, (self.x+self.width+10, self.y+10), (self.x+self.width+10, self.y+self.height-10), 4)
                
            elif self.slot_type == "pcie_slot":
                # Reinforced PCIe Slot
                pygame.draw.rect(screen, (30, 30, 35), (self.x, self.y, self.width, self.height), border_radius=2)
                pygame.draw.rect(screen, SILVER_METAL, (self.x-2, self.y-2, self.width+4, self.height+4), 1)
                pygame.draw.rect(screen, SILVER_METAL, (self.x+self.width-15, self.y, 15, self.height))
                for i in range(5, self.width-20, 8):
                    pygame.draw.line(screen, (15, 15, 15), (self.x+i, self.y+2), (self.x+i, self.y+self.height-2))
            
            elif self.slot_type == "ram_slot":
                # RAM slot with click mechanism
                pygame.draw.rect(screen, (25, 25, 28), (self.x, self.y, self.width, self.height))
                
                # Draw RAM slot clips
                clip_color = SUCCESS_GREEN if hasattr(self, 'clip_open') and self.clip_open else SILVER_METAL
                pygame.draw.rect(screen, clip_color, (self.x-2, self.y+10, 4, self.height-20))
                pygame.draw.rect(screen, clip_color, (self.x+self.width-2, self.y+10, 4, self.height-20))
                pygame.draw.line(screen, (10, 10, 10), (self.x+self.width//2, self.y), (self.x+self.width//2, self.y+self.height), 2)
                
                # Show instruction if clips are open
                if hasattr(self, 'clip_open') and self.clip_open:
                    screen.blit(FONT_SMALL.render("CLIPS OPEN", True, SUCCESS_GREEN), (self.x-20, self.y+60))

            else:
                 pygame.draw.rect(screen, (30, 30, 35), (self.x, self.y, self.width, self.height), 2, border_radius=4)

        # Holographic Target Hover Effect
        if self.hover and not self.occupied:
            glow = pygame.Surface((self.width+30, self.height+30), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 255, 100, 40), (0, 0, self.width+30, self.height+30), border_radius=8)
            pygame.draw.rect(glow, SUCCESS_GREEN, (0, 0, self.width+30, self.height+30), 2, border_radius=8)
            
            # Corner markers
            L = 15
            pygame.draw.line(glow, SUCCESS_GREEN, (0, 0), (L, 0), 3)
            pygame.draw.line(glow, SUCCESS_GREEN, (0, 0), (0, L), 3)
            pygame.draw.line(glow, SUCCESS_GREEN, (self.width+30, 0), (self.width+30-L, 0), 3)
            pygame.draw.line(glow, SUCCESS_GREEN, (self.width+30, 0), (self.width+30, L), 3)
            
            screen.blit(glow, (self.x-15, self.y-15))
        
        # Render installed component
        if self.occupied and self.occupied_by:
            self.occupied_by.x = self.x
            self.occupied_by.y = self.y
            self.occupied_by.draw(screen)

class Cable:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name
        self.connected = False
        self.hover = False
        self.start_x = x
        self.start_y = y
        self.end_x = x + 150
        self.end_y = y
        
    def update(self, mouse_x, mouse_y):
        if not self.connected:
            self.hover = (mouse_x > self.x - 15 and mouse_x < self.x + 30 and 
                         mouse_y > self.y - 10 and mouse_y < self.y + 20)
        
    def draw(self, screen):
        if not self.connected:
            # Draw cable line
            pygame.draw.line(screen, (50, 50, 60), (self.start_x, self.start_y), (self.end_x, self.end_y), 3)
            
            # Draw connector
            connector_color = (255, 100, 0) if self.hover else SILVER_METAL
            pygame.draw.rect(screen, connector_color, (self.end_x-5, self.end_y-8, 10, 16), border_radius=2)
            
            # Draw cable head
            pygame.draw.circle(screen, (30, 30, 35), (self.start_x, self.start_y), 8)
            pygame.draw.circle(screen, SILVER_METAL, (self.start_x, self.start_y), 5)
            
            # Draw label
            screen.blit(FONT_SMALL.render(self.name, True, (150, 150, 150)), (self.start_x-20, self.start_y-15))
        else:
            # Connected cable - show as green and plugged in
            pygame.draw.line(screen, SUCCESS_GREEN, (self.start_x, self.start_y), (self.end_x, self.end_y), 4)
            pygame.draw.circle(screen, SUCCESS_GREEN, (self.start_x, self.start_y), 10)
            pygame.draw.circle(screen, (30, 30, 35), (self.start_x, self.start_y), 6)

class PCBuilderGame:
    def __init__(self):
        self.game_state = "menu"
        
        # Hand tracking
        self.hand_x = 700
        self.hand_y = 450
        self.is_pinching = False
        self.was_pinching = False
        self.pinch_cooldown = 0
        self.pinch_distance = 0
        self.one_finger_pinch = False  # For RAM slot opening
        
        # Debug info
        self.debug_info = ""
        
        # Hardware Accel Camera init
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, 
            max_num_hands=1,
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
        self.cam_surface = pygame.Surface((280, 210))
        
        self.warning = ""
        self.warning_timer = 0
        self.success = ""
        self.success_timer = 0
        
        self.components = []
        self.slots = []
        self.selected_component = None
        self.mobo_cache = None
        self.cables = []  # For GPU cables
        
        self.create_components()
        self.create_slots()
        self.create_cables()
        self.pre_render_motherboard()
    
    def create_components(self):
        # Centered components with better spacing
        center_x = 180  # Moved from 60 to 180 for better center positioning
        self.components = [
            RealisticComponent("Intel i9", center_x, 150, 100, 100, "cpu", "cpu_socket"),
            RealisticComponent("AIO Cooler", center_x, 280, 120, 120, "cooler", "cooler_mount"),
            RealisticComponent("RTX 4090", center_x, 430, 160, 100, "gpu", "pcie_slot"),
            RealisticComponent("Trident RAM", center_x, 560, 120, 40, "ram", "ram_slot"),
            RealisticComponent("Trident RAM", center_x, 620, 120, 40, "ram", "ram_slot"),
            RealisticComponent("1200W PSU", center_x, 690, 130, 90, "psu", "psu_bay"),
            RealisticComponent("2TB NVMe", center_x, 790, 100, 30, "ssd", "m2_slot")  # Moved up from 810 to 790
        ]
    
    def create_slots(self):
        # Slots remain in same position relative to motherboard
        cpu_slot = RealisticSlot("CPU Socket", 700, 200, 100, 100, "cpu_socket")
        cpu_slot.shield_open = False  # Add shield mechanism
        cpu_slot.shield_opened = False
        
        ram1_slot = RealisticSlot("RAM Slot 1", 850, 180, 20, 140, "ram_slot")
        ram1_slot.clip_open = False
        ram2_slot = RealisticSlot("RAM Slot 2", 890, 180, 20, 140, "ram_slot")
        ram2_slot.clip_open = False
        
        self.slots = [
            cpu_slot,
            RealisticSlot("Cooler Mount", 690, 190, 120, 120, "cooler_mount"),
            ram1_slot,
            ram2_slot,
            RealisticSlot("PCIe Slot", 650, 450, 200, 25, "pcie_slot"),
            RealisticSlot("M.2 Slot", 900, 550, 100, 30, "m2_slot"),
            RealisticSlot("PSU Bay", 1000, 700, 150, 110, "psu_bay")
        ]
    
    def create_cables(self):
        # Create 3 cables for the GPU
        self.cables = [
            Cable(680, 520, "8-PIN PCIe"),
            Cable(680, 550, "8-PIN PCIe"),
            Cable(680, 580, "6-PIN PCIe")
        ]
    
    def pre_render_motherboard(self):
        """Pre-renders the complex motherboard background."""
        self.mobo_cache = pygame.Surface((800, 750), pygame.SRCALPHA)
        
        # ATX Form Factor Board
        pygame.draw.rect(self.mobo_cache, MOBO_BASE, (0, 0, 800, 750), border_radius=15)
        pygame.draw.rect(self.mobo_cache, MOBO_ACCENT, (0, 0, 800, 750), 3, border_radius=15)
        
        # Draw circuit traces
        for _ in range(80):
            start_x = random.randint(20, 780)
            start_y = random.randint(20, 730)
            length = random.randint(20, 100)
            direction = random.choice([(1,0), (0,1), (1,1), (1,-1)])
            end_x = start_x + direction[0] * length
            end_y = start_y + direction[1] * length
            pygame.draw.line(self.mobo_cache, TRACE_COLOR, (start_x, start_y), (end_x, end_y), 1)
            pygame.draw.circle(self.mobo_cache, TRACE_COLOR, (end_x, end_y), 2)

        # VRM Heatsinks
        pygame.draw.rect(self.mobo_cache, DARK_METAL, (70, 50, 60, 250), border_radius=4)
        pygame.draw.rect(self.mobo_cache, DARK_METAL, (140, 50, 200, 40), border_radius=4)
        for i in range(10, 240, 15):
            pygame.draw.line(self.mobo_cache, (60, 60, 65), (70, 50+i), (130, 50+i), 2)
        
        # Chipset Heatsink
        pygame.draw.rect(self.mobo_cache, (20, 20, 25), (550, 500, 150, 150), border_radius=8)
        pygame.draw.polygon(self.mobo_cache, NEON_CYAN, [(550, 600), (600, 500), (650, 500), (600, 600)])
        
        # Audio Capacitors
        for i in range(5):
            pygame.draw.circle(self.mobo_cache, (180, 150, 50), (100, 600 + i*25), 8)
            pygame.draw.circle(self.mobo_cache, SILVER_METAL, (100, 600 + i*25), 6)
            
        # Screws
        for pos in [(30,30), (770,30), (30,720), (770,720), (380,380)]:
            pygame.draw.circle(self.mobo_cache, SILVER_METAL, pos, 8)
            pygame.draw.circle(self.mobo_cache, (10, 10, 10), pos, 4)
    
    def detect_pinch(self, hand_landmarks):
        """Detect pinch gesture between thumb and index finger"""
        # Get thumb tip and index finger tip
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        # Calculate Euclidean distance between thumb and index finger
        distance = math.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        
        # Store pinch distance for visualization
        self.pinch_distance = distance
        
        # Pinch threshold (adjusted for better detection)
        pinch_threshold = 0.08
        
        # Check if other fingers are extended (for one-finger pinch)
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        middle_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        
        # Check if other fingers are extended (for one-finger pinch)
        other_fingers_extended = (middle_tip.y < middle_mcp.y and 
                                  ring_tip.y < middle_mcp.y and 
                                  pinky_tip.y < middle_mcp.y)
        
        self.one_finger_pinch = distance < pinch_threshold and other_fingers_extended
        
        return distance < pinch_threshold
    
    def update_hand_tracking(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        # Update camera surface
        frame_small = cv2.resize(frame, (280, 210))
        frame_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        pygame.surfarray.blit_array(self.cam_surface, frame_small.swapaxes(0, 1))
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Use index finger tip for cursor position
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                # Smooth tracking interpolation
                target_x = int(index_tip.x * 1400)
                target_y = int(index_tip.y * 900)
                self.hand_x += (target_x - self.hand_x) * 0.3
                self.hand_y += (target_y - self.hand_y) * 0.3
                
                # Clamp hand position
                self.hand_x = max(0, min(1400, self.hand_x))
                self.hand_y = max(0, min(900, self.hand_y))
                
                # Detect pinch gesture
                self.is_pinching = self.detect_pinch(hand_landmarks)
                
                # Update debug info
                pinch_status = "PINCHING" if self.is_pinching else "open"
                finger_type = " (1-finger)" if self.one_finger_pinch else ""
                self.debug_info = f"Gesture: {pinch_status}{finger_type} | Distance: {self.pinch_distance:.3f}"
        else:
            self.is_pinching = False
            self.one_finger_pinch = False
            self.debug_info = "No hand detected"
        
        if self.game_state == "building":
            self.handle_interaction()
    
    def handle_interaction(self):
        # Cooldown management
        if self.pinch_cooldown > 0:
            self.pinch_cooldown -= 1
        
        # Handle special interactions for RAM slots with one-finger pinch
        if self.one_finger_pinch and not self.was_pinching and self.pinch_cooldown == 0:
            for slot in self.slots:
                if slot.slot_type == "ram_slot" and slot.hover and not slot.occupied:
                    # Open RAM clips
                    slot.clip_open = not getattr(slot, 'clip_open', False)
                    self.pinch_cooldown = 20
                    if slot.clip_open:
                        self.success = f"RAM CLIPS OPEN for {slot.name}"
                    else:
                        self.success = f"RAM CLIPS CLOSED for {slot.name}"
                    self.success_timer = 40
                    break
        
        # Handle CPU shield mechanism
        if self.is_pinching and not self.was_pinching and self.pinch_cooldown == 0:
            for slot in self.slots:
                if slot.slot_type == "cpu_socket" and slot.hover:
                    # Open/close CPU shield
                    if not hasattr(slot, 'shield_open'):
                        slot.shield_open = False
                    slot.shield_open = not slot.shield_open
                    self.pinch_cooldown = 20
                    if slot.shield_open:
                        self.success = "CPU SHIELD OPEN - Ready to install CPU"
                    else:
                        self.success = "CPU SHIELD CLOSED - CPU locked in place"
                    self.success_timer = 40
                    break
        
        # Regular component selection/deselection with pinch
        if self.is_pinching and not self.was_pinching and self.pinch_cooldown == 0:
            if self.selected_component is None:
                # Check for component under hand cursor
                for comp in reversed(self.components):
                    if not comp.installed and comp.hover:
                        # Select this component
                        self.selected_component = comp
                        comp.selected = True
                        self.pinch_cooldown = 15
                        self.success = f"GRABBED: {comp.name}"
                        self.success_timer = 30
                        break
            else:
                # If already selected, deselect it
                self.selected_component.selected = False
                self.selected_component = None
                self.pinch_cooldown = 15
        
        # Release action (pinch released) - TRY TO PLACE selected component
        elif not self.is_pinching and self.was_pinching and self.selected_component is not None and self.pinch_cooldown == 0:
            placed = False
            for slot in self.slots:
                # Check if slot is hovered and empty
                if not slot.occupied and slot.hover:
                    # Check compatibility
                    if slot.slot_type == self.selected_component.slot_name:
                        # Special check: Cooler requires CPU first
                        if slot.slot_type == "cooler_mount":
                            cpu_slot = next((s for s in self.slots if s.slot_type == "cpu_socket"), None)
                            if cpu_slot and not cpu_slot.occupied:
                                self.warning = "CRITICAL: Install CPU BEFORE Cooler!"
                                self.warning_timer = 60
                                break
                        
                        # Check CPU shield is open before installing CPU
                        if slot.slot_type == "cpu_socket":
                            if not hasattr(slot, 'shield_open') or not slot.shield_open:
                                self.warning = "Open CPU shield first! Pinch on CPU socket"
                                self.warning_timer = 60
                                break
                        
                        # Check RAM clips are open before installing RAM
                        if slot.slot_type == "ram_slot":
                            if not getattr(slot, 'clip_open', False):
                                self.warning = f"Open RAM clips first! Pinch on {slot.name}"
                                self.warning_timer = 60
                                break
                        
                        # Place the component
                        slot.occupied = True
                        slot.occupied_by = self.selected_component
                        self.selected_component.installed = True
                        self.selected_component.selected = False
                        self.selected_component = None
                        placed = True
                        self.success = f"{slot.name} INSTALLED!"
                        self.success_timer = 60
                        self.pinch_cooldown = 20
                        break
                    else:
                        self.warning = f"INCOMPATIBLE: {self.selected_component.name} needs {self.selected_component.slot_name.replace('_', ' ').upper()}"
                        self.warning_timer = 60
                        self.pinch_cooldown = 15
                        break
            
            if not placed and self.selected_component:
                # Deselect if not placed
                self.selected_component.selected = False
                self.selected_component = None
                self.pinch_cooldown = 15
        
        # Handle cable connections after GPU is installed
        gpu_installed = any(slot.slot_type == "pcie_slot" and slot.occupied for slot in self.slots)
        if gpu_installed:
            # Update cables
            for cable in self.cables:
                cable.update(self.hand_x, self.hand_y)
                
                # Connect cable with pinch
                if self.is_pinching and not self.was_pinching and cable.hover and not cable.connected:
                    cable.connected = True
                    self.pinch_cooldown = 15
                    self.success = f"{cable.name} CONNECTED!"
                    self.success_timer = 30
        
        self.was_pinching = self.is_pinching
        
        # Update timers
        if self.warning_timer > 0:
            self.warning_timer -= 1
        if self.success_timer > 0:
            self.success_timer -= 1
        
        # Check win condition (all components installed AND all cables connected)
        all_cables_connected = all(cable.connected for cable in self.cables) if self.cables else True
        if all(c.installed for c in self.components) and all_cables_connected:
            self.game_state = "complete"
    
    def draw(self):
        screen.fill(BG_COLOR)
        
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "building":
            self.draw_building()
        elif self.game_state == "complete":
            self.draw_complete()
            
        pygame.display.flip()
    
    def draw_menu(self):
        # High-tech background grid
        for x in range(0, 1400, 50):
            pygame.draw.line(screen, (20, 20, 30), (x, 0), (x, 900))
        for y in range(0, 900, 50):
            pygame.draw.line(screen, (20, 20, 30), (0, y), (1400, y))
        
        draw_glass_panel(screen, 350, 150, 700, 650)
        
        # Title
        title = FONT_TITLE.render("PC BUILDER: ULTRA", True, NEON_CYAN)
        screen.blit(title, (450, 200))
        
        instructions = [
            "SYSTEM INITIALIZATION...",
            "",
            "CONTROL PROTOCOL:",
            "> PINCH ✌️ (thumb + index) to GRAB/PLACE hardware",
            "> ONE-FINGER PINCH (other fingers extended) to open RAM clips",
            "",
            "CPU INSTALLATION:",
            "1. PINCH on CPU socket to OPEN shield",
            "2. GRAB CPU and place in socket",
            "3. PINCH on CPU socket again to CLOSE shield",
            "",
            "RAM INSTALLATION:",
            "1. ONE-FINGER PINCH on RAM slot to open clips",
            "2. GRAB RAM and insert",
            "3. ONE-FINGER PINCH again to close clips",
            "",
            "GPU INSTALLATION:",
            "1. Install GPU in PCIe slot",
            "2. Connect all 3 power cables (PINCH on each cable)",
            "",
            ">> PRESS [SPACE] TO ENGAGE ASSEMBLY MODE <<"
        ]
        
        y = 280
        for line in instructions:
            color = WHITE if not line.startswith(">") else NEON_PURPLE
            if "CPU INSTALLATION:" in line or "RAM INSTALLATION:" in line or "GPU INSTALLATION:" in line:
                color = NEON_CYAN
            screen.blit(FONT_MEDIUM.render(line, True, color), (400, y))
            y += 28
            
    def draw_building(self):
        # Draw pre-rendered motherboard
        screen.blit(self.mobo_cache, (550, 80))
        
        # Draw Slots
        for slot in self.slots:
            slot.update(self.hand_x, self.hand_y)
            slot.draw(screen)
        
        # Draw cables if GPU is installed
        gpu_installed = any(slot.slot_type == "pcie_slot" and slot.occupied for slot in self.slots)
        if gpu_installed:
            for cable in self.cables:
                cable.draw(screen)
            
            # Show cable connection status
            connected_count = sum(1 for c in self.cables if c.connected)
            if connected_count < 3:
                status_text = FONT_SMALL.render(f"Cables: {connected_count}/3 connected", True, (200, 200, 100))
                screen.blit(status_text, (650, 620))
            
        # Draw Left Component Glass Panel (centered and larger)
        draw_glass_panel(screen, 30, 20, 320, 860)
        screen.blit(FONT_LARGE.render("HARDWARE", True, NEON_CYAN), (110, 50))
        pygame.draw.line(screen, NEON_CYAN, (50, 90), (330, 90), 2)
        
        # Draw Components (uninstalled)
        for comp in self.components:
            if not comp.installed:
                comp.update(self.hand_x, self.hand_y)
                comp.draw(screen)
        
        # Draw a guide box to show detection area (for debugging)
        if self.selected_component is None:
            # Highlight hover area for components
            for comp in self.components:
                if not comp.installed and comp.hover:
                    # Draw expanded hover area
                    hover_rect = pygame.Rect(comp.x - 15, comp.y - 15, comp.width + 30, comp.height + 30)
                    pygame.draw.rect(screen, (0, 255, 255, 30), hover_rect, 2)
            
            # Also highlight slot hover area
            for slot in self.slots:
                if not slot.occupied and slot.hover:
                    hover_rect = pygame.Rect(slot.x - 15, slot.y - 15, slot.width + 30, slot.height + 30)
                    pygame.draw.rect(screen, (0, 255, 100, 30), hover_rect, 2)
            
            # Show hint
            hint_text = FONT_SMALL.render("Hover over any component to highlight it", True, (100, 100, 150))
            screen.blit(hint_text, (40, 890))
        
        # Holographic Cursor with visual feedback
        if self.one_finger_pinch:
            # One-finger pinch indicator (for RAM clips)
            pulse = abs(math.sin(pygame.time.get_ticks() / 100))
            radius = 25 + int(8 * pulse)
            pygame.draw.circle(screen, (100, 255, 100), (int(self.hand_x), int(self.hand_y)), radius)
            pygame.draw.circle(screen, (150, 255, 150), (int(self.hand_x), int(self.hand_y)), radius + 5, 3)
            text = "✌️ ONE-FINGER PINCH"
            text_surf = FONT_SMALL.render(text, True, (100, 255, 100))
            screen.blit(text_surf, (self.hand_x - 60, self.hand_y - 50))
        elif self.is_pinching:
            # Regular pinch indicator
            pulse = abs(math.sin(pygame.time.get_ticks() / 100))
            radius = 20 + int(8 * pulse)
            pygame.draw.circle(screen, (255, 100, 0), (int(self.hand_x), int(self.hand_y)), radius)
            pygame.draw.circle(screen, (255, 150, 50), (int(self.hand_x), int(self.hand_y)), radius + 5, 3)
            
            # Draw pinch lines
            angle1 = pygame.time.get_ticks() / 200
            angle2 = angle1 + math.pi
            x1 = self.hand_x + math.cos(angle1) * 25
            y1 = self.hand_y + math.sin(angle1) * 25
            x2 = self.hand_x + math.cos(angle2) * 25
            y2 = self.hand_y + math.sin(angle2) * 25
            pygame.draw.line(screen, (255, 100, 0), (x1, y1), (x2, y2), 4)
            
            # Show pinch text
            pinch_text = FONT_SMALL.render("✌️ PINCH GRAB", True, (255, 150, 0))
            screen.blit(pinch_text, (self.hand_x - 45, self.hand_y - 50))
            
            # Show selected component name
            if self.selected_component:
                name_text = FONT_MEDIUM.render(f"GRABBED: {self.selected_component.name}", True, (255, 150, 0))
                screen.blit(name_text, (self.hand_x - 70, self.hand_y - 75))
        else:
            # Open hand indicator
            pygame.draw.circle(screen, NEON_CYAN, (int(self.hand_x), int(self.hand_y)), 15)
            pygame.draw.circle(screen, NEON_CYAN, (int(self.hand_x), int(self.hand_y)), 40, 2)
            
            # Rotating reticle
            t = pygame.time.get_ticks() / 500
            for i in range(3):
                angle = t + i * (math.pi * 2 / 3)
                x = self.hand_x + math.cos(angle) * 40
                y = self.hand_y + math.sin(angle) * 40
                pygame.draw.circle(screen, NEON_CYAN, (int(x), int(y)), 5)
            
            # Show ready text
            if self.selected_component is None:
                ready_text = FONT_SMALL.render("Pinch to grab", True, (150, 150, 200))
                screen.blit(ready_text, (self.hand_x - 35, self.hand_y - 30))
        
        # Draw debug info
        debug_surface = FONT_SMALL.render(self.debug_info, True, (200, 200, 200))
        screen.blit(debug_surface, (10, 10))
        
        # UI Overlays
        self.draw_ui_overlays()

    def draw_ui_overlays(self):
        # Status Bar Glass Panel
        draw_glass_panel(screen, 350, 20, 600, 60, radius=10)
        
        installed = sum(1 for c in self.components if c.installed)
        total = len(self.components)
        progress = installed / total
        
        # Progress Bar
        pygame.draw.rect(screen, (30, 30, 40), (370, 35, 560, 30), border_radius=5)
        if progress > 0:
            pygame.draw.rect(screen, NEON_PURPLE, (370, 35, int(560 * progress), 30), border_radius=5)
        screen.blit(FONT_MEDIUM.render(f"SYSTEM ASSEMBLY: {int(progress*100)}%", True, WHITE), (540, 42))
        
        # Alerts
        if self.warning_timer > 0:
            draw_glass_panel(screen, 500, 800, 400, 50, radius=8)
            screen.blit(FONT_MEDIUM.render(self.warning, True, WARNING_RED), (520, 815))
        elif self.success_timer > 0:
            draw_glass_panel(screen, 500, 800, 400, 50, radius=8)
            screen.blit(FONT_MEDIUM.render(self.success, True, SUCCESS_GREEN), (520, 815))
            
        # Camera Feed
        screen.blit(self.cam_surface, (1080, 650))
        pygame.draw.rect(screen, NEON_CYAN, (1080, 650, 280, 210), 2)
        screen.blit(FONT_SMALL.render("CAMERA FEED", True, NEON_CYAN), (1085, 655))
        
        # Footer
        footer = FONT_SMALL.render("ENGINEERED BY KEYSHAUN SOOKDAR | WSS ROBOTICS & IT", True, (100, 100, 120))
        screen.blit(footer, (550, 870))

    def draw_complete(self):
        self.draw_building()
        
        # Dark overlay
        overlay = pygame.Surface((1400, 900), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        draw_glass_panel(screen, 400, 300, 600, 300)
        
        title = FONT_TITLE.render("SYSTEM ONLINE", True, SUCCESS_GREEN)
        screen.blit(title, (520, 350))
        
        stats = FONT_MEDIUM.render("All components installed! Power cables connected!", True, WHITE)
        screen.blit(stats, (450, 430))
        
        pulse = abs(math.sin(pygame.time.get_ticks() / 300))
        color = (int(NEON_CYAN[0]*pulse), int(NEON_CYAN[1]*pulse), int(NEON_CYAN[2]*pulse))
        restart = FONT_MEDIUM.render(">> PRESS [SPACE] TO REBOOT SEQUENCE <<", True, color)
        screen.blit(restart, (520, 500))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if self.game_state == "menu":
                        self.game_state = "building"
                    elif self.game_state == "complete":
                        self.__init__()
            
            self.update_hand_tracking()
            self.draw()
            clock.tick(60)
            
        self.cap.release()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PCBuilderGame()
    game.run()