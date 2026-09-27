# BEAT THE AI — Pong

Gözlüklü Terminator'un arka planda izlediği, rakibi **öğrenen ve güçlenen** bir Pong.
Top hızlandıkça **JUDGMENT DAY** moduna geçilir: rakip alevlere bürünür, gerçek
*Terminator 2* tema müziği çalar ve rakip "terminatör" gibi oynar.

Oyun tek HTML dosyasında (Canvas + WebAudio). Rakibin **beyni Python sunucuda**
çalışır; sunucu kapalıyken tarayıcıdaki yerel yedek AI devreye girer (o da aynı
fizikle çalışır, sadece hafızası ve nişan kalitesi düşük olur).

---

## 🚀 Oyunu Çalıştırma

Bağımlılık yok — saf Python `stdlib` yeterlidir.

```bash
cd pong_game
python3 server.py
```

Tarayıcıda aç: **http://localhost:8077/**
(Aynı ağdaki başka cihazdan: `http://<bilgisayar-ip-adın>:8077/`)

Başlatma mesajı:

```
Pong sunucu: http://localhost:8077  (beyin: /brain, hafıza: /ai_memory)
```

> İnternet tarayıcısı açılışında bir kez tuşa/fareye dokunulması gerekir (ses
> için tarayıcı otomatik oynatma kuralı).

### Sunucuyu kapatma
`Ctrl+C` veya
```bash
pkill -f "server.py"
```

---

## 🎮 Nasıl Oynanır

| Tuş | İşlev |
|-----|-------|
| `↑` / `↓` veya `W` / `S` | Raketin yukarı / aşağı hareketi |
| Fare / dokunmatik | Raketini fare imlecine taşır |
| `SPACE` | Maçı başlat · skordan sonra topu servis et · biten maçta yeniden başla |
| `R` | Maçı sıfırdan başlat (skorlar sıfırlanır) |
| `1` `2` `3` `4` | Harita seçimi (aşağı) |
| `Q` / `E` | Haritayı bir önceki / sonraki yap (döngü) |
| `L` | Rakibin öğrenme hafızasını sıfırla |
| Ekran altı butonlar | `SES AÇ/KAPAT` · `HAFIZAYI SIFIRLA` · harita seçimi |
| `EXIT` butonu | Sunucuyu kapatır (`POST /shutdown`; onay sorar, beyin hafızası diskte kalır) |

**Kazanma:** 7 sayıya ilk ulaşan kazanır.
Raketinin neresine çarparsan top o açıyla döner (kenar = keskin açı, merkez = düz).
Her vuruşta top biraz hızlanır; hız eşiği aşılınca JUDGMENT DAY modu tetiklenir.

---

## 🗺️ Haritalar

Seçim: `1-4` tuşları, `Q/E` döngü ya da ekran altı butonlar. Son seçim tarayıcıda
kalıcıdır (localStorage).

| Tuş | Harita | Özellik |
|-----|--------|---------|
| 1 | **Klasik** | Orijinal saha |
| 2 | **Boşluk** | Yıldız alanı + gezegen, **dairesel yörüngede dolaşan asteroid** |
| 3 | **Yer Altı** | Ortada metal daire engel — topa çarpıp sektirir |
| 4 | **Sanayi** | Parlayan çelik barlar, **alçalıp yükselen iki buhar pistonu** |

Hareketli / sabit engeller (2, 3, 4) topa çarpınca onu normal boyunca sektirir.
Beyin ve yerel yedek AI, engel konumunu **adım adım simüle ederek** yörünge
tahminine katar — yani rakip engeli "görüp" hesaplar, rastgele kaçmaz.

---

## 🧠 Rakip (Beyin) Nasıl Çalışır

Rakip **öğrenen, kalıcı hafızalı** bir AI'dır. Üç katmanlı düşünüp oynar:

1. **Göz (yörünge tahmini):** Topa doğru geldiğinde topu ileri sarar;
   duvar sekmeleri **ve harita engelleri dahil** topun kendi raketiyle
   buluşacağı y'yi hesaplar. Bu yüzden topun peşinden koşmaz, *varacağı yeri*
   bekler.
2. **Beyin (nişan + hafıza):** Ekranı 10 dikey bölgeye böler. İki haritayı tutar:
   - **Savunma ısı haritası** — neredede sık durduğunu sayar.
   - **Zayıf bölge banditi** — hangi bölgeden atışta kaçırdığını sayar;
     kaçırdığın bölge "zayıf" olur ve o bölgeye atış ağırlığı artar.
   Sonra 60 aday raket konumunu simüle edip topu hedef bölgeye gönderecek
   **en isabetli temas noktasına** yerleşir (nişan açısı ayarlanır).
3. **Vücut (hareket):** Raket hedefe hız limitli yaklaşır. JUDGMENT DAY modunda
   nişan hatası sıfırlanır ve hız topun dikey hızını geçecek kadar artar
   → neredeyse yenilmez "terminatör" refleks.

### Öğrenme & hafıza
- Sayı senin lehine açıldıkça **beceri** hızla yükselir (daha keskin nişan,
  daha hızlı raket, daha az hata); rakip lehine açıldığında hafifçe gevşer.
- Tüm bunlar `ai_memory.json` dosyasına kalıcı yazılır — oyunu kapatıp açsan da
  öğrendiklerini hatırlar. `L` tuşu / "HAFIZAYI SIFIRLA" butonu hafızayı sıfırlar.
- Zayıf bölgeler sahanın sol kenarında ince kırmızı şeritlerle gösterilir.

> **"Beyin çevrimiçi / çevrimdışı" göstergesi:** Rakibin beyni Python sunucuda
> çalışır. Sunucu ayakta ve `/brain` cevap veriyorsa **çevrimiçi** (yeşil) olur ve
> öğrenen, hafızalı beyin yönetir. Sunucuya ulaşılamazsa **çevrimdışı**
> (kırmızı) olur ve tarayıcıdaki yerel yedek AI devreye girer — oyun yine de
> oynanabilir, sadece rakip hafızasız ve biraz daha sığdır.

---

## 🔥 JUDGMENT DAY Modu

Topun hızı eşiği (12) geçince:
- Rakip raket **alevlere bürünür** (parçacık efekti).
- Ekran üstünde **⚠ JUDGMENT DAY ⚠** uyarısı yanıp söner.
- Gerçek *Terminator 2* tema müziği (`terminator_music.webm`) döngüde çalar.
- Rakip terminatör refleks moduna geçer (sıfır hata, yüksek hız).

Skor arası mod ve müzik kesilir, top yeni servisle yavaş başlar.

---

## 🛠️ Teknik Yapı & Test

| Dosya | Görev |
|-------|-------|
| `server.py` | Statik dosyalar + `/brain` POST + `/clear_memory`, `/ai_memory` (saf stdlib) |
| `brain.py` | Öğrenen AI: yörünge/engel simülasyonu, nişan optimizasyonu, disk hafızası |
| `pong.html` | İstemci: Canvas oyun, WebAudio ses, tema müziği, yerel yedek AI, haritalar |
| `selfplay.py` | Headless test: gerçek fizik taklidiyle AI'ı referans rakibe karşı koşturur |
| `terminator_music.webm` | JUDGMENT DAY tema müziği |
| `ai_memory.json` | AI'ın kalıcı öğrenme durumu — `.gitignore`'lanmıştır, her kurulumda temiz başlar |

Kendi kendine oynama testi:
```bash
python3 selfplay.py 5
```

### API
- `POST /brain` — durum gönder, `{aiY, skill, zone, weak, engaged, diff}` dön.
  Durum alanları: `bx,by,vx,vy,speed,px,ay,phase,score_p,score_a,missed_player,
  dtMs,diff,term,obstacles[]` (hareketli engeller `move:{type,a|ph}` ile gelir).
- `GET /brain` — sağlık kontrolü.
- `GET /ai_memory` — güncel öğrenme durumu.
- `GET /clear_memory` — hafızayı sıfırla.
- `POST /shutdown` — sunucuyu kapatır (oyun içi `EXIT` butonu bunu çağırır;
  beyin hafızası diskte `ai_memory.json` olarak kalır).

---

## 🪟 Windows'ta Çalıştırma

Oyun tarayıcı tabanlıdır; `.exe`'ye dönüştürmek zorunlu değildir. İki seçenek:

### Seçenek 1 — Python ile (önerilen, bağımlılık yok)
Windows makinesine Python kur (python.org → kurulumda **"Add Python to PATH"** kutusunu
işaretle). Sonra bu klasörde:
```bat
baslat.bat
```
Bu, `python3 server.py` çalıştırıp tarayıcıyı otomatik açar.
Sunucu `0.0.0.0:8077` dinlediği için **aynı ağdaki telefon/arkadaş**
`http://<Windows-PC-IP>:8077` ile katılabilir.

### Seçenek 2 — Tek dosya EXE
Aşağıdaki **Build Alma** bölümüne bak: bu makineden `./build-windows.sh`
(wine ile) ya da Windows'ta `exe-yap.bat` ile `Pong.exe` üret, paylaş.

## 📦 Build Alma (Linux + Windows binary'si)

Oyun tarayıcı tabanlıdır; ama tek dosyalık derlenebilir binary üretmek için
scriptler hazırdır (çıktılar repo'ya girmeden, GitHub Release olarak da
paylaşılabilir):

| Script | Ne yapar | Nerede |
|--------|----------|--------|
| `./baslat.sh [port]` | Oyunu çalıştırır (Linux, Python gerekir) | Linux |
| `./build.sh` | **Linux binary** → `dist/Pong` | Linux |
| `./build-windows.sh` | **Windows `.exe`** → `dist-windows/Pong.exe` | bu Linux makinesi (wine) ya da Wine'lı herhangi bir makine |
| `exe-yap.bat` | Windows `.exe` | Windows (yerel, PyInstaller) |
| `baslat.bat` | Oyunu çalıştırır | Windows |

- `build.sh` kendi sanal ortamını (`.build-venv/`) kurar, PyInstaller'i ana
  Python'a dokunmadan oraya kurar; ilk çalıştırmada kendi kendini hazırlar.
- `build-windows.sh` Linux'tan **cross-derleme** yapar: wine içine
  python.org'dan Windows Python kurar (ilk kez ~1-2 dk, sonra önbellek olur
  `~/.wine-pong`), PyInstaller'i wine'da çalıştırır. Gereksinim: `wine`.
  Windows makinesi yok, wine'ın da olmadığı ortamlar için `.github/workflows/release.yml`
  vardır: `git tag v1.0 && git push origin v1.0` → GitHub'ın kendi
  runner'larında **hem Linux hem Windows binary'si** derlenir ve
  **GitHub Release** varlığı olarak eklenir (binary repo'ya girmez).
- Platform ayrımı: Linux binary'si sadece Linux x86_64, `Pong.exe` sadece
  64-bit Windows'ta çalışır. (PyInstaller hedef OS'te derler.)

Örnek:

```bash
./build.sh           # Linux:  dist/Pong
./build-windows.sh   # Windows: dist-windows/Pong.exe  (wine gerekir)
```

### Eski/alternatif yol (Windows makinesinde)
`exe-yap.bat` hâlâ çalışır: Windows makinesinde `pip install pyinstaller`
yapar, `dist\Pong.exe` üretir (tek dosya — `brain.py` ayrı göndermen gerekmez;
AI hafızası `Pong.exe`'nin yanına `ai_memory.json` olarak yazılır).

### EXE'de "not found" (404) çıkarsa
Tarayıcıda `http://localhost:8077/` açıldığında `not found: /pong.html (aranan
dizinler: ...)` görürsen, bu sunucunun **çalıştığının** kanıtıdır; `pong.html`
içine gömülmemiş demektir. `exe-yap.bat` şu `--add-data` satırlarını içerir:
```bat
--add-data "pong.html;." --add-data "terminator_music.webm;."
```
Bu iki satırı silip exe'yi yeniden derle (veya `pong.html` + `terminator_music.webm`
dosyalarını `Pong.exe`'nin yanına koy). Ayrıca tarayıcı adres çubuğunda
`http://localhost:8077/pong.html` ile de deneyebilirsin — doğrudan dosya
yoluyla 200 alıyorsan sorun `--add-data`'dır; almıyorsan exe içinde `pong.html`
yok demektir.

> **Neden exe bu Linux makinesinden verilmedi?** PyInstaller hedef OS'te derler
> (Windows `.exe`'i Windows'ta, Linux binary'si Linux'ta). `build-windows.sh`
> bu yüzden wine içine Windows Python kurup PyInstaller'i wine'da çalıştırır
> (ilk kurulum ~1-2 dk); wine yoksa GitHub workflow'u (`.github/workflows/release.yml`)
> Windows runner'ında derler. Oluşan `Pong.exe`'yi paylaşabilirsin.

### Paylaşım ipuçları
- **En kolayı:** repo klasörünü ZIP'le, arkadaşın indirsin → Python kuru → `baslat.bat` / `./baslat.sh`.
- **Hazır binary:** `./build.sh` (Linux) + `./build-windows.sh` (Windows exe) →
  çıktıları GitHub Release'e ekle ya da ZIP'le paylaş.
- İki taraf da `ai_memory.json` üretir; bu dosya `.gitignore`'da olduğu için
  her kurulum "temiz beyinle" başlar (öğrenme makineye özel kalır).
