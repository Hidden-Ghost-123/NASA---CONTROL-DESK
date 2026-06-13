

import pygame, math, random
pygame.init()

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASA Mission Simulator")
clock = pygame.time.Clock()

WHITE  = (235,235,235)
GREEN  = (80, 255,120)
RED    = (255, 80, 80)
BLUE   = (80, 150,255)
YELLOW = (255,220, 80)
ORANGE = (255,140,  0)
GRAY   = (45,  45, 55)
DARK   = (10,  10, 20)
CYAN   = (80, 220,255)
DIM    = (22,  22, 38)
AMBER  = (255,160, 30)

font_sm = pygame.font.SysFont("consolas", 16)
font_md = pygame.font.SysFont("consolas", 22)
font_lg = pygame.font.SysFont("consolas", 42)
font_xl = pygame.font.SysFont("consolas", 60)

CENTER = (WIDTH//2, HEIGHT//2)
MENU, LAUNCH, ORBIT, WIN, FAIL = "menu","launch","orbit","win","fail"

def sky_color(alt):
    t = min(alt/80000,1.0)
    return (max(0,int(20*(1-t))),max(0,int(100*(1-t))),max(0,int(180*(1-t))))

def fmt(t):
    return f"T+{int(t//60):02}:{int(t%60):02}"

def draw_bar(x,y,w,h,val,mx,col,lbl):
    pygame.draw.rect(screen,(25,25,40),(x,y,w,h))
    fill=max(0,int(w*min(val,mx)/mx))
    pygame.draw.rect(screen,col,(x,y,fill,h))
    pygame.draw.rect(screen,WHITE,(x,y,w,h),1)
    screen.blit(font_sm.render(f"{lbl}  {val:.0f}/{mx:.0f}",True,WHITE),(x,y-20))

def angle_diff(a,b):
    """Signed difference between two angles in [-pi, pi]."""
    d = (a - b) % (math.pi*2)
    if d > math.pi: d -= math.pi*2
    return d

class Stars:
    def __init__(self, n=220):
        rng=random.Random(42)
        self.pts=[(rng.randint(0,WIDTH),rng.randint(0,HEIGHT),rng.randint(1,3)) for _ in range(n)]
    def draw(self,alt):
        alpha=min(255,int(255*alt/35000))
        if alpha<=0: return
        for sx,sy,sz in self.pts:
            b=min(255,110+sz*40)
            s=pygame.Surface((sz*2+1,sz*2+1),pygame.SRCALPHA)
            s.fill((b,b,b,alpha))
            screen.blit(s,(sx-sz,sy-sz))

class Log:
    def __init__(self):
        self.msgs=[]
    def add(self,msg):
        self.msgs.append(msg)
        if len(self.msgs)>10: self.msgs.pop(0)
    def draw(self,x,y):
        pygame.draw.rect(screen,DIM,   (x,y,420,230))
        pygame.draw.rect(screen,GREEN, (x,y,420,230),2)
        screen.blit(font_md.render("MISSION LOG",True,GREEN),(x+10,y+8))
        for i,m in enumerate(self.msgs):
            screen.blit(font_sm.render(m,True,WHITE),(x+10,y+38+i*18))

class OrbitalWindow:
    ARC   = 0.7   # radians (~40°) of green zone

    def __init__(self, start_ang, drift_speed):
        self.ang   = start_ang
        self.spd   = drift_speed
        self.ready = True
        self.cool  = 0.0

    def update(self, dt):
        self.ang += self.spd * dt
        if self.cool > 0:
            self.cool -= dt
            if self.cool <= 0:
                self.ready = True

    def contains(self, rocket_ang):
        return self.ready and abs(angle_diff(rocket_ang, self.ang)) < self.ARC/2

    def deploy(self):
        self.ready = False
        self.cool  = 8.0   # 8-second cooldown

    def draw(self, r):
        col   = GREEN if self.ready else (50,70,50)
        steps = 24
        for i in range(steps):
            a1 = self.ang - self.ARC/2 + (i/steps)*self.ARC
            a2 = self.ang - self.ARC/2 + ((i+1)/steps)*self.ARC
            x1 = int(CENTER[0]+math.cos(a1)*r)
            y1 = int(CENTER[1]+math.sin(a1)*r)
            x2 = int(CENTER[0]+math.cos(a2)*r)
            y2 = int(CENTER[1]+math.sin(a2)*r)
            pygame.draw.line(screen, col, (x1,y1),(x2,y2), 5)
        # Centre marker + label
        mx = int(CENTER[0]+math.cos(self.ang)*(r+24))
        my = int(CENTER[1]+math.sin(self.ang)*(r+24))
        if self.ready:
            pygame.draw.circle(screen,GREEN,(mx,my),5)
            screen.blit(font_sm.render("D",True,GREEN),(mx-4,my-8))
        else:
            remaining = max(0,self.cool)
            screen.blit(font_sm.render(f"{remaining:.0f}s",True,GRAY),(mx-8,my-8))

class Debris:
    def __init__(self, n_debris=5):
        self.pieces = []
        rng = random.Random()
        for _ in range(n_debris):
            d = {
                "ang"  : rng.uniform(0, math.pi*2),
                "r"    : rng.randint(112, 258),
                "spd"  : rng.choice([-1,1]) * rng.uniform(0.005, 0.014),
                "sz"   : rng.randint(3,7),
                "shape": [(rng.uniform(-1.5,1.5), rng.uniform(-1.5,1.5)) for _ in range(6)],
            }
            self.pieces.append(d)

    def update(self, dt):
        for d in self.pieces:
            d["ang"] += d["spd"] * dt * 60

    def pos(self, d):
        return (int(CENTER[0]+math.cos(d["ang"])*d["r"]),
                int(CENTER[1]+math.sin(d["ang"])*d["r"]))

    def check_collision(self, rx, ry, kill_r=16, warn_r=44):
        """Returns ('collision'|'warn'|None)."""
        result = None
        for d in self.pieces:
            px,py = self.pos(d)
            dist  = math.hypot(px-rx, py-ry)
            if dist < kill_r:
                return "collision"
            if dist < warn_r:
                result = "warn"
        return result

    def draw(self, rx, ry, warn_r=44):
        for d in self.pieces:
            px,py = self.pos(d)
            dist  = math.hypot(px-rx, py-ry)
            near  = dist < warn_r
            col   = RED if near else (150,110,70)
            sz    = d["sz"]
            pts   = []
            for i,(ox,oy) in enumerate(d["shape"]):
                a = i * math.pi / 3
                pts.append((int(px+math.cos(a)*(sz+ox)),
                             int(py+math.sin(a)*(sz+oy))))
            pygame.draw.polygon(screen, col, pts)
            if near:
                pygame.draw.circle(screen, (200,50,50),(px,py),sz+6,1)

class Rocket:
    ORBIT_R = 185

    def __init__(self, cfg=None):
        cfg           = cfg or {}
        self.fuel     = cfg.get("fuel", 100.0)
        self.max_fuel = cfg.get("fuel", 100.0)
        self.thrust   = cfg.get("thrust", 35)
        self.vel      = 0.0
        self.alt      = 0.0
        self.stage    = 1
        self.engine   = False
        self.throttle = 0.0   # 0→1, ramps up when engine on
        self.eng_fail = False
        self.fuel_leak= False
        self.orbit_ang= math.pi/2

    def stage_sep(self, log, t):
        if self.stage == 1:
            self.stage   = 2
            self.thrust += 15
            bonus        = 30
            self.fuel    = min(self.fuel+bonus, self.max_fuel+bonus)
            self.max_fuel+= bonus
            log.add(f"{fmt(t)} Stage Sep — Booster away!")

    def update_launch(self, dt):
        # Throttle ramp for drama
        if self.engine and not self.eng_fail and self.fuel>0:
            self.throttle = min(1.0, self.throttle + dt*1.2)
        else:
            self.throttle = max(0.0, self.throttle - dt*3.0)

        th = self.thrust * self.throttle if self.fuel>0 else 0
        if self.throttle > 0.05 and self.fuel > 0 and not self.eng_fail:
            self.fuel -= 0.5 * self.throttle * dt
        if self.fuel_leak:
            self.fuel -= 0.22 * dt
        self.fuel = max(0.0, self.fuel)

        drag = self.vel * 0.02 * max(0,1-self.alt/60000)
        acc  = th - 9.8 - drag
        self.vel = max(0.0, self.vel + acc*dt)
        self.alt = max(0.0, self.alt + self.vel*dt*60)

    def update_orbit(self, dt):
        self.orbit_ang += (0.006 + self.stage*0.001)*dt*60
        self.fuel = max(0.0, self.fuel - 0.008*dt)

    def screen_y(self):
        return max(80, HEIGHT-100-int(self.alt/300))

    def draw_launch(self):
        x  = WIDTH//2
        y  = self.screen_y()
        bh = 50 if self.stage==1 else 36
        pygame.draw.rect(screen,WHITE,(x-12,y-bh,24,bh))
        pygame.draw.polygon(screen,RED,    [(x-12,y-bh),(x+12,y-bh),(x,y-bh-26)])
        pygame.draw.polygon(screen,(160,50,50),[(x-12,y),(x-22,y+14),(x-12,y-12)])
        pygame.draw.polygon(screen,(160,50,50),[(x+12,y),(x+22,y+14),(x+12,y-12)])
        if self.throttle > 0.05 and self.fuel>0 and not self.eng_fail:
            fl  = (22+math.sin(pygame.time.get_ticks()*0.03)*9)*self.throttle
            fl2 = fl*0.55
            pygame.draw.polygon(screen,ORANGE,[(x-10,y),(x+10,y),(x,y+fl)])
            pygame.draw.polygon(screen,YELLOW,[(x-5,y),(x+5,y),(x,y+fl2)])
        if self.eng_fail:
            w=font_sm.render("!! ENGINE FAIL — Press R !!",True,RED)
            screen.blit(w,(x-w.get_width()//2,y-bh-38))
        if self.fuel_leak:
            screen.blit(font_sm.render("FUEL LEAK",True,ORANGE),(x+20,y-bh+10))
        tgt=HEIGHT-100-int(80000/300)
        pygame.draw.line(screen,(0,150,0),(WIDTH-60,tgt),(WIDTH-5,tgt),1)
        screen.blit(font_sm.render("ORBIT ALT",True,GREEN),(WIDTH-120,tgt-18))

    def draw_orbit(self):
        a  = self.orbit_ang
        rx = int(CENTER[0]+math.cos(a)*self.ORBIT_R)
        ry = int(CENTER[1]+math.sin(a)*self.ORBIT_R)
        na = a+math.pi/2
        pts=[(rx+math.cos(na)*9,ry+math.sin(na)*9),
             (rx+math.cos(na+2.4)*5,ry+math.sin(na+2.4)*5),
             (rx+math.cos(na-2.4)*5,ry+math.sin(na-2.4)*5)]
        pygame.draw.polygon(screen,WHITE,[(int(p[0]),int(p[1])) for p in pts])
        return rx,ry

class Satellite:
    def __init__(self):
        self.ang=random.uniform(0,math.pi*2)
        self.r  =random.randint(120,248)
        self.spd=random.uniform(0.003,0.008)
        self.col=random.choice([YELLOW,CYAN,GREEN])
    def update(self,dt): self.ang+=self.spd*dt*60
    def draw(self):
        x=int(CENTER[0]+math.cos(self.ang)*self.r)
        y=int(CENTER[1]+math.sin(self.ang)*self.r)
        pygame.draw.rect(screen,self.col,   (x-4,y-4,8,8))
        pygame.draw.rect(screen,(70,150,70),(x-14,y-2,9,4))
        pygame.draw.rect(screen,(70,150,70),(x+5, y-2,9,4))

class Menu:
    CONTROLS=[
        ("SPACE",  "Toggle engine on / off"),
        ("R",      "Restart engine after failure"),
        ("D",      "Deploy satellite  (in green window!)"),
        ("ENTER",  "Confirm / Restart"),
        ("ESC",    "Quit"),
    ]
    BRIEFING=[
        "Reach 80,000 m altitude to achieve orbit",
        "Stage separation auto-fires at 20 km",
        "Deploy in GREEN WINDOWS only  (timing!)",
        "Dodge debris — collision = mission lost",
        "Fuel is precious — don't waste it!",
    ]
    def draw(self,t):
        screen.fill(DARK)
        rng=random.Random(7)
        for _ in range(200):
            b=rng.randint(60,220)
            pygame.draw.circle(screen,(b,b,b),(rng.randint(0,WIDTH),rng.randint(0,HEIGHT)),1)
        t1=font_xl.render("NASA  MISSION",True,CYAN)
        t2=font_xl.render("SIMULATOR",    True,GREEN)
        screen.blit(t1,(WIDTH//2-t1.get_width()//2,35))
        screen.blit(t2,(WIDTH//2-t2.get_width()//2,105))
        if int(t*2)%2==0:
            p=font_lg.render("PRESS  ENTER  TO  LAUNCH",True,YELLOW)
            screen.blit(p,(WIDTH//2-p.get_width()//2,198))
        cx,cy=55,292
        pygame.draw.rect(screen,DIM,  (cx,cy,470,270))
        pygame.draw.rect(screen,CYAN, (cx,cy,470,270),2)
        screen.blit(font_md.render("CONTROLS",True,CYAN),(cx+12,cy+10))
        for i,(k,d) in enumerate(self.CONTROLS):
            ky=cy+48+i*40
            pygame.draw.rect(screen,(50,60,85),(cx+10,ky,100,26))
            pygame.draw.rect(screen,GREEN,     (cx+10,ky,100,26),1)
            screen.blit(font_sm.render(k,True,GREEN),(cx+15,ky+5))
            screen.blit(font_sm.render(d,True,WHITE),(cx+120,ky+5))
        bx,by=570,292
        pygame.draw.rect(screen,DIM,   (bx,by,580,270))
        pygame.draw.rect(screen,YELLOW,(bx,by,580,270),2)
        screen.blit(font_md.render("MISSION BRIEFING",True,YELLOW),(bx+12,by+10))
        for i,line in enumerate(self.BRIEFING):
            screen.blit(font_sm.render(f"  •  {line}",True,WHITE),(bx+15,by+52+i*40))
        ry=int(HEIGHT-65-45*abs(math.sin(t*0.95)))
        rx=WIDTH//2
        pygame.draw.rect(screen,WHITE,(rx-10,ry-38,20,38))
        pygame.draw.polygon(screen,RED,   [(rx-10,ry-38),(rx+10,ry-38),(rx,ry-62)])
        fl=14+math.sin(t*6)*5
        pygame.draw.polygon(screen,ORANGE,[(rx-8,ry),(rx+8,ry),(rx,ry+fl)])

class HUD:
    def draw(self,rocket,state,t,sats):
        pygame.draw.rect(screen,DIM, (15,15,400,310))
        pygame.draw.rect(screen,CYAN,(15,15,400,310),2)
        screen.blit(font_md.render("FLIGHT COMPUTER",True,CYAN),(25,23))
        rows=[("MODE",state.upper()),("TIME",fmt(t)),
              ("ALT",f"{rocket.alt:,.0f} m"),("VEL",f"{rocket.vel:.1f} m/s"),
              ("STAGE",str(rocket.stage)),("SATS",f"{len(sats)} / 3")]
        for i,(lbl,val) in enumerate(rows):
            y=60+i*32
            screen.blit(font_sm.render(lbl+":",True,GREEN),(25, y))
            screen.blit(font_sm.render(val,    True,WHITE),(140,y))
        draw_bar(25,282,360,16,rocket.fuel,rocket.max_fuel,GREEN,"FUEL")
        if state==LAUNCH:
            draw_bar(25,330,360,12,min(rocket.alt,80000),80000,BLUE,"ORBIT ALT")

    def draw_orbit_panel(self, windows, rocket_ang, warn):
        """Right-side panel: window status and debris warning."""
        px,py,pw,ph = WIDTH-280,15,265,200
        pygame.draw.rect(screen,DIM,  (px,py,pw,ph))
        pygame.draw.rect(screen,AMBER,(px,py,pw,ph),2)
        screen.blit(font_md.render("ORBIT STATUS",True,AMBER),(px+10,py+8))
        in_window=any(w.contains(rocket_ang) for w in windows)
        if in_window:
            msg=font_md.render(">>> DEPLOY NOW <<<",True,GREEN)
            screen.blit(msg,(px+10,py+44))
        else:
            screen.blit(font_sm.render("Align with green window",True,GRAY),(px+10,py+48))
        for i,w in enumerate(windows):
            status="OPEN" if w.ready else f"COOL {max(0,w.cool):.0f}s"
            col   =GREEN if w.ready else GRAY
            screen.blit(font_sm.render(f"Window {i+1}: {status}",True,col),(px+10,py+80+i*28))
        if warn:
            wt=font_md.render("!! DEBRIS NEAR !!",True,RED)
            screen.blit(wt,(px+10,py+170))

class Game:
    def __init__(self):
        self.state    = MENU
        self.rocket   = Rocket()
        self.log      = Log()
        self.hud      = HUD()
        self.menu_scr = Menu()
        self.stars    = Stars()
        self.sats     = []
        self.windows  = [
            OrbitalWindow(0.0,        0.0018),
            OrbitalWindow(math.pi*2/3, 0.0012),
            OrbitalWindow(math.pi*4/3, 0.0022),
        ]
        self.debris   = Debris(5)
        self.t        = 0.0
        self.menu_t   = 0.0
        self.score    = 0
        self.fail_msg = "Unknown"
        self.debris_warn = False
        # Score components
        self.s_fuel  = 0
        self.s_time  = 0
        self.s_sat   = 0

    def reset(self): self.__init__()

    def handle(self,e):
        if e.type!=pygame.KEYDOWN: return
        k=e.key
        if self.state==MENU:
            if k==pygame.K_RETURN:
                self.state=LAUNCH
                self.log.add("T+00:00  Mission start!")
        elif self.state in (LAUNCH,ORBIT):
            if k==pygame.K_SPACE:
                self.rocket.engine=not self.rocket.engine
                self.log.add(f"{fmt(self.t)} Engine {'ON' if self.rocket.engine else 'OFF'}")
            if k==pygame.K_r and self.rocket.eng_fail:
                self.rocket.eng_fail=False
                self.log.add(f"{fmt(self.t)} Engine restarted")
            if k==pygame.K_d and self.state==ORBIT:
                in_win=any(w.contains(self.rocket.orbit_ang) for w in self.windows)
                if in_win:
                    for w in self.windows:
                        if w.contains(self.rocket.orbit_ang):
                            w.deploy(); break
                    self.sats.append(Satellite())
                    n=len(self.sats)
                    self.log.add(f"{fmt(self.t)} Satellite-{n} deployed!")
                    if n>=3:
                        self.s_fuel=int(self.rocket.fuel*12)
                        self.s_time=int(max(0,900-self.t)*2)
                        self.s_sat =300
                        self.score =self.s_fuel+self.s_time+self.s_sat
                else:
                    self.log.add(f"{fmt(self.t)} Not in deploy window!")
        elif self.state in (WIN,FAIL):
            if k==pygame.K_RETURN: self.reset()

    def update(self):
        if self.state not in (LAUNCH,ORBIT):
            if self.state==MENU: self.menu_t+=clock.get_time()/1000
            return
        dt=clock.get_time()/1000
        self.t+=dt
        if random.randint(0,3500)==0 and not self.rocket.eng_fail:
            self.rocket.eng_fail=True
            self.log.add(f"{fmt(self.t)} WARNING — Engine failure!")
        if random.randint(0,5000)==0 and not self.rocket.fuel_leak:
            self.rocket.fuel_leak=True
            self.log.add(f"{fmt(self.t)} WARNING — Fuel leak!")
        if self.state==LAUNCH:
            self.rocket.update_launch(dt)
            if self.rocket.alt>20000 and self.rocket.stage==1:
                self.rocket.stage_sep(self.log,self.t)
            if self.rocket.alt>=80000:
                self.state=ORBIT
                self.log.add(f"{fmt(self.t)} *** ORBIT ACHIEVED! ***")
            if self.rocket.fuel<=0 and self.rocket.alt<500:
                self.state=FAIL
                self.fail_msg="Fuel exhausted on launch pad"
        elif self.state==ORBIT:
            self.rocket.update_orbit(dt)
            for w in self.windows: w.update(dt)
            self.debris.update(dt)
            for s in self.sats: s.update(dt)
            rx,ry=self.rocket.draw_orbit.__func__  # just get pos
            # get actual rocket screen position for collision
            a  =self.rocket.orbit_ang
            crx=int(CENTER[0]+math.cos(a)*self.rocket.ORBIT_R)
            cry=int(CENTER[1]+math.sin(a)*self.rocket.ORBIT_R)
            result=self.debris.check_collision(crx,cry)
            self.debris_warn = (result=="warn")
            if result=="collision":
                self.state=FAIL
                self.fail_msg="Debris collision"
            if len(self.sats)>=3:
                self.state=WIN
                self.log.add("*** MISSION SUCCESS! ***")
            if self.rocket.fuel<=0:
                self.state=FAIL
                self.fail_msg="Fuel exhausted in orbit"

    def draw(self):
        if self.state==MENU:
            self.menu_scr.draw(self.menu_t)
            return

        # Debris warning edge pulse
        if self.state==ORBIT and self.debris_warn:
            ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            ov.fill((180,0,0,int(40+30*math.sin(pygame.time.get_ticks()*0.01))))
            screen.blit(ov,(0,0))

        if self.state==LAUNCH:
            screen.fill(sky_color(self.rocket.alt))
            self.stars.draw(self.rocket.alt)
            pygame.draw.rect(screen,(25,80,25),(0,HEIGHT-80,WIDTH,80))
            self.rocket.draw_launch()
        else:
            screen.fill((5,5,15))
            self.stars.draw(90000)
            # Earth
            pygame.draw.circle(screen,(30,80,160),CENTER,65)
            pygame.draw.circle(screen,(20,150,70),CENTER,65,8)
            pygame.draw.circle(screen,(40,100,180),CENTER,65,2)
            # Orbit ring (drawn before windows so windows appear on top)
            pygame.draw.circle(screen,(20,40,20),CENTER,self.rocket.ORBIT_R,1)
            # Windows
            for w in self.windows: w.draw(self.rocket.ORBIT_R)
            # Debris
            a  =self.rocket.orbit_ang
            crx=int(CENTER[0]+math.cos(a)*self.rocket.ORBIT_R)
            cry=int(CENTER[1]+math.sin(a)*self.rocket.ORBIT_R)
            self.debris.draw(crx,cry)
            # Rocket
            self.rocket.draw_orbit()
            for s in self.sats: s.draw()

        self.hud.draw(self.rocket,self.state,self.t,self.sats)
        self.log.draw(20,490)
        if self.state==ORBIT:
            self.hud.draw_orbit_panel(self.windows, self.rocket.orbit_ang, self.debris_warn)

        if self.state==WIN:
            ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            ov.fill((0,20,0,120)); screen.blit(ov,(0,0))
            m1=font_lg.render("MISSION  SUCCESS!",True,GREEN)
            screen.blit(m1,(WIDTH//2-m1.get_width()//2,HEIGHT//2-80))
            lines=[
                (f"Fuel bonus:  {self.s_fuel}",  CYAN),
                (f"Time bonus:  {self.s_time}",  YELLOW),
                (f"Sat bonus:   {self.s_sat}",   GREEN),
                (f"TOTAL SCORE: {self.score}",   WHITE),
                ("Press ENTER to play again",    GRAY),
            ]
            for i,(txt,col) in enumerate(lines):
                s=font_md.render(txt,True,col)
                screen.blit(s,(WIDTH//2-s.get_width()//2,HEIGHT//2-20+i*34))

        if self.state==FAIL:
            ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            ov.fill((30,0,0,130)); screen.blit(ov,(0,0))
            m1=font_lg.render("MISSION  FAILED",True,RED)
            m2=font_md.render(self.fail_msg,True,AMBER)
            m3=font_md.render("Press ENTER to try again",True,WHITE)
            screen.blit(m1,(WIDTH//2-m1.get_width()//2,HEIGHT//2-60))
            screen.blit(m2,(WIDTH//2-m2.get_width()//2,HEIGHT//2+10))
            screen.blit(m3,(WIDTH//2-m3.get_width()//2,HEIGHT//2+55))

game=Game()
running=True
while running:
    clock.tick(60)
    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False
        if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: running=False
        game.handle(e)
    game.update()
    game.draw()
    pygame.display.flip()
pygame.quit()
