#!/usr/bin/env python3
import os, sys, json, yaml, textwrap, math, re

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
ROOT = os.path.normpath(ROOT)

TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="220" viewBox="0 0 800 220">
  <rect width="100%" height="100%" fill="white"/>
  <g transform="translate(24,24)">
    {badge}
    <text x="120" y="82" font-family="Arial, Helvetica, sans-serif" font-size="56" font-weight="700" fill="{brand_color}">{brand_name}</text>
    <text x="120" y="116" font-family="Arial, Helvetica, sans-serif" font-size="22" fill="#6B7280">{domain}</text>
  </g>
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

def badge_svg(shape, primary, accent, initials, use_gradient=False, gradient_from=None, gradient_to=None, gradient_angle=0):
    defs = ""
    fill = primary
    if use_gradient:
        defs = _gradient_def(gradient_from or primary, gradient_to or accent, gradient_angle)
        fill = "url(#badgeGrad)"
    text_color = pick_initials_color(gradient_from or primary, (gradient_to or accent) if use_gradient else None)
    if shape == "circle":
        return f"""{defs}
    <circle cx="48" cy="48" r="48" fill="{fill}"/>
    <text x="48" y="86" font-family="Arial, Helvetica, sans-serif" font-size="40" text-anchor="middle" fill="{text_color}">{initials}</text>
"""
    elif shape == "diamond":
        return f"""{defs}
    <g transform="translate(0,0)">
      <rect x="0" y="0" width="96" height="96" fill="{fill}" transform="translate(48,48) rotate(45) translate(-48,-48)" rx="16" ry="16"/>
      <text x="72" y="86" font-family="Arial, Helvetica, sans-serif" font-size="36" text-anchor="middle" fill="{text_color}">{initials}</text>
    </g>
"""
    else:  # rounded
        return f"""{defs}
    <rect rx="16" ry="16" width="96" height="96" fill="{fill}"/>
    <text x="72" y="86" font-family="Arial, Helvetica, sans-serif" font-size="40" text-anchor="middle" fill="{text_color}">{initials}</text>
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

def main():
    cfg_path = os.path.join(ROOT, "brands.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for b in data["brands"]:
        folder = os.path.join(ROOT, b["id"])
        os.makedirs(folder, exist_ok=True)
        initials = initials_from_name(b["name"])
        badge_shape = b.get("badge_shape", b.get("bg_shape", "rounded"))
        badge = badge_svg(
            badge_shape,
            b.get("primary", "#111827"),
            b.get("accent", "#6B7280"),
            initials,
            b.get("use_gradient", False),
            b.get("gradient_from"),
            b.get("gradient_to"),
            b.get("gradient_angle", 0),
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

if __name__ == "__main__":
    try:
        import yaml  # ensure dependency present
    except Exception:
        print("PyYAML not available", file=sys.stderr)
    main()
