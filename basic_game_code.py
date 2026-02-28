import pygame
import math
from game_config import *

class Camera:
    def __init__(self):
        self.offset = pygame.Vector2(0, 0)

    def apply(self, target_rect):
        return target_rect.move(self.offset)

    def update(self, target):
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)
        self.offset = pygame.Vector2(x, y)

class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface, camera):
        pygame.draw.rect(surface, WALL_COLOR, camera.apply(self.rect))

class Door:
    def __init__(self, x, y, orientation="vertical"):
        self.is_open = False
        self.thickness = 10
        
        # We store the "tile center" for easier interaction distance checking
        self.center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)

        # Create the thin sliver rect
        if orientation == "vertical":
            self.rect = pygame.Rect(x + (TILE_SIZE // 2 - self.thickness // 2), y, self.thickness, TILE_SIZE)
        else:
            self.rect = pygame.Rect(x, y + (TILE_SIZE // 2 - self.thickness // 2), TILE_SIZE, self.thickness)

    def interact(self, player_rect):
        if not self.is_open:
            self.is_open = True
        else:
            # SAFETY CHECK: Only close if the player isn't currently standing inside the sliver
            if not self.rect.colliderect(player_rect):
                self.is_open = False

    def draw(self, surface, camera):
        color = DOOR_OPEN_COLOR if self.is_open else DOOR_COLOR
        pygame.draw.rect(surface, color, camera.apply(self.rect))

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)

    def move(self, walls, doors):
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

        # Obstacles = Walls + Closed Doors
        obstacles = [w.rect for w in walls] + [d.rect for d in doors if not d.is_open]

        # X movement & collision
        self.rect.x += dx * PLAYER_SPEED
        for obj_rect in obstacles:
            if self.rect.colliderect(obj_rect):
                if dx > 0: self.rect.right = obj_rect.left
                if dx < 0: self.rect.left = obj_rect.right

        # Y movement & collision
        self.rect.y += dy * PLAYER_SPEED
        for obj_rect in obstacles:
            if self.rect.colliderect(obj_rect):
                if dy > 0: self.rect.bottom = obj_rect.top
                if dy < 0: self.rect.top = obj_rect.bottom

    def draw(self, surface, camera):
        pygame.draw.rect(surface, (50, 150, 255), camera.apply(self.rect))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Top Down Door Engine")
    clock = pygame.time.Clock()

    walls = []
    doors = []
    player = None

    # Load level and determine door orientation automatically
    for r, row in enumerate(LEVEL_MAP):
        for c, char in enumerate(row):
            x, y = c * TILE_SIZE, r * TILE_SIZE
            if char == "W":
                walls.append(Wall(x, y, TILE_SIZE, TILE_SIZE))
            elif char == "D":
                # If there are walls to the left and right, it's a horizontal door
                # Otherwise, default to vertical
                orientation = "vertical"
                if 0 < c < len(row) - 1:
                    if LEVEL_MAP[r][c-1] == "W" and LEVEL_MAP[r][c+1] == "W":
                        orientation = "horizontal"
                doors.append(Door(x, y, orientation))
            elif char == "P":
                player = Player(x, y)

    if not player: player = Player(100, 100)
    camera = Camera()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Interact with 'E'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    for door in doors:
                        dist = math.hypot(player.rect.centerx - door.center[0], 
                                          player.rect.centery - door.center[1])
                        if dist < INTERACT_RANGE:
                            door.interact(player.rect)

        player.move(walls, doors)
        camera.update(player)

        screen.fill(BG_COLOR)
        
        for wall in walls: wall.draw(screen, camera)
        for door in doors: door.draw(screen, camera)
        player.draw(screen, camera)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()