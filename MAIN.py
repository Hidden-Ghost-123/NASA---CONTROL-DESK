import pygame
import math
import random

pygame.init()

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASA Mission Simulator - Hour 6")

clock = pygame.time.Clock()

WHITE = (235, 235, 235)
GREEN = (80, 255, 120)
RED = (255, 80, 80)
BLUE = (80, 150, 255)
YELLOW = (255, 220, 80)
GRAY = (45, 45, 55)
BLACK = (10, 10, 20)

font_small = pygame.font.SysFont("consolas", 18)
font_med = pygame.font.SysFont("consolas", 22)
font_big = pygame.font.SysFont("consolas", 40)

CENTER = (WIDTH // 2, HEIGHT // 2)


def sky_color(alt):
    t = min(alt / 100000, 1)
    return (
        int(20 * (1 - t)),
        int(70 * (1 - t)),
        int(150 * (1 - t))
    )


def format_time(t):
    m = int(t // 60)
    s = int(t % 60)
    return f"T+{m:02}:{s:02}"


class MissionLog:
    def __init__(self):
        self.logs = []

    def add(self, msg):
        self.logs.append(msg)
        if len(self.logs) > 12:
            self.logs.pop(0)

    def draw(self):
        panel = pygame.Rect(20, 420, 420, 300)
        pygame.draw.rect(screen, GRAY, panel)
        pygame.draw.rect(screen, GREEN, panel, 2)

        title = font_med.render("MISSION LOG", True, GREEN)
        screen.blit(title, (30, 430))

        y = 470
        for l in self.logs:
            screen.blit(font_small.render(l, True, WHITE), (30, y))
            y += 20


class Rocket:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH // 2
        self.base_y = HEIGHT - 100

        self.altitude = 0
        self.velocity = 0
        self.acceleration = 0

        self.engine = False
        self.fuel = 100

        self.thrust = 35
        self.gravity = 9.8

        self.orbit_angle = 0
        self.orbit_radius = 180
        self.in_orbit = False

        self.engine_failure = False
        self.fuel_leak = False

    def update_launch(self):

        thrust = 0

        if self.engine and self.fuel > 0 and not self.engine_failure:
            thrust = self.thrust

        if self.fuel_leak:
            self.fuel -= 0.08
        elif self.engine:
            self.fuel -= 0.03

        drag = self.velocity * 0.02 * max(0, 1 - self.altitude / 60000)

        self.acceleration = thrust - self.gravity - drag
        self.velocity += self.acceleration * 0.12
        self.altitude += self.velocity

        if self.altitude < 0:
            self.altitude = 0
            self.velocity = 0

    def enter_orbit(self):
        self.in_orbit = True
        self.orbit_angle = math.pi / 2

    def draw_launch(self):
        y = self.base_y - int(self.altitude / 300)

        pygame.draw.rect(screen, WHITE, (self.x - 12, y - 40, 24, 40))
        pygame.draw.polygon(screen, RED, [
            (self.x - 12, y - 40),
            (self.x + 12, y - 40),
            (self.x, y - 65)
        ])

        if self.engine and self.fuel > 0 and not self.engine_failure:
            flame = 20 + math.sin(pygame.time.get_ticks() * 0.02) * 6
            pygame.draw.polygon(screen, (255, 180, 0), [
                (self.x - 10, y),
                (self.x + 10, y),
                (self.x, y + flame)
            ])

    def draw_orbit(self):
        cx, cy = CENTER

        x = cx + math.cos(self.orbit_angle) * self.orbit_radius
        y = cy + math.sin(self.orbit_angle) * self.orbit_radius

        pygame.draw.circle(screen, BLUE, CENTER, 60)
        pygame.draw.rect(screen, WHITE, (x - 10, y - 10, 20, 20))

    def update_orbit(self):
        self.orbit_angle += 0.01


class Satellite:
    def __init__(self):
        self.angle = random.random() * math.pi * 2
        self.radius = random.randint(140, 240)
        self.speed = random.uniform(0.002, 0.006)

    def update(self):
        self.angle += self.speed

    def draw(self):
        x = CENTER[0] + math.cos(self.angle) * self.radius
        y = CENTER[1] + math.sin(self.angle) * self.radius
        pygame.draw.rect(screen, YELLOW, (x - 4, y - 4, 8, 8))


class Game:
    def __init__(self):
        self.rocket = Rocket()
        self.log = MissionLog()
        self.satellites = []

        self.mode = "launch"
        self.t = 0

        self.win = False
        self.fail = False

        self.log.add("T+00:00 Mission Initiated")

    def check_win_condition(self):
        if len(self.satellites) >= 3:
            self.win = True

    def check_fail_condition(self):
        if self.rocket.fuel <= 0 and self.mode == "launch" and not self.satellites:
            self.fail = True

    def trigger_events(self):

        roll = random.randint(0, 1200)

        if roll == 1:
            self.rocket.engine_failure = True
            self.log.add(f"{format_time(self.t)} ENGINE FAILURE")

        if roll == 2:
            self.rocket.fuel_leak = True
            self.log.add(f"{format_time(self.t)} FUEL LEAK")

        if roll == 3:
            self.rocket.engine_failure = False
            self.rocket.fuel_leak = False
            self.log.add(f"{format_time(self.t)} SYSTEM RECOVERED")

    def update(self):

        if self.win or self.fail:
            return

        dt = clock.get_time() / 1000
        self.t += dt

        self.trigger_events()

        if self.mode == "launch":
            self.rocket.update_launch()

            if self.rocket.altitude > 80000:
                self.mode = "orbit"
                self.rocket.enter_orbit()
                self.log.add(f"{format_time(self.t)} Orbit Achieved")

        else:
            self.rocket.update_orbit()
            for s in self.satellites:
                s.update()

        self.check_win_condition()
        self.check_fail_condition()

    def draw_ui(self):

        panel = pygame.Rect(20, 20, 420, 360)
        pygame.draw.rect(screen, GRAY, panel)
        pygame.draw.rect(screen, GREEN, panel, 2)

        if self.win:
            msg = font_big.render("MISSION SUCCESS", True, GREEN)
            screen.blit(msg, (WIDTH//2 - 200, HEIGHT//2 - 40))
            return

        if self.fail:
            msg = font_big.render("MISSION FAILED", True, RED)
            screen.blit(msg, (WIDTH//2 - 180, HEIGHT//2 - 40))
            return

        stats = [
            f"MODE: {self.mode.upper()}",
            f"ALT: {self.rocket.altitude:.0f}",
            f"VEL: {self.rocket.velocity:.1f}",
            f"FUEL: {self.rocket.fuel:.1f}%",
            f"SATS: {len(self.satellites)}",
            f"ENGINE: {'FAIL' if self.rocket.engine_failure else 'OK'}",
            f"LEAK: {'YES' if self.rocket.fuel_leak else 'NO'}"
        ]

        y = 60
        for s in stats:
            screen.blit(font_small.render(s, True, WHITE), (30, y))
            y += 28

    def draw(self):

        if self.mode == "launch":
            screen.fill(sky_color(self.rocket.altitude))
            pygame.draw.rect(screen, BLUE, (0, HEIGHT - 80, WIDTH, 80))
            self.rocket.draw_launch()

        else:
            screen.fill((5, 5, 15))
            pygame.draw.circle(screen, BLUE, CENTER, 60)

            self.rocket.draw_orbit()

            for s in self.satellites:
                s.draw()

        self.draw_ui()
        self.log.draw()

        hint = font_small.render(
            "SPACE engine | M orbit mode | D deploy satellite",
            True,
            GREEN
        )
        screen.blit(hint, (20, HEIGHT - 30))


game = Game()

running = True

while running:
    clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.KEYDOWN:

            if e.key == pygame.K_SPACE:
                game.rocket.engine = not game.rocket.engine

            if e.key == pygame.K_m and game.rocket.altitude > 80000:
                game.mode = "orbit"
                game.rocket.enter_orbit()

            if e.key == pygame.K_d and game.mode == "orbit":
                game.satellites.append(Satellite())

    game.update()
    game.draw()

    pygame.display.flip()

pygame.quit()
