import pygame
import math

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASA Mission Simulator - Hour 1")

clock = pygame.time.Clock()

BLACK = (10, 10, 20)
WHITE = (240, 240, 240)
RED = (255, 80, 80)
GREEN = (80, 255, 120)
BLUE = (80, 150, 255)
GRAY = (50, 50, 60)


font = pygame.font.SysFont("consolas", 20)


class Rocket:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100

        self.altitude = 0
        self.velocity = 0
        self.acceleration = 0

        self.fuel = 100
        self.engine_on = False

        self.gravity = 9.8
        self.thrust = 25

    def update(self):
        thrust_force = 0

        if self.engine_on and self.fuel > 0:
            thrust_force = self.thrust
            self.fuel -= 0.06

        #simple physics
        self.acceleration = thrust_force - self.gravity
        self.velocity += self.acceleration * 0.05
        self.altitude += self.velocity

        if self.altitude < 0:
            self.altitude = 0
            self.velocity = 0

    def draw(self):
        rocket_y = self.y - int(self.altitude / 5)

        # rocket body
        pygame.draw.rect(screen, WHITE, (self.x - 10, rocket_y - 40, 20, 40))

        # nose
        pygame.draw.polygon(screen, RED, [
            (self.x - 10, rocket_y - 40),
            (self.x + 10, rocket_y - 40),
            (self.x, rocket_y - 60)
        ])

        # flame
        if self.engine_on and self.fuel > 0:
            flame_size = 20 + math.sin(pygame.time.get_ticks() * 0.02) * 6
            pygame.draw.polygon(screen, (255, 180, 0), [
                (self.x - 8, rocket_y),
                (self.x + 8, rocket_y),
                (self.x, rocket_y + flame_size)
            ])


def draw_hud(rocket):
    panel = pygame.Rect(20, 20, 300, 180)
    pygame.draw.rect(screen, GRAY, panel)
    pygame.draw.rect(screen, GREEN, panel, 2)

    texts = [
        f"ALTITUDE: {rocket.altitude:.1f} m",
        f"VELOCITY: {rocket.velocity:.2f}",
        f"FUEL: {rocket.fuel:.1f}%",
        f"ENGINE: {'ON' if rocket.engine_on else 'OFF'}"
    ]

    y = 50
    for t in texts:
        img = font.render(t, True, WHITE)
        screen.blit(img, (40, y))
        y += 30


def draw_ground():
    pygame.draw.rect(screen, BLUE, (0, HEIGHT - 80, WIDTH, 80))


rocket = Rocket()
running = True

while running:
    clock.tick(60)

    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                rocket.engine_on = not rocket.engine_on

    rocket.update()

    draw_ground()
    rocket.draw()
    draw_hud(rocket)

    hint = font.render("SPACE = Toggle Engine", True, GREEN)
    screen.blit(hint, (20, HEIGHT - 40))

    pygame.display.flip()

pygame.quit()
