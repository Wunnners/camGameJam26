import pygame
import math

# --- Configuration & Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 5
PLAYER_COLOR = (50, 150, 255)
WALL_COLOR = (70, 70, 80)
BG_COLOR = (30, 30, 35)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.color = PLAYER_COLOR

    def move(self, walls):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        # Input handling
        if keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_DOWN]:  dy += 1

        # Normalize diagonal movement speed
        # Without this, you move ~40% faster diagonally
        if dx != 0 and dy != 0:
            factor = 1 / math.sqrt(2)
            dx *= factor
            dy *= factor

        # Apply speed
        dx *= PLAYER_SPEED
        dy *= PLAYER_SPEED

        # X-axis movement and collision
        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dx > 0: self.rect.right = wall.rect.left
                if dx < 0: self.rect.left = wall.rect.right

        # Y-axis movement and collision
        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dy > 0: self.rect.bottom = wall.rect.top
                if dy < 0: self.rect.top = wall.rect.bottom

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        pygame.draw.rect(surface, WALL_COLOR, self.rect)

# --- Main Game Setup ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Top-Down Prototype")
    clock = pygame.time.Clock()

    player = Player(100, 100)
    
    # Create a simple landscape/room
    walls = [
        Wall(0, 0, SCREEN_WIDTH, 20),           # Top border
        Wall(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20), # Bottom border
        Wall(0, 0, 20, SCREEN_HEIGHT),          # Left border
        Wall(SCREEN_WIDTH - 20, 0, 20, SCREEN_HEIGHT), # Right border
        Wall(300, 200, 200, 30),                # Obstacle 1
        Wall(500, 400, 30, 150),                # Obstacle 2
    ]

    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Update Logic
        player.move(walls)

        # 3. Rendering
        screen.fill(BG_COLOR)
        for wall in walls:
            wall.draw(screen)
        player.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()