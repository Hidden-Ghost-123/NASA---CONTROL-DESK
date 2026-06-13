

import pygame, math, random
pygame.init()

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASA Mission Simulator")
clock = pygame.time.Clock()

WHITE  = (235, 235, 235)
GREEN  = (80,  255, 120)
RED    = (255, 80,  80)
BLUE   = (80,  150, 255)
YELLOW = (255, 220, 80)
ORANGE = (255, 140, 0)
GRAY   = (45,  45,  55)
DARK   = (10,  10,  20)
CYAN   = (80,  220, 255)
DIM    = (22,  22,  38)

font_sm = pygame.font.SysFont("consolas", 16)
font_md = pygame.font.SysFont("consolas", 22)
font_lg = pygame.font.SysFont("consolas", 42)
font_xl = pygame.font.SysFont("consolas", 60)

CENTER = (WIDTH // 2, HEIGHT // 2)

MENU, LAUNCH, ORBIT, WIN, FAIL = "menu","launch","orbit","win","fail"

def sky_color(alt):
    t = min(alt / 80000, 1.0)
    return (max(0,int(20*(1-t))), max(0,int(100*(1-t))), max(0,int(180*(1-t))))

def fmt(t):
    return f"T+{int(t//60):02}:{int(t%60):02}"

def draw_bar(x, y, w, h, val, mx, col, lbl):
    pygame.draw.rect(screen, (25,25,40), (x,y,w,h))
    fill = max(0, int(w * min(val,mx) / mx))
    pygame.draw.rect(screen, col, (x,y,fill,h))
    pygame.draw.rect(screen, WHITE, (x,y,w,h), 1)
    screen.blit(font_sm.render(f"{lbl}  {val:.0f} / {mx:.0f}", True, WHITE), (x, y-20))

class Stars:
    def __init__(self, n=220):
        rng = random.Random(42)
        self.pts = [(rng.randint(0,WIDTH), rng.randint(0,HEIGHT),
                     rng.randint(1,3)) for _ in range(n)]

    def draw(self, alt):
        alpha = min(255, int(255 * alt / 35000))
        if alpha <= 0: return
        for sx, sy, sz in self.pts:
            b = min(255, 110 + sz*40)
            s = pygame.Surface((sz*2+1, sz*2+1), pygame.SRCALPHA)
            s.fill((b, b, b, alpha))
            screen.blit(s, (sx-sz, sy-sz))

class Log:
    def __init__(self):
        self.msgs = []

    def add(self, msg):
        self.msgs.append(msg)
        if len(self.msgs) > 10: self.msgs.pop(0)

    def draw(self, x, y):
        pygame.draw.rect(screen, DIM,   (x,y,420,230))
        pygame.draw.rect(screen, GREEN, (x,y,420,230), 2)
        screen.blit(font_md.render("MISSION LOG", True, GREEN), (x+10, y+8))
        for i, m in enumerate(self.msgs):
            screen.blit(font_sm.render(m, True, WHITE), (x+10, y+38+i*18))


class Rocket:
    ORBIT_R = 185

    def __init__(self, cfg=None):
        cfg = cfg or {}
        self.fuel      = cfg.get("fuel", 100.0)
        self.max_fuel  = cfg.get("fuel", 100.0)
        self.thrust    = cfg.get("thrust", 35)
        self.vel       = 0.0
        self.alt       = 0.0
        self.stage     = 1
        self.engine    = False
        self.eng_fail  = False
        self.fuel_leak = False
        self.orbit_ang = math.pi / 2

    def stage_sep(self, log, t):
        if self.stage == 1:
            self.stage    = 2
            self.thrust  += 15
            bonus         = 30
            self.fuel     = min(self.fuel + bonus, self.max_fuel + bonus)
            self.max_fuel += bonus
            log.add(f"{fmt(t)} Stage Sep — Booster away!")

    def update_launch(self, dt):
        th = self.thrust if (self.engine and self.fuel > 0 and not self.eng_fail) else 0
        if self.engine and not self.eng_fail and self.fuel > 0:
            self.fuel -= 0.5 * dt
        if self.fuel_leak:
            self.fuel -= 0.25 * dt
        self.fuel = max(0.0, self.fuel)

        drag = self.vel * 0.02 * max(0, 1 - self.alt / 60000)
        acc  = th - 9.8 - drag
        self.vel = max(0.0, self.vel + acc * dt)
        self.alt = max(0.0, self.alt + self.vel * dt * 60)

    def update_orbit(self, dt):
        self.orbit_ang += (0.006 + self.stage * 0.001) * dt * 60
        self.fuel       = max(0.0, self.fuel - 0.008 * dt)

    def screen_y(self):
        return max(80, HEIGHT - 100 - int(self.alt / 300))

    def draw_launch(self):
        x  = WIDTH // 2
        y  = self.screen_y()
        bh = 50 if self.stage == 1 else 36

        pygame.draw.rect(screen, WHITE, (x-12, y-bh, 24, bh))
        pygame.draw.polygon(screen, RED,        [(x-12,y-bh),(x+12,y-bh),(x,y-bh-26)])
        pygame.draw.polygon(screen, (160,50,50),[(x-12,y),(x-22,y+14),(x-12,y-12)])
        pygame.draw.polygon(screen, (160,50,50),[(x+12,y),(x+22,y+14),(x+12,y-12)])

        if self.engine and self.fuel > 0 and not self.eng_fail:
            fl  = 22 + math.sin(pygame.time.get_ticks()*0.03)*9
            fl2 = fl * 0.55
            pygame.draw.polygon(screen, ORANGE, [(x-10,y),(x+10,y),(x,y+fl)])
            pygame.draw.polygon(screen, YELLOW, [(x-5, y),(x+5, y),(x,y+fl2)])

        if self.eng_fail:
            w = font_sm.render("!! ENGINE FAIL — Press R !!", True, RED)
            screen.blit(w, (x - w.get_width()//2, y-bh-38))
        if self.fuel_leak:
            screen.blit(font_sm.render("FUEL LEAK", True, ORANGE), (x+20, y-bh+10))

        tgt = HEIGHT - 100 - int(80000/300)
        pygame.draw.line(screen, (0,150,0),(WIDTH-60,tgt),(WIDTH-5,tgt),1)
        screen.blit(font_sm.render("ORBIT ALT",True,GREEN),(WIDTH-120,tgt-18))

    def draw_orbit(self):
        a  = self.orbit_ang
        rx = int(CENTER[0] + math.cos(a)*self.ORBIT_R)
        ry = int(CENTER[1] + math.sin(a)*self.ORBIT_R)
        na = a + math.pi/2
        pts = [
            (rx+math.cos(na)*9,  ry+math.sin(na)*9),
            (rx+math.cos(na+2.4)*5, ry+math.sin(na+2.4)*5),
            (rx+math.cos(na-2.4)*5, ry+math.sin(na-2.4)*5),
        ]
        pygame.draw.polygon(screen, WHITE, [(int(p[0]),int(p[1])) for p in pts])
        return rx, ry

class Satellite:
    def __init__(self):
        self.ang = random.uniform(0, math.pi*2)
        self.r   = random.randint(120, 248)
        self.spd = random.uniform(0.003, 0.008)
        self.col = random.choice([YELLOW, CYAN, GREEN])

    def update(self, dt):
        self.ang += self.spd * dt * 60

    def draw(self):
        x = int(CENTER[0] + math.cos(self.ang)*self.r)
        y = int(CENTER[1] + math.sin(self.ang)*self.r)
        pygame.draw.rect(screen, self.col,       (x-4, y-4, 8, 8))
        pygame.draw.rect(screen, (70,150,70),    (x-14,y-2, 9, 4))
        pygame.draw.rect(screen, (70,150,70),    (x+5, y-2, 9, 4))


class Menu:
    CONTROLS = [
        ("SPACE",  "Toggle engine on / off"),
        ("R",      "Restart engine after failure"),
        ("D",      "Deploy satellite  (orbit only)"),
        ("ENTER",  "Confirm / Restart"),
        ("ESC",    "Quit"),
    ]
    BRIEFING = [
        "Reach 80,000 m altitude to achieve orbit",
        "Stage separation auto-fires at 20 km",
        "Fix engine failures quickly with R",
        "Deploy 3 satellites to complete mission",
        "Fuel is precious — don't waste it!",
    ]

    def draw(self, t):
        screen.fill(DARK)
        rng = random.Random(7)
        for _ in range(200):
            b = rng.randint(60,220)
            pygame.draw.circle(screen,(b,b,b),
                               (rng.randint(0,WIDTH),rng.randint(0,HEIGHT)),1)

        t1 = font_xl.render("NASA  MISSION", True, CYAN)
        t2 = font_xl.render("SIMULATOR",     True, GREEN)
        screen.blit(t1, (WIDTH//2-t1.get_width()//2, 35))
        screen.blit(t2, (WIDTH//2-t2.get_width()//2,105))

        if int(t*2)%2 == 0:
            p = font_lg.render("PRESS  ENTER  TO  LAUNCH", True, YELLOW)
            screen.blit(p, (WIDTH//2-p.get_width()//2, 195))

        # controls box
        cx, cy = 55, 290
        pygame.draw.rect(screen, DIM,  (cx,cy,470,270))
        pygame.draw.rect(screen, CYAN, (cx,cy,470,270),2)
        screen.blit(font_md.render("CONTROLS", True, CYAN),(cx+12,cy+10))
        for i,(k,d) in enumerate(self.CONTROLS):
            ky = cy+48+i*40
            pygame.draw.rect(screen,(50,60,85),(cx+10,ky,100,26))
            pygame.draw.rect(screen,GREEN,     (cx+10,ky,100,26),1)
            screen.blit(font_sm.render(k, True, GREEN),(cx+15,ky+5))
            screen.blit(font_sm.render(d, True, WHITE),(cx+120,ky+5))

        #briefing box
        bx, by = 570, 290
        pygame.draw.rect(screen, DIM,    (bx,by,580,270))
        pygame.draw.rect(screen, YELLOW, (bx,by,580,270),2)
        screen.blit(font_md.render("MISSION BRIEFING",True,YELLOW),(bx+12,by+10))
        for i,line in enumerate(self.BRIEFING):
            screen.blit(font_sm.render(f"  •  {line}",True,WHITE),(bx+15,by+52+i*40))

        # animated rocket
        ry = int(HEIGHT-65-45*abs(math.sin(t*0.95)))
        rx = WIDTH//2
        pygame.draw.rect(screen, WHITE, (rx-10, ry-38, 20, 38))
        pygame.draw.polygon(screen, RED,    [(rx-10,ry-38),(rx+10,ry-38),(rx,ry-62)])
        fl = 14+math.sin(t*6)*5
        pygame.draw.polygon(screen, ORANGE, [(rx-8,ry),(rx+8,ry),(rx,ry+fl)])

class HUD:
    def draw(self, rocket, state, t, sats):
        pygame.draw.rect(screen, DIM,  (15,15,400,310))
        pygame.draw.rect(screen, CYAN, (15,15,400,310),2)
        screen.blit(font_md.render("FLIGHT COMPUTER",True,CYAN),(25,23))
        rows = [
            ("MODE",   state.upper()),
            ("TIME",   fmt(t)),
            ("ALT",    f"{rocket.alt:,.0f} m"),
            ("VEL",    f"{rocket.vel:.1f} m/s"),
            ("STAGE",  str(rocket.stage)),
            ("SATS",   f"{len(sats)} / 3"),
        ]
        for i,(lbl,val) in enumerate(rows):
            y = 60+i*32
            screen.blit(font_sm.render(lbl+":", True, GREEN),(25,  y))
            screen.blit(font_sm.render(val,      True, WHITE),(140, y))
        draw_bar(25,282,360,16, rocket.fuel, rocket.max_fuel, GREEN, "FUEL")
        if state == LAUNCH:
            draw_bar(25,330,360,12, min(rocket.alt,80000), 80000, BLUE, "ORBIT ALT")

class Game:
    def __init__(self):
        self.state   = MENU
        self.rocket  = Rocket()
        self.log     = Log()
        self.hud     = HUD()
        self.menu    = Menu()
        self.stars   = Stars()
        self.sats    = []
        self.t       = 0.0
        self.menu_t  = 0.0
        self.score   = 0

    def reset(self):
        self.__init__()

    def handle(self, e):
        if e.type != pygame.KEYDOWN: return
        k = e.key
        if self.state == MENU:
            if k == pygame.K_RETURN:
                self.state = LAUNCH
                self.log.add("T+00:00  Mission start — Good luck!")
        elif self.state in (LAUNCH, ORBIT):
            if k == pygame.K_SPACE:
                self.rocket.engine = not self.rocket.engine
                self.log.add(f"{fmt(self.t)} Engine {'ON' if self.rocket.engine else 'OFF'}")
            if k == pygame.K_r and self.rocket.eng_fail:
                self.rocket.eng_fail = False
                self.log.add(f"{fmt(self.t)} Engine restarted OK")
            if k == pygame.K_d and self.state == ORBIT:
                self.sats.append(Satellite())
                n = len(self.sats)
                self.log.add(f"{fmt(self.t)} Satellite-{n} deployed")
                if n >= 3:
                    self.score = int(self.rocket.fuel*12 + max(0,900-self.t)*2)
        elif self.state in (WIN, FAIL):
            if k == pygame.K_RETURN:
                self.reset()

    def update(self):
        if self.state not in (LAUNCH, ORBIT):
            if self.state == MENU:
                self.menu_t += clock.get_time()/1000
            return
        dt = clock.get_time()/1000
        self.t += dt

        # Random events
        if random.randint(0,3000)==0 and not self.rocket.eng_fail:
            self.rocket.eng_fail = True
            self.log.add(f"{fmt(self.t)} WARNING — Engine failure!")
        if random.randint(0,4500)==0 and not self.rocket.fuel_leak:
            self.rocket.fuel_leak = True
            self.log.add(f"{fmt(self.t)} WARNING — Fuel leak detected!")

        if self.state == LAUNCH:
            self.rocket.update_launch(dt)
            if self.rocket.alt > 20000 and self.rocket.stage == 1:
                self.rocket.stage_sep(self.log, self.t)
            if self.rocket.alt >= 80000:
                self.state = ORBIT
                self.log.add(f"{fmt(self.t)} *** ORBIT ACHIEVED! ***")
            if self.rocket.fuel <= 0 and self.rocket.alt < 500:
                self.state = FAIL
                self.log.add(f"{fmt(self.t)} FAIL: fuel exhausted on pad")
        elif self.state == ORBIT:
            self.rocket.update_orbit(dt)
            for s in self.sats: s.update(dt)
            if len(self.sats) >= 3:
                self.state = WIN
                self.log.add("*** MISSION SUCCESS! ***")
            if self.rocket.fuel <= 0:
                self.state = FAIL
                self.log.add(f"{fmt(self.t)} FAIL: fuel gone in orbit")

    def draw(self):
        if self.state == MENU:
            self.menu.draw(self.menu_t)
            return

        if self.state == LAUNCH:
            screen.fill(sky_color(self.rocket.alt))
            self.stars.draw(self.rocket.alt)
            pygame.draw.rect(screen, (25,80,25),(0,HEIGHT-80,WIDTH,80))
            self.rocket.draw_launch()
        else:
            screen.fill((5,5,15))
            self.stars.draw(90000)
            pygame.draw.circle(screen,(30,80,160),CENTER,65)
            pygame.draw.circle(screen,(20,150,70),CENTER,65,8)
            pygame.draw.circle(screen,(40,100,180),CENTER,65,2)
            pygame.draw.circle(screen,(0,60,0),CENTER,self.rocket.ORBIT_R,1)
            self.rocket.draw_orbit()
            for s in self.sats: s.draw()

        self.hud.draw(self.rocket, self.state, self.t, self.sats)
        self.log.draw(20, 490)

        if self.state == WIN:
            ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            ov.fill((0,20,0,120)); screen.blit(ov,(0,0))
            m1 = font_lg.render("MISSION  SUCCESS!", True, GREEN)
            m2 = font_md.render(f"Score: {self.score}     Press ENTER to play again", True, YELLOW)
            screen.blit(m1,(WIDTH//2-m1.get_width()//2, HEIGHT//2-50))
            screen.blit(m2,(WIDTH//2-m2.get_width()//2, HEIGHT//2+20))

        if self.state == FAIL:
            ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            ov.fill((30,0,0,130)); screen.blit(ov,(0,0))
            m1 = font_lg.render("MISSION  FAILED", True, RED)
            m2 = font_md.render("Press ENTER to try again", True, WHITE)
            screen.blit(m1,(WIDTH//2-m1.get_width()//2, HEIGHT//2-50))
            screen.blit(m2,(WIDTH//2-m2.get_width()//2, HEIGHT//2+20))


game = Game()
running = True
while running:
    clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: running = False
        game.handle(e)
    game.update()
    game.draw()
    pygame.display.flip()
pygame.quit()
