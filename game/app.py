from __future__ import annotations

import os

import pygame

from game import settings
from game.config import GAME_CONFIG
from game.resources import images
from game.entities.boss import Boss
from game.entities.enemy import Enemy
from game.entities.enemy_projectile import EnemyProjectile
from game.entities.player import Player
from game.entities.projectile import Projectile
from game.entities.ranged_enemy import RangedEnemy
from game.entities.reward import RewardPickup
from game.rooms.room_manager import RoomManager

EnemyEntity = Enemy | RangedEnemy | Boss

MOVE_SCANCODES = {
    "up": {26, 82},
    "down": {22, 81},
    "left": {4, 80},
    "right": {7, 79},
}


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.screen = pygame.display.set_mode(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.player = Player(
            pygame.Vector2(180, settings.WINDOW_HEIGHT / 2)
        )
        self.projectiles: list[Projectile] = []
        self.enemy_projectiles: list[EnemyProjectile] = []
        self.reward: RewardPickup | None = None
        self.room_manager = RoomManager(self.screen.get_rect())
        self.enemies: list[EnemyEntity] = self.room_manager.spawn_current_room_enemies()
        self.fire_cooldown = 0.0
        player_projectile = GAME_CONFIG["projectiles"]["player"]
        self.player_fire_cooldown = player_projectile["fire_cooldown"]
        self.player_projectile_damage = player_projectile["damage"]
        self.min_player_fire_cooldown = player_projectile["min_fire_cooldown"]
        self.rewards_config = GAME_CONFIG["rewards"]
        self.reward_message = ""
        self.reward_message_timer = 0.0
        self.game_over = False
        self.dash_requested = False
        self.running = True

    def run(self) -> None:
        smoke_test = os.environ.get("GAME_CUSTOM_SMOKE_TEST") == "1"
        frames = 0

        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000
            self._handle_events()
            self._update(dt)
            self._render()

            if smoke_test:
                frames += 1
                if frames >= 3:
                    self.running = False

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.dash_requested = True

    def _update(self, dt: float) -> None:
        if self.game_over:
            self.dash_requested = False
            return

        mouse_position = pygame.mouse.get_pos()
        move_direction = self._movement_input()
        self.player.update(
            dt,
            move_direction,
            mouse_position,
            self.screen.get_rect(),
            self.dash_requested,
        )
        self.dash_requested = False
        self.reward_message_timer = max(0.0, self.reward_message_timer - dt)
        self._update_shooting(dt)
        self._update_projectiles(dt)
        self._update_enemies(dt)
        self._update_enemy_projectiles(dt)
        self._handle_projectile_hits()
        self._handle_enemy_projectile_hits()
        self._handle_enemy_contact()
        self._update_room_progress()
        self._handle_reward_pickup()

        if self.player.is_dead:
            self.game_over = True

    def _movement_input(self) -> pygame.Vector2:
        move_direction = pygame.Vector2(0, 0)
        move_actions = self._snapshot_move_actions()

        if move_actions["up"]:
            move_direction.y -= 1
        if move_actions["down"]:
            move_direction.y += 1
        if move_actions["left"]:
            move_direction.x -= 1
        if move_actions["right"]:
            move_direction.x += 1

        if move_direction.length_squared() > 0:
            return move_direction.normalize()

        return move_direction

    def _snapshot_move_actions(self) -> dict[str, bool]:
        pressed = pygame.key.get_pressed()
        move_actions = {}
        for action, scancodes in MOVE_SCANCODES.items():
            move_actions[action] = any(
                self._pressed_snapshot_has(pressed, scancode)
                for scancode in scancodes
            )

        return move_actions

    def _pressed_snapshot_has(
        self, pressed: pygame.key.ScancodeWrapper, key: int
    ) -> bool:
        try:
            return bool(pressed[key])
        except IndexError:
            return False

    def _update_shooting(self, dt: float) -> None:
        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        mouse_buttons = pygame.mouse.get_pressed()

        if mouse_buttons[0] and self.fire_cooldown <= 0:
            self._spawn_player_projectile()
            self.fire_cooldown = self.player_fire_cooldown

    def _spawn_player_projectile(self) -> None:
        spawn_position = (
            self.player.position
            + self.player.aim_direction * GAME_CONFIG["projectiles"]["player"]["spawn_offset"]
        )
        self.projectiles.append(
            Projectile(
                spawn_position.copy(),
                self.player.aim_direction.copy(),
                self.player_projectile_damage,
            )
        )

    def _update_projectiles(self, dt: float) -> None:
        bounds = self.screen.get_rect()

        for projectile in self.projectiles:
            projectile.update(dt)

        self.projectiles = [
            projectile
            for projectile in self.projectiles
            if projectile.is_inside(bounds)
        ]

    def _update_enemies(self, dt: float) -> None:
        for enemy in self.enemies:
            spawned_projectile = enemy.update(dt, self.player.position)
            if spawned_projectile is not None:
                self.enemy_projectiles.append(spawned_projectile)

    def _update_enemy_projectiles(self, dt: float) -> None:
        bounds = self.screen.get_rect()

        for projectile in self.enemy_projectiles:
            projectile.update(dt)

        self.enemy_projectiles = [
            projectile
            for projectile in self.enemy_projectiles
            if projectile.is_inside(bounds)
        ]

    def _handle_projectile_hits(self) -> None:
        remaining_projectiles = []

        for projectile in self.projectiles:
            hit_enemy = self._find_hit_enemy(projectile)
            if hit_enemy is None:
                remaining_projectiles.append(projectile)
                continue

            hit_enemy.take_damage(projectile.damage)

        self.projectiles = remaining_projectiles
        self.enemies = [enemy for enemy in self.enemies if not enemy.is_dead]

    def _find_hit_enemy(self, projectile: Projectile) -> EnemyEntity | None:
        for enemy in self.enemies:
            if enemy.collides_with_circle(projectile.position, projectile.radius):
                return enemy
        return None

    def _handle_enemy_projectile_hits(self) -> None:
        remaining_projectiles = []

        for projectile in self.enemy_projectiles:
            if self.player.collides_with_circle(projectile.position, projectile.radius):
                self.player.take_damage(projectile.damage)
                continue

            remaining_projectiles.append(projectile)

        self.enemy_projectiles = remaining_projectiles

    def _handle_enemy_contact(self) -> None:
        for enemy in self.enemies:
            if self.player.collides_with_circle(enemy.position, enemy.radius):
                self.player.take_damage(enemy.contact_damage)

    def _update_room_progress(self) -> None:
        room_was_cleared = self.room_manager.update_after_enemy_count(len(self.enemies))
        if room_was_cleared:
            self._spawn_room_reward()

        if self.room_manager.player_touches_exit(
            self.player.position, self.player.radius
        ):
            self.enemies = self.room_manager.advance_room()
            self.projectiles.clear()
            self.enemy_projectiles.clear()
            self.reward = None
            self.player.position = pygame.Vector2(180, settings.WINDOW_HEIGHT / 2)

    def _spawn_room_reward(self) -> None:
        reward_type = self.room_manager.current_reward_type
        if reward_type is None or self.room_manager.prototype_complete:
            return

        self.reward = RewardPickup(
            pygame.Vector2(
                self.screen.get_rect().centerx,
                self.screen.get_rect().centery,
            ),
            reward_type,
        )

    def _handle_reward_pickup(self) -> None:
        if self.reward is None:
            return

        if not self.reward.collides_with_circle(self.player.position, self.player.radius):
            return

        self._apply_reward(self.reward)
        self.reward = None

    def _apply_reward(self, reward: RewardPickup) -> None:
        if reward.reward_type == "heal":
            self.player.hp = min(
                self.player.max_hp,
                self.player.hp
                + self.rewards_config["types"][reward.reward_type]["heal_amount"],
            )
        elif reward.reward_type == "fire_rate":
            self.player_fire_cooldown = max(
                self.min_player_fire_cooldown,
                self.player_fire_cooldown
                * self.rewards_config["types"][reward.reward_type]["fire_rate_multiplier"],
            )

        self.reward_message = f"Picked: {reward.label}"
        self.reward_message_timer = self.rewards_config["message_time"]

    def _render(self) -> None:
        self.room_manager.draw(self.screen)
        if self.reward is not None:
            self.reward.draw(self.screen, self.font)
        for enemy in self.enemies:
            enemy.draw(self.screen, self.font)
        for projectile in self.projectiles:
            projectile.draw(self.screen)
        for projectile in self.enemy_projectiles:
            projectile.draw(self.screen)
        self.player.draw(self.screen)
        self._draw_hud()

        if self.game_over:
            self._draw_game_over()
        elif self.room_manager.prototype_complete:
            self._draw_prototype_complete()

        pygame.display.flip()

    def _draw_hud(self) -> None:
        label = self.font.render(
            "WASD move | Mouse aim | Left click shoots | Esc quits",
            True,
            settings.TEXT_COLOR,
        )
        label_rect = label.get_rect(topleft=(24, 22))
        self.screen.blit(label, label_rect)

        hp_label = self.font.render(
            f"HP: {self.player.hp}/{self.player.max_hp}",
            True,
            settings.TEXT_COLOR,
        )
        images.draw_centered(self.screen, "images/ui/icon_heart.png", (36, 68), (24, 24))
        hp_rect = hp_label.get_rect(topleft=(54, 56))
        self.screen.blit(hp_label, hp_rect)

        fire_rate_label = self.font.render(
            f"Fire cooldown: {self.player_fire_cooldown:.2f}s",
            True,
            settings.TEXT_COLOR,
        )
        images.draw_centered(
            self.screen,
            "images/ui/icon_weapon_pistol.png",
            (36, 102),
            (24, 24),
        )
        fire_rate_rect = fire_rate_label.get_rect(topleft=(54, 90))
        self.screen.blit(fire_rate_label, fire_rate_rect)

        dash_text = (
            "Dash: READY"
            if self.player.dash_ready
            else f"Dash: {self.player.dash_cooldown_timer:.1f}s"
        )
        dash_label = self.font.render(dash_text, True, settings.TEXT_COLOR)
        images.draw_centered(self.screen, "images/ui/icon_dash.png", (36, 136), (24, 24))
        dash_rect = dash_label.get_rect(topleft=(54, 124))
        self.screen.blit(dash_label, dash_rect)

        room_label = self.font.render(
            (
                f"Room {self.room_manager.room_number}/{self.room_manager.total_rooms}: "
                f"{self.room_manager.current_room.name} - "
                f"{self.room_manager.room_status_text()}"
            ),
            True,
            settings.TEXT_COLOR,
        )
        room_rect = room_label.get_rect(topleft=(24, 158))
        self.screen.blit(room_label, room_rect)

        if self.reward_message_timer > 0:
            reward_label = self.font.render(
                self.reward_message,
                True,
                settings.REWARD_OUTLINE_COLOR,
            )
            reward_rect = reward_label.get_rect(topleft=(24, 192))
            self.screen.blit(reward_label, reward_rect)

        if self.room_manager.exit_open:
            exit_label = self.font.render("Exit", True, settings.TEXT_COLOR)
            exit_rect = exit_label.get_rect(
                center=(self.room_manager.exit_rect.centerx, self.room_manager.exit_rect.top - 18)
            )
            self.screen.blit(exit_label, exit_rect)

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 80)
        title = title_font.render("DEFEAT", True, settings.TEXT_COLOR)
        title_rect = title.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(title, title_rect)

        hint = self.font.render("Press Esc or close window to quit", True, settings.TEXT_COLOR)
        hint_rect = hint.get_rect(center=(title_rect.centerx, title_rect.bottom + 42))
        self.screen.blit(hint, hint_rect)

    def _draw_prototype_complete(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 72)
        title = title_font.render("PROTOTYPE COMPLETE", True, settings.TEXT_COLOR)
        title_rect = title.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(title, title_rect)


def main() -> None:
    app = GameApp()
    app.run()
