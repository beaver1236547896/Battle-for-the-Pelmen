import math
import pygame
from settings import (
    GRAVITY, MAX_FALL_SPEED, WALKING_ENEMY_SPEED, WALKING_ENEMY_HEALTH,
    FLYING_ENEMY_SPEED, FLYING_ENEMY_HEALTH, ENEMY_INVULN_TIME,
    BOSS_WIDTH, BOSS_HEIGHT, BOSS_MAX_HEALTH, BOSS_SPEED, BOSS_ACTIVATION_RANGE,
    BOSS_ATTACK_COOLDOWN, BOSS_PROJECTILE_DAMAGE, PROJECTILE_SPEED,
    PURPLE, PINK, DARK_RED, YELLOW
)
from player import Projectile

FLYING_DETECTION_RANGE = 180


class WalkingEnemy(pygame.sprite.Sprite):
    is_flying = False

    def __init__(self, x, y, assets, patrol_start, patrol_end):
        super().__init__()
        self.rect = pygame.Rect(x, y, 40, 48)
        self.vel_y = 0
        self.speed = WALKING_ENEMY_SPEED
        self.direction = -1
        self.health = WALKING_ENEMY_HEALTH
        self.patrol_start = patrol_start
        self.patrol_end = patrol_end
        self.image = assets.load_image("grim.png", (40, 48), PURPLE)
        self.invuln_timer = 0
        self.on_ground = True
        self.is_dead = False

    def update(self, platforms):
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat) and self.vel_y >= 0:
                self.rect.bottom = plat.top
                self.vel_y = 0
                self.on_ground = True

        self.rect.x += int(self.speed * self.direction)
        if self.rect.left <= self.patrol_start:
            self.rect.left = self.patrol_start
            self.direction = 1
        elif self.rect.right >= self.patrol_end:
            self.rect.right = self.patrol_end
            self.direction = -1

        if self.invuln_timer > 0:
            self.invuln_timer -= 1

    def take_damage(self, amount):
        if self.invuln_timer <= 0:
            self.health -= amount
            self.invuln_timer = ENEMY_INVULN_TIME
            if self.health <= 0:
                self.is_dead = True
                self.kill()

    def draw(self, surface, offset_x):
        surface.blit(self.image, self.rect.move(-offset_x, 0))


class FlyingEnemy(pygame.sprite.Sprite):
    is_flying = True

    def __init__(self, x, y, assets, patrol_start, patrol_end):
        super().__init__()
        self.rect = pygame.Rect(x, y, 42, 34)
        self.base_y = y
        self.timer = 0
        self.speed = FLYING_ENEMY_SPEED
        self.direction = -1
        self.health = FLYING_ENEMY_HEALTH
        self.patrol_start = patrol_start
        self.patrol_end = patrol_end
        self.image = assets.load_image(None, (42, 34), PINK)
        self.invuln_timer = 0
        self.on_ground = False
        self.is_dead = False

    def update(self, platforms, player_rect=None):
        self.timer += 1
        if player_rect is not None and abs(player_rect.centerx - self.rect.centerx) <= FLYING_DETECTION_RANGE:
            if self.rect.centerx < player_rect.centerx:
                self.rect.x += self.speed
            elif self.rect.centerx > player_rect.centerx:
                self.rect.x -= self.speed
            if self.rect.centery < player_rect.centery:
                self.rect.y += self.speed
            elif self.rect.centery > player_rect.centery:
                self.rect.y -= self.speed
        else:
            self.rect.y = self.base_y + int(math.sin(self.timer * 0.05) * 24)
            self.rect.x += int(self.speed * self.direction)
            if self.rect.left <= self.patrol_start:
                self.direction = 1
            elif self.rect.right >= self.patrol_end:
                self.direction = -1

        if self.invuln_timer > 0:
            self.invuln_timer -= 1

    def take_damage(self, amount):
        if self.invuln_timer <= 0:
            self.health -= amount
            self.invuln_timer = ENEMY_INVULN_TIME
            if self.health <= 0:
                self.is_dead = True
                self.kill()

    def draw(self, surface, offset_x):
        surface.blit(self.image, self.rect.move(-offset_x, 0))


class Boss(pygame.sprite.Sprite):
    is_flying = False

    def __init__(self, x, y, assets):
        super().__init__()
        self.rect = pygame.Rect(x, y, BOSS_WIDTH, BOSS_HEIGHT)
        self.vel_y = 0
        self.max_health = BOSS_MAX_HEALTH
        self.health = BOSS_MAX_HEALTH
        self.direction = -1
        self.speed = BOSS_SPEED
        self.attack_timer = 0
        self.active = False
        self.is_dead = False
        self.on_ground = True
        self.name = "BOSS"
        self.projectiles = pygame.sprite.Group()
        self.image = assets.load_image(None, (BOSS_WIDTH, BOSS_HEIGHT), DARK_RED)
        self.projectile_image = assets.load_image(None, (20, 20), YELLOW, shape="circle")
        self.invuln_timer = 0

    def activate_if_near(self, player_rect):
        if not self.active:
            distance = abs(player_rect.centerx - self.rect.centerx)
            if distance <= BOSS_ACTIVATION_RANGE:
                self.active = True

    def update(self, player_rect, platforms):
        if self.is_dead:
            self.projectiles.update()
            return

        self.activate_if_near(player_rect)

        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED
        self.rect.y += int(self.vel_y)
        for plat in platforms:
            if self.rect.colliderect(plat) and self.vel_y >= 0:
                self.rect.bottom = plat.top
                self.vel_y = 0

        if self.active:
            if player_rect.centerx > self.rect.centerx + 30:
                self.direction = 1
            elif player_rect.centerx < self.rect.centerx - 30:
                self.direction = -1
            else:
                self.direction = 0
            self.rect.x += int(self.speed * self.direction)

            self.attack_timer += 1
            if self.attack_timer >= BOSS_ATTACK_COOLDOWN:
                self.attack_timer = 0
                self.shoot(player_rect)

        self.projectiles.update()
        if self.invuln_timer > 0:
            self.invuln_timer -= 1

    def shoot(self, player_rect):
        direction = 1 if player_rect.centerx > self.rect.centerx else -1
        projectile = Projectile(
            self.rect.centerx, self.rect.centery, direction,
            self.projectile_image, damage=BOSS_PROJECTILE_DAMAGE, owner="boss"
        )
        projectile.speed = PROJECTILE_SPEED - 3
        self.projectiles.add(projectile)

    def take_damage(self, amount):
        if self.invuln_timer <= 0 and not self.is_dead:
            self.health -= amount
            self.invuln_timer = 12
            if self.health <= 0:
                self.health = 0
                self.is_dead = True

    def draw(self, surface, offset_x):
        surface.blit(self.image, self.rect.move(-offset_x, 0))
        for proj in self.projectiles:
            surface.blit(proj.image, proj.rect.move(-offset_x, 0))