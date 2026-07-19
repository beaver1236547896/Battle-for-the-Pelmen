import sys
import math
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    STATE_CHARACTER_SELECT, STATE_PLAYING, STATE_GAME_OVER, STATE_VICTORY,
    CHARACTER_PELMEN, CHARACTER_GRIMLOCK,
    WHITE, BLACK, SKY_BLUE, BROWN, DARK_GREEN, ORANGE, GRAY, DARK_GRAY, RED, YELLOW, CREAM,
    TILE_SIZE, GROUND_HEIGHT, GROUND_Y, LEVEL_WIDTH,
    PLAYER_HEIGHT, ENEMY_CONTACT_DAMAGE, BOSS_CONTACT_DAMAGE, BOSS_HEIGHT
)
from assets import AssetManager
from player import Pelmen, Grimlock
from enemies import WalkingEnemy, FlyingEnemy, Boss
from ui import HUD


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.assets = AssetManager()
        self.hud = HUD(self.assets)

        self.state = STATE_CHARACTER_SELECT
        self.player = None
        self.platforms = []
        self.floating_platforms = []
        self.walking_enemies = []
        self.flying_enemies = []
        self.boss = None
        self.camera_x = 0
        self.running = True

        self.background_image = self.assets.load_image(None, (SCREEN_WIDTH, SCREEN_HEIGHT), SKY_BLUE)
        self.ground_image = self.assets.load_image(None, (TILE_SIZE, GROUND_HEIGHT), BROWN)
        self.platform_image = self.assets.load_image(None, (TILE_SIZE, 24), DARK_GREEN)

        self.pelmen_button = pygame.Rect(SCREEN_WIDTH // 2 - 320, 260, 260, 320)
        self.grimlock_button = pygame.Rect(SCREEN_WIDTH // 2 + 60, 260, 260, 320)

    def build_level(self):
        self.platforms = []
        ground = pygame.Rect(0, GROUND_Y, LEVEL_WIDTH, GROUND_HEIGHT)
        self.platforms.append(ground)

        floating_specs = [
            (350, GROUND_Y - 140, 160), (650, GROUND_Y - 220, 160),
            (1100, GROUND_Y - 160, 200), (1500, GROUND_Y - 240, 160),
            (1900, GROUND_Y - 160, 220), (2300, GROUND_Y - 200, 160),
            (2700, GROUND_Y - 140, 200), (3100, GROUND_Y - 220, 160),
            (3500, GROUND_Y - 160, 220), (3900, GROUND_Y - 200, 160),
            (4300, GROUND_Y - 160, 200),
        ]
        self.floating_platforms = []
        for x, y, w in floating_specs:
            rect = pygame.Rect(x, y, w, 26)
            self.platforms.append(rect)
            self.floating_platforms.append(rect)

        self.walking_enemies = []
        walker_positions = [500, 1100, 1750, 2450, 3150, 3850]
        for x in walker_positions:
            enemy = WalkingEnemy(x, GROUND_Y - 48, self.assets, x - 150, x + 150)
            self.walking_enemies.append(enemy)

        self.flying_enemies = []
        flyer_positions = [2100, 2800, 3500]
        for x in flyer_positions:
            enemy = FlyingEnemy(x, GROUND_Y - 260, self.assets, x - 200, x + 200)
            self.flying_enemies.append(enemy)

        self.boss = Boss(LEVEL_WIDTH - 500, GROUND_Y - BOSS_HEIGHT, self.assets)

    def start_game(self, character):
        self.build_level()
        spawn_x, spawn_y = 100, GROUND_Y - PLAYER_HEIGHT
        if character == CHARACTER_PELMEN:
            self.player = Pelmen(spawn_x, spawn_y, self.assets)
        else:
            self.player = Grimlock(spawn_x, spawn_y, self.assets)
        self.state = STATE_PLAYING
        self.camera_x = 0

    def get_all_enemies(self):
        enemies = list(self.walking_enemies) + list(self.flying_enemies)
        if self.boss and not self.boss.is_dead:
            enemies.append(self.boss)
        return enemies

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.state == STATE_CHARACTER_SELECT:
                    if event.key == pygame.K_1:
                        self.start_game(CHARACTER_PELMEN)
                    elif event.key == pygame.K_2:
                        self.start_game(CHARACTER_GRIMLOCK)
                elif self.state == STATE_PLAYING:
                    if event.key == pygame.K_j:
                        self.player.shoot(self.get_all_enemies())
                    if event.key == pygame.K_k:
                        self.player.special_attack(self.get_all_enemies())
                elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
                    if event.key == pygame.K_r:
                        self.state = STATE_CHARACTER_SELECT

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == STATE_CHARACTER_SELECT:
                    mx, my = event.pos
                    if self.pelmen_button.collidepoint(mx, my):
                        self.start_game(CHARACTER_PELMEN)
                    elif self.grimlock_button.collidepoint(mx, my):
                        self.start_game(CHARACTER_GRIMLOCK)
                elif self.state == STATE_PLAYING:
                    if event.button == 1:
                        self.player.shoot(self.get_all_enemies())
                    elif event.button == 3:
                        self.player.special_attack(self.get_all_enemies())

    def update(self):
        if self.state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()
        self.player.update(keys, self.platforms)

        for enemy in self.walking_enemies:
            enemy.update(self.platforms)
        for enemy in self.flying_enemies:
            enemy.update(self.platforms, self.player.rect)
        if self.boss:
            self.boss.update(self.player.rect, self.platforms)

        for proj in list(self.player.projectiles):
            hit = False
            for enemy in self.walking_enemies + self.flying_enemies:
                if proj.rect.colliderect(enemy.rect):
                    enemy.take_damage(proj.damage)
                    hit = True
                    break
            if not hit and self.boss and not self.boss.is_dead and proj.rect.colliderect(self.boss.rect):
                self.boss.take_damage(proj.damage)
                hit = True
            if hit:
                proj.kill()

        self.walking_enemies = [e for e in self.walking_enemies if not e.is_dead]
        self.flying_enemies = [e for e in self.flying_enemies if not e.is_dead]

        for enemy in self.walking_enemies + self.flying_enemies:
            if self.player.rect.colliderect(enemy.rect):
                self.player.take_damage(ENEMY_CONTACT_DAMAGE)

        if self.boss and not self.boss.is_dead:
            if self.player.rect.colliderect(self.boss.rect):
                self.player.take_damage(BOSS_CONTACT_DAMAGE)
            for proj in list(self.boss.projectiles):
                if proj.rect.colliderect(self.player.rect):
                    self.player.take_damage(proj.damage)
                    proj.kill()

        if self.player.rect.top > SCREEN_HEIGHT + 300:
            self.player.take_damage(self.player.max_health)

        if self.player.is_dead:
            self.state = STATE_GAME_OVER

        if self.boss and self.boss.is_dead:
            self.state = STATE_VICTORY

        target_camera = self.player.rect.centerx - SCREEN_WIDTH // 2
        self.camera_x = max(0, min(target_camera, LEVEL_WIDTH - SCREEN_WIDTH))

    def draw_character_select(self):
        self.screen.blit(self.background_image, (0, 0))
        title = self.hud.title_font.render("Choose Your Hero", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 120)))

        pygame.draw.rect(self.screen, ORANGE, self.pelmen_button, border_radius=16)
        pygame.draw.rect(self.screen, GRAY, self.grimlock_button, border_radius=16)
        pygame.draw.rect(self.screen, WHITE, self.pelmen_button, 4, border_radius=16)
        pygame.draw.rect(self.screen, WHITE, self.grimlock_button, 4, border_radius=16)

        pelmen_portrait_rect = pygame.Rect(0, 0, self.pelmen_button.width - 40, 170)
        pelmen_portrait_rect.midtop = (self.pelmen_button.centerx, self.pelmen_button.y + 16)
        grimlock_portrait_rect = pygame.Rect(0, 0, self.grimlock_button.width - 40, 170)
        grimlock_portrait_rect.midtop = (self.grimlock_button.centerx, self.grimlock_button.y + 16)

        self.draw_pelmen_portrait(pelmen_portrait_rect)
        self.draw_grimlock_portrait(grimlock_portrait_rect)

        pelmen_label = self.hud.sub_font.render("Pelmen (1)", True, WHITE)
        grimlock_label = self.hud.sub_font.render("Grimlock (2)", True, WHITE)
        self.screen.blit(pelmen_label, pelmen_label.get_rect(center=(self.pelmen_button.centerx, self.pelmen_button.bottom + 30)))
        self.screen.blit(grimlock_label, grimlock_label.get_rect(center=(self.grimlock_button.centerx, self.grimlock_button.bottom + 30)))

        pelmen_desc = ["Стріляє фаршем", "", "вібух аромата"]
        grimlock_desc = ["гупає ногою по земілі", "", "трансформується і", "відригає вогнем"]
        desc_y = pelmen_portrait_rect.bottom + 12
        for i, line in enumerate(pelmen_desc):
            text = self.hud.font.render(line, True, BLACK)
            self.screen.blit(text, text.get_rect(center=(self.pelmen_button.centerx, desc_y + i * 28)))
        for i, line in enumerate(grimlock_desc):
            text = self.hud.font.render(line, True, BLACK)
            self.screen.blit(text, text.get_rect(center=(self.grimlock_button.centerx, desc_y + i * 28)))

        hint = self.hud.font.render("Click a hero or press 1 / 2", True, WHITE)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 650)))

        controls = self.hud.font.render("Move: A/D  Jump: SPACE  Attack: J / LMB  Special: K / RMB", True, WHITE)
        self.screen.blit(controls, controls.get_rect(center=(SCREEN_WIDTH // 2, 680)))

    def draw_pelmen_portrait(self, rect):
        cx = rect.centerx
        cy = rect.centery + 14
        body_rect = pygame.Rect(0, 0, int(rect.width * 0.72), int(rect.height * 0.62))
        body_rect.center = (cx, cy)
        pygame.draw.ellipse(self.screen, CREAM, body_rect)
        pygame.draw.ellipse(self.screen, (190, 140, 80), body_rect, 3)

        seam_rect = pygame.Rect(body_rect.x - 6, body_rect.y - 22, body_rect.width + 12, 46)
        pygame.draw.arc(self.screen, (190, 140, 80), seam_rect, math.radians(20), math.radians(160), 5)

        eye_y = cy - 8
        pygame.draw.circle(self.screen, BLACK, (cx - 20, eye_y), 7)
        pygame.draw.circle(self.screen, BLACK, (cx + 20, eye_y), 7)
        pygame.draw.circle(self.screen, WHITE, (cx - 22, eye_y - 2), 2)
        pygame.draw.circle(self.screen, WHITE, (cx + 18, eye_y - 2), 2)

        pygame.draw.circle(self.screen, (235, 150, 150), (cx - 34, cy + 14), 8)
        pygame.draw.circle(self.screen, (235, 150, 150), (cx + 34, cy + 14), 8)

        mouth_rect = pygame.Rect(cx - 18, cy + 4, 36, 22)
        pygame.draw.arc(self.screen, BLACK, mouth_rect, math.radians(200), math.radians(340), 3)

        leg_y = body_rect.bottom - 6
        pygame.draw.circle(self.screen, CREAM, (cx - 26, leg_y), 12)
        pygame.draw.circle(self.screen, CREAM, (cx + 26, leg_y), 12)
        pygame.draw.circle(self.screen, (190, 140, 80), (cx - 26, leg_y), 12, 2)
        pygame.draw.circle(self.screen, (190, 140, 80), (cx + 26, leg_y), 12, 2)

    def draw_grimlock_portrait(self, rect):
        cx = rect.centerx
        cy = rect.centery + 20

        body_rect = pygame.Rect(0, 0, int(rect.width * 0.5), int(rect.height * 0.42))
        body_rect.center = (cx, cy + 24)
        pygame.draw.rect(self.screen, GRAY, body_rect, border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY, body_rect, 3, border_radius=10)

        tail_points = [
            (body_rect.left + 6, body_rect.bottom - 10),
            (body_rect.left - 34, body_rect.bottom + 16),
            (body_rect.left + 10, body_rect.bottom - 22),
        ]
        pygame.draw.polygon(self.screen, GRAY, tail_points)
        pygame.draw.polygon(self.screen, DARK_GRAY, tail_points, 2)

        head_rect = pygame.Rect(0, 0, int(rect.width * 0.4), int(rect.height * 0.34))
        head_rect.midbottom = (cx + 10, body_rect.top + 14)
        pygame.draw.rect(self.screen, GRAY, head_rect, border_radius=8)
        pygame.draw.rect(self.screen, DARK_GRAY, head_rect, 3, border_radius=8)

        snout_rect = pygame.Rect(0, 0, int(head_rect.width * 0.5), int(head_rect.height * 0.5))
        snout_rect.midleft = (head_rect.right - 6, head_rect.centery + 6)
        pygame.draw.rect(self.screen, GRAY, snout_rect, border_radius=6)
        pygame.draw.rect(self.screen, DARK_GRAY, snout_rect, 2, border_radius=6)

        eye_pos = (head_rect.centerx - 2, head_rect.centery - 6)
        pygame.draw.circle(self.screen, RED, eye_pos, 6)
        pygame.draw.circle(self.screen, YELLOW, eye_pos, 6, 2)

        for i in range(3):
            tooth_x = snout_rect.right - 6 - i * 5
            pygame.draw.polygon(self.screen, WHITE, [
                (tooth_x, snout_rect.bottom - 2),
                (tooth_x - 3, snout_rect.bottom + 8),
                (tooth_x + 3, snout_rect.bottom + 8),
            ])

        arm_rect_left = pygame.Rect(0, 0, 14, 34)
        arm_rect_left.midtop = (body_rect.left + 6, body_rect.centery)
        arm_rect_right = pygame.Rect(0, 0, 14, 34)
        arm_rect_right.midtop = (body_rect.right - 6, body_rect.centery)
        pygame.draw.rect(self.screen, DARK_GRAY, arm_rect_left, border_radius=4)
        pygame.draw.rect(self.screen, DARK_GRAY, arm_rect_right, border_radius=4)

        leg_rect_left = pygame.Rect(0, 0, 18, 22)
        leg_rect_left.midtop = (body_rect.centerx - 20, body_rect.bottom - 4)
        leg_rect_right = pygame.Rect(0, 0, 18, 22)
        leg_rect_right.midtop = (body_rect.centerx + 20, body_rect.bottom - 4)
        pygame.draw.rect(self.screen, DARK_GRAY, leg_rect_left, border_radius=5)
        pygame.draw.rect(self.screen, DARK_GRAY, leg_rect_right, border_radius=5)

    def draw_world(self):
        self.screen.blit(self.background_image, (0, 0))

        start_tile = self.camera_x // TILE_SIZE
        tiles_needed = SCREEN_WIDTH // TILE_SIZE + 2
        for i in range(start_tile, start_tile + tiles_needed):
            x = i * TILE_SIZE - self.camera_x
            self.screen.blit(self.ground_image, (x, GROUND_Y))

        for plat in self.floating_platforms:
            draw_rect = plat.move(-self.camera_x, 0)
            if draw_rect.right > 0 and draw_rect.left < SCREEN_WIDTH:
                scaled = pygame.transform.scale(self.platform_image, (plat.width, plat.height))
                self.screen.blit(scaled, draw_rect)

        for enemy in self.walking_enemies:
            enemy.draw(self.screen, self.camera_x)
        for enemy in self.flying_enemies:
            enemy.draw(self.screen, self.camera_x)
        if self.boss:
            self.boss.draw(self.screen, self.camera_x)

        self.player.draw(self.screen, self.camera_x)
        self.hud.draw(self.screen, self.player, self.boss)

    def draw(self):
        if self.state == STATE_CHARACTER_SELECT:
            self.draw_character_select()
        elif self.state == STATE_PLAYING:
            self.draw_world()
        elif self.state == STATE_GAME_OVER:
            self.draw_world()
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            self.hud.draw_center_text(self.screen, "GAME OVER", "Press R to try again", RED)
        elif self.state == STATE_VICTORY:
            self.draw_world()
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (0, 0))
            self.hud.draw_center_text(self.screen, "VICTORY!", "Press R to play again", YELLOW)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()