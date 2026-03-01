import pygame


def _ensure_mixer():
    if not pygame.mixer.get_init():
        pygame.mixer.init()


def play_music(track_path):
    try:
        _ensure_mixer()
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.play(loops=0)
        return True
    except pygame.error:
        return False


def loop_music(track_path):
    try:
        _ensure_mixer()
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.play(loops=-1)
        return True
    except pygame.error:
        return False
