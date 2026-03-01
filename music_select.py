import pygame


def play_menu_music_once(track_path):
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.play(loops=0)
        return True
    except pygame.error:
        return False
