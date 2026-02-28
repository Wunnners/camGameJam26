import pygame
import math
from game_config import *
from reset_dialogue import save_menu
from gate import *

from enemy import *
from cannon import *

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

# --- CLASSES ---
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
    def __init__(self,x,y,sequence,buttons):
        self.rect = pygame.Rect(x,y,40,40)
        self.disabled = False
        self.sequence = sequence
        self.buttons = buttons
    
    def draw(self, surface, camera):
        if self.disabled:
            return
        color = (255, 0, 255)
        pygame.draw.rect(surface, color, camera.apply(self.rect))

    def toggle_draw(self):
        self.disabled = not self.disabled
    
    def update(self, frame, doors, cannons, player_rect):
        # Handle doors
        if self.sequence["doors"] and frame in self.sequence["doors"]:
            for index in self.sequence["doors"][frame]:
                doors[index].interact(player_rect)
        
        # Handle locations
        if self.sequence["locations"] and frame in self.sequence["locations"]:
            self.rect.topleft = self.sequence["locations"][frame]
            
        # Handle cannons
        if self.sequence["cannons"] and frame in self.sequence["cannons"]:
            self.toggle_draw()
            cannon_index = self.sequence["cannons"][frame]
            cannons[cannon_index].busy = not cannons[cannon_index].busy
        if self.sequence["cShoot"] and frame in self.sequence["cShoot"]:
            cannon = cannons[self.sequence["cShoot"][frame][0]]
            cannon.projectiles.append(Projectile(cannon.rect.centerx, cannon.rect.centery, self.sequence["cShoot"][frame][1]))
        button_indices = self.rect.collidelistall(self.buttons)
        for i in button_indices:
            self.buttons[i].press()

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
    
    def handle_door_interact(self):
        """Checks for nearby doors and toggles them. Returns list of toggled door indices."""
        toggled_indices = []
        for i, door in enumerate(self.doors):
            dist = math.hypot(self.rect.centerx - door.center[0], 
                            self.rect.centery - door.center[1])
            if dist < INTERACT_RANGE:
                door.interact(self.rect)
                toggled_indices.append(i)
        return toggled_indices
    
    def interact_cannon(self):
        ind = None
        if self.mounted_cannon:
            ind = self.mounted_cannon.index
            self.mounted_cannon.busy = False
            self.mounted_cannon.mounted = False
            self.mounted_cannon = None
        else:
            closest_cannon = None
            min_dist = INTERACT_RANGE
            for i, cannon in enumerate(self.cannons):
                if cannon.busy:
                    continue
                dist = math.hypot(self.rect.centerx - cannon.rect.centerx, 
                                  self.rect.centery - cannon.rect.centery)
                if dist < min_dist:
                    min_dist = dist
                    closest_cannon = cannon
                    closest_cannon_index = i
            if closest_cannon:
                self.mounted_cannon = closest_cannon
                self.mounted_cannon.mounted = True
                self.rect.center = closest_cannon.rect.center
                self.mounted_cannon.busy = True
                ind = self.mounted_cannon.index
        return(ind)

    def move(self,buttons):
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
        button_indices = self.rect.collidelistall(buttons)
        for i in button_indices:
            buttons[i].press()
    

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
            save_menu(screen,history,saved_slots)
        history = {"doors": {}, # doors: frame -> list of door indices toggled
                   "cShoot": {}, # cShoot: frame -> (cannon index, angle) for every cannon shot
                   "cannons": {}, # cannon: frame -> cannon index interacted with (or None)
                   "locations": {}} #locations: frame -> (player_x, player_y) for every locationInterval frames (look in config)
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
                elif char == "T": 
                    cannon = Cannon(x,y)
                    cannon.index = len(cannons) # Store the index of this cannon for replay purposes
                    cannons.append(cannon)
                elif char == "P": player_start_pos = (x, y)
                elif char == "D":
                    orientation = "vertical"
                    if 0 < c < len(row) - 1:
                        if LEVEL_MAP[r][c-1] == "W" and LEVEL_MAP[r][c+1] == "W":
                            orientation = "horizontal"
                    doors.append(Door(x, y, orientation))
                elif char.islower():
                    button = GateButton(x, y, char.lower())
                    if char not in button_map: button_map[char] = []
                    button_map[char].append(button)
                    buttons.append(button)
                elif char.isupper():
                    if char not in gate_map: gate_map[char] = []
                    gate_map[char].append((x, y))
        for gate_char in gate_map:
            for gate_pos in gate_map[gate_char]:
                gate = Gate(*gate_pos, button_map[gate_char.lower()], gate_char.lower())
                gates.append(gate)
        player = Player(*player_start_pos, walls + waters, doors, cannons, gates)
        ghost1 = None
        ghost2 = None
        if saved_slots[0]:
            ghost1 = Ghost(*saved_slots[0]["locations"][1], saved_slots[0],buttons)
            
        if saved_slots[1]:
            ghost2 = Ghost(*saved_slots[1]["locations"][1], saved_slots[1],buttons)
        camera = Camera()
        reset = False
        while not reset and running:
            frame += 1
            if ghost1: ghost1.update(frame, doors, cannons, player.rect) #note, update doesn't draw the ghost, that is further down
            if ghost2: ghost2.update(frame, doors, cannons, player.rect)

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
                        continue
                    if event.key == pygame.K_e:
                        # Interact with Doors
                        history["doors"][frame] = player.handle_door_interact()
                        # Interact with Buttons

                    if event.key == pygame.K_m:
                        interacted_cannon_index = player.interact_cannon()
                        if interacted_cannon_index is not None:
                            history["cannons"][frame] = interacted_cannon_index

            # --- UPDATE ---
            player.move(buttons)
            camera.update(player)

            
            for c in cannons:
                obstacles = [w.rect for w in walls] + [d.rect for d in doors if not d.is_open] \
                    + [g.rect for g in gates if not g.is_open]
                c.update(camera, obstacles, enemies)
            for g in gates:
                g.update()

            if player.mounted_cannon and pygame.mouse.get_pressed()[0]:
                val = player.mounted_cannon.shoot() #val = cannon_index,angle tuple or None
                if val:
                    history["cShoot"][frame] = val

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
            if ghost1:
                ghost1.draw(screen, camera)
            if ghost2:
                ghost2.draw(screen, camera)
            pygame.display.flip()
            clock.tick(FPS)
            
    pygame.quit()

if __name__ == "__main__":
    main()
