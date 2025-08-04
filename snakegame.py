import pygame
import sys
import random
import os
import math
import json

# --- Configuration ---
CELL_SIZE = 20
FPS = 240               # Render frames per second
MOVE_SPEED = 10         # Snake moves per second
MOVE_INTERVAL = 1000 / MOVE_SPEED  # ms between moves
MERCY_DURATION_MS = 50  # immunity window before game over
PREF_FILE = 'prefs.json'

# Available resolutions (must be multiples of CELL_SIZE)
AVAILABLE_RESOLUTIONS = [
    (600, 400),
    (800, 600),
    (1280, 720),
    (1920, 1080)
]

# --- Globals ---
current_res_index = 0
borderless = False
current_bg_index = -1
background = None
GRID_ALPHA = int(255 * 0.05)
screen = None
clock = None
font = None
cog_rect = pygame.Rect(0, 0, 0, 0)

# --- Preferences Persistence ---
def load_prefs():
    global current_res_index, borderless, current_bg_index
    try:
        with open(PREF_FILE, 'r') as f:
            data = json.load(f)
            current_res_index = data.get('resolution_index', 0)
            borderless = data.get('borderless', False)
            current_bg_index = data.get('background_index', -1)
    except:
        pass


def save_prefs():
    try:
        with open(PREF_FILE, 'w') as f:
            json.dump({
                'resolution_index': current_res_index,
                'borderless': borderless,
                'background_index': current_bg_index
            }, f)
    except:
        pass

# --- Display Setup ---
def apply_display_settings():
    global screen, cog_rect, background, GRID_ALPHA
    w, h = AVAILABLE_RESOLUTIONS[current_res_index]
    flags = pygame.NOFRAME if borderless else 0
    screen = pygame.display.set_mode((w, h), flags)
    pygame.display.set_caption('Snake Game')
    cog_rect = pygame.Rect(w - 50, 0, 50, 50)
    # load PNG backgrounds
    pngs = [f for f in os.listdir('.') if f.lower().endswith('.png')]
    if 0 <= current_bg_index < len(pngs):
        try:
            img = pygame.image.load(pngs[current_bg_index]).convert()
            background = pygame.transform.scale(img, (w, h))
            GRID_ALPHA = int(255 * 0.05)
        except:
            background = None
            GRID_ALPHA = int(255 * 0.2)
    else:
        background = None
        GRID_ALPHA = int(255 * 0.2)
    return background

# --- Drawing Helpers ---
def draw_grid():
    w, h = screen.get_size()
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    col = (0, 0, 0, GRID_ALPHA)
    for x in range(0, w, CELL_SIZE): pygame.draw.line(surf, col, (x, 0), (x, h))
    for y in range(0, h, CELL_SIZE): pygame.draw.line(surf, col, (0, y), (w, y))
    screen.blit(surf, (0, 0))

# Draw smooth pill-shaped snake with eyes
def draw_snake(prev_pts, curr_pts, alpha, direction):
    centers = []
    for p, c in zip(prev_pts, curr_pts):
        x = p[0] + (c[0] - p[0]) * alpha + CELL_SIZE/2
        y = p[1] + (c[1] - p[1]) * alpha + CELL_SIZE/2
        centers.append((x, y))
    radius = (CELL_SIZE - 4) / 2
    for pt in centers:
        pygame.draw.circle(screen, (0, 255, 0), (int(pt[0]), int(pt[1])), int(radius))
    for a, b in zip(centers[:-1], centers[1:]):
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        pygame.draw.circle(screen, (0, 255, 0), (int(mid[0]), int(mid[1])), int(radius))
    # Eyes
    hx, hy = centers[0]
    dx, dy = direction[0]/CELL_SIZE, direction[1]/CELL_SIZE
    fwd = (dx*radius*0.7, dy*radius*0.7)
    side = (-dy*radius*0.5, dx*radius*0.5)
    er = max(int(radius*0.3),2)
    e1 = (hx+fwd[0]+side[0], hy+fwd[1]+side[1])
    e2 = (hx+fwd[0]-side[0], hy+fwd[1]-side[1])
    pygame.draw.circle(screen,(0,0,0),(int(e1[0]),int(e1[1])),er)
    pygame.draw.circle(screen,(0,0,0),(int(e2[0]),int(e2[1])),er)

# Draw apple
def draw_apple(pos):
    cx,posy = pos[0]+CELL_SIZE/2, pos[1]+CELL_SIZE/2
    rr = CELL_SIZE//2-2
    pygame.draw.circle(screen,(255,0,0),(int(cx),int(posy)),rr)
    leaf=(cx+rr*0.6,posy-rr*0.6); lr=max(int(rr*0.4),2)
    pygame.draw.circle(screen,(0,255,0),(int(leaf[0]),int(leaf[1])),lr)

# Draw settings cog
def draw_cog():
    w,_=screen.get_size();cx,cy=w-25,25;orad,irad=12,5
    pygame.draw.circle(screen,(0,0,0),(cx,cy),orad,2)
    for i in range(8):
        ang=math.radians(i*45)
        x1,y1=cx+int(math.cos(ang)*orad),cy+int(math.sin(ang)*orad)
        x2,y2=cx+int(math.cos(ang)*(orad+5)),cy+int(math.sin(ang)*(orad+5))
        pygame.draw.line(screen,(0,0,0),(x1,y1),(x2,y2),2)
    pygame.draw.circle(screen,(0,0,0),(cx,cy),irad)

# Pause and countdown
def pause_and_countdown(prev_pts,curr_pts,direction,food_pos):
    for cnt in [3,2,1]:
        if background: screen.blit(background,(0,0))
        else: screen.fill((255,255,255))
        draw_grid(); draw_snake(prev_pts,curr_pts,1,direction); draw_apple(food_pos)
        txt=font.render(str(cnt),True,(0,0,0));w,h=screen.get_size()
        screen.blit(txt,(w//2-txt.get_width()//2,h//2-txt.get_height()//2));pygame.display.flip();pygame.time.delay(500)
    return pygame.time.get_ticks()

# Settings Menu
def settings_menu():
    global borderless,current_res_index,current_bg_index,background,GRID_ALPHA
    res_lbl=[f"{w}x{h}" for w,h in AVAILABLE_RESOLUTIONS]
    bg_files=[f for f in os.listdir('.') if f.lower().endswith('.png')]
    lh=font.get_height()+20; y0=100
    opts=[{'label':'Toggle Borderless','action':'toggle'},{'label':'Change Resolution','action':'res'},{'label':'Cycle Background','action':'bg'},{'label':'Back','action':'back'}]
    for i,opt in enumerate(opts):opt['rect']=pygame.Rect(50,y0+i*lh,500,lh)
    while True:
        screen.fill((240,240,240))
        for opt in opts:
            r=opt['rect'];screen.blit(font.render(opt['label'],True,(0,0,0)),(r.x,r.y))
            val='' if opt['action']=='toggle' else ''
            if opt['action']=='toggle':val='On' if borderless else 'Off'
            elif opt['action']=='res':val=res_lbl[current_res_index]
            elif opt['action']=='bg':val=bg_files[current_bg_index] if 0<=current_bg_index<len(bg_files) else 'None'
            screen.blit(font.render(val,True,(0,0,255)),(r.x+250,r.y))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:pygame.quit();sys.exit()
            act=None
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                for opt in opts:
                    if opt['rect'].collidepoint(ev.pos):act=opt['action']
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_t:act='toggle'
                elif ev.key==pygame.K_r:act='res'
                elif ev.key==pygame.K_g:act='bg'
                elif ev.key==pygame.K_b:act='back'
            if act=='toggle':borderless=not borderless;save_prefs();apply_display_settings()
            elif act=='res':current_res_index=(current_res_index+1)%len(AVAILABLE_RESOLUTIONS);save_prefs();apply_display_settings()
            elif act=='bg' and bg_files:current_bg_index=(current_bg_index+1)%len(bg_files);save_prefs();apply_display_settings()
            elif act=='back':save_prefs();return
        clock.tick(FPS)

# Main Game Loop
def run_game():
    w,h=screen.get_size();snake=[(w//2,h//2)];direction=(0,-CELL_SIZE)
    food=(random.randint(0,w//CELL_SIZE-1)*CELL_SIZE,random.randint(0,h//CELL_SIZE-1)*CELL_SIZE)
    score=0;high_score=0
    if os.path.exists('high_score.txt'):
        try:high_score=int(open('high_score.txt').read())
        except:pass
    prev=list(snake);last_move=pygame.time.get_ticks();mercy_start=None;input_allowed=True
    while True:
        now=pygame.time.get_ticks();clock.tick(FPS)
        # Handle events
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:return False
            if ev.type==pygame.KEYDOWN:
                if input_allowed:
                    if ev.key in (pygame.K_UP,pygame.K_w) and direction!=(0,CELL_SIZE):direction=(0,-CELL_SIZE);input_allowed=False
                    elif ev.key in (pygame.K_DOWN,pygame.K_s) and direction!=(0,-CELL_SIZE):direction=(0,CELL_SIZE);input_allowed=False
                    elif ev.key in (pygame.K_LEFT,pygame.K_a) and direction!=(CELL_SIZE,0):direction=(-CELL_SIZE,0);input_allowed=False
                    elif ev.key in (pygame.K_RIGHT,pygame.K_d) and direction!=(-CELL_SIZE,0):direction=(CELL_SIZE,0);input_allowed=False
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1 and cog_rect.collidepoint(ev.pos):
                settings_menu();last_move=pause_and_countdown(prev,snake,direction,food);mercy_start=None;input_allowed=True
        # Movement and mercy
        if now-last_move>=MOVE_INTERVAL:
            next_head=(snake[0][0]+direction[0],snake[0][1]+direction[1])
            collision=(next_head[0]<0 or next_head[0]>=w or next_head[1]<0 or next_head[1]>=h or next_head in snake[1:])
            if collision:
                if mercy_start is None:mercy_start=now
                elif now>=mercy_start+MERCY_DURATION_MS:break
            else:
                last_move+=MOVE_INTERVAL;prev=list(snake)
                snake.insert(0,next_head)
                if snake[0]==food:score+=1;food=(random.randint(0,w//CELL_SIZE-1)*CELL_SIZE,random.randint(0,h//CELL_SIZE-1)*CELL_SIZE)
                else:snake.pop()
                mercy_start=None;input_allowed=True
        # Draw
        if background:screen.blit(background,(0,0))
        else:screen.fill((255,255,255))
        draw_grid();alpha=min((now-last_move)/MOVE_INTERVAL,1.0)
        draw_snake(prev,snake,alpha,direction);draw_apple(food);draw_cog()
        screen.blit(font.render(f'Score: {score}',True,(0,0,0)),(10,10));screen.blit(font.render(f'High: {high_score}',True,(0,0,0)),(10,50))
        pygame.display.flip()
    # Game Over
    if score>high_score:open('high_score.txt','w').write(str(score))
    return game_over_menu(score)

# Game Over Menu
def game_over_menu(score):
    w,h=screen.get_size();opts=['Replay','Quit'];idx=0
    while True:
        screen.fill((255,255,255));screen.blit(font.render('Game Over!',True,(255,0,0)),(w//2-80,h//2-100));screen.blit(font.render(f'Score: {score}',True,(0,0,0)),(w//2-60,h//2-60))
        for i,opt in enumerate(opts):col=(0,255,0) if i==idx else (200,200,200);r=pygame.Rect(w//2-80,h//2-20+i*40,160,30);pygame.draw.rect(screen,col,r);screen.blit(font.render(opt,True,(0,0,0)),(r.x+10,r.y+5))
        pygame.display.flip();clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:return False
            if ev.type==pygame.KEYDOWN:
                if ev.key in (pygame.K_UP,pygame.K_w):idx=(idx-1)%len(opts)
                elif ev.key in (pygame.K_DOWN,pygame.K_s):idx=(idx+1)%len(opts)
                elif ev.key==pygame.K_RETURN:return idx==0

# Entry Point
if __name__=='__main__':pygame.init();clock=pygame.time.Clock();font=pygame.font.SysFont(None,36);load_prefs();apply_display_settings();
while run_game():pass
pygame.quit();sys.exit()
