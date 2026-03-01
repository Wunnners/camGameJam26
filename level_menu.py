import os
import json
import shutil
import subprocess
import sys

import pygame

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from music_select import *


MENU_BG = (22, 24, 31)
TITLE_COLOR = (240, 240, 240)
TEXT_COLOR = (205, 205, 210)
SELECTED_BG = (70, 95, 150)
COMPLETED_BG = (60, 125, 80)
COMPLETED_SELECTED_BG = (40, 90, 55)
DISABLED_TEXT = (110, 110, 120)
PANEL_BG = (33, 36, 45)
PREVIEW_BG = (16, 18, 24)
PREVIEW_COLORS = {
    ".": (55, 58, 70),
    "W": (170, 175, 190),
    "B": (45, 95, 180),
    "P": (160, 110, 70),
    "S": (235, 205, 70),
    "G": (210, 80, 80),
    "T": (200, 200, 200),
}
MAP_DIR_CANDIDATES = ["map", "maps"]
TARGET_MAP_PATH = "map_select.txt"
GAME_SCRIPT = "basic_game_code.py"
COMPLETION_FILE = "level_progress.json"
MENU_IMAGE_PATH = "assets/menulol.png"
MENU_MUSIC_PATH = "assets/menu.wav"


def get_map_directory():
    for candidate in MAP_DIR_CANDIDATES:
        if os.path.isdir(candidate):
            return candidate
    return None


def clear_completed_maps():
    with open(COMPLETION_FILE, "w") as progress_file:
        json.dump([], progress_file)


def discover_maps():
    map_dir = get_map_directory()
    options = []
    completed_maps = load_completed_maps()

    if map_dir:
        for entry in sorted(os.listdir(map_dir)):
            full_path = os.path.join(map_dir, entry)
            if os.path.isfile(full_path) and entry.lower().endswith(".txt"):
                options.append(
                    {
                        "label": entry,
                        "map_path": full_path,
                        "enabled": True,
                        "grid": load_map_grid(full_path),
                        "completed": full_path in completed_maps,
                    }
                )

    if not options:
        missing_dir = MAP_DIR_CANDIDATES[0]
        options.append(
            {
                "label": f"No maps found in ./{missing_dir}/",
                "map_path": None,
                "enabled": False,
                "grid": [],
                "completed": False,
            }
        )

    return options


def launch_level(map_path):
    shutil.copyfile(map_path, TARGET_MAP_PATH)
    pygame.quit()
    env = os.environ.copy()
    env["SELECTED_MAP_PATH"] = map_path
    subprocess.run([sys.executable, GAME_SCRIPT], check=False, env=env)


def load_completed_maps():
    if not os.path.exists(COMPLETION_FILE):
        return set()

    with open(COMPLETION_FILE, "r") as progress_file:
        try:
            entries = json.load(progress_file)
        except json.JSONDecodeError:
            return set()

    if not isinstance(entries, list):
        return set()
    return set(entries)


def load_map_grid(path):
    rows = []
    with open(path, "r") as map_file:
        for raw_line in map_file:
            line = raw_line.strip()
            if not line:
                continue
            if " " in line:
                rows.append(line.split())
            else:
                rows.append(list(line))
    return rows


def load_menu_background():
    image = pygame.image.load(MENU_IMAGE_PATH).convert()
    return pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))

def draw_home_screen(screen, background, title_font, item_font):
    screen.blit(background, (0, 0))

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 45))
    screen.blit(overlay, (0, 0))

    button_rect = pygame.Rect(0, 0, 300, 64)
    button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    pygame.draw.rect(screen, (48, 82, 58), button_rect, border_radius=12)
    pygame.draw.rect(screen, (205, 225, 210), button_rect, width=2, border_radius=12)

    button_text = item_font.render("Start", True, (245, 245, 245))
    screen.blit(
        button_text,
        (button_rect.centerx - button_text.get_width() // 2, button_rect.y + 18),
    )

    pygame.display.flip()
    return button_rect


def draw_map_preview(screen, preview_rect, grid):
    pygame.draw.rect(screen, PANEL_BG, preview_rect, border_radius=12)
    inner_rect = preview_rect.inflate(-24, -24)
    pygame.draw.rect(screen, PREVIEW_BG, inner_rect, border_radius=10)

    if not grid:
        return

    grid_width = max(len(row) for row in grid)
    grid_height = len(grid)
    if grid_width == 0 or grid_height == 0:
        return

    cell_size = min(inner_rect.width / grid_width, inner_rect.height / grid_height)
    cell_size = max(4, int(cell_size))
    preview_width = cell_size * grid_width
    preview_height = cell_size * grid_height
    start_x = inner_rect.x + (inner_rect.width - preview_width) // 2
    start_y = inner_rect.y + (inner_rect.height - preview_height) // 2

    for row_index, row in enumerate(grid):
        for col_index, token in enumerate(row):
            tile_key = token[0]
            color = PREVIEW_COLORS.get(tile_key, (70, 95, 185) if tile_key.isupper() else (70, 170, 100))
            cell_rect = pygame.Rect(
                start_x + col_index * cell_size,
                start_y + row_index * cell_size,
                cell_size - 1,
                cell_size - 1,
            )
            pygame.draw.rect(screen, color, cell_rect)


def draw_menu(screen, title_font, item_font, small_font, options, selected_index):
    screen.fill(MENU_BG)

    title = title_font.render("Level Select", True, TITLE_COLOR)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

    hint_text = f"Up/Down to select map, Enter to play, Esc to quit"
    hint = item_font.render(hint_text, True, TEXT_COLOR)
    screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 145))

    list_area = pygame.Rect(70, 220, 330, SCREEN_HEIGHT - 290)
    preview_area = pygame.Rect(440, 220, SCREEN_WIDTH - 510, SCREEN_HEIGHT - 290)
    pygame.draw.rect(screen, PANEL_BG, list_area, border_radius=12)

    item_height = 56
    spacing = 14
    list_start_x = list_area.x + 18
    list_start_y = list_area.y + 18
    for index, option in enumerate(options):
        item_rect = pygame.Rect(
            list_start_x,
            list_start_y + index * (item_height + spacing),
            list_area.width - 36,
            item_height,
        )
        if index == selected_index and option["enabled"]:
            bg_color = COMPLETED_SELECTED_BG if option["completed"] else SELECTED_BG
            pygame.draw.rect(screen, bg_color, item_rect, border_radius=8)
        elif option["completed"]:
            pygame.draw.rect(screen, COMPLETED_BG, item_rect, border_radius=8)
        else:
            pygame.draw.rect(screen, (50, 54, 67), item_rect, border_radius=8)

        color = TEXT_COLOR if option["enabled"] else DISABLED_TEXT
        label = small_font.render(option["label"], True, color)
        screen.blit(label, (item_rect.x + 16, item_rect.y + 15))

    selected_option = options[selected_index]
    preview_title = item_font.render(selected_option["label"], True, TITLE_COLOR)
    screen.blit(preview_title, (preview_area.x + 18, preview_area.y - 42))
    draw_map_preview(screen, preview_area, selected_option.get("grid", []))

    pygame.display.flip()


def main():
    pygame.display.init()
    pygame.font.init()
    clear_completed_maps()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Level Menu")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64)
    item_font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 28)
    home_background = load_menu_background()
    play_music(MENU_MUSIC_PATH)

    options = discover_maps()
    selected_index = 0
    view = "home"

    running = True
    while running:
        home_button = None
        if view == "home":
            home_button = draw_home_screen(screen, home_background, title_font, item_font)
        else:
            draw_menu(screen, title_font, item_font, small_font, options, selected_index)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif view == "home":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        view = "levels"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if home_button and home_button.collidepoint(event.pos):
                        view = "levels"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    selection = options[selected_index]
                    if selection["enabled"] and selection["map_path"]:
                        launch_level(selection["map_path"])
                        pygame.init()
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                        pygame.display.set_caption("Level Menu")
                        title_font = pygame.font.SysFont(None, 64)
                        item_font = pygame.font.SysFont(None, 36)
                        small_font = pygame.font.SysFont(None, 28)
                        home_background = load_menu_background()
                        options = discover_maps()
                        view = "levels"

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
