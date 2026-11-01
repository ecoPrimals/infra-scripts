#!/usr/bin/env python3
"""
print-scan-loop.py — The Pi Remainder Experiment

The chipmunk paints on the easel (digital canvas).
We print it on the Epson ET-2400 (ink tank → paper).
We scan it back (paper → digital).
The DELTA between generation N and generation N+1 is the pi remainder.
Information lost in the physical medium. Ink bleed. Paper fiber. Scanner optics.

After 1000 generations:
  - Sort by degradation (Shannon entropy per generation)
  - Find where the sigmoid knee is (the pi remainder)
  - Top 10% = test set (still recognizable, survived the fire)
  - Middle = training set (degraded but structured)
  - Bottom = ash (into the fire, but we KEEP the ash — it's data too)

Also: generate Escher tessellations and impossible figures.
Print THOSE. See what survives. Impossible geometry vs physical medium.

Hardware:
  Printer: EPSON_ET2400 (ink tank, refillable, organic ink bleed)
  Scanner: epson2:net:192.168.4.200 (flatbed, 75-600 DPI)
  Software: Pillow, scanimage (SANE), lp (CUPS), ImageMagick

scyBorg Triple License: AGPL-3.0 + ORC + CC-BY-SA 4.0
"""

import os
import sys
import json
import time
import math
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import numpy as np
except ImportError:
    print("Need: pip install Pillow numpy")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path("/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data/print-scan")
PRINTER = "EPSON_ET2400"
SCANNER = "epson2:net:192.168.4.200"
SCAN_DPI = 300
CANVAS_SIZE = (400, 400)  # Match easel canvas

# How many physical print→scan cycles
MAX_PHYSICAL_GENERATIONS = 20  # start here, scale up
# How many SIMULATED cycles (for the 1000)
MAX_SIMULATED_GENERATIONS = 1000


# ═══════════════════════════════════════════════════════════════
# PART 1: CHIPMUNK SELF-PORTRAIT GENERATOR
# Adapted from easel.html's painting logic → pure Python
# ═══════════════════════════════════════════════════════════════

def chipmunk_self_portrait(seed=42, style="membrane"):
    """The chipmunk paints itself. Returns PIL Image."""
    rng = np.random.RandomState(seed)
    img = Image.new('RGB', CANVAS_SIZE, (8, 6, 10))  # easel dark bg
    draw = ImageDraw.Draw(img)

    W, H = CANVAS_SIZE

    if style == "membrane":
        # The membrane self-portrait: concentric rings with feed data
        cx, cy = W // 2, H // 2

        # Outer membrane (green glow)
        for r in range(min(W, H) // 2, 0, -1):
            alpha = int(3 + 15 * math.exp(-((r - 120) ** 2) / 2000))
            alpha = min(255, alpha)
            g = 63 + int(120 * math.exp(-((r - 120) ** 2) / 3000))
            color = (0, min(255, g), int(g * 0.3))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color)

        # Inner prion shield (golden rings)
        for i in range(8):
            r = 40 + i * 12
            angle_offset = i * math.pi / 4
            for t in range(360):
                theta = math.radians(t) + angle_offset
                wobble = 3 * math.sin(theta * 5 + i)
                x = cx + (r + wobble) * math.cos(theta)
                y = cy + (r + wobble) * math.sin(theta)
                gold = (210, int(153 + rng.randint(-20, 20)), 34)
                draw.point((int(x), int(y)), fill=gold)

        # Chipmunk eyes — 2 focal points per eye, cross at the nose pillar
        nose_x, nose_y = cx, cy - 5  # the pillar of the nose, where gazes meet
        for eye_side, eye_x in [(-1, cx - 25), (1, cx + 25)]:
            eye_y = cy - 15

            # Outer eye (sclera)
            draw.ellipse([eye_x - 10, eye_y - 7, eye_x + 10, eye_y + 7],
                         fill=(30, 36, 45), outline=(88, 166, 255))

            # Iris
            draw.ellipse([eye_x - 5, eye_y - 5, eye_x + 5, eye_y + 5],
                         fill=(140, 120, 200))

            # Pupil — angled TOWARD the nose (convergence)
            pupil_dx = -eye_side * 2  # shift pupil toward nose
            draw.ellipse([eye_x + pupil_dx - 2, eye_y - 2,
                          eye_x + pupil_dx + 2, eye_y + 2],
                         fill=(10, 10, 15))

            # Focal line — from each eye to the nose pillar (binocular cross)
            draw.line([(eye_x, eye_y), (nose_x, nose_y)],
                      fill=(88, 166, 255, 40), width=1)

            # Second focal — each eye also has a far-field focal
            far_x = cx + eye_side * 60
            far_y = cy - 50
            draw.line([(eye_x, eye_y), (far_x, far_y)],
                      fill=(58, 58, 88), width=1)

        # Nose pillar — where binocular vision converges
        draw.ellipse([nose_x - 2, nose_y - 2, nose_x + 2, nose_y + 2],
                     fill=(210, 168, 255))

        # Whiskers — WAVE not flat. curves not lines.
        # Whiskers are vibrissae — sensory organs that detect vibrations
        # They should oscillate like the signals they detect
        for side in [-1, 1]:
            for w in range(4):
                x_start = cx + side * 18
                y_start = cy + 2 + w * 7
                # Draw whisker as a sine wave, not a straight line
                points = []
                whisker_len = 65 + rng.randint(0, 35)
                wave_freq = 2.5 + rng.random() * 2.0  # oscillation frequency
                wave_amp = 3 + rng.random() * 4  # oscillation amplitude
                droop = 0.15 + w * 0.1  # lower whiskers droop more
                for t in range(whisker_len):
                    frac = t / whisker_len
                    x = x_start + side * t
                    # Wave along the whisker + gentle droop
                    y = y_start + wave_amp * math.sin(frac * wave_freq * math.pi) + t * droop
                    points.append((int(x), int(y)))
                if len(points) > 1:
                    # Fade whisker from bright to dim
                    for i in range(len(points) - 1):
                        frac = i / len(points)
                        brightness = int(160 - 80 * frac)
                        color = (brightness, brightness, int(brightness * 1.1))
                        draw.line([points[i], points[i + 1]], fill=color, width=1)

        # Tiny self-label
        draw.text((10, H - 20), "chipmunk self-portrait #" + str(seed),
                  fill=(110, 118, 129))

    elif style == "escher_tessellation":
        # Generate an Escher-style tessellation
        _draw_tessellation(draw, W, H, rng, "escher")

    elif style == "impossible":
        # Generate an impossible figure (Penrose-style)
        _draw_impossible_triangle(draw, W, H, rng)

    elif style == "halftone_test":
        # Gradient test pattern for measuring degradation
        _draw_halftone_test(draw, W, H, rng)

    return img


def _draw_tessellation(draw, W, H, rng, tiling_type="escher"):
    """Generate Escher-style tessellations from scratch."""
    tile_size = 40
    cols = W // tile_size + 2
    rows = H // tile_size + 2

    # IH1 isohedral tiling: parallelogram with deformed edges
    # Each edge is replaced by a curve, paired edges get the same curve
    control_pts = [(rng.randint(-8, 8), rng.randint(-8, 8)) for _ in range(4)]

    for row in range(-1, rows):
        for col in range(-1, cols):
            x0 = col * tile_size + (row % 2) * (tile_size // 2)
            y0 = row * tile_size

            # Color based on checkerboard + hue shift
            hue_idx = (row + col) % 3
            colors = [
                (63, 185, 80),   # green (membrane)
                (210, 153, 34),  # gold (prion)
                (88, 166, 255),  # blue (water)
            ]
            base_color = colors[hue_idx]

            # Draw deformed tile
            pts = []
            corners = [(x0, y0), (x0 + tile_size, y0),
                       (x0 + tile_size, y0 + tile_size), (x0, y0 + tile_size)]

            for i in range(4):
                c1 = corners[i]
                c2 = corners[(i + 1) % 4]
                # Bezier-ish deformation along each edge
                mid_x = (c1[0] + c2[0]) // 2 + control_pts[i][0]
                mid_y = (c1[1] + c2[1]) // 2 + control_pts[i][1]
                pts.extend([c1, (mid_x, mid_y)])
            pts.append(pts[0])

            draw.polygon(pts[:8], fill=base_color, outline=(30, 36, 45))

            # Add creature features (eyes, limbs) like Escher's lizards
            cx_t = x0 + tile_size // 2
            cy_t = y0 + tile_size // 2
            if hue_idx == 0:
                # Lizard eye
                draw.ellipse([cx_t - 3, cy_t - 6, cx_t + 3, cy_t],
                             fill=(255, 255, 255), outline=(0, 0, 0))
                draw.ellipse([cx_t - 1, cy_t - 4, cx_t + 1, cy_t - 2],
                             fill=(0, 0, 0))


def _draw_impossible_triangle(draw, W, H, rng):
    """Penrose triangle — the impossible figure that printers must confront."""
    cx, cy = W // 2, H // 2
    size = min(W, H) * 0.35

    # Three bars of the Penrose triangle
    angles = [math.radians(a) for a in [90, 210, 330]]
    bar_width = size * 0.18
    colors = [(63, 185, 80), (210, 153, 34), (88, 166, 255)]

    for i in range(3):
        a1 = angles[i]
        a2 = angles[(i + 1) % 3]

        # Outer vertices
        ox1 = cx + size * math.cos(a1)
        oy1 = cy - size * math.sin(a1)
        ox2 = cx + size * math.cos(a2)
        oy2 = cy - size * math.sin(a2)

        # Inner vertices (shifted inward)
        inner_scale = 0.55
        ix1 = cx + size * inner_scale * math.cos(a1)
        iy1 = cy - size * inner_scale * math.sin(a1)
        ix2 = cx + size * inner_scale * math.cos(a2)
        iy2 = cy - size * inner_scale * math.sin(a2)

        # Draw the bar as a parallelogram
        # The impossible part: each bar's end OVERLAPS the next bar's beginning
        pts = [(ox1, oy1), (ox2, oy2), (ix2, iy2), (ix1, iy1)]
        draw.polygon(pts, fill=colors[i], outline=(230, 237, 243))

    # Center label
    draw.text((cx - 60, cy + size + 20),
              "impossible triangle #" + str(rng.randint(0, 999)),
              fill=(110, 118, 129))


def _draw_halftone_test(draw, W, H, rng):
    """Test pattern: gradients + text + shapes for measuring degradation."""
    # Horizontal gradient
    for x in range(W):
        gray = int(255 * x / W)
        draw.line([(x, 0), (x, H // 4)], fill=(gray, gray, gray))

    # Vertical gradient
    for y in range(H // 4, H // 2):
        gray = int(255 * (y - H // 4) / (H // 4))
        draw.line([(0, y), (W, y)], fill=(gray, gray, gray))

    # Concentric circles (moiré test)
    cx, cy = W // 2, 3 * H // 4
    for r in range(1, min(W, H) // 4, 2):
        color = (255, 255, 255) if r % 4 < 2 else (0, 0, 0)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color)

    # Fine text (degradation canary)
    for size_label, y_pos in [("12px", H // 2 + 10), ("8px", H // 2 + 30),
                               ("6px", H // 2 + 45), ("4px", H // 2 + 55)]:
        draw.text((10, y_pos), f"The quick brown fox — {size_label} — k≈1.9 ≈ 1/π",
                  fill=(255, 255, 255))

    draw.text((10, H - 20), "halftone test pattern — print/scan degradation canary",
              fill=(110, 118, 129))


# ═══════════════════════════════════════════════════════════════
# PART 2: PRINT → SCAN → MEASURE LOOP
# ═══════════════════════════════════════════════════════════════

def shannon_entropy(img):
    """Calculate Shannon entropy of an image (bits per pixel)."""
    arr = np.array(img.convert('L')).flatten()
    hist, _ = np.histogram(arr, bins=256, range=(0, 256))
    hist = hist[hist > 0]
    probs = hist / hist.sum()
    return -np.sum(probs * np.log2(probs))


def structural_similarity(img1, img2):
    """Simple SSIM-like metric between two images."""
    a1 = np.array(img1.convert('L'), dtype=np.float64)
    a2 = np.array(img2.convert('L'), dtype=np.float64)

    if a1.shape != a2.shape:
        # Resize to match
        img2_r = img2.resize(img1.size, Image.LANCZOS)
        a2 = np.array(img2_r.convert('L'), dtype=np.float64)

    mu1, mu2 = a1.mean(), a2.mean()
    s1, s2 = a1.std(), a2.std()
    cov = ((a1 - mu1) * (a2 - mu2)).mean()

    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2

    ssim = ((2 * mu1 * mu2 + c1) * (2 * cov + c2)) / \
           ((mu1 ** 2 + mu2 ** 2 + c1) * (s1 ** 2 + s2 ** 2 + c2))
    return float(ssim)


def pixel_hash(img):
    """SHA-256 of raw pixel data."""
    return hashlib.sha256(np.array(img).tobytes()).hexdigest()


def physical_print(image_path, printer=PRINTER):
    """Print an image file to the physical printer."""
    cmd = ["lp", "-d", printer, "-o", "fit-to-page", "-o", "media=A4",
           str(image_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"  PRINT ERROR: {result.stderr}")
        return False
    print(f"  → printed to {printer}: {result.stdout.strip()}")
    return True


def physical_scan(output_path, scanner=SCANNER, dpi=SCAN_DPI):
    """Scan from the flatbed scanner."""
    cmd = ["scanimage", "-d", scanner, "--mode", "Color",
           "--resolution", str(dpi), "--format=png",
           "-x", "100", "-y", "100",  # ~100mm square scan area
           "-o", str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  SCAN ERROR: {result.stderr}")
        return False
    print(f"  → scanned at {dpi}dpi: {output_path}")
    return True


def simulate_print_scan(img, generation, rng):
    """
    SIMULATE the print→scan cycle digitally.
    Models: ink bleed, paper texture, scanner noise, alignment drift, JPEG loss.
    Each effect is calibrated to approximate the Epson ET-2400's behavior.
    """
    arr = np.array(img, dtype=np.float64)

    # 1. INK BLEED — Gaussian blur (ink spreads on paper)
    #    ET-2400 is inkjet tank = more bleed than laser
    blur_sigma = 0.3 + 0.05 * math.log1p(generation)
    img_blur = img.filter(ImageFilter.GaussianBlur(radius=blur_sigma))
    arr = np.array(img_blur, dtype=np.float64)

    # 2. PAPER TEXTURE — additive noise (paper fiber + dust)
    paper_noise = rng.normal(0, 1.5 + 0.1 * generation, arr.shape)
    arr = arr + paper_noise

    # 3. INK QUANTIZATION — printers can't reproduce full 8-bit per channel
    #    ET-2400 prints at ~5760x1440 DPI but effective tonal resolution ≈ 6 bits
    quantize_levels = max(16, 64 - generation // 20)
    arr = np.round(arr / (256 / quantize_levels)) * (256 / quantize_levels)

    # 4. ALIGNMENT DRIFT — slight translation (paper placement varies)
    dx = rng.randint(-1, 2)
    dy = rng.randint(-1, 2)
    arr = np.roll(np.roll(arr, dx, axis=1), dy, axis=0)

    # 5. SCANNER GAMMA — scanners apply their own gamma curve
    arr = np.clip(arr, 0, 255)
    arr = 255.0 * (arr / 255.0) ** (0.98 + rng.normal(0, 0.01))

    # 6. SCANNER NOISE — CCD sensor noise
    scanner_noise = rng.normal(0, 0.8, arr.shape)
    arr = arr + scanner_noise

    # 7. SLIGHT ROTATION — scanner bed alignment
    rotation_deg = rng.normal(0, 0.1)
    result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if abs(rotation_deg) > 0.02:
        result = result.rotate(rotation_deg, resample=Image.BILINEAR,
                               expand=False, fillcolor=(8, 6, 10))

    # 8. JPEG COMPRESSION ARTIFACT — if scanner saves as JPEG
    #    (we simulate by save→load cycle at quality 85)
    import io
    buf = io.BytesIO()
    result.save(buf, format='JPEG', quality=max(50, 90 - generation // 10))
    buf.seek(0)
    result = Image.open(buf).copy()

    return result


# ═══════════════════════════════════════════════════════════════
# PART 3: THE EXPERIMENT
# ═══════════════════════════════════════════════════════════════

def run_experiment(style="membrane", mode="simulate", generations=100, seed=42):
    """
    Run the print→scan degradation experiment.

    mode="simulate" : 1000 cycles, digital simulation
    mode="physical"  : N cycles, actual printer+scanner
    mode="hybrid"    : first cycle physical, rest simulated from the scan
    """
    exp_dir = BASE_DIR / f"{style}_{mode}_{generations}gen"
    exp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"PRINT-SCAN LOOP: {style} / {mode} / {generations} generations")
    print(f"Output: {exp_dir}")
    print(f"{'='*60}\n")

    # Generate the original
    rng = np.random.RandomState(seed)
    original = chipmunk_self_portrait(seed=seed, style=style)
    original_path = exp_dir / "gen_000_original.png"
    original.save(str(original_path))
    print(f"Generation 0: original saved ({original.size})")

    # Measurement arrays
    measurements = []
    current = original.copy()

    for gen in range(1, generations + 1):
        gen_str = f"{gen:04d}"

        if mode == "physical":
            # PHYSICAL: print current, scan back
            print_path = exp_dir / f"gen_{gen_str}_print.png"
            scan_path = exp_dir / f"gen_{gen_str}_scan.png"
            current.save(str(print_path))

            if not physical_print(print_path):
                print(f"  ✗ Print failed at gen {gen}, switching to simulate")
                mode = "simulate"
            else:
                # Wait for print to complete
                print(f"  ⏳ Place printed page on scanner bed, press Enter...")
                if sys.stdin.isatty():
                    input()
                else:
                    time.sleep(10)

                if not physical_scan(scan_path):
                    print(f"  ✗ Scan failed at gen {gen}, switching to simulate")
                    mode = "simulate"
                else:
                    current = Image.open(str(scan_path))
                    current = current.resize(CANVAS_SIZE, Image.LANCZOS)

        if mode in ("simulate", "hybrid"):
            current = simulate_print_scan(current, gen, rng)

        # Save every Nth generation (and first 10, and last 10)
        if gen <= 10 or gen >= generations - 10 or gen % (generations // 20 + 1) == 0:
            save_path = exp_dir / f"gen_{gen_str}.png"
            current.save(str(save_path))

        # MEASURE
        entropy = shannon_entropy(current)
        ssim = structural_similarity(original, current)
        phash = pixel_hash(current)

        m = {
            "generation": gen,
            "entropy": round(entropy, 4),
            "ssim": round(ssim, 6),
            "hash": phash[:16],
            "mean_pixel": round(float(np.array(current.convert('L')).mean()), 2),
            "std_pixel": round(float(np.array(current.convert('L')).std()), 2),
        }
        measurements.append(m)

        if gen % 50 == 0 or gen <= 5:
            print(f"  Gen {gen:4d}: entropy={m['entropy']:.3f} bits  "
                  f"ssim={m['ssim']:.4f}  mean={m['mean_pixel']:.1f}  "
                  f"std={m['std_pixel']:.1f}")

    # ═══ ANALYSIS ═══
    print(f"\n{'='*60}")
    print("ANALYSIS: Finding the pi remainder")
    print(f"{'='*60}\n")

    entropies = [m['entropy'] for m in measurements]
    ssims = [m['ssim'] for m in measurements]

    # Find sigmoid knee (where degradation accelerates)
    # Use second derivative of SSIM
    if len(ssims) > 10:
        d1 = np.diff(ssims)
        d2 = np.diff(d1)
        knee_idx = int(np.argmin(d2)) + 2  # where curvature is most negative
        knee_gen = measurements[knee_idx]['generation']
        knee_ssim = measurements[knee_idx]['ssim']
    else:
        knee_gen = len(measurements) // 3
        knee_ssim = ssims[knee_gen - 1] if knee_gen > 0 else 1.0

    # Pi remainder: what fraction of information survives?
    final_ssim = ssims[-1]
    initial_entropy = entropies[0]
    final_entropy = entropies[-1]
    entropy_ratio = final_entropy / initial_entropy if initial_entropy > 0 else 0
    one_over_pi = 1.0 / math.pi

    # Sort into sets
    # Top 10% by SSIM = test set (survived the fire)
    # Bottom 10% = ash (but we keep it)
    sorted_by_ssim = sorted(measurements, key=lambda m: m['ssim'], reverse=True)
    n = len(sorted_by_ssim)
    test_set = sorted_by_ssim[:n // 10]
    training_set = sorted_by_ssim[n // 10: 9 * n // 10]
    ash_set = sorted_by_ssim[9 * n // 10:]

    results = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "title": f"Print-Scan Loop: {style} — {generations} generations",
        "experiment": {
            "style": style,
            "mode": mode,
            "generations": generations,
            "seed": seed,
            "printer": PRINTER,
            "scanner": SCANNER,
            "canvas_size": list(CANVAS_SIZE),
        },
        "degradation_curve": {
            "initial_entropy": round(initial_entropy, 4),
            "final_entropy": round(final_entropy, 4),
            "entropy_ratio": round(entropy_ratio, 4),
            "one_over_pi": round(one_over_pi, 4),
            "entropy_ratio_vs_pi": round(abs(entropy_ratio - one_over_pi), 4),
            "initial_ssim": round(ssims[0], 6),
            "final_ssim": round(final_ssim, 6),
            "sigmoid_knee_generation": knee_gen,
            "sigmoid_knee_ssim": round(knee_ssim, 6),
        },
        "pi_remainder": {
            "thesis": "Information lost in print→scan = physical medium's tax. The remainder after 1000 generations should converge toward a constant determined by the physics of ink, paper, and optics. If that constant relates to 1/π, the physical medium IS a pi-sorted system.",
            "final_information_retained": round(final_ssim, 4),
            "final_entropy_bits": round(final_entropy, 4),
            "is_near_one_over_pi": bool(abs(entropy_ratio - one_over_pi) < 0.05),
        },
        "sort_sets": {
            "test_set_size": len(test_set),
            "test_set_gen_range": [test_set[-1]['generation'], test_set[0]['generation']] if test_set else [],
            "training_set_size": len(training_set),
            "ash_set_size": len(ash_set),
            "ash_set_gen_range": [ash_set[0]['generation'], ash_set[-1]['generation']] if ash_set else [],
        },
        "measurements_sample": measurements[::max(1, len(measurements) // 20)],

        "scyborg_triple_license": {
            "AGPL_3_0": "code (this script, all analysis)",
            "ORC": "the print→scan loop IS a game mechanic — generational degradation as gameplay, sorting as scoring",
            "CC_BY_SA_4_0": "all generated art, all measurements, all publications",
        }
    }

    # Save results
    results_path = exp_dir / "results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Also publish to HUD feeds
    feed_path = BASE_DIR.parent / "print-scan-loop.json"
    with open(feed_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nRESULTS:")
    print(f"  Entropy: {initial_entropy:.3f} → {final_entropy:.3f} bits "
          f"(ratio: {entropy_ratio:.4f}, 1/π: {one_over_pi:.4f}, "
          f"Δ: {abs(entropy_ratio - one_over_pi):.4f})")
    print(f"  SSIM:    1.000 → {final_ssim:.4f}")
    print(f"  Sigmoid knee: generation {knee_gen} (ssim={knee_ssim:.4f})")
    print(f"  Test set: {len(test_set)} generations (survived the fire)")
    print(f"  Training: {len(training_set)} generations")
    print(f"  Ash:      {len(ash_set)} generations (into the fire)")
    print(f"\n  Results: {results_path}")
    print(f"  Feed:    {feed_path}")

    return results


# ═══════════════════════════════════════════════════════════════
# PART 4: ESCHER TESSELLATION GALLERY
# ═══════════════════════════════════════════════════════════════

def generate_escher_gallery(count=12):
    """Generate a gallery of tessellations and impossible figures for printing."""
    gallery_dir = BASE_DIR / "escher_gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)

    styles = ["escher_tessellation", "impossible", "halftone_test"]
    manifest = []

    for i in range(count):
        style = styles[i % len(styles)]
        seed = 100 + i
        img = chipmunk_self_portrait(seed=seed, style=style)
        path = gallery_dir / f"escher_{i:03d}_{style}.png"
        img.save(str(path))

        entropy = shannon_entropy(img)
        manifest.append({
            "id": i,
            "style": style,
            "seed": seed,
            "entropy": round(entropy, 4),
            "hash": pixel_hash(img)[:16],
            "path": str(path.name),
        })
        print(f"  Generated {style} #{i} (entropy={entropy:.3f})")

    manifest_path = gallery_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nGallery: {count} images in {gallery_dir}")
    return manifest


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Print-Scan Loop — The Pi Remainder Experiment")
    parser.add_argument("--mode", choices=["simulate", "physical", "hybrid"],
                        default="simulate", help="simulate (digital), physical (real printer), hybrid")
    parser.add_argument("--style", choices=["membrane", "escher_tessellation", "impossible", "halftone_test"],
                        default="membrane", help="what to paint")
    parser.add_argument("--generations", type=int, default=100, help="number of generations")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--gallery", action="store_true", help="generate Escher gallery instead of loop")
    parser.add_argument("--all", action="store_true", help="run all styles through simulation")
    args = parser.parse_args()

    if args.gallery:
        generate_escher_gallery()
    elif args.all:
        for style in ["membrane", "escher_tessellation", "impossible", "halftone_test"]:
            run_experiment(style=style, mode="simulate",
                           generations=args.generations, seed=args.seed)
    else:
        run_experiment(style=args.style, mode=args.mode,
                       generations=args.generations, seed=args.seed)
