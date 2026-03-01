import pygame
import math
from game_config import *
from reset_dialogue import *
from win_dialogue import win_menu
from music_select import play_music, loop_music
from gate import *
from ss import *
from animation import *

# from enemy import *
from enemy_basic import *
from cannon import *

WARP_MUSIC_PATH = "assets/warp.wav"
NORMAL_MUSIC_PATH = "assets/normal.wav"
INTENSE_MUSIC_PATH = "assets/intense.wav"

sps9, tilea = None, None

def drawtiles(surface, p, cam):
    global sps9, tilea
    screen_pos = cam.apply(p)
    if sps9 is None:
        sps9 = Spritesheet('assets/ppp/Texture/TX Tileset Grass.png', 16)
        tilea = (
        Animation(sps9, 5, list(range(256))),
        )
    rx = (p.x // TILE_SIZE) * TILE_SIZE
    ry = (p.y // TILE_SIZE) * TILE_SIZE
    screen_pos = cam.apply(pygame.Rect(rx, ry, 0, 0))
    wx = screen_pos.x
    wy = screen_pos.y
    for x in range(-30, 30):
        for y in range(-20, 20):
            xx = x + (p.x // TILE_SIZE)
            yy = y + (p.y // TILE_SIZE)
            img = tilea[0].get_image((xx + 377 * yy + 3 * xx * xx) % 256)
            img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            surface.blit(img, (wx + x * TILE_SIZE, wy + y * TILE_SIZE))

def get_room(player, room_info) -> int:
    """
    Determines which room the player is in based on their center point.
    Returns the integer room ID (0-7) or -1 if in a corridor.
    """
    player_center = player.rect.center
    
    for room_id_str, coords in room_info.items():
        if not coords:
            continue
            
        # Find the boundaries of the room based on the digit positions
        min_x = min(c[0] for c in coords)
        max_x = max(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_y = max(c[1] for c in coords)
        
        # Create a Rect covering the room (including the tiles the digits were on)
        room_rect = pygame.Rect(min_x, min_y, 
                                max_x - min_x + TILE_SIZE, 
                                max_y - min_y + TILE_SIZE)
        
        if room_rect.collidepoint(player_center):
            return int(room_id_str)
            
    return -1 # Not in a numbered room (Alleyway)


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
    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        self.offset = pygame.Vector2(0, 0)
        self.width = width
        self.height = height
        self.view_rect = pygame.Rect(0, 0, self.width, self.height)

    def apply(self, target_rect):
        return target_rect.move(self.offset)

    def update(self, target):
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)
        self.offset = pygame.Vector2(x, y)
        self.view_rect.center = target.rect.center

def draw_mini_camera(main_screen, ghost, all_objects, screen_x, screen_y):
    capture_size = MINICAM_CAPTURE_SIZE

    display_size = MINICAM_DISPLAY_SIZE
    mini_surface = pygame.Surface((capture_size, capture_size))
    mini_surface.fill(BG_COLOR) 

    mini_camera = Camera(width=capture_size, height=capture_size)
    mini_camera.update(ghost)

    for obj in all_objects:
        if mini_camera.view_rect.colliderect(obj.rect):
            obj.draw(mini_surface, mini_camera)
    
    scaled_surface = pygame.transform.smoothscale(mini_surface, (display_size, display_size))
    # 4. Draw a nice border around the mini-map so it pops
    pygame.draw.rect(scaled_surface, (255, 255, 255), scaled_surface.get_rect(), 3)

    # 5. Paste the mini_surface onto the main screen at the desired UI coordinates
    main_screen.blit(scaled_surface, (screen_x, screen_y))
class Boundary:
    def __init__(self, x, y, w, h, color):
        self.color = color
        self.rect = pygame.Rect(x, y, w, h)

        # sps = Spritesheet('assets/ss/dungeon_ v1.0/dungeon_.png', 8)
        # self.a = (
        #     Animation(sps, 5, [64]),
        # )

        sps1 = Spritesheet('assets/ppp/Texture/TX Tileset Wall.png', 32)
        sps2 = Spritesheet('assets/ppp/Texture/TX Tileset Grass.png', 16)
        sps3 = Spritesheet('assets/Water+.png', 16)
        self.a = (
            Animation(sps1, 5, [22 + 16]),
            Animation(sps2, 5, [21]),
            Animation(sps3, 60, [2, 3, 4]),
            # Animation(sps3, 800, [5, 6]),
        )
    def draw(self, surface, camera):
        if self.color == WALL_COLOR:
            img = self.a[0].get_image()
            bruh = camera.apply(self.rect)
            # surface.blit(pygame.transform.scale(img, self.rect.size), self.rect)
            surface.blit(pygame.transform.scale(img, bruh.size), bruh)
            return
        if self.color == WATER_COLOR:
            img = self.a[2].get_image()
            bruh = camera.apply(self.rect)
            # surface.blit(pygame.transform.scale(img, self.rect.size), self.rect)
            surface.blit(pygame.transform.scale(img, bruh.size), bruh)
            return
        pygame.draw.rect(surface, self.color, camera.apply(self.rect))


class Goal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def draw(self, surface, camera):
        pygame.draw.rect(surface, (220, 200, 40), camera.apply(self.rect))


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
        sps = Spritesheet('assets/Players/Dwarf/dwarf x4.png', 128)
        self.down = (Animation(sps, 5, [15, 16, 17, 18]), Animation(sps, 5, [2]))
        self.right = (Animation(sps, 5, [5, 6, 7, 8]), Animation(sps, 5, [0]))
        self.up = (Animation(sps, 5, [10, 11, 12, 13]), Animation(sps, 5, [1]))

        self.orit = 2
        self.idle = True
    
    def draw(self, surface, camera):
        if self.disabled:
            return

        # 1. Pick the correct animation set
        if self.orit == 0: bb = self.up
        elif self.orit == 2: bb = self.down
        else: bb = self.right
        
        # 2. Get the raw image
        img = bb[self.idle].get_image().copy() # Copy so we don't tint the original
        if self.orit == 1:
            img = pygame.transform.flip(img, True, False)

        # 3. Apply "Ghost" Tint (Grey/Blue tint)
        # This fills the non-transparent parts of the sprite with a color
        tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        tint.fill((200, 200, 200, 150)) # Grey-blue with some alpha
        img.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Optional: Set overall transparency
        img.set_alpha(180) 

        # 4. Blit to screen
        screen_pos = camera.apply(self.rect)
        img_size = img.get_size()
        surface.blit(img, (screen_pos.x - img_size[0] / 4, screen_pos.y - img_size[1] / 2))

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
        if self.sequence["animations"] and frame in self.sequence["animations"]:
            self.orit,self.idle = self.sequence["animations"][frame]


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
        self.orit = 0 # [0=w, 1=a, 2=s, 3=d]
        self.idle = True
        
        sps = Spritesheet('assets/Players/Dwarf/dwarf x4.png', 128)
        self.down = (Animation(sps, 5, [15, 16, 17, 18]), Animation(sps, 5, [2]))
        self.right = (Animation(sps, 5, [5, 6, 7, 8]), Animation(sps, 5, [0]))
        self.up = (Animation(sps, 5, [10, 11, 12, 13]), Animation(sps, 5, [1]))

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

        if keys[pygame.K_w]:
            dy -= 1
            self.orit = 0
        if keys[pygame.K_a]:
            dx -= 1
            self.orit = 1
        if keys[pygame.K_s]:
            dy += 1
            self.orit = 2
        if keys[pygame.K_d]:
            dx += 1
            self.orit = 3

        if dx != 0 and dy != 0:
            factor = 1 / math.sqrt(2)
            dx, dy = dx * factor, dy * factor

        if dx == 0 and dy == 0:
            self.idle = True
        else:
            self.idle = False

        obstacles = [w.rect for w in self.boundary] + \
        [d.rect for d in self.doors if not d.is_open] + \
        [g.rect for g in self.gates if not g.is_open]
        move_with_collision(self.rect, dx * PLAYER_SPEED, dy * PLAYER_SPEED, obstacles)
        button_indices = self.rect.collidelistall(buttons)
        for i in button_indices:
            buttons[i].press()
        return(self.orit,self.idle)
    

    def draw(self, surface, camera):
        if self.mounted_cannon: return 
        now = pygame.time.get_ticks()
        color = (255, 0, 0) if now - self.flash_timer < 150 else (50, 150, 255)
        if self.orit == 0:
            bb = self.up
        elif self.orit == 2:
            bb = self.down
        else:
            bb = self.right
        img = bb[self.idle].get_image()
        if self.orit == 1:
            img = pygame.transform.flip(img, 1, 0)
        bruh = camera.apply(self.rect)
        # surface.blit(img, (0, 0))
        pp = img.get_size()
        # print(pp)
        # surface.blit(img, (bruh.x - pp[0] / 4, bruh.y - pp[1] / 2))
        surface.blit(img, (bruh.x - pp[0] / 4 - 5, bruh.y - pp[1] / 2 - 20))
        # print(bruh, pp)
        # surface.blit(pygame.transform.scale(img, bruh.size), (bruh.x, bruh.y))
        # surface.blit(img, (bruh.x - bruh.w, bruh.y - bruh.h))
        # pygame.dr
        # pygame.draw.rect(surface, color, camera.apply(self.rect))
        self.health.draw(surface, camera)
        return (self.orit, self.idle)

# --- MAIN ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Top Down Melee, Cannon & Gate Engine")
    clock = pygame.time.Clock()
    
    running = True
    saved_slots = [None, None]
    history = None
    warped_once = False

    while running:
        if warped_once:
            loop_music(INTENSE_MUSIC_PATH)
        else:
            loop_music(NORMAL_MUSIC_PATH)

        if history:
            save_menu(screen,history,saved_slots)
        history = {"doors": {}, # doors: frame -> list of door indices toggled
                   "cShoot": {}, # cShoot: frame -> (cannon index, angle) for every cannon shot
                   "cannons": {}, # cannon: frame -> cannon index interacted with (or None)
                   "animations": {}, # animations: frame -> list of animation types triggered (e.g. "cannon_shoot") for every frame that an animation is triggered (used for replaying cannon shoot animations since they don't have a physical representation like doors do)
                   "locations": {}} #locations: frame -> (player_x, player_y) for every locationInterval frames (look in config)
        walls, doors, waters, cannons, buttons, gates, enemies = [], [], [], [], [], [], []
        goal = None
        player = None
        frame = 0
        
        # Load Level
        button_map: dict[str, list[GateButton]] = {}
        gate_map: dict[str, list[tuple]] = {}
        room_info: dict[str, tuple] = {}
        for r, row in enumerate(LEVEL_MAP):
            for c, char in enumerate(row):
                x, y = c * TILE_SIZE, r * TILE_SIZE
                if char == '.':
                    continue
                elif char.isdigit():
                    if char not in room_info:
                        room_info[char] = []
                    room_info[char].append((x, y))
                    walls.append(Boundary(x, y, TILE_SIZE, TILE_SIZE, WALL_COLOR))
                elif char == "W": walls.append(Boundary(x, y, TILE_SIZE, TILE_SIZE, WALL_COLOR))
                elif char == "B": waters.append(Boundary(x, y, TILE_SIZE, TILE_SIZE, WATER_COLOR))
                elif char == "G": enemies.append(Basic(x, y))
                elif char == "T": 
                    cannon = Cannon(x,y)
                    cannon.index = len(cannons) # Store the index of this cannon for replay purposes
                    cannons.append(cannon)
                elif char == "P": player_start_pos = (x, y)
                elif char == "S": goal = Goal(x, y)
                elif char.lower() == "d":
                    orientation = "vertical" if char.isupper() else "horizontal"
                    doors.append(Door(x, y, orientation))
                elif char.lower() < 'q':
                    if char.islower():
                        button = GateButton(x, y, char.lower())
                        if char not in button_map: button_map[char] = []
                        button_map[char].append(button)
                        buttons.append(button)
                    else:
                        if char not in gate_map: gate_map[char] = []
                        gate_map[char].append((x, y))
                elif char.lower() >= 'q':
                    if char.islower():
                        enemy = Basic(x, y)
                        enemies.append(enemy)
                        if char not in button_map: button_map[char] = []
                        button_map[char].append(enemy)
                    else:
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
        all_drawables = walls + waters + doors + buttons + gates + enemies + cannons
        if goal:
            all_drawables.append(goal)
        reset = False
        trigger_rewind = False
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
                        play_music(WARP_MUSIC_PATH)
                        warped_once = True
                        trigger_rewind = True
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
                    
            if trigger_rewind:
                active_ghosts = [g for g in [ghost1, ghost2] if g is not None]
                replay_reverse(screen, history, all_drawables, camera, player, active_ghosts)
                save_menu(screen, history, saved_slots)
                history = None
                continue

            # --- UPDATE ---
            if not pygame.mixer.music.get_busy():
                if warped_once:
                    loop_music(INTENSE_MUSIC_PATH)
                else:
                    loop_music(NORMAL_MUSIC_PATH)

            player.move(buttons)
            camera.update(player)

            
            for c in cannons:
                obstacles = [w.rect for w in walls] + [d.rect for d in doors if not d.is_open] \
                    + [g.rect for g in gates if not g.is_open]
                c.update(camera, obstacles, enemies)
            gate_blockers = [player.rect] + [enemy.rect for enemy in enemies]
            for g in gates:
                g.update(gate_blockers)

            if player.mounted_cannon and pygame.mouse.get_pressed()[0]:
                val = player.mounted_cannon.shoot() #val = cannon_index,angle tuple or None
                if val:
                    history["cShoot"][frame] = val

            for e in enemies:
                nav_data = {
                    "level_map": LEVEL_MAP,
                    "boundaries": [w.rect for w in (waters + walls)],
                    "doors": doors,
                    "gates": gates,
                }
                e.update(player, nav_data)
                if e.health.is_dead: enemies.remove(e)

            if goal and player.rect.colliderect(goal.rect):
                win_menu(screen)
                history = None
                running = False
                reset = True
                continue

            # --- DRAW ---
            screen.fill(BG_COLOR)
            drawtiles(screen, player.rect, camera)
            # Draw everything in order
            all_drawables = walls + waters + doors + buttons + gates + enemies + cannons
            if goal:
                all_drawables.append(goal)
            for obj in all_drawables:
                if camera.view_rect.colliderect(obj.rect):
                    obj.draw(screen, camera)
            
            if ghost1: ghost1.draw(screen, camera)
            if ghost2: ghost2.draw(screen, camera)
            history["animations"][frame] = player.draw(screen, camera)
            screen_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            if ghost1 and not ghost1.disabled:
                ghost1_screen_pos = camera.apply(ghost1.rect)
                if not screen_rect.colliderect(ghost1_screen_pos): # If off-screen
                    # Draw at the top left
                    if ghost2:
                        ghosts = [ghost1,ghost2]
                    else:
                        ghosts = [ghost1]
                    draw_mini_camera(screen, ghost1, all_drawables + [player] + ghosts, 20, 20)

            if ghost2 and not ghost2.disabled:
                ghost2_screen_pos = camera.apply(ghost2.rect)
                if not screen_rect.colliderect(ghost2_screen_pos): # If off-screen
                    # Draw slightly below the first mini-camera
                    if ghost1:
                        ghosts = [ghost1,ghost2]
                    else:
                        ghosts = [ghost2]
                    draw_mini_camera(screen, ghost2, all_drawables + [player] + ghosts, 20, 40 + MINICAM_DISPLAY_SIZE)

            
            pygame.display.flip()
            clock.tick(FPS)
            
    pygame.quit()

if __name__ == "__main__":
    main()
