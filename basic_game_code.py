import pygame
import math
from game_config import *
from reset_dialogue import save_menu

from enemy import *

def handle_door_interact(player, doors):
    """Checks for nearby doors and toggles them. Returns list of toggled door indices."""
    toggled_indices = []
    for i, door in enumerate(doors):
        dist = math.hypot(player.rect.centerx - door.center[0], 
                          player.rect.centery - door.center[1])
        if dist < INTERACT_RANGE:
            door.interact(player.rect)
            toggled_indices.append(i)
    return toggled_indices

def handle_door_interact(player, doors):
    """Checks for nearby doors and toggles them. Returns list of toggled door indices."""
    toggled_indices = []
    for i, door in enumerate(doors):
        dist = math.hypot(player.rect.centerx - door.center[0], 
                          player.rect.centery - door.center[1])
        if dist < INTERACT_RANGE:
            door.interact(player.rect)
            toggled_indices.append(i)
    return toggled_indices

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

class Ghost:
    def __init__(self,x,y):
        self.rect = pygame.Rect(x,y,40,40)
    
    def draw(self, surface, camera):
        color = (255, 0, 255)
        pygame.draw.rect(surface, color, camera.apply(self.rect))

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.health = Health(100, self.rect)
        self.flash_timer = -100000

    def take_damage(self, amount):
        self.health.take_damage(amount)
        self.flash_timer = pygame.time.get_ticks()
    
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
        move_with_collision(self.rect, dx * PLAYER_SPEED, dy * PLAYER_SPEED, obstacles)

    def draw(self, surface, camera):
        now = pygame.time.get_ticks()
        color = (255, 0, 0) if now - self.flash_timer < 150 else (50, 150, 255)
        pygame.draw.rect(surface, color, camera.apply(self.rect))
        self.health.draw(surface, camera)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Top Down Door Engine")
    clock = pygame.time.Clock()
    running = True
    saved_slots = [None,None]
    history = None
    while running:
        if history:
            save_menu(screen,history,saved_slots)
        history = {"interactions": {}, # interactions: frame -> list of door indices toggled
                   "locations": {}} #locations: frame -> (player_x, player_y) for every locationInterval frames (look in config)
        walls = []
        doors = []
        player = None
        seq1 = None
        seq2 = None
        enemies = []
        frame = 0
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
                elif char == "G":
                    enemies.append(Grunt(x, y))
                elif char == "P":
                    player = Player(x, y)

        if not player: 
            player = Player(100, 100)
        if saved_slots[0]:
            seq1 = saved_slots[0]
            ghost1 = Ghost(*saved_slots[0]["locations"][1])
        if saved_slots[1]:
            seq2 = saved_slots[1]
            ghost2 = Ghost(*saved_slots[1]["locations"][1])
        camera = Camera()

        reset = False
        while not reset:
            frame += 1
            if seq1:
                if seq1["interactions"] and frame in seq1["interactions"]:
                    for index in seq1["interactions"][frame]:
                        door = doors[index]
                        door.interact(player.rect)
                if seq1["locations"] and frame in seq1["locations"]:
                    ghost1.rect.topleft = seq1["locations"][frame]

            if seq2:
                if seq2["interactions"] and frame in seq2["interactions"]:
                    for index in seq2["interactions"][frame]:
                        door = doors[index]
                        door.interact(player.rect) # Ghost interacts with the door, but it still toggles)
                if seq2["locations"] and frame in seq2["locations"]:
                    ghost2.rect.topleft = seq2["locations"][frame]

            if frame % LOCATION_INTERVAL == 0 or frame == 1:
                history["locations"][frame] = (player.rect.x, player.rect.y)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    reset = True
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        reset = True
                    if event.key == pygame.K_e:
                        history["interactions"][frame] = handle_door_interact(player,doors)

            player.move(walls, doors)
            camera.update(player)

            screen.fill(BG_COLOR)
        
            for wall in walls: wall.draw(screen, camera)
            for door in doors: door.draw(screen, camera)
            player.draw(screen, camera)
            if seq1:
                ghost1.draw(screen, camera)
            if seq2:
                ghost2.draw(screen, camera)
            pygame.display.flip()
            clock.tick(FPS)
    print(history)
    pygame.quit()

if __name__ == "__main__":
    main()
