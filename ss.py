import pygame
from config import *

class Spritesheet:
    def __init__(self, file, image_tilesize):
        self.spritesheet = pygame.image.load(file).convert_alpha()
        self.tilesize = image_tilesize

        width, height = self.spritesheet.get_size()
        self.w = width // self.tilesize
        self.h = height // self.tilesize

    def get_image(self, x, y):
        sprite = pygame.Surface((self.tilesize, self.tilesize), pygame.SRCALPHA, 32).convert_alpha()
        sprite.blit(self.spritesheet, (0, 0), 
                    (x * self.tilesize, y * self.tilesize, self.tilesize, self.tilesize))
        return sprite

    def get_image_idx(self, idx):
        return self.get_image(idx % self.w, idx // self.w)
