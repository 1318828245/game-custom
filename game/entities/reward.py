from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.config import GAME_CONFIG
from game.resources import images
from game import settings


@dataclass(frozen=True)
class RewardDefinition:
    label: str
    color: tuple[int, int, int]


REWARD_COLORS = {
    "heal": settings.REWARD_HEAL_COLOR,
    "fire_rate": settings.REWARD_FIRE_RATE_COLOR,
}


class RewardPickup:
    def __init__(self, position: pygame.Vector2, reward_type: str) -> None:
        reward_config = GAME_CONFIG["rewards"]["types"][reward_type]
        self.position = position
        self.reward_type = reward_type
        self.radius = GAME_CONFIG["rewards"]["pickup_radius"]
        self.definition = RewardDefinition(
            reward_config["label"],
            REWARD_COLORS[reward_type],
        )
        self.asset_path = {
            "heal": "images/items/item_heal.png",
            "fire_rate": "images/items/item_fire_rate.png",
        }[reward_type]

    @property
    def label(self) -> str:
        return self.definition.label

    def collides_with_circle(self, position: pygame.Vector2, radius: float) -> bool:
        distance_squared = self.position.distance_squared_to(position)
        combined_radius = self.radius + radius
        return distance_squared <= combined_radius * combined_radius

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        center = (round(self.position.x), round(self.position.y))
        drew_sprite = images.draw_centered(
            surface,
            self.asset_path,
            center,
            (self.radius * 2 + 8, self.radius * 2 + 8),
        )
        points = [
            (center[0], center[1] - self.radius),
            (center[0] + self.radius, center[1]),
            (center[0], center[1] + self.radius),
            (center[0] - self.radius, center[1]),
        ]

        if not drew_sprite:
            pygame.draw.polygon(surface, self.definition.color, points)
            pygame.draw.polygon(surface, settings.REWARD_OUTLINE_COLOR, points, 2)

        label = font.render(self.label, True, settings.TEXT_COLOR)
        label_rect = label.get_rect(center=(center[0], center[1] - self.radius - 22))
        surface.blit(label, label_rect)
