from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.config import GAME_CONFIG
from game.resources import images
from game import settings
from game.entities.boss import Boss
from game.entities.enemy import Enemy
from game.entities.ranged_enemy import RangedEnemy

EnemyEntity = Enemy | RangedEnemy | Boss


@dataclass(frozen=True)
class RoomDefinition:
    name: str
    kind: str
    enemy_spawns: tuple[dict[str, object], ...]
    reward_type: str | None = None


class RoomManager:
    def __init__(self, bounds: pygame.Rect) -> None:
        self.bounds = bounds
        self.rooms = self._load_room_definitions()
        self.current_index = 0
        self.state = "cleared"
        self.prototype_complete = False
        self.exit_rect = pygame.Rect(0, 0, settings.EXIT_WIDTH, settings.EXIT_HEIGHT)
        self.exit_rect.midright = (self.bounds.right - 26, self.bounds.centery)

    @property
    def current_room(self) -> RoomDefinition:
        return self.rooms[self.current_index]

    @property
    def room_number(self) -> int:
        return self.current_index + 1

    @property
    def total_rooms(self) -> int:
        return len(self.rooms)

    @property
    def is_last_room(self) -> bool:
        return self.current_index == len(self.rooms) - 1

    @property
    def exit_open(self) -> bool:
        return self.state == "cleared" and not self.prototype_complete

    @property
    def current_reward_type(self) -> str | None:
        return self.current_room.reward_type

    def spawn_current_room_enemies(self) -> list[EnemyEntity]:
        self.state = "combat" if self.current_room.enemy_spawns else "cleared"
        return [
            self._create_enemy(spawn)
            for spawn in self.current_room.enemy_spawns
        ]

    def update_after_enemy_count(self, enemy_count: int) -> bool:
        if self.state == "combat" and enemy_count == 0:
            self.state = "cleared"
            if self.is_last_room:
                self.prototype_complete = True
            return True

        return False

    def player_touches_exit(self, position: pygame.Vector2, radius: float) -> bool:
        if not self.exit_open:
            return False

        touch_rect = self.exit_rect.inflate(radius * 2, radius * 2)
        return touch_rect.collidepoint(round(position.x), round(position.y))

    def advance_room(self) -> list[EnemyEntity]:
        if not self.exit_open:
            return []

        if self.is_last_room:
            self.prototype_complete = True
            return []

        self.current_index += 1
        self.prototype_complete = False
        return self.spawn_current_room_enemies()

    def _load_room_definitions(self) -> list[RoomDefinition]:
        rooms = GAME_CONFIG["rooms"]
        if not isinstance(rooms, list) or not rooms:
            raise ValueError("Game config 'rooms' must be a non-empty list.")

        return [
            RoomDefinition(
                room["name"],
                room["kind"],
                tuple(room.get("enemy_spawns", ())),
                room.get("reward_type"),
            )
            for room in rooms
        ]

    def _create_enemy(self, spawn: dict[str, object]) -> EnemyEntity:
        enemy_type = str(spawn["type"])
        x = int(spawn["x"])
        y = int(spawn["y"])
        position = pygame.Vector2(x, y)

        if enemy_type == "ranged":
            return RangedEnemy(position)

        if enemy_type == "boss":
            return Boss(position)

        return Enemy(position)

    def room_status_text(self) -> str:
        if self.prototype_complete:
            return "Prototype complete"

        if self.state == "combat":
            return "Combat"

        return "Cleared - exit open"

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(settings.ROOM_FLOOR_COLOR)
        pygame.draw.rect(surface, settings.ROOM_BORDER_COLOR, self.bounds, 4)
        self._draw_exit(surface)

    def _draw_exit(self, surface: pygame.Surface) -> None:
        color = settings.EXIT_COLOR if self.exit_open else settings.EXIT_CLOSED_COLOR
        asset_path = (
            "images/rooms/door_open.png"
            if self.exit_open
            else "images/rooms/door_closed.png"
        )
        if images.draw_centered(
            surface,
            asset_path,
            self.exit_rect.center,
            self.exit_rect.size,
        ):
            return

        pygame.draw.rect(surface, color, self.exit_rect)
        pygame.draw.rect(surface, settings.EXIT_OUTLINE_COLOR, self.exit_rect, 2)
