SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 5
WHITE = (255, 255, 255)
WALL_COLOR = (70, 70, 80)
BG_COLOR = (30, 30, 35)
TILE_SIZE = 50
DOOR_COLOR = (150, 75, 0)
DOOR_OPEN_COLOR = (80, 50, 20)
INTERACT_RANGE = 60
with open("map_export.txt", "r") as f:
    LEVEL_MAP = [line.strip() for line in f.readlines()]
