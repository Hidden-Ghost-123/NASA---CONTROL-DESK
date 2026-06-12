import pygame
import math

pygame.init()


WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASA Mission Simulator - Hour 2")

clock = pygame.time.Clock()


BLACK = (10, 10, 20)
WHITE = (240, 240, 240)
RED = (255, 80, 80)
GREEN = (80, 255, 120)
BLUE = (80, 150, 255)

font = pygame.font.SysFont("consolas", 20)

def get_sky_color(altitude):
    # 0m = blue sky, high altitude = space black
    t = min(altitude / 50000, 1)
    
    r = int(20 * (1 - t))
    g = int(60 * (1 - t))
    b = int(120 * (1 - t))
    
    return (r, g, b)


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
        self.thrust = 28

    def update(self):
        thrust_force = 0

        # engine + fuel
        if self.engine_on and self.fuel > 0:
            thrust_force = self.thrust
            self.fuel -= 0.05

        # simple atmosphere drag (stronger low down, weaker high up)
        drag = -self.velocity * 0.02 * max(0, 1 - self.altitude / 60000)

        # physics
        self.acceleration = thrust_force - self.gravity + drag
        self.velocity += self.acceleration * 0.05
        self.altitude += self.velocity

        if self.altitude < 0:
            self.altitude = 0
            self.velocity = 0

    def draw(self):
        rocket_y = self.y - int(self.altitude / 6)

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
            flame = 20 + math.sin(pygame.time.get_ticks() * 0.02) * 6
            pygame.draw.polygon(screen, (255, 180, 0), [
                (self.x - 8, rocket_y),
                (self.x + 8, rocket_y),
                (self.x, rocket_y + flame)
            ])


def draw_hud(rocket):
    panel = pygame.Rect(20, 20, 320, 200)
    pygame.draw.rect(screen, (40, 40, 50), panel)
    pygame.draw.rect(screen, GREEN, panel, 2)

    karman = "SPACE" if rocket.altitude > 100000 else "ATMOSPHERE"

    texts = [
        f"ALTITUDE: {rocket.altitude:.0f} m",
        f"VELOCITY: {rocket.velocity:.2f}",
        f"FUEL: {rocket.fuel:.1f}%",
        f"ENGINE: {'ON' if rocket.engine_on else 'OFF'}",
        f"ZONE: {karman}"
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

    # dynamic sky based on altitude
    screen.fill(get_sky_color(rocket.altitude))

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
