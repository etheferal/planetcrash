import math
import os
import sys
import time
import numpy as np

# Windows terminalinde ANSI renk ve kaçış dizilerini aktif et
if os.name == 'nt':
    os.system('')

# Ekranı temizle ve imleci gizle
sys.stdout.write('\033[?25l\033[2J')
sys.stdout.flush()

# Karakter seti (karanlıktan aydınlığa)
CHARS = np.array(
    list(" .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$")
)

# Terminal ızgarası boyutları
WIDTH, HEIGHT = 75, 26

# Koordinat ızgarası (-1.0 ile 1.0 arası normalize)
y_indices, x_indices = np.indices((HEIGHT, WIDTH))
x = (x_indices - WIDTH / 2) / (WIDTH / 2)
# Karakterlerin dikey/yatay oran farkını eşitlemek için dikey ölçek
y = (y_indices - HEIGHT / 2) / (HEIGHT / 2) * 2.1

# Arka plan için sabit rastgele yıldızlar
np.random.seed(42)
star_mask = (np.random.rand(HEIGHT, WIDTH) > 0.985).astype(np.float32)
star_twinkle_phase = np.random.rand(HEIGHT, WIDTH) * 2 * np.pi


def smooth_min(d1, d2, k=0.35):
    """Metaball (yumuşak birleşme) için smin fonksiyonu"""
    h = np.clip(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0)
    return d2 * (1.0 - h) + d1 * h - k * h * (1.0 - h), h


def render_frame(t):
    # Gezegenlerin yaklaşma ve birleşme hareketi (mesafe döngüsü)
    # -1 ile 1 arasında yumuşak gidip gelme
    cycle = 0.5 + 0.5 * np.cos(t * 1.2)
    # distance: 0.8 (uzak) -> 0.0 (tamamen birleşmiş)
    dist_offset = 0.85 * cycle

    # 1. Gezegen (Mavi - Sol)
    p1_x, p1_y = -dist_offset, 0.0
    # 2. Gezegen (Turuncu - Sağ)
    p2_x, p2_y = dist_offset, 0.0

    # Gezegen yarıçapları (birleştikçe kütle çekimiyle hafifçe büyür)
    base_r = 0.38 + 0.06 * (1.0 - cycle)
    d1 = np.sqrt((x - p1_x) ** 2 + (y - p1_y) ** 2) - base_r
    d2 = np.sqrt((x - p2_x) ** 2 + (y - p2_y) ** 2) - base_r

    # Gezegenlerin yüzey birleşimi ve karışım faktörü (blend)
    dist_merged, blend = smooth_min(d1, d2, k=0.45)

    # Katı gövde maskesi ve atmosferik ışıma (glow)
    body_mask = np.clip(-dist_merged * 6.0, 0.0, 1.0)
    glow_mask = np.clip(np.exp(-np.maximum(dist_merged, 0.0) * 4.0), 0.0, 1.0)

    # 3B küresel gölgelendirme (ışık merkezden vuruyor gibi parlaklık)
    sphere_shade = np.clip(1.0 - np.maximum(dist_merged, -base_r) / base_r, 0, 1)

    # --- Renk Paletleri ---
    # Mavi Gezegen: Canlı Cyan / Kobalt Mavi
    blue_r, blue_g, blue_b = 30.0, 140.0, 255.0
    # Turuncu Gezegen: Canlı Ateş Turuncusu / Altın
    orange_r, orange_g, orange_b = 255.0, 110.0, 25.0

    # İki gezegen renginin karışımı: blend = 1 ise Mavi, blend = 0 ise Turuncu
    # Ortada birleşirken mor/magenta ve akkor altın tonları oluşturan katkı
    mixed_r = blue_r * blend + orange_r * (1.0 - blend)
    mixed_g = blue_g * blend + orange_g * (1.0 - blend)
    mixed_b = blue_b * blend + orange_b * (1.0 - blend)

    # Birleşme hattında açığa çıkan yüksek enerji (mor/magenta ve beyazımsı parıltı)
    overlap_zone = 4.0 * blend * (1.0 - blend) * (1.0 - cycle)
    mixed_r += overlap_zone * 60.0
    mixed_g += overlap_zone * 20.0
    mixed_b += overlap_zone * 100.0

    # RGB Kanallarını birleştirme
    r = (mixed_r * sphere_shade) * body_mask + (mixed_r * 0.4) * glow_mask
    g = (mixed_g * sphere_shade) * body_mask + (mixed_g * 0.4) * glow_mask
    b = (mixed_b * sphere_shade) * body_mask + (mixed_b * 0.4) * glow_mask

    # Arka plan yıldızları (parıldayan beyaz/hafif mavi noktalar)
    twinkle = 0.4 + 0.6 * np.sin(t * 3.0 + star_twinkle_phase)
    stars = star_mask * (1.0 - np.clip(glow_mask * 1.5, 0, 1)) * twinkle
    r += stars * 220
    g += stars * 230
    b += stars * 255

    # Yoğunluk (Luminance) hesabı ve ASCII karakter eşleme
    intensity = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0
    char_indices = np.clip(
        (intensity * (len(CHARS) - 1)).astype(int), 0, len(CHARS) - 1
    )
    frame_chars = CHARS[char_indices]

    # Terminal çıktısını derleme (ANSI 24-bit TrueColor)
    output = ["\033[H"]
    for i in range(HEIGHT):
        row = []
        for j in range(WIDTH):
            ch = frame_chars[i, j]
            red = int(np.clip(r[i, j], 0, 255))
            green = int(np.clip(g[i, j], 0, 255))
            blue = int(np.clip(b[i, j], 0, 255))
            row.append(f"\033[38;2;{red};{green};{blue}m{ch}")
        output.append("".join(row))

    output.append("\033[0m")
    sys.stdout.write("\n".join(output))
    sys.stdout.flush()


def main():
    try:
        t = 0.0
        while True:
            render_frame(t)
            time.sleep(0.035)  # ~30 FPS
            t += 0.045
    except KeyboardInterrupt:
        # Programdan çıkıldığında imleci geri getir
        sys.stdout.write("\033[?25h\033[0m\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()