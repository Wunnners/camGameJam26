import json
import os

from game_config import *
import pygame

COMPLETION_FILE = "level_progress.json"


def mark_selected_level_completed():
    selected_map_path = os.environ.get("SELECTED_MAP_PATH")
    if not selected_map_path:
        return

    completed_levels = []
    if os.path.exists(COMPLETION_FILE):
        with open(COMPLETION_FILE, "r") as progress_file:
            try:
                loaded = json.load(progress_file)
                if isinstance(loaded, list):
                    completed_levels = loaded
            except json.JSONDecodeError:
                completed_levels = []

    if selected_map_path not in completed_levels:
        completed_levels.append(selected_map_path)
        with open(COMPLETION_FILE, "w") as progress_file:
            json.dump(completed_levels, progress_file)


def win_menu(screen):
    mark_selected_level_completed()

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    font = pygame.font.SysFont(None, 64)
    small_font = pygame.font.SysFont(None, 32)
    title_surf = font.render("You Win", True, (255, 255, 255))
    prompt_surf = small_font.render("Press Enter to go back to level selection", True, (220, 220, 220))

    center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    screen.blit(title_surf, (center_x - title_surf.get_width() // 2, center_y - 50))
    screen.blit(prompt_surf, (center_x - prompt_surf.get_width() // 2, center_y + 20))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return True
