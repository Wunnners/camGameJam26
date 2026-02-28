import pygame
import math
from config import *

class Camera:
    def __init__(self, width, height):
        # We store the offset as a simple tuple or vector
        self.offset = pygame.Vector2(0, 0)

    def apply(self, target_rect):
        # Move the world-space rect by our camera offset
        return target_rect.move(self.offset)

    def update(self, target):
        # Center the camera on the target (player)
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)
        self.offset = (x, y)

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

        # Normalization so diagonal movement isn't faster
        if dx != 0 and dy != 0:
            factor = 1 / math.sqrt(2)
            dx *= factor
            dy *= factor

        # X movement & collision
        self.rect.x += dx * PLAYER_SPEED
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dx > 0: self.rect.right = wall.rect.left
                if dx < 0: self.rect.left = wall.rect.right

        # Y movement & collision
        self.rect.y += dy * PLAYER_SPEED
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dy > 0: self.rect.bottom = wall.rect.top
                if dy < 0: self.rect.top = wall.rect.bottom

    def draw(self, surface, camera):
        # FIX: We pass self.rect, not self
        pygame.draw.rect(surface, (50, 150, 255), camera.apply(self.rect))

class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface, camera):
        pygame.draw.rect(surface, WALL_COLOR, camera.apply(self.rect))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Top Down Melee Engine")
    clock = pygame.time.Clock()

    walls = []
    player = None

    # Load map from config.py
    for row_index, row in enumerate(LEVEL_MAP):
        for col_index, char in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            if char == "W":
                walls.append(Wall(x, y, TILE_SIZE, TILE_SIZE))
            elif char == "P":
                player = Player(x, y)

    if player is None:
        player = Player(100, 100)

    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player.move(walls)
        camera.update(player)

        screen.fill(BG_COLOR)
        
        for wall in walls:
            wall.draw(screen, camera)
        player.draw(screen, camera)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()