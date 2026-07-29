from __future__ import annotations

import math

import pygame

from game.config import GAME_CONFIG
from game.resources import images
from game import settings
from game.entities.enemy_projectile import EnemyProjectile


class Boss:
    def __init__(self, position: pygame.Vector2) -> None:
        params = GAME_CONFIG["enemies"]["boss"]
        projectile_params = GAME_CONFIG["projectiles"]["boss"]
        self.position = position
        self.radius = params["radius"]
        self.max_hp = params["max_hp"]
        self.hp = self.max_hp
        self.contact_damage = params["contact_damage"]
        self.shoot_interval = params["shoot_interval"]
        self.hit_flash_time = params["hit_flash_time"]
        self.projectile_radius = projectile_params["radius"]
        self.projectile_speed = projectile_params["speed"]
        self.projectile_damage = projectile_params["damage"]
        self.hit_flash_timer = 0.0
        self.shoot_timer = self.shoot_interval * 0.5
        self.pulse_timer = 0.0

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0

    def update(
        self, dt: float, player_position: pygame.Vector2
    ) -> EnemyProjectile | None:
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        self.shoot_timer = max(0.0, self.shoot_timer - dt)
        self.pulse_timer += dt
        to_player = player_position - self.position

        if to_player.length_squared() <= 0:
            return None

        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_interval
            direction = to_player.normalize()
            spawn_position = self.position + direction * (self.radius + 14)
            return EnemyProjectile(
                spawn_position.copy(),
                direction,
                self.projectile_radius,
                self.projectile_speed,
                self.projectile_damage,
                "images/projectiles/projectile_boss.png",
            )

        return None

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)
        self.hit_flash_timer = self.hit_flash_time

    def collides_with_circle(self, position: pygame.Vector2, radius: float) -> bool:
        distance_squared = self.position.distance_squared_to(position)
        combined_radius = self.radius + radius
        return distance_squared <= combined_radius * combined_radius

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        color = (
            settings.BOSS_HIT_COLOR
            if self.hit_flash_timer > 0
            else settings.BOSS_COLOR
        )
        pulse = math.sin(self.pulse_timer * 5.0) * 4
        radius = self.radius + pulse
        center = (round(self.position.x), round(self.position.y))
        points = [
            (round(self.position.x), round(self.position.y - radius)),
            (round(self.position.x + radius), round(self.position.y)),
            (round(self.position.x), round(self.position.y + radius)),
            (round(self.position.x - radius), round(self.position.y)),
        ]

        drew_sprite = images.draw_centered(
            surface,
            "images/enemies/boss_idle.png",
            center,
            (self.radius * 2 + 36, self.radius * 2 + 36),
        )
        if drew_sprite:
            if self.hit_flash_timer > 0:
                pygame.draw.circle(surface, settings.BOSS_HIT_COLOR, center, self.radius, 4)
        else:
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, settings.BOSS_OUTLINE_COLOR, points, 3)
            pygame.draw.circle(surface, settings.BOSS_OUTLINE_COLOR, center, 9, 2)
        self._draw_health_bar(surface)
        self._draw_health_text(surface, font)

    def _draw_health_bar(self, surface: pygame.Surface) -> None:
        width = self.radius * 3
        height = 10
        left = round(self.position.x - width / 2)
        top = round(self.position.y - self.radius - 28)
        background_rect = pygame.Rect(left, top, width, height)
        fill_ratio = self.hp / self.max_hp
        fill_rect = pygame.Rect(left, top, round(width * fill_ratio), height)

        pygame.draw.rect(surface, settings.HEALTH_BAR_BACKGROUND, background_rect)
        pygame.draw.rect(surface, settings.HEALTH_BAR_FILL, fill_rect)
        pygame.draw.rect(surface, settings.BOSS_OUTLINE_COLOR, background_rect, 1)

    def _draw_health_text(
        self, surface: pygame.Surface, font: pygame.font.Font
    ) -> None:
        label = font.render(f"Boss {self.hp}/{self.max_hp}", True, settings.TEXT_COLOR)
        label_rect = label.get_rect(
            center=(self.position.x, self.position.y + self.radius + 22)
        )
        surface.blit(label, label_rect)
