"""
Generate an educational YouTube Shorts-style video:
"What's Hidden Under Antarctica?"

Creates a vertical (1080x1920) animated video with:
- Cross-section view drilling through ice layers
- Bold text overlays with facts
- Smooth transitions between layers
- Blue/white color palette
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioClip, concatenate_videoclips
import math
import os

W, H = 1080, 1920
FPS = 30
OUTPUT = "/home/user/LangGraph/antarctica_shorts.mp4"


def get_font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def draw_stars(draw, count, seed, alpha=255):
    rng = np.random.RandomState(seed)
    for _ in range(count):
        x = rng.randint(0, W)
        y = rng.randint(0, H // 4)
        s = rng.randint(1, 3)
        brightness = rng.randint(150, 255)
        draw.ellipse([x - s, y - s, x + s, y + s], fill=(brightness, brightness, brightness, alpha))


def draw_snowflakes(draw, t, count=60):
    rng = np.random.RandomState(42)
    for _ in range(count):
        base_x = rng.randint(0, W)
        base_y = rng.randint(-100, H)
        speed = rng.uniform(0.5, 2.0)
        drift = rng.uniform(-30, 30)
        size = rng.randint(2, 6)
        y = (base_y + t * speed * 200) % (H + 100) - 50
        x = base_x + math.sin(t * 2 + base_x * 0.01) * drift
        alpha = rng.randint(150, 255)
        draw.ellipse([x - size, y - size, x + size, y + size],
                      fill=(255, 255, 255, alpha))


def draw_text_with_shadow(draw, text, pos, font, fill=(255, 255, 255, 255),
                           shadow_color=(0, 0, 0, 180), shadow_offset=3):
    x, y = pos
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color, anchor="mm")
    draw.text((x, y), text, font=font, fill=fill, anchor="mm")


def draw_gradient_rect(draw, bbox, color_top, color_bottom, steps=50):
    x0, y0, x1, y1 = bbox
    h = y1 - y0
    for i in range(steps):
        t = i / steps
        r = int(lerp(color_top[0], color_bottom[0], t))
        g = int(lerp(color_top[1], color_bottom[1], t))
        b = int(lerp(color_top[2], color_bottom[2], t))
        a = int(lerp(color_top[3] if len(color_top) > 3 else 255,
                      color_bottom[3] if len(color_bottom) > 3 else 255, t))
        row_y0 = y0 + int(h * i / steps)
        row_y1 = y0 + int(h * (i + 1) / steps)
        draw.rectangle([x0, row_y0, x1, row_y1], fill=(r, g, b, a))


def draw_ice_texture(draw, y_start, y_end, t, depth_factor=0.0):
    rng = np.random.RandomState(77)
    base_r, base_g, base_b = (
        int(lerp(220, 20, depth_factor)),
        int(lerp(235, 60, depth_factor)),
        int(lerp(255, 140, depth_factor)),
    )
    for _ in range(200):
        x = rng.randint(0, W)
        y = rng.randint(y_start, max(y_start + 1, y_end))
        w = rng.randint(10, 80)
        h = rng.randint(2, 8)
        var = rng.randint(-20, 20)
        alpha = rng.randint(30, 80)
        draw.ellipse([x, y, x + w, y + h],
                      fill=(base_r + var, base_g + var, base_b + var, alpha))


def make_title_frame(t, duration):
    img = Image.new("RGBA", (W, H), (5, 5, 30, 255))
    draw = ImageDraw.Draw(img)

    draw_gradient_rect(draw, (0, 0, W, H), (5, 10, 40), (10, 30, 80))
    draw_stars(draw, 100, 42)

    ice_y = int(H * 0.55)
    draw_gradient_rect(draw, (0, ice_y, W, H), (200, 220, 255), (100, 150, 220))

    for i in range(20):
        rng = np.random.RandomState(i + 100)
        peak_x = rng.randint(0, W)
        peak_h = rng.randint(30, 120)
        base_w = rng.randint(60, 200)
        points = [(peak_x - base_w, ice_y + 10),
                  (peak_x, ice_y - peak_h),
                  (peak_x + base_w, ice_y + 10)]
        draw.polygon(points, fill=(220, 235, 255, 200))

    draw_snowflakes(draw, t)

    progress = min(t / (duration * 0.4), 1.0)
    alpha = int(255 * ease_in_out(progress))

    title_font = get_font(72)
    sub_font = get_font(42)
    emoji_font = get_font(90)

    draw_text_with_shadow(draw, "?", (W // 2, H * 0.25), emoji_font,
                           fill=(255, 255, 255, alpha))
    draw_text_with_shadow(draw, "What's Hidden", (W // 2, H * 0.33), title_font,
                           fill=(255, 255, 255, alpha))
    draw_text_with_shadow(draw, "Under Antarctica?", (W // 2, H * 0.39), title_font,
                           fill=(100, 200, 255, alpha))

    if t > duration * 0.3:
        sub_progress = min((t - duration * 0.3) / (duration * 0.3), 1.0)
        sub_alpha = int(255 * ease_in_out(sub_progress))
        draw_text_with_shadow(draw, "Let's drill down and find out...",
                               (W // 2, H * 0.47), sub_font,
                               fill=(200, 230, 255, sub_alpha))

    return np.array(img.convert("RGB"))


def make_layer_frame(t, duration, layer_idx, scroll_offset):
    img = Image.new("RGBA", (W, H), (5, 5, 30, 255))
    draw = ImageDraw.Draw(img)

    layers = [
        {
            "name": "Surface Snow",
            "depth": "0 - 50m",
            "fact": "Fresh snow compresses\ninto dense firn over\nhundreds of years",
            "colors_top": (240, 245, 255),
            "colors_bot": (200, 220, 255),
            "detail_color": (255, 255, 255, 60),
        },
        {
            "name": "Glacial Ice",
            "depth": "50m - 2,000m",
            "fact": "Ancient air bubbles\ntrapped for 800,000 years\nreveal Earth's climate history",
            "colors_top": (150, 200, 255),
            "colors_bot": (50, 100, 200),
            "detail_color": (100, 180, 255, 80),
        },
        {
            "name": "Subglacial Lakes",
            "depth": "2,000m - 3,500m",
            "fact": "Over 400 hidden lakes\nexist beneath the ice\nincluding Lake Vostok",
            "colors_top": (30, 60, 150),
            "colors_bot": (10, 30, 100),
            "detail_color": (50, 120, 200, 60),
        },
        {
            "name": "Ancient Mountains",
            "depth": "3,500m - 4,000m",
            "fact": "The Gamburtsev Mountains\nare as tall as the Alps\nbut completely buried in ice",
            "colors_top": (80, 60, 50),
            "colors_bot": (50, 40, 35),
            "detail_color": (120, 100, 80, 80),
        },
        {
            "name": "Volcanic Activity",
            "depth": "Deep Underground",
            "fact": "91 volcanoes discovered\nbeneath the ice sheet\nstill geothermally active!",
            "colors_top": (100, 30, 10),
            "colors_bot": (60, 15, 5),
            "detail_color": (255, 100, 30, 60),
        },
    ]

    layer = layers[min(layer_idx, len(layers) - 1)]
    draw_gradient_rect(draw, (0, 0, W, H), layer["colors_top"], layer["colors_bot"])

    if layer_idx == 0:
        draw_snowflakes(draw, t, 40)
        rng = np.random.RandomState(55)
        for _ in range(100):
            x, y = rng.randint(0, W), rng.randint(0, H)
            s = rng.randint(1, 4)
            draw.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, rng.randint(20, 60)))

    elif layer_idx == 1:
        draw_ice_texture(draw, 0, H, t, 0.3)
        rng = np.random.RandomState(88)
        for _ in range(30):
            x, y = rng.randint(50, W - 50), rng.randint(50, H - 50)
            r = rng.randint(5, 15)
            draw.ellipse([x - r, y - r, x + r, y + r],
                          fill=(180, 220, 255, 40), outline=(200, 230, 255, 60))

    elif layer_idx == 2:
        for wave in range(5):
            points = []
            for x in range(0, W + 20, 20):
                y = H // 2 + math.sin(x * 0.01 + t * 2 + wave * 0.5) * (40 + wave * 20)
                points.append((x, y))
            if len(points) > 1:
                for i in range(len(points) - 1):
                    draw.line([points[i], points[i + 1]],
                              fill=(50, 120, 200, 30 + wave * 10), width=3)
        rng = np.random.RandomState(99)
        for _ in range(8):
            x = rng.randint(100, W - 100)
            y = rng.randint(H // 3, 2 * H // 3)
            glow_r = rng.randint(20, 50)
            pulse = math.sin(t * 3 + x * 0.01) * 0.3 + 0.7
            alpha = int(40 * pulse)
            draw.ellipse([x - glow_r, y - glow_r, x + glow_r, y + glow_r],
                          fill=(80, 180, 255, alpha))

    elif layer_idx == 3:
        rng = np.random.RandomState(111)
        mountain_base = int(H * 0.65)
        for i in range(15):
            peak_x = rng.randint(0, W)
            peak_h = rng.randint(100, 400)
            base_w = rng.randint(80, 250)
            shade = rng.randint(60, 120)
            points = [(peak_x - base_w, mountain_base),
                      (peak_x, mountain_base - peak_h),
                      (peak_x + base_w, mountain_base)]
            draw.polygon(points, fill=(shade, shade - 10, shade - 20, 200))
            cap_h = peak_h // 4
            cap_points = [(peak_x - base_w // 3, mountain_base - peak_h + cap_h),
                          (peak_x, mountain_base - peak_h),
                          (peak_x + base_w // 3, mountain_base - peak_h + cap_h)]
            draw.polygon(cap_points, fill=(shade + 40, shade + 30, shade + 20, 150))
        draw_gradient_rect(draw, (0, mountain_base, W, H), (50, 40, 35), (30, 25, 20))

    elif layer_idx == 4:
        rng = np.random.RandomState(222)
        for _ in range(20):
            x = rng.randint(0, W)
            y = rng.randint(H // 2, H)
            for r in range(50, 5, -5):
                pulse = math.sin(t * 4 + x * 0.01) * 0.3 + 0.7
                alpha = int((50 - r) * 2 * pulse)
                draw.ellipse([x - r, y - r, x + r, y + r],
                              fill=(255, int(80 * (r / 50)), 0, alpha))

        lava_y = int(H * 0.85)
        for x in range(0, W, 3):
            wave_h = math.sin(x * 0.02 + t * 3) * 20 + math.sin(x * 0.05 + t * 5) * 10
            y = lava_y + int(wave_h)
            draw.rectangle([x, y, x + 3, H], fill=(200, 60, 10, 180))
            draw.rectangle([x, y, x + 3, y + 5], fill=(255, 200, 50, 200))

    depth_indicator_progress = min(t / (duration * 0.3), 1.0)
    if depth_indicator_progress > 0:
        bar_x = 50
        bar_top = 200
        bar_bottom = H - 200
        bar_h = int((bar_bottom - bar_top) * ease_in_out(depth_indicator_progress))

        draw.rectangle([bar_x, bar_top, bar_x + 8, bar_top + bar_h],
                        fill=(255, 255, 255, 100))

        marker_y = bar_top + bar_h
        draw.ellipse([bar_x - 6, marker_y - 6, bar_x + 14, marker_y + 6],
                      fill=(100, 200, 255, 255))

        depth_font = get_font(28)
        draw.text((bar_x + 25, marker_y), layer["depth"],
                  font=depth_font, fill=(200, 230, 255, 200), anchor="lm")

    text_progress = max(0, min((t - duration * 0.15) / (duration * 0.3), 1.0))
    text_alpha = int(255 * ease_in_out(text_progress))

    name_font = get_font(64)
    fact_font = get_font(38)

    box_padding = 30
    box_y = int(H * 0.12)
    box_h = 100
    draw.rounded_rectangle([W // 2 - 350, box_y - box_padding,
                             W // 2 + 350, box_y + box_h + box_padding],
                            radius=20, fill=(0, 0, 0, 120))
    draw_text_with_shadow(draw, layer["name"], (W // 2, box_y + 20), name_font,
                           fill=(255, 255, 255, text_alpha))
    draw_text_with_shadow(draw, layer["depth"], (W // 2, box_y + 75), fact_font,
                           fill=(150, 200, 255, text_alpha))

    fact_progress = max(0, min((t - duration * 0.35) / (duration * 0.3), 1.0))
    fact_alpha = int(255 * ease_in_out(fact_progress))
    fact_y = int(H * 0.75)
    lines = layer["fact"].split("\n")

    fact_box_h = len(lines) * 50 + 40
    draw.rounded_rectangle([W // 2 - 380, fact_y - 30,
                             W // 2 + 380, fact_y + fact_box_h],
                            radius=20, fill=(0, 0, 0, 100))

    for i, line in enumerate(lines):
        draw_text_with_shadow(draw, line, (W // 2, fact_y + i * 50 + 15),
                               fact_font, fill=(255, 255, 255, fact_alpha))

    drill_x = W - 80
    drill_top = 0
    drill_length = int(H * 0.5 * ease_in_out(min(t / (duration * 0.5), 1.0)))
    draw.rectangle([drill_x - 3, drill_top, drill_x + 3, drill_top + drill_length],
                    fill=(180, 180, 180, 200))
    if drill_length > 10:
        bit_y = drill_top + drill_length
        draw.polygon([(drill_x - 12, bit_y - 10), (drill_x, bit_y + 10),
                       (drill_x + 12, bit_y - 10)], fill=(200, 200, 200, 220))
        glow_pulse = math.sin(t * 8) * 0.3 + 0.7
        for r in range(20, 5, -3):
            draw.ellipse([drill_x - r, bit_y - r, drill_x + r, bit_y + r],
                          fill=(255, 200, 100, int(20 * glow_pulse)))

    return np.array(img.convert("RGB"))


def make_outro_frame(t, duration):
    img = Image.new("RGBA", (W, H), (5, 10, 30, 255))
    draw = ImageDraw.Draw(img)

    draw_gradient_rect(draw, (0, 0, W, H), (5, 10, 40), (20, 40, 80))
    draw_stars(draw, 150, 42)

    progress = min(t / (duration * 0.4), 1.0)
    alpha = int(255 * ease_in_out(progress))

    title_font = get_font(56)
    sub_font = get_font(36)

    draw_text_with_shadow(draw, "Antarctica holds", (W // 2, H * 0.3), title_font,
                           fill=(255, 255, 255, alpha))
    draw_text_with_shadow(draw, "secrets older than", (W // 2, H * 0.36), title_font,
                           fill=(255, 255, 255, alpha))
    draw_text_with_shadow(draw, "humanity itself", (W // 2, H * 0.42), title_font,
                           fill=(100, 200, 255, alpha))

    facts = [
        "400+ subglacial lakes",
        "800,000 years of climate data",
        "91 hidden volcanoes",
        "Mountains as tall as the Alps",
    ]
    fact_font = get_font(32)
    for i, fact in enumerate(facts):
        delay = 0.3 + i * 0.12
        fact_progress = max(0, min((t - duration * delay) / (duration * 0.2), 1.0))
        fact_alpha = int(255 * ease_in_out(fact_progress))
        y = H * 0.55 + i * 60
        bullet_x = W // 2 - 280
        draw.ellipse([bullet_x, y - 5, bullet_x + 10, y + 5],
                      fill=(100, 200, 255, fact_alpha))
        draw.text((bullet_x + 25, y), fact, font=fact_font,
                  fill=(220, 235, 255, fact_alpha), anchor="lm")

    if t > duration * 0.6:
        cta_progress = min((t - duration * 0.6) / (duration * 0.2), 1.0)
        cta_alpha = int(255 * ease_in_out(cta_progress))
        cta_font = get_font(40)
        draw_text_with_shadow(draw, "Follow for more!", (W // 2, H * 0.88), cta_font,
                               fill=(255, 220, 100, cta_alpha))

    return np.array(img.convert("RGB"))


def make_transition_frame(t, duration, from_layer, to_layer):
    progress = ease_in_out(min(t / duration, 1.0))

    frame_from = make_layer_frame(3.0, 4.0, from_layer, 0)
    frame_to = make_layer_frame(0.2, 4.0, to_layer, 0)

    blended = (frame_from * (1 - progress) + frame_to * progress).astype(np.uint8)
    return blended


def generate_audio(duration):
    sample_rate = 44100

    def audio_func(t):
        if isinstance(t, np.ndarray):
            result = np.zeros((len(t), 2))
            base_freq = 80
            for harmonic in range(1, 5):
                freq = base_freq * harmonic
                amp = 0.08 / harmonic
                wave = amp * np.sin(2 * np.pi * freq * t)
                result[:, 0] += wave
                result[:, 1] += wave

            pad_freq = 220
            pad = 0.05 * np.sin(2 * np.pi * pad_freq * t)
            pad += 0.03 * np.sin(2 * np.pi * pad_freq * 1.5 * t)
            result[:, 0] += pad
            result[:, 1] += pad

            sweep = 0.02 * np.sin(2 * np.pi * (300 + 200 * np.sin(0.1 * t)) * t)
            result[:, 0] += sweep
            result[:, 1] += sweep

            noise = 0.01 * np.random.randn(len(t))
            result[:, 0] += noise
            result[:, 1] += noise

            fade_in = np.minimum(t / 1.0, 1.0)
            fade_out = np.minimum((duration - t) / 1.0, 1.0)
            envelope = fade_in * fade_out
            result[:, 0] *= envelope
            result[:, 1] *= envelope

            return result
        else:
            return np.array([0.0, 0.0])

    return AudioClip(audio_func, duration=duration, fps=sample_rate)


def main():
    print("Generating Antarctica educational video...")

    scene_config = [
        ("title", 4.0),
        ("layer", 3.5, 0),    # Snow
        ("trans", 0.8, 0, 1),
        ("layer", 3.5, 1),    # Glacial ice
        ("trans", 0.8, 1, 2),
        ("layer", 3.5, 2),    # Subglacial lakes
        ("trans", 0.8, 2, 3),
        ("layer", 3.5, 3),    # Mountains
        ("trans", 0.8, 3, 4),
        ("layer", 3.5, 4),    # Volcanoes
        ("outro", 4.5),
    ]

    clips = []
    for i, scene in enumerate(scene_config):
        scene_type = scene[0]
        scene_duration = scene[1]
        print(f"  Rendering scene {i + 1}/{len(scene_config)}: {scene_type}...")

        if scene_type == "title":
            clip = VideoClip(lambda t, d=scene_duration: make_title_frame(t, d),
                             duration=scene_duration)
        elif scene_type == "layer":
            layer_idx = scene[2]
            clip = VideoClip(
                lambda t, d=scene_duration, li=layer_idx: make_layer_frame(t, d, li, 0),
                duration=scene_duration,
            )
        elif scene_type == "trans":
            from_l, to_l = scene[2], scene[3]
            clip = VideoClip(
                lambda t, d=scene_duration, fl=from_l, tl=to_l: make_transition_frame(t, d, fl, tl),
                duration=scene_duration,
            )
        elif scene_type == "outro":
            clip = VideoClip(lambda t, d=scene_duration: make_outro_frame(t, d),
                             duration=scene_duration)
        else:
            continue

        clips.append(clip)

    print("  Concatenating clips...")
    final = concatenate_videoclips(clips, method="compose")

    print("  Generating ambient audio...")
    audio = generate_audio(final.duration)
    final = final.with_audio(audio)

    print(f"  Writing video to {OUTPUT}...")
    final.write_videofile(
        OUTPUT,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger="bar",
    )

    print(f"\nDone! Video saved to: {OUTPUT}")
    print(f"Duration: {final.duration:.1f}s | Resolution: {W}x{H} | FPS: {FPS}")


if __name__ == "__main__":
    main()
