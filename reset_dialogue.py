from game_config import *
import pygame


def replay_reverse(screen, history, all_drawables, camera):
    """
    Fast-forwards the current run's history in reverse.
    Draws only the environment and the current run's path.
    """
    if not history or not history["locations"]:
        return

    # Speed of the rewind (frames skipped per update)
    REPLAY_SPEED = 1
    # Get the frames in descending order for reverse playback
    loc_frames = sorted(history["locations"].keys(), reverse=True)
    
    clock = pygame.time.Clock()

    i = 0
    while i < len(loc_frames):
        if i % 5 == 0:
            REPLAY_SPEED += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return

        # Identify current frame and position
        frame = loc_frames[i]
        pos = history["locations"][frame]
        
        # Update camera to follow the rewind point
        rewind_rect = pygame.Rect(pos[0], pos[1], 40, 40)
        camera.update(type('obj', (object,), {'rect': rewind_rect}))

        screen.fill(BG_COLOR)
        
        # Draw the world state exactly as it ended
        for obj in all_drawables:
            if camera.view_rect.colliderect(obj.rect):
                obj.draw(screen, camera)
        
        # Draw the "Rewind" indicator for the current run
        # Using a bright color to distinguish it from a normal player
        pygame.draw.rect(screen, (0, 255, 255), camera.apply(rewind_rect))

        # Simple HUD overlay
        font = pygame.font.SysFont(None, 36)
        text = font.render("REWINDING CURRENT RUN...", True, (255, 50, 50))
        screen.blit(text, (20, 20))

        pygame.display.flip()
        clock.tick(0.5 * FPS)
        i += REPLAY_SPEED

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
