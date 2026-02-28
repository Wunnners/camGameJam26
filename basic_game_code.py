import pygame
import math
from game_config import *
from reset_dialogue import save_menu
from gate import *

from enemy import *
from cannon import Cannon

def move_with_collision(rect, dx, dy, obstacles):
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

class Boundary:
    def __init__(self, x, y, w, h, color):
        self.color = color
        self.rect = pygame.Rect(x, y, w, h)
    def draw(self, surface, camera):
        pygame.draw.rect(surface, self.color, camera.apply(self.rect))


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

class Ghost:
    def __init__(self,x,y):
        self.rect = pygame.Rect(x,y,40,40)
    
    def draw(self, surface, camera):
        color = (255, 0, 255)
        pygame.draw.rect(surface, color, camera.apply(self.rect))

class Player:
    def __init__(self, x, y, boundary, doors, cannons, gates):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.health = Health(100, self.rect)
        self.flash_timer = -100000
        self.mounted_cannon = None
        self.cannons = cannons
        self.boundary = boundary 
        self.doors = doors
        self.gates = gates

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
        if self.mounted_cannon: return
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_DOWN]:  dy += 1

        if dx != 0 and dy != 0:
            factor = 1 / math.sqrt(2)
            dx, dy = dx * factor, dy * factor

        obstacles = [w.rect for w in self.boundary] + \
        [d.rect for d in self.doors if not d.is_open] + \
        [g.rect for g in self.gates if not g.is_open]
        move_with_collision(self.rect, dx * PLAYER_SPEED, dy * PLAYER_SPEED, obstacles)

    def draw(self, surface, camera):
        if self.mounted_cannon: return 
        now = pygame.time.get_ticks()
        color = (255, 0, 0) if now - self.flash_timer < 150 else (50, 150, 255)
        pygame.draw.rect(surface, color, camera.apply(self.rect))
        self.health.draw(surface, camera)

# --- MAIN ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Top Down Melee, Cannon & Gate Engine")
    clock = pygame.time.Clock()
    
    running = True
    saved_slots = [None, None]
    history = None

    while running:
        if history:
            save_menu(screen, history, saved_slots)
        
        history = {"interactions": {}, "locations": {}}
        walls, doors, waters, cannons, buttons, gates, enemies = [], [], [], [], [], [], []
        player = None
        seq1, seq2 = None, None
        frame = 0
        
        # Load Level
        button_map: dict[str, list[GateButton]] = {}
        gate_map: dict[str, list[tuple]] = {}
        for r, row in enumerate(LEVEL_MAP):
            for c, char in enumerate(row):
                x, y = c * TILE_SIZE, r * TILE_SIZE
                if char == "W": walls.append(Boundary(x, y, TILE_SIZE, TILE_SIZE, WALL_COLOR))
                elif char == "B": waters.append(Boundary(x, y, TILE_SIZE, TILE_SIZE, WATER_COLOR))
                elif char == "G": enemies.append(Grunt(x, y))
                elif char == "T": cannons.append(Cannon(x, y))
                elif char == "P": player_start_pos = (x, y)
                elif char == "D":
                    orientation = "vertical"
                    if 0 < c < len(row) - 1:
                        if LEVEL_MAP[r][c-1] == "W" and LEVEL_MAP[r][c+1] == "W":
                            orientation = "horizontal"
                    doors.append(Door(x, y, orientation))
                elif char.islower():
                    button = GateButton(x, y)
                    if char not in button_map: button_map[char] = []
                    button_map[char].append(button)
                    buttons.append(button)
                elif char.isupper():
                    if char not in gate_map: gate_map[char] = []
                    gate_map[char].append((x, y))
        for gate_char in gate_map:
            for gate_pos in gate_map[gate_char]:
                gate = Gate(*gate_pos, button_map[gate_char.lower()])
                gates.append(gate)

        player = Player(*player_start_pos, walls + waters, doors, cannons, gates)
        if saved_slots[0]:
            seq1 = saved_slots[0]
            ghost1 = Ghost(*saved_slots[0]["locations"][1])
        if saved_slots[1]:
            seq2 = saved_slots[1]
            ghost2 = Ghost(*saved_slots[1]["locations"][1])
        camera = Camera()
        reset = False
        while not reset and running:
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
            
            # --- EVENTS ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    reset = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        reset = True
                    if event.key == pygame.K_e:
                        # Interact with Doors
                        history["interactions"][frame] = handle_door_interact(player, doors)
                        # Interact with Buttons
                        
                    if event.key == pygame.K_m:
                        player.interact_cannon()

            # --- UPDATE ---
            player.move()
            camera.update(player)

            
            for c in cannons:
                obstacles = [w.rect for w in walls] + [d.rect for d in doors if not d.is_open] \
                    + [g.rect for g in gates if not g.is_open]
                c.update(camera, obstacles, enemies)

            if player.mounted_cannon and pygame.mouse.get_pressed()[0]:
                player.mounted_cannon.shoot()

            for e in enemies:
                obstacles = [w.rect for w in (waters + walls)] + [d.rect for d in doors if not d.is_open]
                e.update(player, obstacles)
                if e.health.is_dead: enemies.remove(e)

            # --- DRAW ---
            screen.fill(BG_COLOR)
            # Draw everything in order
            for obj in walls + waters + doors + buttons + gates + enemies + cannons:
                obj.draw(screen, camera)
            
            if seq1: ghost1.draw(screen, camera)
            if seq2: ghost2.draw(screen, camera)
            
            player.draw(screen, camera)
            
            pygame.display.flip()
            clock.tick(FPS)
            
    pygame.quit()

if __name__ == "__main__":
    main()
