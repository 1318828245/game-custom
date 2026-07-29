from __future__ import annotations

import pygame

from game import settings


class Target:
    def __init__(self, position: pygame.Vector2) -> None:
        self.position = position
        self.radius = settings.TARGET_RADIUS
        self.max_hp = settings.TARGET_MAX_HP
        self.hp = self.max_hp
        self.hit_flash_timer = 0.0

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0

    def update(self, dt: float) -> None:
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)
        self.hit_flash_timer = settings.TARGET_HIT_FLASH_TIME

    def collides_with_circle(self, position: pygame.Vector2, radius: float) -> bool:
        distance_squared = self.position.distance_squared_to(position)
        combined_radius = self.radius + radius
        return distance_squared <= combined_radius * combined_radius

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        center = (round(self.position.x), round(self.position.y))
        color = (
            settings.TARGET_HIT_COLOR
            if self.hit_flash_timer > 0
            else settings.TARGET_COLOR
        )

        pygame.draw.circle(surface, color, center, self.radius)
        pygame.draw.circle(surface, settings.TARGET_OUTLINE_COLOR, center, self.radius, 2)
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
