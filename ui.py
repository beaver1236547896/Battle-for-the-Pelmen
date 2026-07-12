import pygame
from settings import SCREEN_WIDTH, WHITE, DARK_GRAY, DARK_RED


def draw_heart(surface, x, y, size, fill_ratio):
    empty_color = (70, 70, 80)
    fill_color = (225, 45, 65)
    outline_color = (20, 20, 25)

    def draw_shape(target, color, clip_rect=None):
        if clip_rect:
            target.set_clip(clip_rect)
        radius = size // 4
        pygame.draw.circle(target, color, (x + radius, y + radius), radius)
        pygame.draw.circle(target, color, (x + size - radius, y + radius), radius)
        points = [(x, y + size * 0.35), (x + size // 2, y + size), (x + size, y + size * 0.35)]
        pygame.draw.polygon(target, color, points)
        if clip_rect:
            target.set_clip(None)

    draw_shape(surface, empty_color)
    if fill_ratio >= 1.0:
        draw_shape(surface, fill_color)
    elif fill_ratio > 0:
        clip_rect = pygame.Rect(x, y, size // 2, size)
        draw_shape(surface, fill_color, clip_rect)

    radius = size // 4
    pygame.draw.circle(surface, outline_color, (x + radius, y + radius), radius, 2)
    pygame.draw.circle(surface, outline_color, (x + size - radius, y + radius), radius, 2)


class HUD:
    def __init__(self, assets):
        self.assets = assets
        pygame.font.init()
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.title_font = pygame.font.SysFont("arial", 64, bold=True)
        self.sub_font = pygame.font.SysFont("arial", 28)

    def draw(self, surface, player, boss=None):
        panel = pygame.Surface((300, 90), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 140), (0, 0, 300, 90), border_radius=14)
        surface.blit(panel, (16, 16))

        name_text = self.font.render(player.name, True, WHITE)
        surface.blit(name_text, (32, 24))

        total_hearts = int(player.max_health)
        for i in range(total_hearts):
            value = player.health - i
            if value >= 1:
                fill = 1.0
            elif value == 0.5:
                fill = 0.5
            else:
                fill = 0.0
            draw_heart(surface, 32 + i * 40, 52, 32, fill)

        if boss is not None and boss.active and not boss.is_dead:
            self.draw_boss_bar(surface, boss)

    def draw_boss_bar(self, surface, boss):
        bar_width = 500
        bar_height = 26
        x = SCREEN_WIDTH // 2 - bar_width // 2
        y = 24
        pygame.draw.rect(surface, DARK_GRAY, (x - 4, y - 4, bar_width + 8, bar_height + 8), border_radius=8)
        pygame.draw.rect(surface, (30, 30, 30), (x, y, bar_width, bar_height), border_radius=6)
        ratio = max(0, boss.health / boss.max_health)
        pygame.draw.rect(surface, DARK_RED, (x, y, int(bar_width * ratio), bar_height), border_radius=6)
        label = self.font.render(boss.name, True, WHITE)
        surface.blit(label, (x, y - 28))

    def draw_center_text(self, surface, title, subtitle, color=WHITE):
        title_surf = self.title_font.render(title, True, color)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, surface.get_height() // 2 - 40)))
        if subtitle:
            sub_surf = self.sub_font.render(subtitle, True, WHITE)
            surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, surface.get_height() // 2 + 30)))