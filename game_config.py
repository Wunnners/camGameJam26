SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 5
WHITE = (255, 255, 255)
WALL_COLOR = (70, 70, 80)
WATER_COLOR = (0, 0, 255)
BG_COLOR = (30, 30, 35)
TILE_SIZE = 50
DOOR_COLOR = (150, 75, 0)
DOOR_OPEN_COLOR = (80, 50, 20)
CLOSED_COLOR = (50, 50, 200)
OPEN_COLOR = (180, 190, 255)
INTERACT_RANGE = 60
LOCATION_INTERVAL = 1 # Record player location every LOCATION_INTERVAL frames for replay
with open("map_export.txt", "r") as f:
    LEVEL_MAP = [line.strip() for line in f.readlines()]
