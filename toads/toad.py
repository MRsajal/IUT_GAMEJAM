from pathlib import Path

import pygame


TOAD_MAX_HEALTH = 20
TOAD_ATTACK_DAMAGE = 20
TOAD_SPEED = 45
TOAD_ATTACK_RANGE = 24
TOAD_IDLE_SPEED = 6
TOAD_WALK_SPEED = 8
TOAD_ATTACK_SPEED = 8
TOAD_ATTACK_FRAME_COUNT = 3
TOAD_ATTACK_DURATION = TOAD_ATTACK_FRAME_COUNT / TOAD_ATTACK_SPEED
TOAD_ATTACK_COOLDOWN = 1.2
TOAD_FRAME_SIZE = (48, 38)
TOAD_SPAWN_SHIFT = 8
BOSS_FRAME_SIZE = (72, 57)
BOSS_MAX_HEALTH = 100
BOSS_ATTACK_DAMAGE = 30
BOSS_SPEED = 35
BOSS_ATTACK_RANGE = 40
TOAD_KNOCKBACK_DECELERATION = 850
KNOCKBACK_AIR_TIME = 0.45
KNOCKBACK_ARC_HEIGHT = 24

TOAD_PATH = Path(__file__).parent


class Toad:
    _animations = None

    def __init__(self, zone_left, zone_right, bottom_y, is_boss=False):
        self._load_animations()

        self.is_boss = is_boss
        self.zone_left = zone_left
        self.zone_right = zone_right
        body_size = (48, 34) if is_boss else (28, 20)
        self.rect = pygame.Rect(0, 0, *body_size)
        self.rect.midbottom = (
            (zone_left + zone_right) // 2 + TOAD_SPAWN_SHIFT,
            bottom_y,
        )
        self.position_x = float(self.rect.x)

        self.max_health = BOSS_MAX_HEALTH if is_boss else TOAD_MAX_HEALTH
        self.health = self.max_health
        self.attack_damage = (
            BOSS_ATTACK_DAMAGE if is_boss else TOAD_ATTACK_DAMAGE
        )
        self.attack_range = (
            BOSS_ATTACK_RANGE if is_boss else TOAD_ATTACK_RANGE
        )
        self.speed = BOSS_SPEED if is_boss else TOAD_SPEED
        self.facing_right = False
        self.state = "idle"
        self.animation_time = 0.0
        self.attack_time_left = 0.0
        self.attack_cooldown_left = 0.0
        self.attack_has_dealt_damage = False
        self.knockback_velocity = 0.0
        self.knockback_air_time = 0.0

    @classmethod
    def _load_animations(cls):
        if cls._animations is not None:
            return

        right = {
            "idle": cls._load_folder("idle", 4),
            # The supplied movement animation folder is named "jump".
            "walk": cls._load_folder("jump", 4),
            "attack": cls._load_folder("attack", 3),
        }
        left = {
            name: [pygame.transform.flip(frame, True, False) for frame in frames]
            for name, frames in right.items()
        }
        cls._animations = {"right": right, "left": left}

    @classmethod
    def _load_folder(cls, folder_name, frame_count):
        frames = []
        for frame_number in range(frame_count):
            path = TOAD_PATH / folder_name / f"{frame_number}.png"
            original = pygame.image.load(path).convert_alpha()
            frames.append(
                pygame.transform.smoothscale(original, TOAD_FRAME_SIZE)
            )
        return frames

    @property
    def alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0, self.health - max(0, amount))

    def apply_knockback(self, distance):
        """Launch the toad horizontally instead of teleporting it."""
        # Bosses are heavier, so the same kick moves them less.
        strength = 3.0 if self.is_boss else 5.5
        self.knockback_velocity = distance * strength
        self.knockback_air_time = KNOCKBACK_AIR_TIME
        self.attack_time_left = 0.0
        self.attack_has_dealt_damage = False

    def _player_is_in_zone(self, player):
        return self.zone_left <= player.rect.centerx <= self.zone_right

    def _get_attack_rect(self):
        if self.facing_right:
            return pygame.Rect(
                self.rect.left,
                self.rect.top,
                self.rect.width + self.attack_range,
                self.rect.height,
            )

        return pygame.Rect(
            self.rect.left - self.attack_range,
            self.rect.top,
            self.rect.width + self.attack_range,
            self.rect.height,
        )

    def _start_attack(self):
        self.state = "attack"
        self.animation_time = 0.0
        self.attack_time_left = TOAD_ATTACK_DURATION
        self.attack_cooldown_left = TOAD_ATTACK_COOLDOWN
        self.attack_has_dealt_damage = False

    def update(self, delta_time, player):
        if not self.alive:
            return

        self.attack_cooldown_left = max(
            0, self.attack_cooldown_left - delta_time
        )
        self.knockback_air_time = max(
            0, self.knockback_air_time - delta_time
        )

        if abs(self.knockback_velocity) > 1:
            self.state = "walk"
            self.animation_time += delta_time
            self.position_x += self.knockback_velocity * delta_time
            self.position_x = max(
                self.zone_left,
                min(self.position_x, self.zone_right - self.rect.width),
            )
            at_boundary = self.position_x in (
                self.zone_left,
                self.zone_right - self.rect.width,
            )
            deceleration = TOAD_KNOCKBACK_DECELERATION * delta_time
            if self.knockback_velocity > 0:
                self.knockback_velocity = max(
                    0, self.knockback_velocity - deceleration
                )
            else:
                self.knockback_velocity = min(
                    0, self.knockback_velocity + deceleration
                )
            if at_boundary:
                self.knockback_velocity = 0.0
            self.rect.x = round(self.position_x)
            return

        self.knockback_velocity = 0.0

        if self.attack_time_left > 0:
            self.state = "attack"
            self.animation_time += delta_time
            attack_elapsed = TOAD_ATTACK_DURATION - self.attack_time_left

            # Apply damage as the second attack frame starts.
            if (
                not self.attack_has_dealt_damage
                and attack_elapsed >= 1 / TOAD_ATTACK_SPEED
            ):
                if self._get_attack_rect().colliderect(player.rect):
                    player.take_damage(self.attack_damage)
                self.attack_has_dealt_damage = True

            self.attack_time_left = max(
                0, self.attack_time_left - delta_time
            )
            return

        if not self._player_is_in_zone(player):
            self.state = "idle"
            self.animation_time += delta_time
            return

        distance = player.rect.centerx - self.rect.centerx
        if distance != 0:
            self.facing_right = distance > 0

        edge_distance = abs(distance) - (
            self.rect.width + player.rect.width
        ) / 2
        if edge_distance < self.attack_range:
            if self.attack_cooldown_left <= 0:
                self._start_attack()
            else:
                self.state = "idle"
                self.animation_time += delta_time
            return

        direction = 1 if distance > 0 else -1
        self.state = "walk"
        self.animation_time += delta_time
        self.position_x += direction * self.speed * delta_time
        self.position_x = max(
            self.zone_left,
            min(
                self.position_x,
                self.zone_right - self.rect.width,
            ),
        )
        self.rect.x = round(self.position_x)

    def draw(self, screen, camera_x):
        direction = "right" if self.facing_right else "left"
        frames = self._animations[direction][self.state]
        speed = {
            "idle": TOAD_IDLE_SPEED,
            "walk": TOAD_WALK_SPEED,
            "attack": TOAD_ATTACK_SPEED,
        }[self.state]
        frame_index = min(
            int(self.animation_time * speed) % len(frames),
            len(frames) - 1,
        )
        image = frames[frame_index]

        if self.is_boss:
            image = pygame.transform.smoothscale(image, BOSS_FRAME_SIZE)

        # Preserve the character anchor after scaling the 80px source frame.
        if self.is_boss:
            anchor_x = 45 if self.facing_right else 27
        else:
            anchor_x = 30 if self.facing_right else 18
        air_progress = self.knockback_air_time / KNOCKBACK_AIR_TIME
        arc_offset = round(
            4 * KNOCKBACK_ARC_HEIGHT * air_progress * (1 - air_progress)
        )
        draw_rect = image.get_rect(
            bottomleft=(
                self.rect.centerx - round(camera_x) - anchor_x,
                self.rect.bottom - arc_offset,
            )
        )
        screen.blit(image, draw_rect)

        if self.is_boss:
            bar_width = 72
            bar_rect = pygame.Rect(
                self.rect.centerx - round(camera_x) - bar_width // 2,
                draw_rect.top - 7,
                bar_width,
                5,
            )
            pygame.draw.rect(screen, (45, 20, 20), bar_rect)
            health_width = round(bar_width * self.health / self.max_health)
            pygame.draw.rect(
                screen,
                (210, 55, 55),
                (bar_rect.x, bar_rect.y, health_width, bar_rect.height),
            )
