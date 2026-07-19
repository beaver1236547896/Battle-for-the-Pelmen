import pygame
from settings import (
    GRAVITY, MAX_FALL_SPEED, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPEED,
    PLAYER_JUMP_STRENGTH, PLAYER_INVULN_TIME, PROJECTILE_SPEED, PROJECTILE_LIFETIME,
    WHITE, RED, ORANGE, CREAM, GRAY, DARK_GREEN, YELLOW
)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, image, damage, owner="player"):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed = PROJECTILE_SPEED
        self.damage = damage
        self.owner = owner
        self.lifetime = PROJECTILE_LIFETIME

    def update(self):
        self.rect.x += int(self.speed * self.direction)
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


class AoEEffect:
    def __init__(self, x, y, max_radius, color, lifetime=20):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.color = color
        self.lifetime = lifetime
        self.timer = 0

    def update(self):
        self.timer += 1
        return self.timer < self.lifetime

    def draw(self, surface, offset_x):
        progress = self.timer / self.lifetime
        radius = max(1, int(self.max_radius * progress))
        alpha = max(0, 255 - int(255 * progress))
        layer = pygame.Surface((self.max_radius * 2, self.max_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(layer, (*self.color, alpha), (self.max_radius, self.max_radius), radius, width=6)
        surface.blit(layer, (self.x - offset_x - self.max_radius, self.y - self.max_radius))


class FireBreathEffect:
    def __init__(self, origin_x, origin_y, length, height, direction, lifetime=22):
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.length = length
        self.height = height
        self.direction = direction
        self.lifetime = lifetime
        self.timer = 0

    def update(self):
        self.timer += 1
        return self.timer < self.lifetime

    def draw(self, surface, offset_x):
        progress = self.timer / self.lifetime
        reach = int(self.length * min(1.0, progress * 2.2))
        alpha = max(0, 255 - int(255 * (progress ** 1.5)))
        layer = pygame.Surface((self.length, self.height), pygame.SRCALPHA)
        segments = 5
        for i in range(segments):
            seg_w = max(2, int(reach * (segments - i) / segments))
            seg_h = max(4, self.height - i * (self.height // segments))
            seg_x = 0 if self.direction == 1 else self.length - seg_w
            seg_y = (self.height - seg_h) // 2
            seg_color = (255, 90 + i * 25, 10, max(0, alpha - i * 30))
            pygame.draw.rect(layer, seg_color, (seg_x, seg_y, seg_w, seg_h), border_radius=8)
        draw_x = self.origin_x if self.direction == 1 else self.origin_x - self.length
        surface.blit(layer, (draw_x - offset_x, self.origin_y - self.height // 2))


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, assets):
        super().__init__()
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing = 1
        self.max_health = 3.0
        self.health = 3.0
        self.invuln_timer = 0
        self.attack_cooldown = 18
        self.attack_cooldown_timer = 0
        self.special_cooldown = 150
        self.special_cooldown_timer = 0
        self.projectiles = pygame.sprite.Group()
        self.effects = []
        self.name = "Player"
        self.assets = assets
        self.image = assets.load_image(None, (PLAYER_WIDTH, PLAYER_HEIGHT), WHITE)
        self.is_dead = False

    def handle_input(self, keys):
        self.vel_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED
            self.facing = 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = PLAYER_JUMP_STRENGTH
            self.on_ground = False

    def apply_physics(self, platforms):
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        self.rect.x += int(self.vel_x)
        self._resolve_collisions(platforms, axis="x")

        self.rect.y += int(self.vel_y)
        self.on_ground = False
        self._resolve_collisions(platforms, axis="y")

    def _resolve_collisions(self, platforms, axis):
        for plat in platforms:
            if self.rect.colliderect(plat):
                if axis == "x":
                    if self.vel_x > 0:
                        self.rect.right = plat.left
                    elif self.vel_x < 0:
                        self.rect.left = plat.right
                else:
                    if self.vel_y > 0:
                        self.rect.bottom = plat.top
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0:
                        self.rect.top = plat.bottom
                        self.vel_y = 0

    def update(self, keys, platforms):
        if self.is_dead:
            return
        self.handle_input(keys)
        self.apply_physics(platforms)
        if self.invuln_timer > 0:
            self.invuln_timer -= 1
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1
        if self.special_cooldown_timer > 0:
            self.special_cooldown_timer -= 1
        self.projectiles.update()
        self.effects = [effect for effect in self.effects if effect.update()]

    def take_damage(self, amount):
        if self.invuln_timer <= 0 and not self.is_dead:
            self.health -= amount
            self.invuln_timer = PLAYER_INVULN_TIME
            if self.health <= 0:
                self.health = 0
                self.is_dead = True

    def shoot(self, enemies):
        pass

    def special_attack(self, enemies):
        pass

    def draw(self, surface, offset_x):
        blink_visible = self.invuln_timer == 0 or (self.invuln_timer // 4) % 2 == 0
        if blink_visible:
            surface.blit(self.image, self.rect.move(-offset_x, 0))
        for proj in self.projectiles:
            surface.blit(proj.image, proj.rect.move(-offset_x, 0))
        for effect in self.effects:
            effect.draw(surface, offset_x)


class Pelmen(Player):
    def __init__(self, x, y, assets):
        super().__init__(x, y, assets)
        self.name = "Pelmen"
        self.attack_cooldown = 16
        self.special_cooldown = 180
        self.image = assets.load_image("котпуль.png", (PLAYER_WIDTH, PLAYER_HEIGHT), ORANGE)
        self.projectile_image = assets.load_image(None, (16, 16), CREAM, shape="circle")

    def shoot(self, enemies):
        if self.attack_cooldown_timer <= 0:
            self.attack_cooldown_timer = self.attack_cooldown
            spawn_x = self.rect.right if self.facing == 1 else self.rect.left
            projectile = Projectile(spawn_x, self.rect.centery, self.facing, self.projectile_image, damage=1, owner="player")
            self.projectiles.add(projectile)

    def special_attack(self, enemies):
        if self.special_cooldown_timer <= 0:
            self.special_cooldown_timer = self.special_cooldown
            radius = 160
            for enemy in enemies:
                dx = enemy.rect.centerx - self.rect.centerx
                dy = enemy.rect.centery - self.rect.centery
                distance = (dx * dx + dy * dy) ** 0.5
                if distance <= radius:
                    enemy.take_damage(2)
            self.effects.append(AoEEffect(self.rect.centerx, self.rect.centery, radius, ORANGE))


class Grimlock(Player):
    def __init__(self, x, y, assets):
        super().__init__(x, y, assets)
        self.name = "Grimlock"
        self.attack_cooldown = 40
        self.special_cooldown = 260
        self.image = assets.load_image('grim.png', (PLAYER_WIDTH, PLAYER_HEIGHT), GRAY)
        self.trex_image = assets.load_image(
            "grim-din.png", (int(PLAYER_WIDTH * 1.7), int(PLAYER_HEIGHT * 1.35)), DARK_GREEN
        )
        self.transform_timer = 0
        self.transform_duration = 45

    def shoot(self, enemies):
        if self.attack_cooldown_timer <= 0 and self.on_ground:
            self.attack_cooldown_timer = self.attack_cooldown
            radius = 120
            for enemy in enemies:
                if not getattr(enemy, "is_flying", False):
                    dx = enemy.rect.centerx - self.rect.centerx
                    if abs(dx) <= radius and abs(enemy.rect.bottom - self.rect.bottom) <= 60:
                        enemy.take_damage(1)
            self.effects.append(AoEEffect(self.rect.centerx, self.rect.bottom, radius, GRAY, lifetime=16))

    def special_attack(self, enemies):
        if self.special_cooldown_timer <= 0 and self.on_ground:
            self.special_cooldown_timer = self.special_cooldown
            self.transform_timer = self.transform_duration

            breath_length = 360
            breath_height = 80
            origin_x = self.rect.right if self.facing == 1 else self.rect.left
            origin_y = self.rect.centery

            if self.facing == 1:
                breath_rect = pygame.Rect(origin_x, origin_y - breath_height // 2, breath_length, breath_height)
            else:
                breath_rect = pygame.Rect(origin_x - breath_length, origin_y - breath_height // 2, breath_length, breath_height)

            targets_in_line = [
                enemy for enemy in enemies
                if breath_rect.colliderect(enemy.rect)
            ]
            targets_in_line.sort(key=lambda enemy: abs(enemy.rect.centerx - self.rect.centerx))

            for enemy in targets_in_line[:3]:
                enemy.take_damage(4)

            self.effects.append(
                FireBreathEffect(origin_x, origin_y, breath_length, breath_height, self.facing)
            )

    def update(self, keys, platforms):
        super().update(keys, platforms)
        if self.transform_timer > 0:
            self.transform_timer -= 1

    def draw(self, surface, offset_x):
        blink_visible = self.invuln_timer == 0 or (self.invuln_timer // 4) % 2 == 0
        if blink_visible:
            if self.transform_timer > 0:
                trex_rect = self.trex_image.get_rect(midbottom=self.rect.move(-offset_x, 0).midbottom)
                surface.blit(self.trex_image, trex_rect)
            else:
                surface.blit(self.image, self.rect.move(-offset_x, 0))
        for proj in self.projectiles:
            surface.blit(proj.image, proj.rect.move(-offset_x, 0))
        for effect in self.effects:
            effect.draw(surface, offset_x)