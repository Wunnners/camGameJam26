import pygame
import math
from game_config import *
from enemy import *
from cannon import Cannon

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
        self.center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
        if orientation == "vertical":
            self.rect = pygame.Rect(x + (TILE_SIZE // 2 - self.thickness // 2), y, self.thickness, TILE_SIZE)
        else:
            self.rect = pygame.Rect(x, y + (TILE_SIZE // 2 - self.thickness // 2), TILE_SIZE, self.thickness)

    def interact(self, player_rect):
        if not self.is_open:
            self.is_open = True
        else:
            if not self.rect.colliderect(player_rect):
                self.is_open = False

    def draw(self, surface, camera):
        color = DOOR_OPEN_COLOR if self.is_open else DOOR_COLOR
        pygame.draw.rect(surface, color, camera.apply(self.rect))

class Player:
    def __init__(self, x, y, walls, doors, cannons):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.health = Health(100, self.rect)
        self.flash_timer = -100000
        self.mounted_cannon = None
        self.cannons = cannons
        self.walls = walls 
        self.doors = doors

    def take_damage(self, amount):
        self.health.take_damage(amount)
        self.flash_timer = pygame.time.get_ticks()
    
    def interact_cannon(self):
        if self.mounted_cannon:
            self.mounted_cannon.mounted = False
            self.mounted_cannon = None
        else:
            closest_cannon = None
            min_dist = INTERACT_RANGE
            for cannon in self.cannons:
                dist = math.hypot(self.rect.centerx - cannon.rect.centerx, 
                                  self.rect.centery - cannon.rect.centery)
                if dist < min_dist:
                    min_dist = dist
                    closest_cannon = cannon
            if closest_cannon:
                self.mounted_cannon = closest_cannon
                self.mounted_cannon.mounted = True
                self.rect.center = closest_cannon.rect.center

    def move(self):
        if self.mounted_cannon:
            return
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_DOWN]:  dy += 1

        if dx != 0 and dy != 0:
            factor = 1 / math.sqrt(2)
            dx, dy = dx * factor, dy * factor

        obstacles = [w.rect for w in self.walls] + [d.rect for d in self.doors if not d.is_open]
        move_with_collision(self.rect, dx * PLAYER_SPEED, dy * PLAYER_SPEED, obstacles)

    def draw(self, surface, camera):
        if self.mounted_cannon: 
            return 
        now = pygame.time.get_ticks()
        color = (255, 0, 0) if now - self.flash_timer < 150 else (50, 150, 255)
        pygame.draw.rect(surface, color, camera.apply(self.rect))
        self.health.draw(surface, camera)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    walls, doors, enemies, cannons, projectiles = [], [], [], [], []
    player = None
    player_start_pos = (100, 100)

    for r, row in enumerate(LEVEL_MAP):
        for c, char in enumerate(row):
            x, y = c * TILE_SIZE, r * TILE_SIZE
            if char == "W": walls.append(Wall(x, y, TILE_SIZE, TILE_SIZE))
            elif char == "G": enemies.append(Grunt(x, y))
            elif char == "T": cannons.append(Cannon(x, y))
            elif char == "P": player_start_pos = (x, y)
            elif char == "D":
                orientation = "vertical"
                if 0 < c < len(row) - 1:
                    if LEVEL_MAP[r][c-1] == "W" and LEVEL_MAP[r][c+1] == "W":
                        orientation = "horizontal"
                doors.append(Door(x, y, orientation))

    player = Player(player_start_pos[0], player_start_pos[1], walls, doors, cannons)
    camera = Camera()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e: # Door interaction logic
                    pass 
                if event.key == pygame.K_m:
                    player.interact_cannon()

        # --- UPDATE ---
        player.move()
        camera.update(player)

        # Get shared obstacles for the cannons to use for their projectiles
        obstacles = [w.rect for w in walls] + [d.rect for d in doors if not d.is_open]

        for c in cannons:
            # Cannon handles its own projectiles and enemy damage internally
            c.update(camera, obstacles, enemies)

        # If mounted, the player triggers the shoot function
        if player.mounted_cannon and pygame.mouse.get_pressed()[0]:
            player.mounted_cannon.shoot()

        for e in enemies[:]:
            e.update(player, walls, doors)
            if e.health.is_dead: enemies.remove(e)

        # --- DRAW ---
        screen.fill(BG_COLOR)
        for obj in walls + doors + enemies + cannons: # Projectiles drawn via cannon.draw()
            obj.draw(screen, camera)
            
        player.draw(screen, camera)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()