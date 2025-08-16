#!/usr/bin/env python3
import os, sys, json, yaml, textwrap, math, re
try:
    import cairosvg
except Exception:
    cairosvg = None

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
ROOT = os.path.normpath(ROOT)

TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="220" viewBox="0 0 800 220">
  {badge}
  <text x="250" y="110" font-family="Arial, Helvetica, sans-serif" font-size="56" font-weight="bold" fill="{brand_color}">{brand_name}</text>
  <text x="250" y="150" font-family="Arial, Helvetica, sans-serif" font-size="22" fill="#6B7280">{domain}</text>
</svg>
"""

def _hex_to_rgb(col):
    col = col.lstrip("#")
    r, g, b = int(col[0:2], 16) / 255.0, int(col[2:4], 16) / 255.0, int(col[4:6], 16) / 255.0
    return r, g, b

def _rel_lum(col):
    def chan(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _hex_to_rgb(col)
    r, g, b = chan(r), chan(g), chan(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(a, b):
    l1, l2 = sorted([_rel_lum(a), _rel_lum(b)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

def pick_initials_color(primary, accent=None):
    backgrounds = [primary]
    if accent:
        backgrounds.append(accent)
    if all(contrast_ratio(bg, "#FFFFFF") >= 4.5 for bg in backgrounds):
        return "white"
    return "#111827"

def _gradient_def(gradient_from, gradient_to, angle):
    rad = math.radians(angle % 360)
    x1 = 0.5 - 0.5 * math.cos(rad)
    y1 = 0.5 - 0.5 * math.sin(rad)
    x2 = 0.5 + 0.5 * math.cos(rad)
    y2 = 0.5 + 0.5 * math.sin(rad)
    return f"""
    <defs>
      <linearGradient id="badgeGrad" x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}">
        <stop offset="0%" stop-color="{gradient_from}"/>
        <stop offset="100%" stop-color="{gradient_to}"/>
      </linearGradient>
    </defs>
"""

def badge_svg(shape, primary, accent, initials, use_gradient=False,
              gradient_from=None, gradient_to=None, gradient_angle=0,
              stroke_color=None, stroke_width=None):
    defs = ""
    fill = primary
    if use_gradient:
        gradient_from = gradient_from or primary
        gradient_to = gradient_to or accent
        defs = _gradient_def(gradient_from, gradient_to, gradient_angle)
        fill = "url(#badgeGrad)"
        text_color = pick_initials_color(gradient_from, gradient_to)
    else:
        text_color = pick_initials_color(primary, accent)

    stroke = ""
    if stroke_color is not None and stroke_width is not None:
        stroke = f' stroke="{stroke_color}" stroke-width="{stroke_width}"'

    if shape == "circle":
        return f"""{defs}
  <circle cx="110" cy="110" r="90" fill="{fill}"{stroke}/>
  <text x="110" y="110" font-family="Arial, Helvetica, sans-serif" font-size="72" font-weight="bold" text-anchor="middle" dominant-baseline="middle" fill="{text_color}">{initials}</text>
"""
    elif shape == "diamond":
        return f"""{defs}
  <g transform="translate(110,110)">
    <rect x="-90" y="-90" width="180" height="180" rx="40" ry="40" fill="{fill}"{stroke} transform="rotate(45)"/>
    <text x="0" y="0" font-family="Arial, Helvetica, sans-serif" font-size="72" font-weight="bold" text-anchor="middle" dominant-baseline="middle" fill="{text_color}">{initials}</text>
  </g>
"""
    else:  # rounded
        return f"""{defs}
  <rect x="20" y="20" width="180" height="180" rx="40" ry="40" fill="{fill}"{stroke}/>
  <text x="110" y="110" font-family="Arial, Helvetica, sans-serif" font-size="72" font-weight="bold" text-anchor="middle" dominant-baseline="middle" fill="{text_color}">{initials}</text>
"""

def initials_from_name(name):
    """Return up to three initials derived from *name*.

    Splits the input on whitespace, non-letter transitions, and camelCase
    boundaries. Small connector words are ignored. If no letters are found a
    bullet "\u2022" is returned.
    """

    tokens = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[a-z]+", name)
    if not tokens:
        return "•"

    letters = []
    for tok in tokens:
        if tok.lower() in {"of", "and", "the", "a", "an"}:
            continue
        letters.append(tok[0])
        if len(letters) == 3:
            break

    s = "".join(letters) or name[0]
    return s[:3]

def save_svg(path, svg):
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def save_pngs(svg_path, folder):
    """Export PNGs at standard sizes from *svg_path* into *folder*."""
    if cairosvg is None:
        print("cairosvg not available; skipping PNG export", file=sys.stderr)
        return
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_data = f.read()
    sizes = [
        (320, 88, "logo.png"),
        (640, 176, "logo@2x.png"),
    ]
    for w, h, name in sizes:
        out = os.path.join(folder, name)
        cairosvg.svg2png(bytestring=svg_data, write_to=out,
                          output_width=w, output_height=h)
        print(f"wrote {out}")

def main():
    cfg_path = os.path.join(ROOT, "brands.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for b in data["brands"]:
        folder = os.path.join(ROOT, b["id"])
        os.makedirs(folder, exist_ok=True)
        initials = b.get("badge_initials") or initials_from_name(b["name"])
        badge_shape = b.get("badge_shape", b.get("bg_shape", "rounded"))
        use_grad = b.get("use_gradient", False)
        grad_from = b.get("gradient_from") if use_grad else None
        grad_to = b.get("gradient_to") if use_grad else None
        grad_angle = b.get("gradient_angle", 0) if use_grad else 0
        stroke_color = b.get("badge_stroke_color")
        stroke_width = b.get("badge_stroke_width")
        badge = badge_svg(
            badge_shape,
            b.get("primary", "#111827"),
            b.get("accent", "#6B7280"),
            initials,
            use_grad,
            grad_from,
            grad_to,
            grad_angle,
            stroke_color,
            stroke_width,
        )
        svg = TEMPLATE.format(
            badge=badge,
            brand_color=b.get("accent", "#111827"),
            brand_name=b["name"],
            domain=b["domain"]
        )
        # trim indentation
        svg = textwrap.dedent(svg)
        out = os.path.join(folder, "logo.svg")
        save_svg(out, svg)
        print(f"wrote {out}")
        save_pngs(out, folder)

if __name__ == "__main__":
    try:
        import yaml  # ensure dependency present
    except Exception:
        print("PyYAML not available", file=sys.stderr)
    main()
