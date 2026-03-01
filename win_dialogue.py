from game_config import *
import pygame

def win_menu(screen):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    font = pygame.font.SysFont(None, 64)
    small_font = pygame.font.SysFont(None, 32)
    title_surf = font.render("You Win", True, (255, 255, 255))
    prompt_surf = small_font.render("Press any key to continue", True, (220, 220, 220))

    center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    screen.blit(title_surf, (center_x - title_surf.get_width() // 2, center_y - 50))
    screen.blit(prompt_surf, (center_x - prompt_surf.get_width() // 2, center_y + 20))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                return True
