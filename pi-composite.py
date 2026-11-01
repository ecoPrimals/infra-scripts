#!/usr/bin/env python3
"""
pi-composite.py — Pi-filter all paintings to a single composite signal.

Takes ALL generation images across ALL experiments.
Pi-sorts them (frac(n × π) position determines layer alpha and placement).
Composites into ONE image: the pi-filtered signal.

Also fixes the chipmunk anatomy:
  - Eyes focal lines extend to become EARS (audio antennae)
  - L eye → L ear, R eye → R ear
  - The angle of the focal line IS the angle of the audio pickup
  - Binocular vision and binaural hearing share the SAME axis

scyBorg Triple License: AGPL-3.0 + ORC + CC-BY-SA 4.0
"""

import os
import sys
import math
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np

BASE = Path("/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data/print-scan")
OUTPUT = BASE.parent
CANVAS = (800, 800)  # composite is 2× the painting size
PI = math.pi


# ═══════════════════════════════════════════════════════════════
# PI FILTER — sort all images by frac(n × π)
# ═══════════════════════════════════════════════════════════════

def pi_position(n):
    """Where does image N land on the unit circle? frac(n × π)."""
    return (n * PI) % 1.0


def pi_alpha(n, total):
    """Alpha for layer N: pi-sorted, so irrational spacing."""
    pos = pi_position(n)
    # Alpha peaks at 1/π position (0.3183) and fades from there
    distance_from_pi = abs(pos - (1.0 / PI))
    # Sigmoid falloff from the pi position
    alpha = 1.0 / (1.0 + math.exp(10 * (distance_from_pi - 0.15)))
    # Scale: peak at ~0.3, minimum at ~0.01
    return 0.01 + 0.29 * alpha


def collect_all_images():
    """Find all generation images across all experiments."""
    images = []
    idx = 0

    for exp_dir in sorted(BASE.glob("*_simulate_*")):
        if not exp_dir.is_dir():
            continue
        style = exp_dir.name.split("_simulate")[0]

        for img_path in sorted(exp_dir.glob("gen_*.png")):
            name = img_path.stem  # gen_0042
            gen_num = int(name.split("_")[1]) if "_" in name else 0
            images.append({
                "path": img_path,
                "style": style,
                "generation": gen_num,
                "index": idx,
                "pi_pos": pi_position(idx),
                "pi_alpha": pi_alpha(idx, 1),
            })
            idx += 1

    # Add gallery images
    gallery = BASE / "escher_gallery"
    if gallery.exists():
        for img_path in sorted(gallery.glob("*.png")):
            images.append({
                "path": img_path,
                "style": "gallery",
                "generation": 0,
                "index": idx,
                "pi_pos": pi_position(idx),
                "pi_alpha": pi_alpha(idx, 1),
            })
            idx += 1

    # Add v2 portraits
    for img_path in sorted(BASE.glob("chipmunk-v2-*.png")):
        images.append({
            "path": img_path,
            "style": "portrait",
            "generation": 0,
            "index": idx,
            "pi_pos": pi_position(idx),
            "pi_alpha": pi_alpha(idx, 1),
        })
        idx += 1

    return images


# ═══════════════════════════════════════════════════════════════
# CHIPMUNK WITH EARS — focal lines become audio antennae
# ═══════════════════════════════════════════════════════════════

def draw_chipmunk_with_ears(size=800, seed=42):
    """
    The FULL chipmunk: eyes with binocular convergence,
    focal lines that extend to become EARS (audio antennae).

    L eye focal → extends up-left → L ear
    R eye focal → extends up-right → R ear
    The visual axis and the auditory axis are the SAME line.
    """
    rng = np.random.RandomState(seed)
    img = Image.new('RGBA', (size, size), (8, 6, 10, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    scale = size / 400  # scale factor from 400px base

    # === OUTER MEMBRANE ===
    for r in range(int(size * 0.48), 0, -1):
        ring_r = r / scale
        g = 63 + int(120 * math.exp(-((ring_r - 120) ** 2) / 3000))
        color = (0, min(255, g), int(g * 0.3))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color)

    # === PRION SHIELD (golden rings) ===
    for i in range(8):
        r = int((40 + i * 12) * scale)
        for t in range(720):
            theta = math.radians(t / 2) + i * PI / 4
            wobble = 3 * scale * math.sin(theta * 5 + i)
            x = cx + (r + wobble) * math.cos(theta)
            y = cy + (r + wobble) * math.sin(theta)
            gold = (210, 153 + rng.randint(-20, 20), 34)
            draw.point((int(x), int(y)), fill=gold)

    # === NOSE PILLAR ===
    nose_x, nose_y = cx, int(cy - 5 * scale)

    # === EARS — positioned along the extended eye focal axis ===
    ear_positions = {}
    for side_name, side, eye_x_offset in [("left", -1, -25), ("right", 1, 25)]:
        eye_x = int(cx + eye_x_offset * scale)
        eye_y = int(cy - 15 * scale)

        # The focal axis extends from eye THROUGH far field to the ear
        # Ear is above and to the side — like a chipmunk's real ear
        ear_x = int(cx + side * 80 * scale)
        ear_y = int(cy - 90 * scale)
        ear_positions[side_name] = (ear_x, ear_y)

        # === AUDIO ANTENNA LINE — the focal line IS the ear ===
        # Draw as a dashed line from eye to ear (the antenna)
        steps = 40
        for t in range(steps):
            frac = t / steps
            lx = eye_x + frac * (ear_x - eye_x)
            ly = eye_y + frac * (ear_y - eye_y)
            # Wave along the antenna (it vibrates with sound)
            wave = 2 * scale * math.sin(frac * 6 * PI)
            perp_x = -(ear_y - eye_y) / max(1, math.sqrt((ear_x - eye_x)**2 + (ear_y - eye_y)**2))
            perp_y = (ear_x - eye_x) / max(1, math.sqrt((ear_x - eye_x)**2 + (ear_y - eye_y)**2))
            lx += wave * perp_x
            ly += wave * perp_y

            # Color: transitions from visual blue to auditory gold
            r_c = int(88 + frac * (210 - 88))
            g_c = int(166 + frac * (153 - 166))
            b_c = int(255 + frac * (34 - 255))
            brightness = int(180 - 80 * frac)
            draw.ellipse([int(lx) - 1, int(ly) - 1, int(lx) + 1, int(ly) + 1],
                         fill=(r_c, g_c, b_c))

        # === EAR (the terminus of the antenna) ===
        ear_r = int(18 * scale)
        # Outer ear (pinna — the dish that catches sound)
        draw.ellipse([ear_x - ear_r, ear_y - int(ear_r * 1.3),
                      ear_x + ear_r, ear_y + int(ear_r * 1.3)],
                     fill=(45, 35, 25), outline=(210, 153, 34))
        # Inner ear (warm)
        inner_r = int(ear_r * 0.6)
        draw.ellipse([ear_x - inner_r, ear_y - int(inner_r * 1.2),
                      ear_x + inner_r, ear_y + int(inner_r * 1.2)],
                     fill=(140, 80, 60))

        # === EYE ===
        er = int(10 * scale)
        draw.ellipse([eye_x - er, eye_y - int(er * 0.7),
                      eye_x + er, eye_y + int(er * 0.7)],
                     fill=(30, 36, 45), outline=(88, 166, 255))
        # Iris
        ir = int(5 * scale)
        draw.ellipse([eye_x - ir, eye_y - ir, eye_x + ir, eye_y + ir],
                     fill=(140, 120, 200))
        # Convergent pupil
        pd = int(-side * 2 * scale)
        pr = int(2.5 * scale)
        draw.ellipse([eye_x + pd - pr, eye_y - pr,
                      eye_x + pd + pr, eye_y + pr],
                     fill=(10, 10, 15))
        # Focal to nose
        draw.line([(eye_x, eye_y), (nose_x, nose_y)],
                  fill=(88, 166, 255), width=1)

    # Nose pillar convergence point
    draw.ellipse([nose_x - 3, nose_y - 3, nose_x + 3, nose_y + 3],
                 fill=(210, 168, 255))

    # === WAVE WHISKERS ===
    for side in [-1, 1]:
        for w in range(4):
            x_start = int(cx + side * 18 * scale)
            y_start = int(cy + (2 + w * 7) * scale)
            whisker_len = int((65 + rng.randint(0, 35)) * scale)
            wave_freq = 2.5 + rng.random() * 2.0
            wave_amp = (3 + rng.random() * 4) * scale
            droop = (0.15 + w * 0.1)
            points = []
            for t in range(whisker_len):
                frac = t / whisker_len
                x = x_start + side * t
                y = y_start + wave_amp * math.sin(frac * wave_freq * PI) + t * droop
                points.append((int(x), int(y)))
            if len(points) > 1:
                for i in range(len(points) - 1):
                    frac = i / len(points)
                    brt = int(160 - 80 * frac)
                    draw.line([points[i], points[i + 1]],
                              fill=(brt, brt, int(brt * 1.1)), width=1)

    # === HEAD TURN SEQUENCE — moves left to right, sees its own ears and nose ===
    # The chipmunk turns its head. At each angle, different parts come into focus.
    # This is the SPECTRUM: head angle → what's visible → what's in focus
    # Left turn: sees right ear (near), nose (mid), left ear (far, blurry)
    # Center: sees nose (near), both ears (peripheral)
    # Right turn: sees left ear (near), nose (mid), right ear (far, blurry)

    # Draw the focus/depth overlay as concentric awareness rings
    # from the current "gaze point" — scanning left to right
    for scan_phase in range(5):
        # 5 scan positions: far-left, left, center, right, far-right
        t = scan_phase / 4.0  # 0.0 to 1.0
        gaze_x = int(cx + (t - 0.5) * 120 * scale)
        gaze_y = int(cy - 30 * scale)

        # Focus ring at gaze point (what's sharp NOW)
        focus_r = int(35 * scale)
        alpha_base = int(12 - scan_phase * 1.5)  # earlier scans fade more
        for ring in range(3):
            r = focus_r + ring * int(15 * scale)
            ring_alpha = max(2, alpha_base - ring * 3)
            # Spectrum color shifts with head angle: blue(left) → green(center) → gold(right)
            spec_r = int(88 + t * (210 - 88))
            spec_g = int(166 - abs(t - 0.5) * 60)
            spec_b = int(255 * (1 - t) + 34 * t)
            color = (spec_r, spec_g, spec_b, ring_alpha)
            draw.ellipse([gaze_x - r, gaze_y - r, gaze_x + r, gaze_y + r],
                         outline=color)

        # Tiny scan-position dot
        draw.ellipse([gaze_x - 1, gaze_y - 1, gaze_x + 1, gaze_y + 1],
                     fill=(spec_r, spec_g, spec_b, 30))

    # === TOPOLOGY OVERLAY — what connects to what when the head turns ===
    # Lines between ears and nose showing the structural triangle
    # This is the TOPOLOGY: ear-nose-ear forms a triangle
    # As the head turns, different edges of the triangle are in focus
    left_ear = ear_positions["left"]
    right_ear = ear_positions["right"]

    # Ear-to-ear arc (over the head)
    arc_steps = 30
    for i in range(arc_steps):
        t = i / arc_steps
        # Parabolic arc over the top of the head
        ax = left_ear[0] + t * (right_ear[0] - left_ear[0])
        ay = left_ear[1] + t * (right_ear[1] - left_ear[1]) - 40 * scale * math.sin(t * PI)
        draw.ellipse([int(ax) - 1, int(ay) - 1, int(ax) + 1, int(ay) + 1],
                     fill=(210, 153, 34, 20))

    # Ear-to-nose lines (the structural triangle)
    for ear_pos in [left_ear, right_ear]:
        steps = 20
        for i in range(steps):
            t = i / steps
            lx = ear_pos[0] + t * (nose_x - ear_pos[0])
            ly = ear_pos[1] + t * (nose_y - ear_pos[1])
            draw.ellipse([int(lx) - 1, int(ly) - 1, int(lx) + 1, int(ly) + 1],
                         fill=(139, 148, 158, 15))

    # === TAIL — every animal has one except Vitruvian man ===
    # The chipmunk MUST paint its tail. It's there.
    # But the tail is in the NULL AWARENESS ZONE — behind the body.
    # The chipmunk can't see it. It paints from memory and touch.
    tail_base_x = cx
    tail_base_y = int(cy + 120 * scale)  # bottom of the body sphere

    # Bushy chipmunk tail — curves upward and to one side
    tail_segments = 50
    tail_points = []
    for seg in range(tail_segments):
        frac = seg / tail_segments
        # Tail curves up and to the right (asymmetric — life isn't symmetric)
        tx = tail_base_x + frac * 45 * scale + 8 * scale * math.sin(frac * 3 * PI)
        ty = tail_base_y + frac * 30 * scale - frac * frac * 70 * scale  # parabolic lift
        tail_points.append((int(tx), int(ty)))

    # Draw the tail fur (bushy — many offset lines)
    for fluff in range(-3, 4):
        pts = []
        for i, (tx, ty) in enumerate(tail_points):
            frac = i / len(tail_points)
            bushiness = (6 + frac * 12) * scale  # gets bushier at the tip
            fx = tx + fluff * bushiness * 0.3
            fy = ty + abs(fluff) * bushiness * 0.15 * (-1 if fluff % 2 else 1)
            pts.append((int(fx), int(fy)))
        if len(pts) > 1:
            for i in range(len(pts) - 1):
                frac = i / len(pts)
                # Striped chipmunk tail: alternating brown and cream
                if int(frac * 8) % 2 == 0:
                    color = (140, 90, 45, 140)
                else:
                    color = (200, 175, 130, 120)
                draw.line([pts[i], pts[i + 1]], fill=color, width=max(1, int(2 * scale)))

    # === NULL AWARENESS AXIS — tail → body center → nose/3rd eye ===
    # This is the line the chipmunk CANNOT see along.
    # Front half: visible (nose, 3rd eye). Back half: NULL (tail, back).

    # 3rd eye position (between the two eyes, on the forehead)
    third_eye_x = cx
    third_eye_y = int(cy - 35 * scale)

    # Draw the FULL axis as a dashed line: tail → center → 3rd eye → nose
    axis_points = [
        (tail_base_x + int(22 * scale), tail_base_y + int(15 * scale)),  # tail tip area
        (tail_base_x, tail_base_y),  # tail base
        (cx, cy),  # body center
        (third_eye_x, third_eye_y),  # 3rd eye
        (nose_x, nose_y),  # nose
    ]

    for seg_idx in range(len(axis_points) - 1):
        p1 = axis_points[seg_idx]
        p2 = axis_points[seg_idx + 1]
        steps = 25
        for s in range(steps):
            frac = s / steps
            ax = p1[0] + frac * (p2[0] - p1[0])
            ay = p1[1] + frac * (p2[1] - p1[1])

            # Behind center = NULL (red/dim), ahead of center = AWARE (bright blue)
            if seg_idx < 2:  # tail → center: the blind zone
                color = (180, 40, 40, 12 if s % 3 == 0 else 0)
            else:  # center → 3rd eye → nose: the aware zone
                color = (88, 166, 255, 18 if s % 2 == 0 else 0)

            if color[3] > 0:
                draw.ellipse([int(ax) - 1, int(ay) - 1, int(ax) + 1, int(ay) + 1],
                             fill=color)

    # 3rd eye marker (where pineal gland sits on the axis)
    draw.ellipse([third_eye_x - int(4 * scale), third_eye_y - int(4 * scale),
                  third_eye_x + int(4 * scale), third_eye_y + int(4 * scale)],
                 outline=(210, 168, 255, 60))
    draw.ellipse([third_eye_x - int(2 * scale), third_eye_y - int(2 * scale),
                  third_eye_x + int(2 * scale), third_eye_y + int(2 * scale)],
                 fill=(210, 168, 255, 40))

    # === BLIND ZONE — the back half the chipmunk can't see ===
    # Subtle dark wash over the lower-back region
    blind_zone = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    bz_draw = ImageDraw.Draw(blind_zone)
    for by_offset in range(int(40 * scale)):
        y_pos = int(cy + 30 * scale) + by_offset
        half_width = int(math.sqrt(max(0, (size * 0.48) ** 2 - (y_pos - cy) ** 2)))
        if half_width > 0:
            # Very subtle darkening — "you can't see back here"
            bz_draw.line([(cx - half_width, y_pos), (cx + half_width, y_pos)],
                         fill=(0, 0, 0, 3))
    img = Image.alpha_composite(img, blind_zone)
    draw = ImageDraw.Draw(img)  # re-bind after composite

    # "only humans scratch their own back" label at the blind zone
    draw.text((int(cx - 70 * scale), int(cy + 50 * scale)),
              "null zone · can't see here",
              fill=(180, 40, 40, 25))

    # === HANDS — the chipmunk tries to draw its own hands ===
    # But it's UNSURE. So the hands are sketchy, tentative, transparent.
    # It'll come back to them later.
    for hand_side in [-1, 1]:
        hand_x = int(cx + hand_side * 55 * scale)
        hand_y = int(cy + 70 * scale)

        # Rough oval for the palm (very low alpha — uncertainty)
        palm_r = int(12 * scale)
        draw.ellipse([hand_x - palm_r, hand_y - int(palm_r * 0.8),
                      hand_x + palm_r, hand_y + int(palm_r * 0.8)],
                     outline=(139, 148, 158, 15))

        # 4 finger stubs — drawn then partially erased (the doubt)
        for f in range(4):
            angle = math.radians(-40 + f * 25 + hand_side * 5)
            fx = hand_x + int(palm_r * 1.5 * math.cos(angle))
            fy = hand_y - int(palm_r * 1.5 * math.sin(angle))
            # Dashed line (draw-skip-draw) = the hesitation
            for seg in range(5):
                if seg % 2 == 0:  # only draw even segments
                    t1 = seg / 5
                    t2 = (seg + 1) / 5
                    sx = int(hand_x + t1 * (fx - hand_x))
                    sy = int(hand_y + t1 * (fy - hand_y))
                    ex = int(hand_x + t2 * (fx - hand_x))
                    ey = int(hand_y + t2 * (fy - hand_y))
                    draw.line([(sx, sy), (ex, ey)],
                              fill=(139, 148, 158, 10), width=1)

        # Thumb (even more uncertain — just a dot and a question)
        thumb_x = hand_x + int(hand_side * palm_r * 1.2)
        thumb_y = hand_y - int(palm_r * 0.3)
        draw.ellipse([thumb_x - 2, thumb_y - 2, thumb_x + 2, thumb_y + 2],
                     fill=(139, 148, 158, 12))

        # The doubt marker: a tiny "?" near each hand
        draw.text((hand_x - 3, hand_y + int(palm_r * 1.2)),
                  "?", fill=(110, 118, 129, 20))

    # Label
    draw.text((int(10 * scale), int((400 - 20) * scale)),
              "chipmunk · tail + null axis + 3rd eye · only vitruvian has no tail · hands: unsure",
              fill=(110, 118, 129))

    return img


# ═══════════════════════════════════════════════════════════════
# PI COMPOSITE — all images filtered into one signal
# ═══════════════════════════════════════════════════════════════

def make_pi_composite():
    """
    Layer ALL generation images using pi-sorted alpha.
    Each image sits at frac(n×π) on the unit circle.
    Alpha peaks at the 1/π position.
    Result: the pi-filtered signal — all noise compressed to meaning.
    """
    print("Collecting all images...")
    images = collect_all_images()
    print(f"  Found {len(images)} images across all experiments")

    # Sort by pi position (irrational spacing)
    images.sort(key=lambda x: x["pi_pos"])

    # Create composite canvas
    composite = Image.new('RGBA', CANVAS, (8, 6, 10, 255))

    print("Compositing with pi-filter...")
    for i, entry in enumerate(images):
        try:
            layer = Image.open(str(entry["path"])).convert('RGBA')
            layer = layer.resize(CANVAS, Image.LANCZOS)
        except Exception as e:
            continue

        # Pi-sorted alpha
        alpha = entry["pi_alpha"]

        # Also offset by pi position (slight spatial shift)
        offset_x = int(20 * math.cos(entry["pi_pos"] * 2 * PI))
        offset_y = int(20 * math.sin(entry["pi_pos"] * 2 * PI))

        # Apply alpha to layer
        r, g, b, a = layer.split()
        a = a.point(lambda x: int(x * alpha))
        layer = Image.merge('RGBA', (r, g, b, a))

        # Paste with offset
        temp = Image.new('RGBA', CANVAS, (0, 0, 0, 0))
        paste_x = max(0, min(CANVAS[0] - layer.width, offset_x))
        paste_y = max(0, min(CANVAS[1] - layer.height, offset_y))
        temp.paste(layer, (paste_x, paste_y))
        composite = Image.alpha_composite(composite, temp)

        if (i + 1) % 25 == 0:
            print(f"  Layer {i + 1}/{len(images)} "
                  f"(pi_pos={entry['pi_pos']:.4f}, alpha={alpha:.3f})")

    print("Done compositing.")
    return composite


def make_all_to_signal():
    """
    Simple version: average ALL images into one signal.
    No pi-filter, just straight accumulation.
    Then compare with the pi-filtered version.
    """
    images = collect_all_images()
    if not images:
        print("No images found!")
        return None

    acc = np.zeros((*CANVAS, 3), dtype=np.float64)
    count = 0

    for entry in images:
        try:
            img = Image.open(str(entry["path"])).convert('RGB').resize(CANVAS, Image.LANCZOS)
            acc += np.array(img, dtype=np.float64)
            count += 1
        except Exception:
            continue

    if count == 0:
        return None

    avg = (acc / count).astype(np.uint8)
    return Image.fromarray(avg)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("PI COMPOSITE — all paintings filtered to one signal")
    print("=" * 60)

    # 1. Generate the full chipmunk with ears
    print("\n--- Chipmunk with binocular eyes + binaural ears ---")
    chipmunk = draw_chipmunk_with_ears(size=800, seed=189)
    chipmunk_path = OUTPUT / "chipmunk-full-binocular-binaural.png"
    chipmunk.save(str(chipmunk_path))
    print(f"  Saved: {chipmunk_path}")

    # 2. Pi composite (pi-filtered layers)
    print("\n--- Pi composite ---")
    pi_comp = make_pi_composite()
    pi_path = OUTPUT / "pi-composite.png"
    pi_comp.save(str(pi_path))
    print(f"  Saved: {pi_path}")

    # 3. Straight average (all to one signal, no filter)
    print("\n--- All-to-signal (unfiltered average) ---")
    avg_signal = make_all_to_signal()
    if avg_signal:
        avg_path = OUTPUT / "all-to-signal.png"
        avg_signal.save(str(avg_path))
        print(f"  Saved: {avg_path}")

    # 4. Measure: compare pi-filtered vs unfiltered
    from PIL import Image as PILImage
    pi_arr = np.array(pi_comp.convert('RGB'), dtype=np.float64)
    if avg_signal:
        avg_arr = np.array(avg_signal, dtype=np.float64)
        diff = np.abs(pi_arr - avg_arr).mean()
        print(f"\n  Pi-filtered vs unfiltered mean pixel diff: {diff:.2f}")
        print(f"  Pi composite entropy: {-np.sum(np.histogram(pi_arr.flatten(), 256, (0,256))[0][np.histogram(pi_arr.flatten(), 256, (0,256))[0]>0] / pi_arr.size * np.log2(np.histogram(pi_arr.flatten(), 256, (0,256))[0][np.histogram(pi_arr.flatten(), 256, (0,256))[0]>0] / pi_arr.size)):.3f} bits")

    # 5. Results feed
    results = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "title": "Pi Composite — all paintings filtered to one signal through π",
        "images_composited": len(collect_all_images()),
        "chipmunk": "binocular eyes + binaural ears — focal lines become audio antennae",
        "anatomy": {
            "eyes": "2 focal points each, binocular convergence at nose pillar",
            "ears": "positioned at terminus of focal axis — visual line extends to become auditory antenna",
            "L_eye_to_L_ear": "left focal axis = left audio pickup angle",
            "R_eye_to_R_ear": "right focal axis = right audio pickup angle",
            "wave_transition": "focal line color transitions from visual blue (88,166,255) to auditory gold (210,153,34)",
            "whiskers": "sine wave vibrissae — detect vibrations in the signal",
            "tail": "bushy striped chipmunk tail — every animal has one EXCEPT Vitruvian man",
            "null_axis": "line from tail → body center → 3rd eye → nose. Back half is NULL (blind zone), front half is AWARE",
            "third_eye": "pineal position on the null axis, between the two optical eyes. Where the axis crosses from blind→aware",
            "blind_zone": "the back of the body — the chipmunk CANNOT see here. Only humans can scratch their own back AND others'",
            "hands": "attempted but UNSURE — the drawing instrument cannot draw itself. Will return later",
            "head_turn_spectrum": "5 scan positions L→R. At each angle the chipmunk sees different parts of itself. Color: blue→green→gold"
        },
        "pi_filter": {
            "method": "frac(n × π) determines layer alpha and spatial offset",
            "alpha_peak": "at 1/π position (0.3183) on the unit circle",
            "spatial_offset": "20px circular shift at pi_pos angle",
            "result": "images near the 1/π position are BRIGHTEST — they survived the pi filter"
        },
        "outputs": {
            "chipmunk_full": str(chipmunk_path.name),
            "pi_composite": "pi-composite.png",
            "all_to_signal": "all-to-signal.png"
        },
        "printable": True,
        "3d_printable": "the pi-composite IS a heightmap — pixel brightness = Z height. import as grayscale heightmap into any 3D slicer.",
        "scyborg_triple_license": {
            "AGPL_3_0": "code",
            "ORC": "pi-filtering is a game mechanic — sort by irrational position, compress to signal",
            "CC_BY_SA_4_0": "all generated art"
        }
    }

    feed_path = OUTPUT / "pi-composite.json"
    with open(feed_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Feed: {feed_path}")

    print("\n✅ Done. Print any of these. The pi-composite IS the signal.")
    print("   For 3D printing: import pi-composite.png as a heightmap.")
