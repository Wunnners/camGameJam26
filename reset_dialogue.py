from game_config import *
import pygame


def replay_reverse(screen, history, all_drawables, camera, player, ghosts=None):
    """
    Fast-forwards the current run's history in reverse.
    Draws the environment, the player's animations, and rewinds active ghosts.
    """
    if not history or not history["locations"]:
        return

    REPLAY_SPEED = 1
    loc_frames = sorted(history["locations"].keys(), reverse=True)
    max_frames = len(loc_frames)
    clock = pygame.time.Clock()

    # Create a persistent surface for scanlines to save performance
    scanline_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for y in range(0, SCREEN_HEIGHT, 4):
        pygame.draw.line(scanline_surf, (0, 0, 0, 40), (0, y), (SCREEN_WIDTH, y))

    i = 0
    while i < max_frames:
        if i % 5 == 0:
            REPLAY_SPEED += 1
            
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return

        # Identify current frame and position for the Player
        frame = loc_frames[i]
        pos = history["locations"][frame]
        orit, idle = history["animations"].get(frame, (2, True)) 
        
        rewind_rect = pygame.Rect(pos[0], pos[1], 40, 40)
        camera.update(type('obj', (object,), {'rect': rewind_rect}))

        screen.fill(BG_COLOR)
        
        # Draw the world state
        for obj in all_drawables:
            if camera.view_rect.colliderect(obj.rect):
                obj.draw(screen, camera)
        
        # --- DRAW REWINDING PLAYER ---
        # 1. Select the correct animation set based on orientation
        if orit == 0: bb = player.up
        elif orit == 2: bb = player.down
        else: bb = player.right
        
        # 2. Get the image and flip if facing left
        img = bb[idle].get_image()
        if orit == 1:
            img = pygame.transform.flip(img, True, False)
            
        # 3. Blit the player image using your offset logic
        drawn_rect = camera.apply(rewind_rect)
        img_size = img.get_size()
        screen.blit(img, (drawn_rect.x - img_size[0] / 4, drawn_rect.y - img_size[1] / 2))

        # --- DRAW REWINDING GHOSTS ---
        if ghosts:
            for ghost in ghosts:
                # Force the ghost's position and animation state to match the rewound frame
                if ghost.sequence["locations"] and frame in ghost.sequence["locations"]:
                    ghost.rect.topleft = ghost.sequence["locations"][frame]
                if ghost.sequence["animations"] and frame in ghost.sequence["animations"]:
                    ghost.orit, ghost.idle = ghost.sequence["animations"][frame]
                
                # Draw the ghost (this will use the tinting logic we added earlier)
                ghost.draw(screen, camera)

        # --- REPLAY OVERLAY LAYER ---
        
        # 2. Draw Scanlines (VHS Effect)
        screen.blit(scanline_surf, (0, 0))

        # 3. Tint the screen slightly red/blue
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 20)) # Very faint red tint
        screen.blit(overlay, (0, 0))

        # 4. HUD Text & Rewind Icon
        font = pygame.font.SysFont("Courier", 40, bold=True)
        # Flickering effect using frame count
        if (i // 2) % 2 == 0:
            text = font.render("<< REWIND", True, (255, 255, 255))
            screen.blit(text, (30, 30))
        
        # 5. Progress Bar at the bottom
        bar_width = SCREEN_WIDTH - 100
        progress = (i / max_frames)
        fill_width = int(bar_width * (1 - progress)) # Decreases as we go back
        
        pygame.draw.rect(screen, (50, 50, 50), (50, SCREEN_HEIGHT - 50, bar_width, 10))
        pygame.draw.rect(screen, (255, 255, 255), (50, SCREEN_HEIGHT - 50, fill_width, 10))

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
