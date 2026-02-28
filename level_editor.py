import pygame
import sys

# --- Configuration ---
GRID_SIZE = 30
CELL_SIZE = 20
WINDOW_SIZE = GRID_SIZE * CELL_SIZE

# Color Palette (R, G, B)
COLORS = {
    "." : (30, 30, 30),    # Empty - Dark Grey
    "W" : (200, 200, 200), # Wall - White/Light Grey
    "D" : (150, 75, 0),    # Door - Brown
    "T" : (255, 0, 0),      # Trap - Red
    "P" : (0, 255, 0)       # Player Start - Green
}

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Level Painter: Press 'S' to Export")

# Initialize grid with empty space
grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def export_grid(grid_data):
    """Converts the 2D list into a list of strings and saves to file."""
    level_strings = ["".join(row) for row in grid_data]
    
    with open("map_export.txt", "w") as f:
        for line in level_strings:
            f.write(f'"{line}",\n')
    print("Level exported to map_export.txt!")
    return level_strings

# --- Main Loop ---
current_char = "W" # Default drawing tool
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Keyboard Selection
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: current_char = "W" # Wall
            if event.key == pygame.K_2: current_char = "." # Erase
            if event.key == pygame.K_3: current_char = "D" # Door
            if event.key == pygame.K_4: current_char = "T" # Trap
            if event.key == pygame.K_s:
                export_grid(grid)

    # Drawing Logic (Hold mouse to paint)
    mouse_buttons = pygame.mouse.get_pressed()
    if mouse_buttons[0]: # Left Click
        pos = pygame.mouse.get_pos()
        x, y = pos[0] // CELL_SIZE, pos[1] // CELL_SIZE
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            grid[y][x] = current_char

    # --- Rendering ---
    screen.fill((0, 0, 0))
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            char = grid[row][col]
            pygame.draw.rect(
                screen, 
                COLORS[char], 
                (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            )
    
    pygame.display.flip()

pygame.quit()
sys.exit()
