import os
import pygame


class DummySound:
    def play(self, *args, **kwargs):
        return None

    def set_volume(self, *args, **kwargs):
        return None

    def stop(self, *args, **kwargs):
        return None


class AssetManager:
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.mixer_available = pygame.mixer.get_init() is not None

    def load_image(self, path, size=None, fallback_color=(255, 0, 255), shape="rect"):
        key = (path, size, fallback_color, shape)
        if key in self.images:
            return self.images[key]

        surface = None
        if path and os.path.exists(path):
            try:
                surface = pygame.image.load(path).convert_alpha()
                if size:
                    surface = pygame.transform.smoothscale(surface, size)
            except (pygame.error, FileNotFoundError):
                surface = None

        if surface is None:
            surface = self._generate_placeholder(size or (40, 40), fallback_color, shape)

        self.images[key] = surface
        return surface

    def _generate_placeholder(self, size, color, shape):
        width, height = size
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        outline = (255, 255, 255, 200)

        if shape == "circle":
            radius = min(width, height) // 2
            pygame.draw.circle(surface, color, (width // 2, height // 2), radius)
            pygame.draw.circle(surface, outline, (width // 2, height // 2), radius, 2)
        elif shape == "triangle":
            points = [(width // 2, 0), (width, height), (0, height)]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, outline, points, 2)
        else:
            pygame.draw.rect(surface, color, (0, 0, width, height), border_radius=6)
            pygame.draw.rect(surface, outline, (0, 0, width, height), 2, border_radius=6)

        return surface

    def load_sound(self, path):
        if path in self.sounds:
            return self.sounds[path]

        sound = None
        if self.mixer_available and path and os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
            except (pygame.error, FileNotFoundError):
                sound = None

        if sound is None:
            sound = DummySound()

        self.sounds[path] = sound
        return sound