import pygame
import math
import random
from game_config import *
from abc import ABC, abstractmethod

import pygame

def move_with_collision(rect, dx, dy, obstacles):
    """
    Moves a rect by dx, dy while checking against a list of obstacle rects.
    """
    # Handle X movement
    rect.x += dx
    for wall in obstacles:
        if rect.colliderect(wall):
            if dx > 0: rect.right = wall.left
            if dx < 0: rect.left = wall.right

    # Handle Y movement
    rect.y += dy
    for wall in obstacles:
        if rect.colliderect(wall):
            if dy > 0: rect.bottom = wall.top
            if dy < 0: rect.top = wall.bottom


class Health:
    def __init__(self, max_hp, owner_rect):
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.owner_rect = owner_rect # Needs the rect to know where to draw

    def take_damage(self, amount):
        assert amount > 0
        self.current_hp = max(0, self.current_hp - amount)

    @property
    def is_dead(self):
        return self.current_hp <= 0

    def draw(self, surface, camera):
        if self.current_hp < self.max_hp:
            # Draw health bar relative to owner's position
            rect = self.owner_rect
            bar_bg = pygame.Rect(rect.x, rect.y - 12, rect.width, 6)
            pygame.draw.rect(surface, (50, 0, 0), camera.apply(bar_bg))
            
            hp_ratio = self.current_hp / self.max_hp
            bar_fg = pygame.Rect(rect.x, rect.y - 12, rect.width * hp_ratio, 6)
            pygame.draw.rect(surface, (0, 255, 0), camera.apply(bar_fg))

class Enemy(ABC):
    @abstractmethod
    def __init__(self, x, y):
        pass
    @abstractmethod
    def take_damage(self, amount):
        pass
    @abstractmethod
    def update(self, player, boundary, doors):
        pass
    @abstractmethod
    def draw(self, surface, camera):
        pass


class Grunt(Enemy):
    """A basic enemy that handles all its own initialization and logic"""
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 35, 35)
        
        self.speed = 2
        self.color = (255, 50, 50)
        self.attack_damage = 10
        self.attack_cooldown = 2000
        self.last_attack_time = 0
        self.health = Health(50, self.rect)

    def take_damage(self, amount):
        self.health.take_damage(amount)
    
    def update(self, player, boundaries, doors):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist != 0 and dist < 400:
            vx = (dx / dist) * self.speed
            vy = (dy / dist) * self.speed
            obstacles = [w.rect for w in boundaries] + [d.rect for d in doors if not d.is_open]
            move_with_collision(self.rect, vx, vy, obstacles)

        if self.rect.colliderect(player.rect):
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack_time > self.attack_cooldown:
                player.take_damage(self.attack_damage)
                self.last_attack_time = current_time

    def draw(self, surface, camera):
        pygame.draw.rect(surface, self.color, camera.apply(self.rect))
        self.health.draw(surface, camera)
