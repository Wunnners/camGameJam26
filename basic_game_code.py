import pygame
import math
from config import *

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        # Shift the entity's rect by the camera's negative position
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        # Calculate offset to keep target in the center
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)
        self.camera.topleft = (x, y)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)

    def move(self, walls):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_DOWN]:  dy += 1

        if dx != 0 and dy != 0:
            factor = 1 / math.sqrt(2)
            dx *= factor
            dy *= factor

        # X movement
        self.rect.x += dx * PLAYER_SPEED
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dx > 0: self.rect.right = wall.rect.left
                if dx < 0: self.rect.left = wall.rect.right

        # Y movement
        self.rect.y += dy * PLAYER_SPEED
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dy > 0: self.rect.bottom = wall.rect.top
                if dy < 0: self.rect.top = wall.rect.bottom

    def draw(self, surface, camera):
        # Draw the player at their camera-offset position
        pygame.draw.rect(surface, (50, 150, 255), camera.apply(self))

class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface, camera):
        pygame.draw.rect(surface, WALL_COLOR, camera.apply(self))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # The player is now at a "World" coordinate (e.g., 400, 300)
    player = Player(400, 300)
    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Create a larger "World" with walls spread out
    walls = [
        Wall(100, 100, 200, 30),
        Wall(600, 500, 30, 200),
        Wall(-200, 300, 150, 30),
        Wall(800, -100, 30, 300),
        # A floor boundary just to see the movement better
        Wall(-500, -500, 2000, 20),
        Wall(-500, 1000, 2000, 20),
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 1. Update Player Logic (World Space)
        player.move(walls)
        
        # 2. Update Camera (Follow Player)
        camera.update(player)

        # 3. Render
        screen.fill(BG_COLOR)
        
        # Draw everything relative to camera
        for wall in walls:
            wall.draw(screen, camera)
        player.draw(screen, camera)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
