"""Generate the Hermes caduceus icon — wings + snakes on a staff."""
from pathlib import Path

def create_icon_svg() -> str:
    return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <!-- Dark background circle -->
  <circle cx="128" cy="128" r="120" fill="#1a1a2e" stroke="#c0a030" stroke-width="4"/>

  <!-- Staff (vertical rod) -->
  <rect x="124" y="60" width="8" height="160" fill="#c0a030" rx="2"/>

  <!-- Wings at top of staff -->
  <!-- Left wing -->
  <path d="M 128 70 Q 90 50 60 55 Q 75 65 85 72 Q 70 70 55 78 Q 75 82 90 80 Q 80 88 72 95 Q 95 88 110 82 Z"
        fill="#e0e0e0" stroke="#a0a0a0" stroke-width="1"/>
  <!-- Right wing -->
  <path d="M 128 70 Q 166 50 196 55 Q 181 65 171 72 Q 186 70 201 78 Q 181 82 166 80 Q 176 88 184 95 Q 161 88 146 82 Z"
        fill="#e0e0e0" stroke="#a0a0a0" stroke-width="1"/>

  <!-- Wing feather details -->
  <line x1="100" y1="72" x2="75" y2="62" stroke="#b0b0b0" stroke-width="1"/>
  <line x1="105" y1="76" x2="82" y2="68" stroke="#b0b0b0" stroke-width="1"/>
  <line x1="110" y1="80" x2="90" y2="75" stroke="#b0b0b0" stroke-width="1"/>
  <line x1="156" y1="72" x2="181" y2="62" stroke="#b0b0b0" stroke-width="1"/>
  <line x1="151" y1="76" x2="174" y2="68" stroke="#b0b0b0" stroke-width="1"/>
  <line x1="146" y1="80" x2="166" y2="75" stroke="#b0b0b0" stroke-width="1"/>

  <!-- Top knob of staff -->
  <circle cx="128" cy="62" r="10" fill="#c0a030" stroke="#d0b040" stroke-width="2"/>

  <!-- Left snake (intertwined) -->
  <path d="M 128 85 Q 105 100 128 115 Q 151 130 128 145 Q 105 160 128 175 Q 145 185 128 200"
        fill="none" stroke="#2d8659" stroke-width="7" stroke-linecap="round"/>
  <!-- Left snake head -->
  <ellipse cx="118" cy="88" rx="8" ry="6" fill="#2d8659" transform="rotate(-30 118 88)"/>
  <circle cx="115" cy="86" r="1.5" fill="#ff4444"/>

  <!-- Right snake (intertwined, opposite direction) -->
  <path d="M 128 85 Q 151 100 128 115 Q 105 130 128 145 Q 151 160 128 175 Q 111 185 128 200"
        fill="none" stroke="#2d6b85" stroke-width="7" stroke-linecap="round"/>
  <!-- Right snake head -->
  <ellipse cx="138" cy="88" rx="8" ry="6" fill="#2d6b85" transform="rotate(30 138 88)"/>
  <circle cx="141" cy="86" r="1.5" fill="#ff4444"/>

  <!-- Bottom knob -->
  <circle cx="128" cy="218" r="8" fill="#c0a030" stroke="#d0b040" stroke-width="2"/>
</svg>'''


def create_icon_ico(output_path: Path):
    """Create a multi-size ICO from the SVG using PIL."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise RuntimeError("Pillow not installed. Run: pip install Pillow")

    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx, cy = size / 2, size / 2
        r = int(size * 0.47)

        # Background circle
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(26, 26, 46, 255),
                     outline=(192, 160, 48, 255), width=max(1, size // 64))

        # Staff
        staff_w = max(2, size // 32)
        staff_x = int(cx - staff_w / 2)
        staff_top = int(size * 0.23)
        staff_bot = int(size * 0.85)
        draw.rectangle([staff_x, staff_top, staff_x + staff_w, staff_bot],
                       fill=(192, 160, 48, 255))

        # Top knob
        knob_r = max(3, size // 25)
        draw.ellipse([cx - knob_r, int(size * 0.24) - knob_r,
                      cx + knob_r, int(size * 0.24) + knob_r],
                     fill=(192, 160, 48, 255), outline=(208, 176, 64, 255),
                     width=max(1, size // 128))

        # Bottom knob
        draw.ellipse([cx - knob_r, staff_bot - knob_r,
                      cx + knob_r, staff_bot + knob_r],
                     fill=(192, 160, 48, 255), outline=(208, 176, 64, 255),
                     width=max(1, size // 128))

        # Wings
        wing_y = int(size * 0.27)
        wing_span = int(size * 0.28)
        wing_h = int(size * 0.10)
        wing_color = (224, 224, 224, 255)
        # Left wing
        draw.polygon([
            (int(cx), wing_y),
            (int(cx - wing_span), wing_y - wing_h // 3),
            (int(cx - wing_span * 0.7), wing_y + wing_h // 4),
            (int(cx - wing_span * 0.5), wing_y),
            (int(cx - wing_span * 0.3), wing_y + wing_h // 3),
            (int(cx - wing_span * 0.15), wing_y + wing_h // 4),
        ], fill=wing_color, outline=(160, 160, 160, 255))
        # Right wing
        draw.polygon([
            (int(cx), wing_y),
            (int(cx + wing_span), wing_y - wing_h // 3),
            (int(cx + wing_span * 0.7), wing_y + wing_h // 4),
            (int(cx + wing_span * 0.5), wing_y),
            (int(cx + wing_span * 0.3), wing_y + wing_h // 3),
            (int(cx + wing_span * 0.15), wing_y + wing_h // 4),
        ], fill=wing_color, outline=(160, 160, 160, 255))

        # Snakes — simplified curves
        snake_w = max(2, size // 36)
        snake_top = int(size * 0.33)
        snake_bot = int(size * 0.78)
        snake_amp = int(size * 0.09)

        # Left snake (green)
        points_l = []
        for i in range(8):
            t = i / 7
            y = snake_top + int(t * (snake_bot - snake_top))
            x = int(cx - snake_amp * (1 - abs(t * 2 - 1)) * (1 if i % 2 == 0 else -1))
            points_l.append((x, y))
        for i in range(len(points_l) - 1):
            draw.line([points_l[i], points_l[i + 1]], fill=(45, 134, 89, 255), width=snake_w)

        # Right snake (blue)
        points_r = []
        for i in range(8):
            t = i / 7
            y = snake_top + int(t * (snake_bot - snake_top))
            x = int(cx + snake_amp * (1 - abs(t * 2 - 1)) * (1 if i % 2 == 1 else -1))
            points_r.append((x, y))
        for i in range(len(points_r) - 1):
            draw.line([points_r[i], points_r[i + 1]], fill=(45, 107, 133, 255), width=snake_w)

        # Snake heads
        head_r = max(2, size // 32)
        draw.ellipse([points_l[0][0] - head_r, points_l[0][1] - head_r,
                      points_l[0][0] + head_r, points_l[0][1] + head_r],
                     fill=(45, 134, 89, 255))
        draw.ellipse([points_r[0][0] - head_r, points_r[0][1] - head_r,
                      points_r[0][0] + head_r, points_r[0][1] + head_r],
                     fill=(45, 107, 133, 255))

        images.append(img)

    images[0].save(output_path, format='ICO', sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    return output_path


if __name__ == "__main__":
    out = Path(__file__).parent / "hermes_icon.ico"
    create_icon_ico(out)
    print(f"Icon saved to: {out}")
