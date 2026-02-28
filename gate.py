import pygame
from game_config import *

class GateButton:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.pressed_timer = -10000
        self.duration = 3000 # 3 seconds

    def press(self):
        self.pressed_timer = pygame.time.get_ticks()

    def is_active(self):
        now = pygame.time.get_ticks()
        return now - self.pressed_timer < self.duration

    def draw(self, surface, camera):
        # Green if pressed, Dark Red if not
        color = (0, 255, 0) if self.is_active() else (150, 0, 0)
        pygame.draw.rect(surface, color, camera.apply(self.rect))

class Gate:
    def __init__(self, x, y, buttons):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.buttons = buttons
        self.is_open = False

    def update(self):
        if self.is_open:
            return
        self.is_open = all(button.is_active() for button in self.buttons)

    def draw(self, surface, camera):
        current_color = OPEN_COLOR if self.is_open else CLOSED_COLOR
        pygame.draw.rect(surface, current_color, camera.apply(self.rect))
        if self.is_open:
            pygame.draw.rect(surface, (100, 100, 255), camera.apply(self.rect), 2)