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
    "T" : (255, 0, 0),     # Trap - Red
    "P" : (0, 255, 0)      # Player Start - Green
}

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Level Painter: Press 'S' to Export")

# Initialize grid with empty space
grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
traps = [] # NEW: Tracks the (cx, cy) center of every 3x3 trap

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
            
            # --- 3x3 TRAP LOGIC ---
            if current_char == "T":
                # 1. Clip to edges: force the center to be at least 1 tile away from the border
                cx = max(1, min(x, GRID_SIZE - 2))
                cy = max(1, min(y, GRID_SIZE - 2))
                
                # Only execute if we aren't dragging over the exact same trap
                if (cx, cy) not in traps:
                    
                    # 2. Find any existing traps that this new 3x3 will overlap with
                    # (Overlap happens if their centers are within 2 tiles of each other)
                    traps_to_destroy = [t for t in traps if abs(t[0] - cx) <= 2 and abs(t[1] - cy) <= 2]
                    
                    for t in traps_to_destroy:
                        traps.remove(t)
                        # Clear the old trap
                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                grid[t[1] + dy][t[0] + dx] = "."
                    
                    # 3. Draw the new trap
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            grid[cy + dy][cx + dx] = "T"
                    traps.append((cx, cy))
            
            # --- SINGLE TILE LOGIC (Wall, Door, Erase) ---
            else:
                # 1. Check if the tile we clicked is part of an existing 3x3 trap
                traps_to_destroy = [t for t in traps if abs(t[0] - x) <= 1 and abs(t[1] - y) <= 1]
                
                for t in traps_to_destroy:
                    traps.remove(t)
                    # Destroy the entire 3x3 trap to "."
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            grid[t[1] + dy][t[0] + dx] = "."
                
                # 2. Place the single tile (which might overwrite the "." we just made)
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
