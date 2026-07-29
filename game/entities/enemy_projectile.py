from __future__ import annotations

import pygame

from game.config import GAME_CONFIG
from game.resources import images
from game import settings


class EnemyProjectile:
    def __init__(
        self,
        position: pygame.Vector2,
        direction: pygame.Vector2,
        radius: int | None = None,
        speed: int | None = None,
        damage: int | None = None,
        asset_path: str = "images/projectiles/projectile_enemy.png",
    ) -> None:
        params = GAME_CONFIG["projectiles"]["enemy"]
        self.position = position
        self.direction = direction.normalize()
        self.radius = radius or params["radius"]
        self.speed = speed or params["speed"]
        self.damage = damage or params["damage"]
        self.asset_path = asset_path

    def update(self, dt: float) -> None:
        self.position += self.direction * self.speed * dt

    def draw(self, surface: pygame.Surface) -> None:
        center = (round(self.position.x), round(self.position.y))
        if images.draw_centered(
            surface,
            self.asset_path,
            center,
            (self.radius * 3, self.radius * 3),
        ):
            return

        pygame.draw.circle(surface, settings.ENEMY_PROJECTILE_COLOR, center, self.radius)
        pygame.draw.circle(
            surface,
            settings.ENEMY_PROJECTILE_OUTLINE_COLOR,
            center,
            self.radius,
            2,
        )

    def is_inside(self, bounds: pygame.Rect) -> bool:
        return (
            self.position.x >= bounds.left - self.radius
            and self.position.x <= bounds.right + self.radius
            and self.position.y >= bounds.top - self.radius
            and self.position.y <= bounds.bottom + self.radius
        )
