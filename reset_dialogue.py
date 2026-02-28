from game_config import *
import pygame


def save_menu(screen, history, saved_slots):
    """
    Displays a save menu over the current screen.
    Pauses execution until the user presses 1, 2, or ESC.
    """
    # 1. Create a dark, semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180) # 0 is fully transparent, 255 is fully opaque
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # 2. Setup fonts
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 36)

    # 3. Render text surfaces
    title_surf = font.render("Run Ended! Save this sequence?", True, (255, 255, 255))
    slot1_surf = small_font.render("Press '1' to save to Slot 1", True, (200, 255, 200))
    slot2_surf = small_font.render("Press '2' to save to Slot 2", True, (200, 255, 200))
    skip_surf  = small_font.render("Press 'ESC' to discard and restart", True, (255, 150, 150))

    # 4. Blit text to the center of the screen
    center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    screen.blit(title_surf, (center_x - title_surf.get_width() // 2, center_y - 100))
    screen.blit(slot1_surf, (center_x - slot1_surf.get_width() // 2, center_y - 20))
    screen.blit(slot2_surf, (center_x - slot2_surf.get_width() // 2, center_y + 20))
    screen.blit(skip_surf,  (center_x - skip_surf.get_width() // 2,  center_y + 80))

    pygame.display.flip() # Update the screen to show the menu

    # 5. Mini event loop to wait for player input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit() # Immediately close the program
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    saved_slots[0] = history
                    print("Saved to Slot 1!")
                    waiting = False
                elif event.key == pygame.K_2:
                    saved_slots[1] = history
                    print("Saved to Slot 2!")
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    print("Run discarded.")
                    waiting = False
