import pygame
import math
from game_config import *

class Projectile:
    def __init__(self, x, y, angle, speed=10, damage=50): # Added default values
        self.rect = pygame.Rect(x, y, 10, 10)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.damage = damage
        self.active = True

    def update(self, obstacles, enemies):
        # Combined 'obstacles' logic is cleaner for the projectile
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        # Check environment collisions (walls/doors combined)
        for obj_rect in obstacles:
            if self.rect.colliderect(obj_rect):
                self.active = False 
                return # Stop processing if we hit a wall

        # Check for enemy collisions
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                enemy.take_damage(self.damage)
                self.active = False
                break

    def draw(self, surface, camera):
        # Using camera.apply().center directly for the drawing position
        pygame.draw.circle(surface, (200, 200, 200), camera.apply(self.rect).center, 5)


class Cannon:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.mounted = False
        self.angle = 0
        self.last_shot = 0
        self.shoot_cooldown = 400 
        self.projectiles = []
        self.busy = False
        self.index = None

    def update(self, camera, obstacles, enemies):
        if self.mounted:
            # Handle aiming relative to world-space mouse
            mx, my = pygame.mouse.get_pos()
            world_mx = mx - camera.offset.x
            world_my = my - camera.offset.y
            self.angle = math.atan2(world_my - self.rect.centery, world_mx - self.rect.centerx)

        # Update all projectiles
        for p in self.projectiles[:]:
            p.update(obstacles, enemies)
            if not p.active:
                self.projectiles.remove(p)

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_cooldown:
            # FIX: Added speed and damage arguments (or used defaults from __init__)
            self.projectiles.append(Projectile(self.rect.centerx, self.rect.centery, self.angle))
            self.last_shot = now
            return(self.index,self.angle)
        else:
            return None

    def draw(self, surface, camera):
        # Draw the base
        pygame.draw.rect(surface, (100, 100, 110), camera.apply(self.rect))
        
        # Draw the barrel
        end_x = self.rect.centerx + math.cos(self.angle) * 40
        end_y = self.rect.centery + math.sin(self.angle) * 40
        
        # Convert world end-point to screen coordinates via camera
        barrel_end = camera.apply(pygame.Rect(end_x, end_y, 0, 0)).topleft
        
        pygame.draw.line(surface, (20, 20, 20), 
                         camera.apply(self.rect).center, 
                         barrel_end, 8)
        
        # Draw bullets
        for p in self.projectiles:
            p.draw(surface, camera)
