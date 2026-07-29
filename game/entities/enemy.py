from __future__ import annotations

import pygame

from game.config import GAME_CONFIG
from game.resources import images
from game import settings


class Enemy:
    def __init__(self, position: pygame.Vector2) -> None:
        params = GAME_CONFIG["enemies"]["melee"]
        self.position = position
        self.radius = params["radius"]
        self.max_hp = params["max_hp"]
        self.hp = self.max_hp
        self.speed = params["speed"]
        self.contact_damage = params["contact_damage"]
        self.hit_flash_time = params["hit_flash_time"]
        self.hit_flash_timer = 0.0

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0

    def update(self, dt: float, player_position: pygame.Vector2) -> None:
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        chase_direction = player_position - self.position

        if chase_direction.length_squared() > 0:
            self.position += chase_direction.normalize() * self.speed * dt

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)
        self.hit_flash_timer = self.hit_flash_time

    def collides_with_circle(self, position: pygame.Vector2, radius: float) -> bool:
        distance_squared = self.position.distance_squared_to(position)
        combined_radius = self.radius + radius
        return distance_squared <= combined_radius * combined_radius

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        center = (round(self.position.x), round(self.position.y))
        color = (
            settings.ENEMY_HIT_COLOR
            if self.hit_flash_timer > 0
            else settings.ENEMY_COLOR
        )

        drew_sprite = images.draw_centered(
            surface,
            "images/enemies/enemy_melee_idle.png",
            center,
            (self.radius * 2 + 8, self.radius * 2 + 8),
        )
        if drew_sprite:
            if self.hit_flash_timer > 0:
                pygame.draw.circle(surface, settings.ENEMY_HIT_COLOR, center, self.radius, 3)
        else:
            pygame.draw.circle(surface, color, center, self.radius)
            pygame.draw.circle(surface, settings.ENEMY_OUTLINE_COLOR, center, self.radius, 2)
        self._draw_health_bar(surface)
        self._draw_health_text(surface, font)

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
