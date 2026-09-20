# pong_game

Öğrenen, güçlenen yapay zekâ rakipli bir Pong. Oyun HTML/Canvas'ta, rakibin **beyni Python sunucuda** çalışıyor.

## Nasıl çalışır

- `server.py` — Statik dosyalar + `/brain` endpoint'ini servis eder (saf stdlib, bağımlılık yok).
- `brain.py` — ÖĞRENEN AI: savunma ısı haritası + zayıf-bölge banditi + optimizasyon tabanlı nişancılık. Hafızayı `ai_memory.json`'a **diskte** kalıcı tutar.
- `pong.html` — İstemci: Canvas oyun + WebAudio ses efektleri. Her karede durumu `/brain`'e gönderir, AI'nın hedef konumunu uygular. Beyin yanıt vermezse yerel yedek AI'ya düşer.
- `selfplay.py` — Kendi kendine oynama (headless) testi: gerçek oyun fizik taklidiyle AI'ı referans rakibe karşı koşturur.

## Çalıştırma

```bash
python3 server.py
# tarayıcıda: http://localhost:8077/
```

Zorluk modları (başta butonlar / `1 2 3 4`):

| Mod | Başlangıç beceri |
|-----|------------------|
| Kolay | 10 |
| Orta | 35 |
| Zor | 60 |
| Çok Zor | 85 |

Her mod **baştan hazır zekâ** ile gelir; oyuncu üstünlük kurdukça beceri o temelin üstüne canlı artar, rakip üstünlük kurunca gevşer. Öğrenme kalıcıdır (mod başına ayrı saklanır).

Kontroller: `↑ ↓` / `W S` / fare · `SPACE` başlat · `R` yeniden · `1 2 3 4` mod · `L` hafızayı sıfırla.

## Test

```bash
python3 selfplay.py 5   # her modu 5'er maç kendinden oynatır
```

## Dosyalar

- `ai_memory.json` — AI'nın kalıcı öğrenme durumu; `.gitignore`'lanmıştır (her kurulumda temiz başlar).
