#!/usr/bin/env python3
"""Pong beyni kendini test eder: tam oyun fizik taklidi ile AI (sağ) vs
referans rakip (sol). Gerçek kurallar: servis, duvar sekmesi, çarpışma,
sayı, top hızlanması. Rezilse rezilliği sayılarla gösterir."""
import brain, math, random, os, tempfile

W, H, BALL_R, PAD_H, PAD_W = 800, 500, 8, 90, 12
BALL_SPEED0, BALL_ACC, BALL_MAX = 6, 1.3, 17
PLAYER_SPEED = 8.0            # "insan" rakip hızı
WIN = 7

# beyin hafızasını geçici dosyaya yönlendir (gerçek oyunu kirletme)
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
brain.LS_PATH = tmp.name
brain._memory = None
brain.load_memory()

PLAYER_X = 24
AI_X = W - 24 - PAD_W

def clamp(v,a,b): return max(a,min(b,v))

class Ball:
    def __init__(s): s.x=W/2; s.y=H/2; s.vx=0; s.vy=0; s.speed=BALL_SPEED0
def new_ball(): return Ball()

def serve(b, dir):
    b.x=W/2; b.y=H/2; b.speed=BALL_SPEED0; b.prevX=b.x
    a=(random.random()*0.6-0.3)*math.pi
    b.vx=math.cos(a)*b.speed*dir; b.vy=math.sin(a)*b.speed

def hit_paddle(p_y, out, b):
    rel=clamp((b.y-(p_y+PAD_H/2))/(PAD_H/2),-1,1)
    ang=rel*(math.pi*0.35)
    b.speed=min(b.speed+BALL_ACC,BALL_MAX)
    b.vx=math.cos(ang)*b.speed*out
    b.vy=math.sin(ang)*b.speed
    if out>0: b.x=PLAYER_X+PAD_W+BALL_R+1
    else: b.x=AI_X-BALL_R-1

# ---------- Referans sol rakip: gerçekçi "insan". Topu tahmin etmez,
#              anlık pozisyonunu sınırlı hızla kovalar; top hızlanınca yetişemez ----------
def move_player(py, b, dtF):
    c = py + PAD_H/2
    # top sola geliyorsa kovalar; gelmiyorsa orta civarına süzülür (gerçek insan)
    target = b.y if b.vx < 0 else (H/2 + (b.y - H/2) * 0.25)
    d = target - c
    if abs(d) > 2:
        py = clamp(py + clamp(d, -PLAYER_SPEED*dtF, PLAYER_SPEED*dtF), 0, H-PAD_H)
    return py

# ---------- Bir maç ----------
def play_game(max_points=40, diff="normal"):
    b=new_ball(); serve(b, random.choice([-1,1]))
    player_y=H/2-PAD_H/2
    # AI başlangıç y: beyinden al
    ai_y=H/2-PAD_H/2
    sp=sa=0; rally=0; maxrally=0
    ai_defense_errors=0; ai_returned=0
    dtF=1.0
    serve_dir=1
    frames=0
    while sp<WIN and sa<WIN and frames<max_points*4000:
        frames+=1
        # --- sol rakip hareket ---
        player_y=move_player(player_y,b,dtF)
        # --- AI (beyin) hareket ---
        st={'bx':b.x,'by':b.y,'vx':b.vx,'vy':b.vy,'speed':b.speed,
            'px':player_y+PAD_H/2,'ay':ai_y,'phase':'playing',
            'score_p':sp,'score_a':sa,'dtMs':16.7,'diff':diff}
        out=brain.brain(st)
        ai_y=clamp(out['aiY'],0,H-PAD_H)
        # --- top ---
        prevX=b.x
        b.x+=b.vx*dtF; b.y+=b.vy*dtF
        if b.y-BALL_R<0: b.y=BALL_R; b.vy=abs(b.vy)
        if b.y+BALL_R>H: b.y=H-BALL_R; b.vy=-abs(b.vy)
        # çarpışmalar
        ai_hit=False; pl_hit=False
        if b.vx<0:
            face=PLAYER_X+PAD_W
            if prevX-BALL_R>=face and b.x-BALL_R<=face and player_y-BALL_R<b.y<player_y+PAD_H+BALL_R:
                hit_paddle(player_y,1,b); pl_hit=True
        if b.vx>0:
            face=AI_X
            if prevX+BALL_R<=face and b.x+BALL_R>=face and ai_y-BALL_R<b.y<ai_y+PAD_H+BALL_R:
                hit_paddle(ai_y,-1,b); ai_hit=True; ai_returned+=1
        if ai_hit or pl_hit:
            rally+=1; maxrally=max(maxrally,rally)
        else:
            # top bir kenardan çıktı mu?
            if b.x<-20:
                sa+=1; rally=0; serve_dir=1
                st2={'bx':b.x,'by':b.y,'vx':b.vx,'vy':b.vy,'speed':b.speed,
                     'px':player_y+PAD_H/2,'ay':ai_y,'phase':'playing',
                     'score_p':sp,'score_a':sa,'missed_player':True,'dtMs':16.7,'diff':diff}
                brain.brain(st2)
                serve(b,1); 
            elif b.x>W+20:
                sp+=1; rally=0; serve_dir=-1
                # AI kaçırdı mı? (top sağdan çıktı, AI'nın vuruşu beklendi)
                ai_defense_errors+=1
                serve(b,-1)
            else:
                pass
    return {'winner':'AI' if sa>sp else 'PLAYER','sp':sp,'sa':sa,
            'maxrally':maxrally,'ai_defense_errors':ai_defense_errors,
            'ai_returned':ai_returned}

def run(n, label, fresh_each=False, diff="normal"):
    print(f"\n=== {label} [{diff}]: {n} maç (ilk {WIN} sayan kazanır) ===")
    wins=0; tsp=tas=0; tot_err=tot_ret=0; rallies=[]
    for i in range(n):
        if fresh_each:
            brain._memory=brain._default_memory()
        g=play_game(diff=diff)
        if g['winner']=='AI': wins+=1
        tsp+=g['sp']; tas+=g['sa']
        tot_err+=g['ai_defense_errors']; tot_ret+=g['ai_returned']
        rallies.append(g['maxrally'])
        if (i+1)%5==0 or i==n-1:
            print(f"  maç {i+1:2d}: {g['winner']:6s}  oyuncu {g['sp']} - {g['sa']} AI  "
                  f"(en uzun ralli {g['maxrally']}, AI döndürdü {g['ai_returned']}, "
                  f"AI kaçırma {g['ai_defense_errors']})  skill={round(brain._memory['skills'][diff],0)}")
    avg_rally=sum(rallies)/len(rallies) if rallies else 0
    print(f"  >> AI galibiyet oranı: {wins}/{n} ({100*wins//max(1,n)}%)")
    print(f"  >> Toplam sayı: oyuncu {tsp} - AI {tas}")
    print(f"  >> Ort. en-uzun-ralli: {avg_rally:.1f}  |  AI top döndürme: {tot_ret}, "
          f"AI kaçırma (sağdan çıkan): {tot_err}")
    print(f"  >> Son beceri ({diff}): {round(brain._memory['skills'][diff],1)}")
    return wins,n

if __name__=='__main__':
    import sys
    n=int(sys.argv[1]) if len(sys.argv)>1 else 8
    # Her zorluk modunu ayrı ayrı dene (referans "insan" aynı)
    for d in ["easy","normal","hard","very_hard"]:
        brain._memory=brain._default_memory()
        run(n, f"MOD TEST", diff=d)
