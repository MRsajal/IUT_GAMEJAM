import pygame


CRYSTAL_SIZE = 34
DEBRIS_DAMAGE = 12


class MovableCrystal:
    def __init__(self, x, bottom_y, color=(80, 230, 255)):
        self.spawn = (x, bottom_y)
        self.color = color
        self.rect = pygame.Rect(x, bottom_y - CRYSTAL_SIZE, CRYSTAL_SIZE, CRYSTAL_SIZE)
        self.blockers = []

    def reset(self):
        self.rect.topleft = (self.spawn[0], self.spawn[1] - CRYSTAL_SIZE)

    def can_move(self, dx):
        moved = self.rect.move(dx, 0)
        return not any(moved.colliderect(rect) for rect in self.blockers)

    def push(self, dx):
        if dx and self.can_move(dx):
            self.rect.x += dx
            return True
        return False

    def take_damage(self, amount):
        return False

    def apply_knockback(self, distance):
        step = 2 if distance > 0 else -2
        for _ in range(abs(int(distance)) // 2):
            if not self.push(step):
                break

    def draw(self, screen, camera_x):
        rect = self.rect.move(-round(camera_x), 0)
        points = [
            (rect.centerx, rect.top),
            (rect.right, rect.centery),
            (rect.centerx, rect.bottom),
            (rect.left, rect.centery),
        ]
        pygame.draw.polygon(screen, (25, 70, 105), points)
        inner = rect.inflate(-10, -8)
        pygame.draw.polygon(
            screen,
            self.color,
            [
                (inner.centerx, inner.top),
                (inner.right, inner.centery),
                (inner.centerx, inner.bottom),
                (inner.left, inner.centery),
            ],
        )


class CrystalSocket:
    def __init__(self, center_x, bottom_y, color):
        self.color = color
        self.rect = pygame.Rect(0, 0, 42, 12)
        self.rect.midbottom = (center_x, bottom_y)

    def accepts(self, crystal):
        return (
            crystal.color == self.color
            and abs(crystal.rect.centerx - self.rect.centerx) <= 9
            and crystal.rect.bottom >= self.rect.top
        )

    def draw(self, screen, camera_x, active):
        rect = self.rect.move(-round(camera_x), 0)
        pygame.draw.ellipse(screen, (25, 35, 65), rect)
        pygame.draw.ellipse(
            screen, self.color if active else (80, 90, 120), rect, 3
        )


class FireBarrier:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.destroyed = False

    def take_damage(self, amount):
        return False

    def take_fire_damage(self, amount):
        if self.destroyed:
            return False
        self.destroyed = True
        return True

    def draw(self, screen, camera_x):
        if self.destroyed:
            return
        rect = self.rect.move(-round(camera_x), 0)
        pygame.draw.rect(screen, (75, 20, 85), rect)
        for y in range(rect.top + 8, rect.bottom, 18):
            pygame.draw.line(
                screen, (255, 100, 75), (rect.left, y), (rect.right, y - 8), 3
            )


class FallingDebris:
    def __init__(self, center_x, start_y=0):
        self.rect = pygame.Rect(0, 0, 14, 14)
        self.rect.midtop = (center_x, start_y)
        self.position_y = float(self.rect.y)
        self.warning_time = 0.55
        self.speed = 210
        self.hit = False

    def update(self, delta_time):
        if self.warning_time > 0:
            self.warning_time = max(0, self.warning_time - delta_time)
            return
        self.position_y += self.speed * delta_time
        self.rect.y = round(self.position_y)

    def draw(self, screen, camera_x, map_height):
        screen_x = self.rect.centerx - round(camera_x)
        if self.warning_time > 0:
            pygame.draw.line(
                screen, (255, 85, 85), (screen_x, map_height - 34),
                (screen_x, map_height - 8), 3
            )
            return
        pygame.draw.polygon(
            screen,
            (135, 100, 175),
            [
                (screen_x, self.rect.top),
                (screen_x + 8, self.rect.centery),
                (screen_x, self.rect.bottom),
                (screen_x - 8, self.rect.centery),
            ],
        )


class Shrine:
    def __init__(self, center_x, bottom_y):
        self.rect = pygame.Rect(0, 0, 34, 54)
        self.rect.midbottom = (center_x, bottom_y)

    def nearby(self, player):
        return self.rect.inflate(60, 30).colliderect(player.rect)

    def recharge(self, player):
        player.magic_uses["Fire Magic"] = max(
            3, player.magic_uses.get("Fire Magic", 0)
        )
        player.combat_message = "Shrine restored 3 Fire Magic charges."
        player.combat_message_time_left = 2.0

    def draw(self, screen, camera_x):
        rect = self.rect.move(-round(camera_x), 0)
        pygame.draw.rect(screen, (55, 45, 90), rect, border_radius=6)
        pygame.draw.circle(screen, (100, 235, 255), (rect.centerx, rect.y + 15), 9)
        pygame.draw.circle(screen, (255, 125, 80), (rect.centerx, rect.y + 15), 4)


class ResetPedestal:
    def __init__(self, center_x, bottom_y):
        self.rect = pygame.Rect(0, 0, 30, 40)
        self.rect.midbottom = (center_x, bottom_y)

    def nearby(self, player):
        return self.rect.inflate(55, 25).colliderect(player.rect)

    def draw(self, screen, camera_x):
        rect = self.rect.move(-round(camera_x), 0)
        pygame.draw.rect(screen, (105, 90, 135), rect)
        pygame.draw.rect(screen, (190, 175, 230), rect, 2)
        pygame.draw.circle(screen, (110, 245, 225), (rect.centerx, rect.top + 8), 5)
