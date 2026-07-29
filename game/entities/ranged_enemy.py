from __future__ import annotations

import pygame

from game.config import GAME_CONFIG
from game.resources import images
from game import settings
from game.entities.enemy_projectile import EnemyProjectile


class RangedEnemy:
    def __init__(self, position: pygame.Vector2) -> None:
        params = GAME_CONFIG["enemies"]["ranged"]
        self.position = position
        self.radius = params["radius"]
        self.max_hp = params["max_hp"]
        self.hp = self.max_hp
        self.speed = params["speed"]
        self.contact_damage = params["contact_damage"]
        self.shoot_interval = params["shoot_interval"]
        self.keep_distance = params["keep_distance"]
        self.distance_tolerance = params["distance_tolerance"]
        self.hit_flash_time = params["hit_flash_time"]
        self.hit_flash_timer = 0.0
        self.shoot_timer = self.shoot_interval * 0.6

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0

    def update(
        self, dt: float, player_position: pygame.Vector2
    ) -> EnemyProjectile | None:
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        self.shoot_timer = max(0.0, self.shoot_timer - dt)
        to_player = player_position - self.position

        if to_player.length_squared() <= 0:
            return None

        self._adjust_distance(dt, to_player)

        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_interval
            spawn_position = self.position + to_player.normalize() * (self.radius + 8)
            return EnemyProjectile(spawn_position.copy(), to_player.copy())

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
            settings.RANGED_ENEMY_HIT_COLOR
            if self.hit_flash_timer > 0
            else settings.RANGED_ENEMY_COLOR
        )
        rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        rect.center = (round(self.position.x), round(self.position.y))

        drew_sprite = images.draw_centered(
            surface,
            "images/enemies/enemy_ranged_idle.png",
            rect.center,
            (self.radius * 2 + 10, self.radius * 2 + 10),
        )
        if drew_sprite:
            if self.hit_flash_timer > 0:
                pygame.draw.rect(surface, settings.RANGED_ENEMY_HIT_COLOR, rect, 3, 6)
        else:
            pygame.draw.rect(surface, color, rect, border_radius=6)
            pygame.draw.rect(surface, settings.RANGED_ENEMY_OUTLINE_COLOR, rect, 2, 6)
            self._draw_barrel(surface)
        self._draw_health_bar(surface)
        self._draw_health_text(surface, font)

    def _adjust_distance(self, dt: float, to_player: pygame.Vector2) -> None:
        distance = to_player.length()
        direction = to_player.normalize()
        lower_bound = self.keep_distance - self.distance_tolerance
        upper_bound = self.keep_distance + self.distance_tolerance

        if distance < lower_bound:
            self.position -= direction * self.speed * dt
        elif distance > upper_bound:
            self.position += direction * self.speed * dt

    def _draw_barrel(self, surface: pygame.Surface) -> None:
        top = (round(self.position.x), round(self.position.y - self.radius - 5))
        bottom = (round(self.position.x), round(self.position.y + self.radius + 5))
        pygame.draw.line(surface, settings.RANGED_ENEMY_OUTLINE_COLOR, top, bottom, 3)

    def _draw_health_bar(self, surface: pygame.Surface) -> None:
        width = self.radius * 2
        height = 6
        left = round(self.position.x - self.radius)
        top = round(self.position.y - self.radius - 14)
        background_rect = pygame.Rect(left, top, width, height)
        fill_ratio = self.hp / self.max_hp
        fill_rect = pygame.Rect(left, top, round(width * fill_ratio), height)

        pygame.draw.rect(surface, settings.HEALTH_BAR_BACKGROUND, background_rect)
        pygame.draw.rect(surface, settings.HEALTH_BAR_FILL, fill_rect)

    def _draw_health_text(
        self, surface: pygame.Surface, font: pygame.font.Font
    ) -> None:
        label = font.render(str(self.hp), True, settings.TEXT_COLOR)
        label_rect = label.get_rect(center=self.position)
        surface.blit(label, label_rect)
