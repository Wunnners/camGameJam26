import pygame
import math
from game_config import *

from ss import *
from animation import *

pygame.font.init()
DEBUG_FONT = pygame.font.SysFont('Arial', 20, bold=True)

bruh = {
    'O': 0,
    'A': 1,
    'M': 2,
    'N': 3,
    'L': 4,
    # sus
    'K': 0,
    'I': 0,
    'J': 0,
}

class GateButton:
    def __init__(self, x, y, button_id: str):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.id = button_id.upper()
        self.pressed_timer = -10000
        self.duration = 10  # 10ms
        print(self.id)
        
        self.text_surf = DEBUG_FONT.render(self.id.upper(), True, (255, 255, 255))
        self.text_rect = self.text_surf.get_rect()
        
        sps = Spritesheet('assets/bb/button UI.png', 16)
        pp = [24, 24 + 36, 24 + 2 * 36, 24 + 3 * 36, 30, 30 + 36, 30 + 72, 30 + 108]
        self.a = (Animation(sps, 5, [pp[bruh[self.id]]]),)

    def press(self):
        self.pressed_timer = pygame.time.get_ticks()

    def is_active(self):
        now = pygame.time.get_ticks()
        return now - self.pressed_timer < self.duration

    def draw(self, surface, camera):
        # 1. Determine State and Color
        active = self.is_active()
        color = (0, 200, 0) if active else (150, 0, 0)
        draw_rect = camera.apply(self.rect)
        
        # 2. Draw Button Base
        img = self.a[0].get_image()
        surface.blit(pygame.transform.scale(img, (draw_rect.width, draw_rect.height)), draw_rect)
        # surface.blit(img, (draw_rect.x, draw_rect.y))
        # pygame.draw.rect(surface, color, draw_rect)
        pygame.draw.rect(surface, (50, 50, 50), draw_rect, 2) # Dark border

        # 3. Draw ID Text (Centered)
        # self.text_rect.center = draw_rect.center
        # surface.blit(self.text_surf, self.text_rect)

        # 4. Optional: Draw Timer Bar if active
        if active:
            time_passed = pygame.time.get_ticks() - self.pressed_timer
            # Calculate width based on remaining time (0.0 to 1.0)
            ratio = 1.0 - (time_passed / self.duration)
            bar_width = int(self.rect.width * ratio)
            # Draw a small yellow bar at the bottom of the button
            bar_rect = pygame.Rect(draw_rect.left, draw_rect.bottom - 5, bar_width, 5)
            pygame.draw.rect(surface, (255, 255, 0), bar_rect)

class Gate:
    def __init__(self, x, y, buttons, gate_id: str):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.buttons = buttons
        self.is_open = False
        self.id = gate_id.upper()
        
        # Pre-render Gate ID
        self.text_surf = DEBUG_FONT.render(self.id, True, (255, 255, 255))
        self.text_rect = self.text_surf.get_rect()

        sps = Spritesheet('assets/bb/button UI.png', 16)
        # self.a = (Animation(sps, 5, [16]), Animation(sps, 5, [17]))

        pp1 = [16, 16 + 36, 16 + 2 * 36, 16 + 3 * 36,
               22, 22 + 36, 22 + 2 * 36, 22 + 3 * 36]
        pp2 = [x + 1 for x in pp1]
        self.a = (Animation(sps, 5, [pp1[bruh[self.id]]]),
                  Animation(sps, 5, [pp2[bruh[self.id]]]))

    def update(self, blocker_rects=None):
        target_is_open = all(button.is_active() for button in self.buttons)
        if target_is_open:
            self.is_open = True
            return

        if blocker_rects is None:
            blocker_rects = []

        if any(self.rect.colliderect(blocker_rect) for blocker_rect in blocker_rects):
            return

        self.is_open = False

    def draw(self, surface, camera):
        draw_rect = camera.apply(self.rect)
        
        # current_color = OPEN_COLOR if self.is_open else CLOSED_COLOR
        # pygame.draw.rect(surface, current_color, draw_rect)
        # text_color = (255, 255, 255) if not self.is_open else (50, 50, 100)
        # id_surf = DEBUG_FONT.render(self.id, True, text_color)
        # self.text_rect.center = draw_rect.center
        # surface.blit(id_surf, self.text_rect)
        # border_color = (100, 100, 255) if self.is_open else (20, 20, 100)
        # pygame.draw.rect(surface, border_color, draw_rect, 2)

        img = self.a[self.is_open].get_image()
        surface.blit(pygame.transform.scale(img, (draw_rect.width, draw_rect.height)), draw_rect)
