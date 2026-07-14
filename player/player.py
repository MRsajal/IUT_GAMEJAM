from pathlib import Path

import pygame


PLAYER_SPEED = 180
GRAVITY = 1000
IDLE_ANIMATION_SPEED = 8
ATTACK_ANIMATION_SPEED = 12
ATTACK_FRAME_COUNT = 5
STARTING_HEALTH = 50
STARTING_ATTACK_DAMAGE = 20
ATTACK_RANGE = 20
ATTACK_DURATION = ATTACK_FRAME_COUNT / ATTACK_ANIMATION_SPEED
ATTACK_COOLDOWN = 0.5

IDLE_PATH = Path(__file__).parent / "idle"
ATTACK_PATH = Path(__file__).parent / "attack"


class Player:
    def __init__(self, x, y):
        self.idle_right = self._load_idle_frames()
        self.idle_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.idle_right
        ]
        self.attack_right = self._load_attack_frames()
        self.attack_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.attack_right
        ]

        # The collision box is slightly narrower than the sprite.
        self.rect = pygame.Rect(x, y, 24, 40)
        self.position = pygame.Vector2(self.rect.topleft)
        self.velocity_y = 0.0
        self.facing_right = True
        self.animation_time = 0.0

        # Combat stats. level_up() can increase both values later.
        self.level = 1
        self.max_health = STARTING_HEALTH
        self.health = self.max_health
        self.attack_damage = STARTING_ATTACK_DAMAGE

        self.attack_time_left = 0.0
        self.attack_cooldown_left = 0.0
        self.attack_has_dealt_damage = False
        self.ui_font = pygame.font.Font(None, 20)

    def _load_idle_frames(self):
        frames = []

        for frame_number in range(6):
            path = IDLE_PATH / f"{frame_number}.png"
            frames.append(pygame.image.load(path).convert_alpha())

        return frames

    def _load_attack_frames(self):
        frames = []

        for frame_number in range(ATTACK_FRAME_COUNT):
            path = ATTACK_PATH / f"{frame_number}.png"
            frames.append(pygame.image.load(path).convert_alpha())

        return frames

    def handle_event(self, event):
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
            and self.attack_cooldown_left <= 0
        ):
            self.attack_time_left = ATTACK_DURATION
            self.attack_cooldown_left = ATTACK_COOLDOWN
            self.attack_has_dealt_damage = False

    def get_attack_rect(self):
        """Return the attack area in world coordinates."""
        if self.facing_right:
            return pygame.Rect(
                self.rect.right,
                self.rect.top,
                ATTACK_RANGE,
                self.rect.height,
            )

        return pygame.Rect(
            self.rect.left - ATTACK_RANGE,
            self.rect.top,
            ATTACK_RANGE,
            self.rect.height,
        )

    @property
    def is_attacking(self):
        return self.attack_time_left > 0

    def _update_attack(self, delta_time, damage_targets):
        self.attack_cooldown_left = max(
            0, self.attack_cooldown_left - delta_time
        )

        if not self.is_attacking:
            return

        if not self.attack_has_dealt_damage:
            attack_rect = self.get_attack_rect()

            for target in damage_targets:
                take_damage = getattr(target, "take_damage", None)
                target_rect = getattr(target, "rect", None)

                if (
                    target_rect is not None
                    and callable(take_damage)
                    and attack_rect.colliderect(target_rect)
                ):
                    take_damage(self.attack_damage)

            # Each target can only be damaged once per attack press.
            self.attack_has_dealt_damage = True

        self.attack_time_left = max(0, self.attack_time_left - delta_time)

    def take_damage(self, amount):
        """Reduce player health without allowing it to go below zero."""
        self.health = max(0, self.health - max(0, amount))

    def level_up(self, health_increase, attack_damage_increase):
        """Increase level and apply progression values chosen by the game."""
        health_increase = max(0, health_increase)
        attack_damage_increase = max(0, attack_damage_increase)

        self.level += 1
        self.max_health += health_increase
        self.health += health_increase
        self.attack_damage += attack_damage_increase

    def update(self, delta_time, platform_rects, map_width, damage_targets=()):
        keys = pygame.key.get_pressed()
        direction = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction -= 1
            self.facing_right = False

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction += 1
            self.facing_right = True

        # Horizontal player movement.
        self.position.x += direction * PLAYER_SPEED * delta_time
        self.position.x = max(
            0, min(self.position.x, map_width - self.rect.width)
        )
        self.rect.x = round(self.position.x)

        # Gravity and one-way platform collision.
        old_bottom = self.rect.bottom
        self.velocity_y += GRAVITY * delta_time
        self.position.y += self.velocity_y * delta_time
        self.rect.y = round(self.position.y)

        if self.velocity_y >= 0:
            for platform_rect in platform_rects:
                horizontally_overlapping = (
                    self.rect.right > platform_rect.left
                    and self.rect.left < platform_rect.right
                )
                crossed_platform_top = (
                    old_bottom <= platform_rect.top
                    and self.rect.bottom >= platform_rect.top
                )

                if horizontally_overlapping and crossed_platform_top:
                    self.rect.bottom = platform_rect.top
                    self.position.y = self.rect.y
                    self.velocity_y = 0
                    break

        self.animation_time += delta_time
        self._update_attack(delta_time, damage_targets)

    def draw(self, screen, camera_x):
        if self.is_attacking:
            frames = (
                self.attack_right if self.facing_right else self.attack_left
            )
            attack_elapsed = ATTACK_DURATION - self.attack_time_left
            frame_index = min(
                int(attack_elapsed * ATTACK_ANIMATION_SPEED),
                len(frames) - 1,
            )
        else:
            frames = self.idle_right if self.facing_right else self.idle_left
            frame_index = int(
                self.animation_time * IDLE_ANIMATION_SPEED
            ) % len(frames)

        image = frames[frame_index]

        # Keep differently sized animation frames aligned at the feet.
        draw_rect = image.get_rect(
            midbottom=(self.rect.centerx - round(camera_x), self.rect.bottom)
        )
        screen.blit(image, draw_rect)

    def draw_health_bar(self, screen):
        """Draw player health in screen coordinates, independent of camera."""
        bar_x = 16
        bar_y = 16
        bar_width = 180
        bar_height = 16
        health_ratio = self.health / self.max_health

        pygame.draw.rect(
            screen, (35, 35, 35), (bar_x, bar_y, bar_width, bar_height)
        )
        pygame.draw.rect(
            screen,
            (45, 190, 75),
            (bar_x, bar_y, round(bar_width * health_ratio), bar_height),
        )
        pygame.draw.rect(
            screen, (245, 245, 245), (bar_x, bar_y, bar_width, bar_height), 2
        )

        label = self.ui_font.render(
            f"HP {self.health}/{self.max_health}   LV {self.level}",
            True,
            (255, 255, 255),
        )
        screen.blit(label, (bar_x + 4, bar_y - 1))
