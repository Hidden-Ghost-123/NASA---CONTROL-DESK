import pygame
import math
import random

pygame.init()

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASA Mission Simulator - Hour 4")

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
font_big = pygame.font.SysFont("consolas", 32)

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

    def update_launch(self):
        thrust = 0
        if self.engine and self.fuel > 0:
            thrust = self.thrust
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

        if self.engine and self.fuel > 0:
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


rocket = Rocket()
satellites = []
log = MissionLog()

mode = "launch"
t = 0

log.add("T+00:00 Launch Ready")

running = True
while running:
    dt = clock.tick(60) / 1000
    t += dt

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.KEYDOWN:

            if e.key == pygame.K_SPACE:
                rocket.engine = not rocket.engine
                log.add(f"{format_time(t)} Engine Toggle")

            if e.key == pygame.K_m:
                if rocket.altitude > 80000:
                    mode = "orbit"
                    rocket.enter_orbit()
                    log.add(f"{format_time(t)} Orbit Mode Activated")

            if e.key == pygame.K_d and mode == "orbit":
                satellites.append(Satellite())
                log.add(f"{format_time(t)} Satellite Deployed")

    if mode == "launch":
        rocket.update_launch()

        if rocket.altitude > 100 and rocket.engine:
            log.add(f"{format_time(t)} Liftoff")

        screen.fill(sky_color(rocket.altitude))
        pygame.draw.rect(screen, BLUE, (0, HEIGHT - 80, WIDTH, 80))

        rocket.draw_launch()

        panel = pygame.Rect(20, 20, 420, 360)
        pygame.draw.rect(screen, GRAY, panel)
        pygame.draw.rect(screen, GREEN, panel, 2)

        stats = [
            f"MODE: LAUNCH",
            f"ALT: {rocket.altitude:.0f} m",
            f"VEL: {rocket.velocity:.1f}",
            f"FUEL: {rocket.fuel:.1f}%",
            f"ENGINE: {rocket.engine}"
        ]

        y = 60
        for s in stats:
            screen.blit(font_small.render(s, True, WHITE), (30, y))
            y += 28

        hint = font_small.render("SPACE toggle engine", True, GREEN)
        screen.blit(hint, (20, HEIGHT - 30))

    else:
        screen.fill((5, 5, 15))

        pygame.draw.circle(screen, BLUE, CENTER, 60)

        rocket.update_orbit()
        rocket.draw_orbit()

        for s in satellites:
            s.update()
            s.draw()

        panel = pygame.Rect(20, 20, 420, 360)
        pygame.draw.rect(screen, GRAY, panel)
        pygame.draw.rect(screen, GREEN, panel, 2)

        stats = [
            f"MODE: ORBIT",
            f"SATELLITES: {len(satellites)}",
            f"ORBIT ANGLE: {rocket.orbit_angle:.2f}"
        ]

        y = 60
        for s in stats:
            screen.blit(font_small.render(s, True, WHITE), (30, y))
            y += 28

        hint = font_small.render("D deploy satellite | M orbit mode", True, GREEN)
        screen.blit(hint, (20, HEIGHT - 30))

    log.draw()

    pygame.display.flip()

pygame.quit()
