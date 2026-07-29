from __future__ import annotations

import pygame

from game.config import GAME_CONFIG
from game.resources import images
from game import settings


class Projectile:
    def __init__(
        self,
        position: pygame.Vector2,
        direction: pygame.Vector2,
        damage: int | None = None,
    ) -> None:
        params = GAME_CONFIG["projectiles"]["player"]
        self.position = position
        self.direction = direction.normalize()
        self.radius = params["radius"]
        self.speed = params["speed"]
        self.damage = damage or params["damage"]

    def update(self, dt: float) -> None:
        self.position += self.direction * self.speed * dt

    def draw(self, surface: pygame.Surface) -> None:
        center = (round(self.position.x), round(self.position.y))
        if images.draw_centered(
            surface,
            "images/projectiles/projectile_player.png",
            center,
            (self.radius * 4, self.radius * 4),
        ):
            return

        pygame.draw.circle(surface, settings.PROJECTILE_COLOR, center, self.radius)
        pygame.draw.circle(
            surface, settings.PROJECTILE_OUTLINE_COLOR, center, self.radius, 1
        )

    def is_inside(self, bounds: pygame.Rect) -> bool:
        return (
            self.position.x >= bounds.left - self.radius
            and self.position.x <= bounds.right + self.radius
            and self.position.y >= bounds.top - self.radius
            and self.position.y <= bounds.bottom + self.radius
        )
