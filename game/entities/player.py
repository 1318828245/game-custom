from __future__ import annotations

import math

import pygame

from game.resources import images
from game import settings


class Player:
    def __init__(self, position: pygame.Vector2) -> None:
        self.position = position
        self.radius = settings.PLAYER_RADIUS
        self.speed = settings.PLAYER_SPEED
        self.aim_direction = pygame.Vector2(1, 0)
        self.max_hp = settings.PLAYER_MAX_HP
        self.hp = self.max_hp
        self.invulnerable_timer = 0.0
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dash_direction = pygame.Vector2(1, 0)

    def update(
        self,
        dt: float,
        move_direction: pygame.Vector2,
        mouse_position: tuple[int, int],
        bounds: pygame.Rect,
        dash_requested: bool = False,
    ) -> None:
        self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        self.dash_timer = max(0.0, self.dash_timer - dt)
        self.dash_cooldown_timer = max(0.0, self.dash_cooldown_timer - dt)

        aim_vector = pygame.Vector2(mouse_position) - self.position
        if aim_vector.length_squared() > 0:
            self.aim_direction = aim_vector.normalize()

        if dash_requested:
            self._try_start_dash(move_direction)

        if self.is_dashing:
            self.position += self.dash_direction * settings.PLAYER_DASH_SPEED * dt
            self._clamp_to_bounds(bounds)
        elif move_direction.length_squared() > 0:
            self.position += move_direction * self.speed * dt
            self._clamp_to_bounds(bounds)

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0

    @property
    def is_dashing(self) -> bool:
        return self.dash_timer > 0

    @property
    def dash_ready(self) -> bool:
        return self.dash_cooldown_timer <= 0 and not self.is_dashing

    def take_damage(self, amount: int) -> bool:
        if self.invulnerable_timer > 0 or self.is_dead:
            return False

        self.hp = max(0, self.hp - amount)
        self.invulnerable_timer = settings.PLAYER_INVULNERABLE_TIME
        return True

    def collides_with_circle(self, position: pygame.Vector2, radius: float) -> bool:
        distance_squared = self.position.distance_squared_to(position)
        combined_radius = self.radius + radius
        return distance_squared <= combined_radius * combined_radius

    def _try_start_dash(self, move_direction: pygame.Vector2) -> None:
        if not self.dash_ready:
            return

        self.dash_direction = (
            move_direction.copy()
            if move_direction.length_squared() > 0
            else self.aim_direction.copy()
        )
        self.dash_timer = settings.PLAYER_DASH_DURATION
        self.dash_cooldown_timer = settings.PLAYER_DASH_COOLDOWN
        self.invulnerable_timer = max(
            self.invulnerable_timer, settings.PLAYER_DASH_INVULNERABLE_TIME
        )

    def draw(self, surface: pygame.Surface) -> None:
        center = (round(self.position.x), round(self.position.y))
        aim_end = self.position + self.aim_direction * settings.AIM_LINE_LENGTH
        aim_end_pos = (round(aim_end.x), round(aim_end.y))
        player_color = (
            settings.PLAYER_HIT_COLOR
            if self.invulnerable_timer > 0
            else settings.PLAYER_COLOR
        )

        pygame.draw.line(surface, settings.AIM_COLOR, center, aim_end_pos, 4)
        pygame.draw.circle(surface, settings.AIM_DOT_COLOR, aim_end_pos, 5)
        angle = -math.degrees(math.atan2(self.aim_direction.y, self.aim_direction.x))
        if images.draw_centered(
            surface,
            "images/player/player_idle.png",
            center,
            (self.radius * 2 + 12, self.radius * 2 + 12),
            angle,
        ):
            if self.invulnerable_timer > 0:
                pygame.draw.circle(surface, settings.PLAYER_HIT_COLOR, center, self.radius, 3)
            return

        pygame.draw.circle(surface, player_color, center, self.radius)
        pygame.draw.circle(
            surface, settings.PLAYER_OUTLINE_COLOR, center, self.radius, 2
        )

    def _clamp_to_bounds(self, bounds: pygame.Rect) -> None:
        self.position.x = max(
            bounds.left + self.radius,
            min(self.position.x, bounds.right - self.radius),
        )
        self.position.y = max(
            bounds.top + self.radius,
            min(self.position.y, bounds.bottom - self.radius),
        )
