from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_PATH = Path(__file__).resolve().parent.parent / "assets" / "data" / "gameplay.json"
REQUIRED_SECTIONS = ("rooms", "enemies", "projectiles", "rewards")
REQUIRED_ENEMIES = ("melee", "ranged", "boss")
REQUIRED_PROJECTILES = ("player", "enemy", "boss")


class ConfigError(RuntimeError):
    pass


def load_game_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Failed to read game config: {path}") from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"Failed to parse game config {path}: line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Game config root must be a JSON object: {path}")

    missing = [section for section in REQUIRED_SECTIONS if section not in data]
    if missing:
        raise ConfigError(
            f"Game config {path} is missing required section(s): {', '.join(missing)}"
        )

    _validate_game_config(data, path)
    return data


def _validate_game_config(data: dict[str, Any], path: Path) -> None:
    rooms = data["rooms"]
    if not isinstance(rooms, list) or not rooms:
        raise ConfigError(f"Game config {path} section 'rooms' must be a non-empty list.")

    for index, room in enumerate(rooms):
        if not isinstance(room, dict):
            raise ConfigError(f"Game config {path} rooms[{index}] must be an object.")

        _require_keys(room, ("name", "kind", "enemy_spawns", "reward_type"), path, f"rooms[{index}]")
        if not isinstance(room["enemy_spawns"], list):
            raise ConfigError(
                f"Game config {path} rooms[{index}].enemy_spawns must be a list."
            )

        for spawn_index, spawn in enumerate(room["enemy_spawns"]):
            if not isinstance(spawn, dict):
                raise ConfigError(
                    f"Game config {path} rooms[{index}].enemy_spawns[{spawn_index}] must be an object."
                )
            _require_keys(
                spawn,
                ("type", "x", "y"),
                path,
                f"rooms[{index}].enemy_spawns[{spawn_index}]",
            )

    enemies = _require_mapping(data, "enemies", path)
    for enemy_type in REQUIRED_ENEMIES:
        params = _require_mapping(enemies, enemy_type, path)
        _require_keys(params, ("radius", "max_hp", "contact_damage", "hit_flash_time"), path, f"enemies.{enemy_type}")

    _require_keys(enemies["melee"], ("speed",), path, "enemies.melee")
    _require_keys(
        enemies["ranged"],
        ("speed", "shoot_interval", "keep_distance", "distance_tolerance"),
        path,
        "enemies.ranged",
    )
    _require_keys(enemies["boss"], ("shoot_interval",), path, "enemies.boss")

    projectiles = _require_mapping(data, "projectiles", path)
    for projectile_type in REQUIRED_PROJECTILES:
        params = _require_mapping(projectiles, projectile_type, path)
        _require_keys(params, ("radius", "speed", "damage"), path, f"projectiles.{projectile_type}")

    _require_keys(
        projectiles["player"],
        ("spawn_offset", "fire_cooldown", "min_fire_cooldown"),
        path,
        "projectiles.player",
    )

    rewards = _require_mapping(data, "rewards", path)
    _require_keys(rewards, ("pickup_radius", "message_time", "types"), path, "rewards")
    reward_types = _require_mapping(rewards, "types", path)
    _require_keys(reward_types, ("heal", "fire_rate"), path, "rewards.types")
    _require_keys(reward_types["heal"], ("label", "heal_amount"), path, "rewards.types.heal")
    _require_keys(
        reward_types["fire_rate"],
        ("label", "fire_rate_multiplier"),
        path,
        "rewards.types.fire_rate",
    )


def _require_mapping(source: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = source.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"Game config {path} section '{key}' must be an object.")
    return value


def _require_keys(
    source: dict[str, Any],
    keys: tuple[str, ...],
    path: Path,
    location: str,
) -> None:
    missing = [key for key in keys if key not in source]
    if missing:
        raise ConfigError(
            f"Game config {path} location '{location}' is missing key(s): {', '.join(missing)}"
        )


GAME_CONFIG = load_game_config()
