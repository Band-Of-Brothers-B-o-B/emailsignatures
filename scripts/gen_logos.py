#!/usr/bin/env python3
import os, sys, json, yaml, textwrap

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
ROOT = os.path.normpath(ROOT)

TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="220" viewBox="0 0 800 220">
  <rect width="100%" height="100%" fill="white"/>
  <g transform="translate(24,24)">
    {badge}
    <text x="120" y="82" font-family="Arial, Helvetica, sans-serif" font-size="56" font-weight="700" fill="{title_color}">{brand_name}</text>
    <text x="120" y="116" font-family="Arial, Helvetica, sans-serif" font-size="22" fill="#6B7280">{domain}</text>
  </g>
</svg>
"""

def badge_svg(shape, primary, accent, initials):
    if shape == "circle":
        return f"""
    <circle cx="48" cy="48" r="48" fill="{primary}"/>
    <text x="48" y="86" font-family="Arial, Helvetica, sans-serif" font-size="40" text-anchor="middle" fill="white">{initials}</text>
"""
    elif shape == "diamond":
        return f"""
    <g transform="translate(0,0)">
      <rect x="0" y="0" width="96" height="96" fill="{primary}" transform="translate(48,48) rotate(45) translate(-48,-48)" rx="16" ry="16"/>
      <text x="72" y="86" font-family="Arial, Helvetica, sans-serif" font-size="36" text-anchor="middle" fill="white">{initials}</text>
    </g>
"""
    else:  # rounded
        return f"""
    <rect rx="16" ry="16" width="96" height="96" fill="{primary}"/>
    <text x="72" y="86" font-family="Arial, Helvetica, sans-serif" font-size="40" text-anchor="middle" fill="white">{initials}</text>
"""

def initials_from_name(name):
    parts = [p for p in name.split() if p and p[0].isalnum()]
    if not parts: return "•"
    # e.g., "Font of Madness" -> "FoM"
    letters = []
    for p in parts:
        if p.lower() in {"of","and","the","a","an"}:  # skip small words
            continue
        letters.append(p[0])
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
        badge = badge_svg(b.get("bg_shape","rounded"), b.get("primary","#111827"), b.get("accent","#6B7280"), initials)
        svg = TEMPLATE.format(
            badge=badge,
            title_color=b.get("accent","#111827"),
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
