#!/usr/bin/env python3
"""Pong "beyni" — öğrenen, güçlenen AI.
İstemci her karede durumu POST /brain'e gönderir, AI raketin hedef y
koordinatını döndürür. Hafıza diskte (ai_memory.json) kalıcıdır.

Sıfırdan: bağımlılık yok (yalnız stdlib).
"""
import json, os, math, random, threading, time

# ---- Sabitler (HTML ile aynı alan: 800x500) ----
W, H = 800, 500
BALL_R = 8
AI_X = W - 24 - 12          # ai raket sol yüzü
AI_FACE_X = AI_X
PLAYER_FACE_X = 24 + 12 + BALL_R   # oyuncu yüzünden çıkış
ZONES = 10
ZH = H / ZONES
LS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_memory.json")
MAX_SPEED = 17
PAD_H = 90

# ---- Zorluk modları: her biri BAŞTAN hazır bir zekâ ile gelir;
#      canlı gelişme bu temelin ÜSTÜNE eklenir (kalıcı, mod başına ayrı) ----
# base    = başlangıç becerisi (0..100)
# learn   = oyuncu üstünlük kurdukça öğrenme hızı çarpanı
# decay   = AI üstünlük kurduğunda gevşeme çarpanı
# err/speed_scale = modun genel yetenek ölçeği
DIFFICULTIES = {
    "easy":      {"base": 10, "learn": 0.5, "decay": 0.10, "err_scale": 1.40, "speed_scale": 0.90},
    "normal":    {"base": 35, "learn": 1.0, "decay": 0.25, "err_scale": 1.00, "speed_scale": 1.00},
    "hard":      {"base": 60, "learn": 1.6, "decay": 0.15, "err_scale": 0.75, "speed_scale": 1.05},
    "very_hard": {"base": 85, "learn": 2.2, "decay": 0.08, "err_scale": 0.50, "speed_scale": 1.10},
}
DEFAULT_DIFF = "normal"

_mem_lock = threading.Lock()
_memory = None
_last_save = [0.0]
SAVE_EVERY = 0.25   # saniye: normalde en fazla bu sıklıkta diske yaz (throttle)

def _default_memory():
    return {
        "zone_def": [{"tries": 0, "missed": 0} for _ in range(ZONES)],  # bandit: bölge nişan denemeleri
        "player_pos": [0.0] * ZONES,   # savunma ısı haritası
        "skills": {k: float(v["base"]) for k, v in DIFFICULTIES.items()},  # mod başına beceri (canlı gelişir)
        "diff": DEFAULT_DIFF,          # aktif mod
        "last_target": -1,
    }

def load_memory():
    global _memory
    with _mem_lock:
        if _memory is not None:
            return _memory
        m = None
        try:
            with open(LS_PATH) as f:
                m = json.load(f)
            if not (isinstance(m, dict) and "zone_def" in m and "player_pos" in m):
                m = None
        except Exception:
            m = None
        if m is None:
            m = _default_memory()
        else:
            # eski format migrate: tek "skill" alanı -> mod başına skills
            if "skills" not in m:
                old = m.pop("skill", 0.0)
                m["skills"] = {k: float(v["base"]) for k, v in DIFFICULTIES.items()}
                m["skills"][m.get("diff", DEFAULT_DIFF)] = clamp(old, 0.0, 100.0)
            # eksik modları tamamla (yeni mod eklenirse)
            for k, v in DIFFICULTIES.items():
                m["skills"].setdefault(k, float(v["base"]))
            m.setdefault("diff", DEFAULT_DIFF)
            if m.get("diff") not in DIFFICULTIES:
                m["diff"] = DEFAULT_DIFF
        _memory = m
        return _memory

def save_memory(force=False):
    """Hafızayı diske yaz. Normal çağrılar throttle'lanır (SAVE_EVERY sn'de bir);
    force=True kritik olaylarda (kaçırma/sayı/maç) anında yazar."""
    now = time.monotonic()
    if not force and now - _last_save[0] < SAVE_EVERY:
        return
    _last_save[0] = now
    with _mem_lock:
        if _memory is None:
            return
        try:
            with open(LS_PATH, "w") as f:
                json.dump(_memory, f)
        except Exception:
            pass

def clear_memory():
    """Hafızayı sıfırla: bölge haritasını temizle, beceriyi MOD TEMELİNE döndür."""
    global _memory
    with _mem_lock:
        keep = _memory.get("diff", DEFAULT_DIFF) if _memory else DEFAULT_DIFF
        if keep not in DIFFICULTIES:
            keep = DEFAULT_DIFF
        _memory = _default_memory()
        _memory["diff"] = keep
    save_memory(force=True)

def clamp(v, a, b):
    return max(a, min(b, v))

# ---- Beceri parametreleri (aktif modun beceri değeri s -> 0..1) ----
def ai_params(active_skill, diff_name):
    s = clamp(active_skill, 0.0, 100.0) / 100.0
    D = DIFFICULTIES.get(diff_name, DIFFICULTIES[DEFAULT_DIFF])
    return {
        "speed": (7.5 + 3.5 * s) * D["speed_scale"],
        "error": (46 - 40 * s) * D["err_scale"],
        "engage": 150 + 330 * s,
        "deadzone": 6 - 3 * s,
        "s": s,
        "diff": D,
    }

# ---- Bölge kullanışlılığı (bandit ağırlığı) ----
def zone_usefulness(z):
    d = _memory["zone_def"][z]
    t = d["tries"]
    if t < 2:
        return 1.0
    return 0.4 + 1.6 * (d["missed"] / t)

def pick_target_zone():
    mem = _memory
    sum_pos = sum(mem["player_pos"]) or 1.0
    weights = []
    total = 0.0
    for z in range(ZONES):
        u = zone_usefulness(z)
        pos_penalty = mem["player_pos"][z] / sum_pos
        w = max(0.05, u * (1.35 - 0.9 * pos_penalty))
        weights.append(w)
        total += w
    r = random.random() * total
    for z in range(ZONES):
        r -= weights[z]
        if r <= 0:
            return z
    return ZONES - 1

# ---- Smaç nişancılığı: raketin tam nerede durması gerektiğini simülasyonla seç ----
def _simulate_hit(ai_y, ball_x, ball_y, vx, vy, speed, target_y):
    """Raket ai_y'de olsa topun oyuncu yüzüne varacağı y'yi hesapla."""
    # smaç: top ai yüzüne çarpıyor, çıkış açısı raket merkezine göre
    rel = clamp((ball_y - (ai_y + PAD_H / 2)) / (PAD_H / 2), -1, 1)
    angle = rel * (math.pi * 0.35)
    nvy = math.sin(angle) * speed
    nvx = math.cos(angle) * speed          # sağa (oyuncuya doğru)
    # topun çıkış noktası: ai yüzü
    x = AI_FACE_X - BALL_R
    y = ball_y
    for _ in range(600):
        x -= nvx
        y += nvy
        if y < BALL_R:
            y = BALL_R; nvy = abs(nvy)
        elif y > H - BALL_R:
            y = H - BALL_R; nvy = -abs(nvy)
        if x <= PLAYER_FACE_X:
            return y
    return y

def _aim_shot(ball_x, ball_y, vx, vy, speed, P):
    """Hedef bölge seç, 60 aday raket konumu simüle et, en yakınına yerleş."""
    z = pick_target_zone()
    _memory["last_target"] = z
    target_y = (z + 0.5) * ZH
    best_y = ball_y - PAD_H / 2
    best_d = float("inf")
    # adaylar: hedefe yakın dikey aralıkta 60 nokta
    candidates = []
    lo = max(PAD_H / 2 + 6, target_y - 220)
    hi = min(H - PAD_H / 2 - 6, target_y + 220)
    if hi <= lo:
        hi = H - PAD_H / 2 - 6
        lo = max(PAD_H / 2 + 6, hi - 440)
    for i in range(60):
        candidates.append(lo + (hi - lo) * i / 59.0)
    # beceri düşüklüğünde aday kümesine rastgele dağılma
    for cy in candidates:
        d = abs(_simulate_hit(cy, ball_x, ball_y, vx, vy, speed, target_y) - target_y)
        d += random.random() * P["error"] * (1 - P["s"])
        if d < best_d:
            best_d = d
            best_y = cy
    # raket y (üst köşe) = merkez - PAD_H/2
    return clamp(best_y - PAD_H / 2, 0, H - PAD_H), z

# ---- Yörünge tahmini (top sağa gidiyorsa) ----
def predict_y(target_x, ball_x, ball_y, vx, vy):
    if vx <= 0:
        return H / 2
    x, y = ball_x, ball_y
    for _ in range(600):
        x += vx; y += vy
        if y < BALL_R:
            y = BALL_R; vy = abs(vy)
        elif y > H - BALL_R:
            y = H - BALL_R; vy = -abs(vy)
        if x >= target_x:
            return y
    return y

# ============================================================
#  Ana giriş noktası: istemci durumu alır, AI hedef y döner
# ============================================================
def brain(state):
    """state: {bx,by,vx,vy,speed, px(py merkez), ay(ai y üst), phase,
               missed_player:bool, score_p, score_a, dtMs,
               diff (zorluk modu), clear:bool}
    return: {aiY, skill, zone, weak, engaged, diff, diffLabel}
    """
    mem = load_memory()
    if state.get("clear"):
        clear_memory()
        m2 = load_memory()
        diff = m2["diff"]
        return {"aiY": H / 2 - PAD_H / 2, "skill": round(m2["skills"][diff]),
                "zone": -1, "weak": [], "engaged": False,
                "diff": diff, "diffLabel": DIFFICULTIES[diff]["base"]}

    # ---- Aktif modu belirle (istemci gönderiyorsa onu kullan, kalıcı) ----
    diff = state.get("diff", mem.get("diff", DEFAULT_DIFF))
    if diff not in DIFFICULTIES:
        diff = DEFAULT_DIFF
    mem["diff"] = diff
    skills = mem["skills"]
    skills[diff] = clamp(skills.get(diff, float(DIFFICULTIES[diff]["base"])), 0.0, 100.0)

    # ---- Beceri güncelle: SAYI ÜSTÜNLÜĞÜ (modun öğrenme hızıyla) ----
    sp = state.get("score_p"); sa = state.get("score_a")
    if sp is not None and sa is not None and (sp != sa):
        D = DIFFICULTIES[diff]
        if sp > sa:
            skills[diff] = clamp(skills[diff] + D["learn"] * 0.4 * (sp - sa), 0, 100)
        else:
            skills[diff] = clamp(skills[diff] - D["decay"] * (sa - sp), 0, 100)
    save_memory()

    P = ai_params(skills[diff], diff)
    bx, by = state["bx"], state["by"]
    vx, vy = state["vx"], state["vy"]
    speed = state.get("speed", 6)
    ai_y = state.get("ay", H / 2 - PAD_H / 2)
    phase = state.get("phase", "playing")

    target = H / 2
    engaged = False

    # ralli başına stabil nişan hatası: top yön değiştirdikçe yeniden atılır
    vsign = 1 if vx > 0 else (-1 if vx < 0 else 0)
    if vsign != mem.get("_last_vsign", 0):
        mem["_last_vsign"] = vsign
        mem["_rally_err"] = (random.random() * 2 - 1) * P["error"]
    aim_err = mem.get("_rally_err", 0.0)

    if phase == "playing" and vx > 0:
        dist = (AI_FACE_X - BALL_R) - bx
        if dist < P["engage"]:
            # ---- ÖNCELİK: topu yakala (raket merkezi -> topun AI yüzüne varacağı y) ----
            hit_y = predict_y(AI_FACE_X - BALL_R, bx, by, vx, vy)
            # ---- Sonra nişan: çıkış açısı, temas noktasının merkeze göre konumundan
            #      gelir. Merkez'i hafifçe kaydırarak topu istenen bölgeye göndeririz.
            #      Merkezi hit_y'nin ALTINA al -> topu aşağı (büyük y) vur;
            #      hit_y'nin ÜSTÜNE al -> topu yukarı (küçük y) vur. Ofset sınırlıdır
            #      ki yakalama bozulmasın. ----
            z = pick_target_zone()
            mem["last_target"] = z
            target_y = (z + 0.5) * ZH + aim_err
            # ---- Çıkış açısı: topu hedef bölgeye taşıyacak açını ----
            # Top AI'dan çıkıp oyuncu yüzüne varma süresi ~ (mesafe / |vx|).
            # İstenen dikey hız = (target_y - hit_y) / t. Bu açıyı, raket merkezini
            # temas noktasının üstüne/altına kaydırarak üretiriz:
            #   rel = (ball_y - center)/(PAD_H/2),  angle = rel * 0.35π
            #   angle = atan2(vy, |vx|)  ->  rel = angle/(0.35π)
            import math as _m
            travel = (AI_FACE_X - BALL_R - PLAYER_FACE_X)      # AI -> oyuncu mesafesi
            t_cross = max(0.5, travel / max(1.0, abs(vx) * 0.9))  # geçiş süresi (kare)
            vy_want = clamp((target_y - hit_y) / max(1.0, t_cross), -abs(vx)*1.2, abs(vx)*1.2)
            ang = _m.atan2(vy_want, max(1.0, abs(vx)))
            rel_ideal = clamp(ang / (0.35 * _m.pi), -0.92, 0.92)   # 0.92: tam kenara çelme
            # Düşük beceride açılar daralır (yakalama öncelikli), yüksek beceride genişler
            rel_ideal *= (0.4 + 0.6 * P["s"])
            ai_center = hit_y - (PAD_H / 2) * rel_ideal
            target = clamp(ai_center, PAD_H/2 + 6, H - PAD_H/2 - 6)
            engaged = True
        else:
            # uzaktan: savunma haritasının en yoğun bölgesine süzül
            mz, bi = 0, -1
            for z in range(ZONES):
                if mem["player_pos"][z] > bi:
                    bi = mem["player_pos"][z]; mz = z
            target = (mz + 0.5) * ZH * 0.6 + H / 2 * 0.4

    # ---- Savunma ısı haritasını güncelle (oyuncu pozisyonundan) ----
    p_center = state.get("px", H / 2)
    if p_center is not None:
        z = clamp(int(p_center // ZH), 0, ZONES - 1)
        lo, hi = max(0, z - 1), min(ZONES - 1, z + 1)
        mem["player_pos"][lo] = min(mem["player_pos"][lo] + 0.05, 5000)
        mem["player_pos"][z]  = min(mem["player_pos"][z]  + 0.20, 5000)
        mem["player_pos"][hi] = min(mem["player_pos"][hi] + 0.05, 5000)

    # ---- Oyuncu topu kaçırdıysa: son nişan bölgesi zayıf ----
    if state.get("missed_player"):
        zt = mem.get("last_target", -1)
        if 0 <= zt < ZONES:
            mem["zone_def"][zt]["missed"] += 1
            save_memory(force=True)

    # ---- Hareket (speed limitli yaklaşma, dt ölçekli) ----
    dead = P["deadzone"]
    dtf = clamp(state.get("dtMs", 16.7) / 16.667, 0.3, 3.0)
    new_y = ai_y
    d = target - (ai_y + PAD_H / 2)
    if abs(d) > dead:
        new_y = clamp(ai_y + clamp(d, -P["speed"] * dtf, P["speed"] * dtf), 0, H - PAD_H)
    new_y = clamp(new_y, 0, H - PAD_H)

    save_memory()
    weak = [z for z in range(ZONES)
            if mem["zone_def"][z]["tries"] >= 2
            and mem["zone_def"][z]["missed"] / mem["zone_def"][z]["tries"] > 0.4]
    return {
        "aiY": new_y,
        "skill": round(skills[diff]),
        "zone": mem.get("last_target", -1),
        "weak": weak,
        "engaged": engaged,
        "diff": diff,
    }
