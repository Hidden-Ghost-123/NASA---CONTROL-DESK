#final

import pygame, math, random
pygame.init()

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASA Mission Simulator")
clock  = pygame.time.Clock()

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
PINK   = (255,120,180)

font_sm = pygame.font.SysFont("consolas", 16)
font_md = pygame.font.SysFont("consolas", 22)
font_lg = pygame.font.SysFont("consolas", 42)
font_xl = pygame.font.SysFont("consolas", 58)

CENTER = (WIDTH//2, HEIGHT//2)

MENU, MISSION_SELECT, LAUNCH, ORBIT, WIN, FAIL = \
    "menu","mission_select","launch","orbit","win","fail"

MISSIONS = {
    "STANDARD": {
        "fuel":10.0, "thrust":35, "debris":5,
        "fail_rate":3500, "leak_rate":5000,
        "desc":["Normal fuel load and hazard rates",
                "Good mission to learn the ropes",
                "Time bonus: ×2"],
        "time_mult":2, "fuel_mult":12,
    },
    "EXPRESS": {
        "fuel":70.0, "thrust":42, "debris":4,
        "fail_rate":6000, "leak_rate":9000,
        "desc":["Lighter fuel load — must be efficient",
                "Fewer failures, big time bonus",
                "Time bonus: ×4  |  Fuel bonus: ×18"],
        "time_mult":4, "fuel_mult":18,
    },
    "DEBRIS STORM": {
        "fuel":100.0, "thrust":35, "debris":9,
        "fail_rate":2500, "leak_rate":3500,
        "desc":["9 debris pieces — orbit is a minefield",
                "High failure + leak rates",
                "Biggest score multiplier if you survive"],
        "time_mult":3, "fuel_mult":15,
    },
}
MISSION_KEYS = list(MISSIONS.keys())

high_scores: dict[str, list[int]] = {k: [] for k in MISSION_KEYS}

def record_score(mission: str, score: int):
    hs = high_scores[mission]
    hs.append(score)
    hs.sort(reverse=True)
    high_scores[mission] = hs[:5]

def sky_color(alt):
    t=min(alt/80000,1.0)
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
    d=(a-b)%(math.pi*2)
    if d>math.pi: d-=math.pi*2
    return d

class Shake:
    def __init__(self):
        self.mag=0.0
        self.decay=8.0

    def trigger(self, magnitude=8.0):
        self.mag=max(self.mag, magnitude)

    def update(self, dt):
        self.mag=max(0.0, self.mag-self.decay*dt)

    def offset(self):
        if self.mag<0.5: return (0,0)
        return (int(random.uniform(-self.mag,self.mag)),
                int(random.uniform(-self.mag,self.mag)))

shake = Shake()

class Particle:
    __slots__=["x","y","vx","vy","life","max_life","col","sz"]
    def __init__(self,x,y,vx,vy,life,col,sz=2):
        self.x,self.y=float(x),float(y)
        self.vx,self.vy=vx,vy
        self.life=life; self.max_life=life
        self.col=col; self.sz=sz

class Particles:
    def __init__(self):
        self.pool: list[Particle]=[]

    def emit(self, x, y, n, vx_range, vy_range, life_range, colors, sz=2):
        for _ in range(n):
            vx=random.uniform(*vx_range)
            vy=random.uniform(*vy_range)
            li=random.uniform(*life_range)
            col=random.choice(colors)
            self.pool.append(Particle(x,y,vx,vy,li,col,sz))

    def burst(self, x, y, n, speed, colors, sz=3):
        for _ in range(n):
            a=random.uniform(0,math.pi*2)
            v=random.uniform(0,speed)
            self.pool.append(Particle(x,y,math.cos(a)*v,math.sin(a)*v,
                                       random.uniform(0.3,1.0),random.choice(colors),sz))

    def update(self, dt):
        alive=[]
        for p in self.pool:
            p.life-=dt
            if p.life<=0: continue
            p.x+=p.vx*dt*60
            p.y+=p.vy*dt*60
            p.vy+=0.8*dt       # slight gravity pull
            alive.append(p)
        self.pool=alive

    def draw(self):
        for p in self.pool:
            alpha=int(255*(p.life/p.max_life))
            r,g,b=p.col
            c=(min(255,r),min(255,g),min(255,b))
            sz=max(1,int(p.sz*(p.life/p.max_life)))
            s=pygame.Surface((sz*2,sz*2),pygame.SRCALPHA)
            s.fill((c[0],c[1],c[2],alpha))
            screen.blit(s,(int(p.x)-sz,int(p.y)-sz))

particles = Particles()

class Stars:
    def __init__(self,n=220):
        rng=random.Random(42)
        self.pts=[(rng.randint(0,WIDTH),rng.randint(0,HEIGHT),rng.randint(1,3)) for _ in range(n)]
    def draw(self,alt):
        alpha=min(255,int(255*alt/35000))
        if alpha<=0: return
        for sx,sy,sz in self.pts:
            b=min(255,110+sz*40)
            s=pygame.Surface((sz*2+1,sz*2+1),pygame.SRCALPHA)
            s.fill((b,b,b,alpha)); screen.blit(s,(sx-sz,sy-sz))

class Log:
    def __init__(self):
        self.msgs=[]
    def add(self,msg):
        self.msgs.append(msg)
        if len(self.msgs)>10: self.msgs.pop(0)
    def draw(self,x,y):
        pygame.draw.rect(screen,DIM,  (x,y,420,230))
        pygame.draw.rect(screen,GREEN,(x,y,420,230),2)
        screen.blit(font_md.render("MISSION LOG",True,GREEN),(x+10,y+8))
        for i,m in enumerate(self.msgs):
            screen.blit(font_sm.render(m,True,WHITE),(x+10,y+38+i*18))

class OrbitalWindow:
    ARC=0.7
    def __init__(self,start_ang,drift_spd):
        self.ang=start_ang; self.spd=drift_spd
        self.ready=True; self.cool=0.0; self.ping=0.0
    def update(self,dt):
        self.ang+=self.spd*dt
        if self.ping>0: self.ping-=dt
        if self.cool>0:
            self.cool-=dt
            if self.cool<=0:
                self.ready=True; self.ping=0.8
    def contains(self,rang):
        return self.ready and abs(angle_diff(rang,self.ang))<self.ARC/2
    def deploy(self):
        self.ready=False; self.cool=8.0
    def draw(self,r):
        col=GREEN if self.ready else (50,70,50)
        # Ping flash ring
        if self.ping>0:
            pr=r+8+int((1-self.ping/0.8)*18)
            pa=int(180*self.ping/0.8)
            sx=int(CENTER[0]+math.cos(self.ang)*pr)
            sy=int(CENTER[1]+math.sin(self.ang)*pr)
            ps=pygame.Surface((pr*2,pr*2),pygame.SRCALPHA)
            pygame.draw.circle(ps,(80,255,120,pa),(pr,pr),10,2)
            screen.blit(ps,(sx-pr,sy-pr))
        steps=24
        for i in range(steps):
            a1=self.ang-self.ARC/2+(i/steps)*self.ARC
            a2=self.ang-self.ARC/2+((i+1)/steps)*self.ARC
            x1=int(CENTER[0]+math.cos(a1)*r); y1=int(CENTER[1]+math.sin(a1)*r)
            x2=int(CENTER[0]+math.cos(a2)*r); y2=int(CENTER[1]+math.sin(a2)*r)
            pygame.draw.line(screen,col,(x1,y1),(x2,y2),5)
        mx=int(CENTER[0]+math.cos(self.ang)*(r+24))
        my=int(CENTER[1]+math.sin(self.ang)*(r+24))
        if self.ready:
            pygame.draw.circle(screen,GREEN,(mx,my),5)
            screen.blit(font_sm.render("D",True,GREEN),(mx-4,my-8))
        else:
            screen.blit(font_sm.render(f"{max(0,self.cool):.0f}s",True,GRAY),(mx-8,my-8))

class Debris:
    def __init__(self,n=5):
        self.pieces=[]
        rng=random.Random()
        for _ in range(n):
            self.pieces.append({
                "ang" :rng.uniform(0,math.pi*2),
                "r"   :rng.randint(112,260),
                "spd" :rng.choice([-1,1])*rng.uniform(0.005,0.014),
                "sz"  :rng.randint(3,7),
                "shape":[(rng.uniform(-1.5,1.5),rng.uniform(-1.5,1.5)) for _ in range(6)],
            })
    def update(self,dt):
        for d in self.pieces: d["ang"]+=d["spd"]*dt*60
    def pos(self,d):
        return (int(CENTER[0]+math.cos(d["ang"])*d["r"]),
                int(CENTER[1]+math.sin(d["ang"])*d["r"]))
    def check(self,rx,ry,kill=16,warn=44):
        closest=9999
        for d in self.pieces:
            px,py=self.pos(d)
            dist=math.hypot(px-rx,py-ry)
            closest=min(closest,dist)
            if dist<kill: return "collision",dist
        return ("warn" if closest<warn else None),closest
    def draw(self,rx,ry,warn_r=44):
        for d in self.pieces:
            px,py=self.pos(d)
            dist=math.hypot(px-rx,py-ry)
            near=dist<warn_r
            col=RED if near else (150,110,70)
            sz=d["sz"]
            pts=[(int(px+math.cos(i*math.pi/3)*(sz+d["shape"][i][0])),
                   int(py+math.sin(i*math.pi/3)*(sz+d["shape"][i][1])))
                 for i in range(6)]
            pygame.draw.polygon(screen,col,pts)
            if near:
                pygame.draw.circle(screen,(200,50,50),(px,py),sz+6,1)

class Rocket:
    ORBIT_R=185
    def __init__(self,cfg):
        self.fuel     =cfg["fuel"]
        self.max_fuel =cfg["fuel"]
        self.thrust   =cfg["thrust"]
        self.vel      =0.0; self.alt=0.0; self.stage=1
        self.engine   =False; self.throttle=0.0
        self.eng_fail =False; self.fuel_leak=False
        self.orbit_ang=math.pi/2

    def stage_sep(self,log,t):
        if self.stage==1:
            self.stage=2; self.thrust+=15
            bonus=30
            self.fuel=min(self.fuel+bonus,self.max_fuel+bonus)
            self.max_fuel+=bonus
            log.add(f"{fmt(t)} Stage Sep — Booster away!")
            shake.trigger(12)
            # Burst of sparks
            x=WIDTH//2; y=HEIGHT-100-int(self.alt/300)
            particles.burst(x,y+40,30,5,[WHITE,YELLOW,ORANGE],3)

    def update_launch(self,dt,fail_rate,leak_rate):
        if self.engine and not self.eng_fail and self.fuel>0:
            self.throttle=min(1.0,self.throttle+dt*1.2)
        else:
            self.throttle=max(0.0,self.throttle-dt*3.0)
        th=self.thrust*self.throttle if self.fuel>0 else 0
        if self.throttle>0.05 and self.fuel>0 and not self.eng_fail:
            self.fuel-=0.5*self.throttle*dt
            # Emit exhaust particles
            x=WIDTH//2; y=self.screen_y()
            if random.randint(0,2)==0:
                particles.emit(x,y+2,2,(-0.4,0.4),(1.5,3.5),(0.2,0.6),
                               [ORANGE,YELLOW,(255,100,0)])
        if self.fuel_leak: self.fuel-=0.22*dt
        self.fuel=max(0.0,self.fuel)
        drag=self.vel*0.02*max(0,1-self.alt/60000)
        self.vel=max(0.0,self.vel+(self.thrust*self.throttle-9.8-drag)*dt)
        self.alt=max(0.0,self.alt+self.vel*dt*60)

    def update_orbit(self,dt):
        self.orbit_ang+=(0.006+self.stage*0.001)*dt*60
        self.fuel=max(0.0,self.fuel-0.008*dt)

    def screen_y(self): return max(80,HEIGHT-100-int(self.alt/300))

    def draw_launch(self):
        x=WIDTH//2; y=self.screen_y()
        bh=50 if self.stage==1 else 36
        pygame.draw.rect(screen,WHITE,(x-12,y-bh,24,bh))
        pygame.draw.polygon(screen,RED,[(x-12,y-bh),(x+12,y-bh),(x,y-bh-26)])
        pygame.draw.polygon(screen,(160,50,50),[(x-12,y),(x-22,y+14),(x-12,y-12)])
        pygame.draw.polygon(screen,(160,50,50),[(x+12,y),(x+22,y+14),(x+12,y-12)])
        if self.throttle>0.05 and self.fuel>0 and not self.eng_fail:
            fl=(22+math.sin(pygame.time.get_ticks()*0.03)*9)*self.throttle
            pygame.draw.polygon(screen,ORANGE,[(x-10,y),(x+10,y),(x,y+fl)])
            pygame.draw.polygon(screen,YELLOW,[(x-5,y),(x+5,y),(x,y+fl*0.55)])
        if self.eng_fail:
            w=font_sm.render("!! ENGINE FAIL — Press R !!",True,RED)
            screen.blit(w,(x-w.get_width()//2,y-bh-38))
        if self.fuel_leak:
            screen.blit(font_sm.render("FUEL LEAK",True,ORANGE),(x+20,y-bh+10))
        tgt=HEIGHT-100-int(80000/300)
        pygame.draw.line(screen,(0,150,0),(WIDTH-60,tgt),(WIDTH-5,tgt),1)
        screen.blit(font_sm.render("ORBIT ALT",True,GREEN),(WIDTH-120,tgt-18))

    def draw_orbit(self):
        a=self.orbit_ang
        rx=int(CENTER[0]+math.cos(a)*self.ORBIT_R)
        ry=int(CENTER[1]+math.sin(a)*self.ORBIT_R)
        na=a+math.pi/2
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
        pygame.draw.rect(screen,(70,150,70),(x+5,y-2,9,4))

class MenuScreen:
    CONTROLS=[
        ("SPACE",  "Toggle engine on / off"),
        ("R",      "Restart engine after failure"),
        ("D",      "Deploy satellite (green window!)"),
        ("ENTER",  "Confirm / Restart"),
        ("H",      "View high scores"),
        ("ESC",    "Quit"),
    ]
    def draw(self,t,show_scores):
        screen.fill(DARK)
        rng=random.Random(7)
        for _ in range(200):
            b=rng.randint(60,220)
            pygame.draw.circle(screen,(b,b,b),(rng.randint(0,WIDTH),rng.randint(0,HEIGHT)),1)
        t1=font_xl.render("NASA  MISSION",True,CYAN)
        t2=font_xl.render("SIMULATOR",   True,GREEN)
        screen.blit(t1,(WIDTH//2-t1.get_width()//2,30))
        screen.blit(t2,(WIDTH//2-t2.get_width()//2,100))
        if not show_scores:
            if int(t*2)%2==0:
                p=font_lg.render("PRESS  ENTER  TO  LAUNCH",True,YELLOW)
                screen.blit(p,(WIDTH//2-p.get_width()//2,192))
            cx,cy=55,280
            pygame.draw.rect(screen,DIM, (cx,cy,470,300))
            pygame.draw.rect(screen,CYAN,(cx,cy,470,300),2)
            screen.blit(font_md.render("CONTROLS",True,CYAN),(cx+12,cy+10))
            for i,(k,d) in enumerate(self.CONTROLS):
                ky=cy+45+i*38
                pygame.draw.rect(screen,(50,60,85),(cx+10,ky,95,26))
                pygame.draw.rect(screen,GREEN,     (cx+10,ky,95,26),1)
                screen.blit(font_sm.render(k,True,GREEN),(cx+15,ky+5))
                screen.blit(font_sm.render(d,True,WHITE),(cx+118,ky+5))
            bx,by=570,280
            pygame.draw.rect(screen,DIM,   (bx,by,580,300))
            pygame.draw.rect(screen,YELLOW,(bx,by,580,300),2)
            screen.blit(font_md.render("MISSION OBJECTIVES",True,YELLOW),(bx+12,by+10))
            tips=["Reach 80,000 m to achieve orbit",
                  "Stage separation auto-fires at 20 km",
                  "Deploy in GREEN WINDOWS only — timing!",
                  "Dodge debris — collision ends mission",
                  "Fix engine failures fast with R",
                  "Fuel is precious — every drop counts!"]
            for i,line in enumerate(tips):
                screen.blit(font_sm.render(f"  •  {line}",True,WHITE),(bx+15,by+48+i*38))
        else:
            # score view
            hx,hy=200,220
            pygame.draw.rect(screen,DIM,   (hx,hy,800,400))
            pygame.draw.rect(screen,AMBER, (hx,hy,800,400),2)
            screen.blit(font_md.render("HIGH SCORES  (Session)",True,AMBER),(hx+12,hy+10))
            col_x=[hx+20, hx+270, hx+520]
            for ci,mname in enumerate(MISSION_KEYS):
                cx2=col_x[ci]
                pygame.draw.rect(screen,(30,30,50),(cx2,hy+46,230,310))
                pygame.draw.rect(screen,CYAN,      (cx2,hy+46,230,310),1)
                screen.blit(font_sm.render(mname,True,CYAN),(cx2+6,hy+52))
                scores=high_scores[mname]
                if not scores:
                    screen.blit(font_sm.render("No runs yet",True,GRAY),(cx2+6,hy+80))
                for si,sc in enumerate(scores):
                    col=YELLOW if si==0 else WHITE
                    screen.blit(font_sm.render(f"{si+1}. {sc:,}",True,col),(cx2+6,hy+80+si*38))
            screen.blit(font_sm.render("Press H to go back",True,GRAY),(hx+12,hy+360))
        ry=int(HEIGHT-65-45*abs(math.sin(t*0.95)))
        rx=WIDTH//2
        pygame.draw.rect(screen,WHITE,(rx-10,ry-38,20,38))
        pygame.draw.polygon(screen,RED,   [(rx-10,ry-38),(rx+10,ry-38),(rx,ry-62)])
        fl=14+math.sin(t*6)*5
        pygame.draw.polygon(screen,ORANGE,[(rx-8,ry),(rx+8,ry),(rx,ry+fl)])

class MissionSelectScreen:
    def draw(self, t, selected):
        screen.fill(DARK)
        rng=random.Random(7)
        for _ in range(160):
            b=rng.randint(40,160)
            pygame.draw.circle(screen,(b,b,b),(rng.randint(0,WIDTH),rng.randint(0,HEIGHT)),1)
        title=font_xl.render("SELECT  MISSION",True,CYAN)
        screen.blit(title,(WIDTH//2-title.get_width()//2,30))
        sub=font_md.render("← → to choose   |   ENTER to confirm",True,GRAY)
        screen.blit(sub,(WIDTH//2-sub.get_width()//2,110))
        w=320; gap=30; total=len(MISSION_KEYS)*w+(len(MISSION_KEYS)-1)*gap
        start_x=(WIDTH-total)//2
        for ci,mname in enumerate(MISSION_KEYS):
            cfg=MISSIONS[mname]
            cx=start_x+ci*(w+gap); cy=158
            sel=ci==selected
            border=YELLOW if sel else GRAY
            bg=(30,35,50) if sel else (18,18,30)
            pygame.draw.rect(screen,bg,     (cx,cy,w,430))
            pygame.draw.rect(screen,border, (cx,cy,w,430),2)
            if sel:
                pygame.draw.rect(screen,(50,55,80),(cx,cy,w,430),4)
            nc=CYAN if sel else WHITE
            nm=font_md.render(mname,True,nc)
            screen.blit(nm,(cx+w//2-nm.get_width()//2,cy+14))
            for i,line in enumerate(cfg["desc"]):
                l=font_sm.render(line,True,WHITE)
                screen.blit(l,(cx+12,cy+58+i*28))
            stats=[
                (f"Fuel:         {cfg['fuel']:.0f} units", CYAN),
                (f"Thrust:       {cfg['thrust']}",         GREEN),
                (f"Debris:       {cfg['debris']}",         AMBER if cfg['debris']>5 else WHITE),
                (f"Fuel mult:    ×{cfg['fuel_mult']}",     YELLOW),
                (f"Time mult:    ×{cfg['time_mult']}",     YELLOW),
            ]
            for si,(stat,col) in enumerate(stats):
                screen.blit(font_sm.render(stat,True,col),(cx+12,cy+175+si*36))
            hs=high_scores[mname]
            screen.blit(font_sm.render("BEST SCORES",True,GRAY),(cx+12,cy+370))
            if hs:
                screen.blit(font_sm.render(f"1st: {hs[0]:,}",True,YELLOW),(cx+12,cy+395))
            else:
                screen.blit(font_sm.render("No runs yet",True,GRAY),(cx+12,cy+395))
        if sel:
            arr=font_lg.render("▼  ENTER TO LAUNCH  ▼",True,YELLOW)
            screen.blit(arr,(WIDTH//2-arr.get_width()//2,620))

class HUD:
    def draw(self,rocket,state,t,sats,mission_name):
        pygame.draw.rect(screen,DIM, (15,15,415,340))
        pygame.draw.rect(screen,CYAN,(15,15,415,340),2)
        header=f"FLIGHT COMPUTER  [{mission_name}]"
        screen.blit(font_md.render(header,True,CYAN),(25,23))
        # Engine light
        ecol=GREEN if rocket.engine and not rocket.eng_fail else (80,30,30)
        pygame.draw.circle(screen,ecol,(390,31),8)
        pygame.draw.circle(screen,WHITE,(390,31),8,1)
        rows=[("MODE",state.upper()),("TIME",fmt(t)),
              ("ALT",f"{rocket.alt:,.0f} m"),("VEL",f"{rocket.vel:.1f} m/s"),
              ("STAGE",str(rocket.stage)),("SATS",f"{len(sats)} / 3")]
        for i,(lbl,val) in enumerate(rows):
            y=60+i*32
            screen.blit(font_sm.render(lbl+":",True,GREEN),(25,y))
            screen.blit(font_sm.render(val,    True,WHITE),(145,y))
        draw_bar(25,258,375,16,rocket.fuel,rocket.max_fuel,GREEN,"FUEL")
        # Throttle
        draw_bar(25,300,375,10,rocket.throttle*100,100,ORANGE,"THROTTLE")
        if state==LAUNCH:
            draw_bar(25,332,375,10,min(rocket.alt,80000),80000,BLUE,"ORBIT ALT")

    def draw_orbit_panel(self, windows, rocket_ang, warn, closest_dist):
        px,py,pw,ph=WIDTH-285,15,270,230
        pygame.draw.rect(screen,DIM,  (px,py,pw,ph))
        pygame.draw.rect(screen,AMBER,(px,py,pw,ph),2)
        screen.blit(font_md.render("ORBIT STATUS",True,AMBER),(px+10,py+8))
        in_win=any(w.contains(rocket_ang) for w in windows)
        if in_win:
            msg=font_md.render(">>> DEPLOY NOW <<<",True,GREEN)
            screen.blit(msg,(px+10,py+44))
        else:
            screen.blit(font_sm.render("Align with green window",True,GRAY),(px+10,py+48))
        for i,w in enumerate(windows):
            status="OPEN" if w.ready else f"COOL {max(0,w.cool):.0f}s"
            col=GREEN if w.ready else GRAY
            screen.blit(font_sm.render(f"Window {i+1}: {status}",True,col),(px+10,py+82+i*28))
        # Debris distance
        dist_col=RED if closest_dist<44 else AMBER if closest_dist<80 else GREEN
        screen.blit(font_sm.render(f"Nearest debris: {closest_dist:.0f} m",True,dist_col),
                    (px+10,py+170))
        if warn:
            screen.blit(font_md.render("!! DEBRIS NEAR !!",True,RED),(px+10,py+198))

class Game:
    def __init__(self, mission_key="STANDARD"):
        self.mission_key = mission_key
        self.cfg         = MISSIONS[mission_key]
        self.state       = LAUNCH
        self.rocket      = Rocket(self.cfg)
        self.log         = Log()
        self.hud         = HUD()
        self.stars       = Stars()
        self.sats        = []
        self.windows     = [
            OrbitalWindow(0.0,          0.0018),
            OrbitalWindow(math.pi*2/3,  0.0012),
            OrbitalWindow(math.pi*4/3,  0.0022),
        ]
        self.debris      = Debris(self.cfg["debris"])
        self.t           = 0.0
        self.score       = 0
        self.fail_msg    = ""
        self.debris_warn = False
        self.closest     = 9999
        self.s_fuel=self.s_time=self.s_sat=0
        self.log.add(f"T+00:00  [{mission_key}] Mission start!")

class App:
    def __init__(self):
        self.state     = MENU
        self.menu      = MenuScreen()
        self.sel_scr   = MissionSelectScreen()
        self.game      = None
        self.t         = 0.0
        self.show_hs   = False
        self.sel_idx   = 0   # selected mission index

    def handle(self, e):
        if e.type != pygame.KEYDOWN: return
        k = e.key

        if self.state == MENU:
            if k == pygame.K_RETURN:
                self.state = MISSION_SELECT
            if k == pygame.K_h:
                self.show_hs = not self.show_hs

        elif self.state == MISSION_SELECT:
            if k == pygame.K_LEFT:
                self.sel_idx = (self.sel_idx-1) % len(MISSION_KEYS)
            if k == pygame.K_RIGHT:
                self.sel_idx = (self.sel_idx+1) % len(MISSION_KEYS)
            if k == pygame.K_RETURN:
                mkey = MISSION_KEYS[self.sel_idx]
                self.game  = Game(mkey)
                self.state = LAUNCH
            if k == pygame.K_ESCAPE:
                self.state = MENU

        elif self.state in (LAUNCH, ORBIT):
            g = self.game
            if k == pygame.K_SPACE:
                g.rocket.engine = not g.rocket.engine
                g.log.add(f"{fmt(g.t)} Engine {'ON' if g.rocket.engine else 'OFF'}")
            if k == pygame.K_r and g.rocket.eng_fail:
                g.rocket.eng_fail = False
                g.log.add(f"{fmt(g.t)} Engine restarted")
            if k == pygame.K_d and self.state == ORBIT:
                in_win = any(w.contains(g.rocket.orbit_ang) for w in g.windows)
                if in_win:
                    for w in g.windows:
                        if w.contains(g.rocket.orbit_ang):
                            w.deploy(); break
                    g.sats.append(Satellite())
                    n = len(g.sats)
                    g.log.add(f"{fmt(g.t)} Satellite-{n} deployed!")
                    # Spark burst at satellite position
                    a=g.sats[-1].ang
                    sx=int(CENTER[0]+math.cos(a)*g.sats[-1].r)
                    sy=int(CENTER[1]+math.sin(a)*g.sats[-1].r)
                    particles.burst(sx,sy,20,3,[YELLOW,CYAN,GREEN],2)
                else:
                    g.log.add(f"{fmt(g.t)} Not in deploy window!")

        elif self.state in (WIN, FAIL):
            if k == pygame.K_RETURN:
                self.state = MENU
                self.game  = None
                particles.pool.clear()

    def update(self):
        dt = clock.get_time()/1000
        self.t += dt
        shake.update(dt)
        particles.update(dt)

        if self.state not in (LAUNCH, ORBIT): return
        g = self.game
        g.t += dt

        cfg = g.cfg
        #random events
        if random.randint(0, cfg["fail_rate"])==0 and not g.rocket.eng_fail:
            g.rocket.eng_fail = True
            g.log.add(f"{fmt(g.t)} WARNING — Engine failure!")
            shake.trigger(7)
        if random.randint(0, cfg["leak_rate"])==0 and not g.rocket.fuel_leak:
            g.rocket.fuel_leak = True
            g.log.add(f"{fmt(g.t)} WARNING — Fuel leak!")

        if self.state == LAUNCH:
            g.rocket.update_launch(dt, cfg["fail_rate"], cfg["leak_rate"])
            if g.rocket.alt > 20000 and g.rocket.stage == 1:
                g.rocket.stage_sep(g.log, g.t)
            if g.rocket.alt >= 80000:
                self.state = ORBIT
                g.log.add(f"{fmt(g.t)} *** ORBIT ACHIEVED! ***")
            if g.rocket.fuel <= 0 and g.rocket.alt < 500:
                self.state = FAIL
                g.fail_msg = "Fuel exhausted on launch pad"

        elif self.state == ORBIT:
            g.rocket.update_orbit(dt)
            for w in g.windows: w.update(dt)
            g.debris.update(dt)
            for s in g.sats: s.update(dt)

            a  = g.rocket.orbit_ang
            crx= int(CENTER[0]+math.cos(a)*g.rocket.ORBIT_R)
            cry= int(CENTER[1]+math.sin(a)*g.rocket.ORBIT_R)
            result, g.closest = g.debris.check(crx,cry)
            g.debris_warn = (result=="warn")
            if g.debris_warn: shake.trigger(3)
            if result == "collision":
                self.state = FAIL
                g.fail_msg = "Debris collision"
                shake.trigger(18)
                particles.burst(crx,cry,40,5,[RED,ORANGE,YELLOW],3)
            if len(g.sats) >= 3:
                self.state = WIN
                g.s_fuel = int(g.rocket.fuel * cfg["fuel_mult"])
                g.s_time = int(max(0,900-g.t) * cfg["time_mult"])
                g.s_sat  = 300
                g.score  = g.s_fuel + g.s_time + g.s_sat
                record_score(g.mission_key, g.score)
                g.log.add("*** MISSION SUCCESS! ***")
                particles.burst(CENTER[0],CENTER[1],60,8,[GREEN,CYAN,YELLOW,WHITE],4)
            if g.rocket.fuel <= 0:
                self.state = FAIL
                g.fail_msg = "Fuel exhausted in orbit"

    def draw(self):
        ox, oy = shake.offset()

        if self.state == MENU:
            self.menu.draw(self.t, self.show_hs)
            particles.draw()
            return

        if self.state == MISSION_SELECT:
            self.sel_scr.draw(self.t, self.sel_idx)
            return

        g = self.game

        #world render with shake offset
        shifted = pygame.Surface((WIDTH, HEIGHT))

        if self.state in (LAUNCH, WIN, FAIL) and g.game_mode_was_launch():
            shifted.fill(sky_color(g.rocket.alt))
        # (handled below)

        if self.state in (LAUNCH,) or (self.state in (WIN,FAIL) and g.rocket.alt<80000):
            screen.fill(sky_color(g.rocket.alt))
            # stars
            _draw_stars_direct(g.rocket.alt)
            pygame.draw.rect(screen,(25,80,25),(ox,HEIGHT-80+oy,WIDTH,80))
            g.rocket.draw_launch()
        elif self.state in (ORBIT, WIN, FAIL):
            screen.fill((5,5,15))
            _draw_stars_direct(90000)
            # Debris warning edge glow
            if g.debris_warn:
                ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
                ov.fill((180,0,0,int(35+25*math.sin(pygame.time.get_ticks()*0.01))))
                screen.blit(ov,(0,0))
            pygame.draw.circle(screen,(30,80,160),  (CENTER[0]+ox,CENTER[1]+oy),65)
            pygame.draw.circle(screen,(20,150,70),  (CENTER[0]+ox,CENTER[1]+oy),65,8)
            pygame.draw.circle(screen,(40,100,180), (CENTER[0]+ox,CENTER[1]+oy),65,2)
            pygame.draw.circle(screen,(20,40,20),   (CENTER[0]+ox,CENTER[1]+oy),g.rocket.ORBIT_R,1)
            for w in g.windows: w.draw(g.rocket.ORBIT_R)
            a=g.rocket.orbit_ang
            crx=int(CENTER[0]+math.cos(a)*g.rocket.ORBIT_R)
            cry=int(CENTER[1]+math.sin(a)*g.rocket.ORBIT_R)
            g.debris.draw(crx,cry)
            g.rocket.draw_orbit()
            for s in g.sats: s.draw()

        particles.draw()
        g.hud.draw(g.rocket, self.state, g.t, g.sats, g.mission_key)
        g.log.draw(20,490)
        if self.state == ORBIT:
            g.hud.draw_orbit_panel(g.windows, g.rocket.orbit_ang, g.debris_warn, g.closest)

        if self.state == WIN:
            ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            ov.fill((0,20,0,115)); screen.blit(ov,(0,0))
            # Scanline animation
            scan_y=(int(self.t*60)%HEIGHT)
            pygame.draw.line(screen,(0,80,0,80),(0,scan_y),(WIDTH,scan_y),2)
            m1=font_lg.render("MISSION  SUCCESS!",True,GREEN)
            screen.blit(m1,(WIDTH//2-m1.get_width()//2,HEIGHT//2-100))
            lines=[
                (f"Fuel bonus:   {g.s_fuel:,}",   CYAN),
                (f"Time bonus:   {g.s_time:,}",   YELLOW),
                (f"Sat  bonus:   {g.s_sat:,}",    GREEN),
                (f"TOTAL SCORE:  {g.score:,}",    WHITE),
                ("",""),
                (f"[{g.mission_key}]  Press ENTER for menu", GRAY),
            ]
            for i,(txt,col) in enumerate(lines):
                if txt:
                    s=font_md.render(txt,True,col)
                    screen.blit(s,(WIDTH//2-s.get_width()//2,HEIGHT//2-35+i*36))

        if self.state == FAIL:
            ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            ov.fill((30,0,0,128)); screen.blit(ov,(0,0))
            m1=font_lg.render("MISSION  FAILED",True,RED)
            m2=font_md.render(g.fail_msg,True,AMBER)
            m3=font_md.render(f"Survived: {fmt(g.t)}",True,GRAY)
            m4=font_md.render("Press ENTER for menu",True,WHITE)
            screen.blit(m1,(WIDTH//2-m1.get_width()//2,HEIGHT//2-80))
            screen.blit(m2,(WIDTH//2-m2.get_width()//2,HEIGHT//2-20))
            screen.blit(m3,(WIDTH//2-m3.get_width()//2,HEIGHT//2+25))
            screen.blit(m4,(WIDTH//2-m4.get_width()//2,HEIGHT//2+70))


def _draw_stars_direct(alt):
    alpha=min(255,int(255*alt/35000))
    if alpha<=0: return
    rng=random.Random(42)
    for _ in range(220):
        sx=rng.randint(0,WIDTH); sy=rng.randint(0,HEIGHT); sz=rng.randint(1,3)
        b=min(255,110+sz*40)
        s=pygame.Surface((sz*2+1,sz*2+1),pygame.SRCALPHA)
        s.fill((b,b,b,alpha)); screen.blit(s,(sx-sz,sy-sz))


def _game_mode_was_launch(self):
    return True   # always route through orbit draw in orbit state
Game.game_mode_was_launch = _game_mode_was_launch

app     = App()
running = True
while running:
    clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if app.state in (MENU,): running = False
            else: app.state = MENU; app.game = None
        app.handle(e)
    app.update()
    app.draw()
    pygame.display.flip()
pygame.quit()
