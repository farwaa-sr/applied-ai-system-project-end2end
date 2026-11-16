"""Hand-drawn pastel SVG illustrations for the UI. No assets to download: every scene is code.

`data_uri(svg)` turns a scene into an <img>-ready data URI, which sidesteps HTML sanitising and
gradient-id clashes when several scenes share one page.
"""
import base64

SKY = ("#FFE2D2", "#F2DDF6", "#D8E6FB")

# (background, accent) per scene
PALETTE = {
    "moon": "#E4DCF8",
    "sun": "#FFEAD0",
    "rain": "#DAEAFB",
    "heart": "#FBDCE6",
    "bolt": "#FFE3D3",
    "leaf": "#D9F1E4",
    "note": "#E3E8FC",
}

MOOD_SCENE = {
    "happy": "sun", "uplifting": "sun", "playful": "sun", "euphoric": "sun", "confident": "sun",
    "sad": "rain", "heartbroken": "rain", "melancholic": "rain", "yearning": "rain",
    "romantic": "heart",
    "intense": "bolt", "aggressive": "bolt",
    "moody": "moon", "focused": "moon", "dreamy": "moon",
    "chill": "leaf", "relaxed": "leaf", "nostalgic": "leaf",
}


def data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def scene_for(mood: str) -> str:
    return MOOD_SCENE.get((mood or "").lower(), "note")


def _spark(x, y, s=1.0, fill="#FFFFFF", op=0.95):
    return (f'<path transform="translate({x} {y}) scale({s})" opacity="{op}" fill="{fill}" '
            'd="M0-8 L2.2-2.2 L8 0 L2.2 2.2 L0 8 L-2.2 2.2 L-8 0 L-2.2-2.2Z"/>')


def _cloud(x, y, s=1.0, fill="#FFFFFF", op=0.9):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="{fill}" opacity="{op}">'
            '<ellipse cx="0" cy="0" rx="34" ry="13"/><circle cx="-12" cy="-10" r="14"/>'
            '<circle cx="8" cy="-15" r="17"/><circle cx="24" cy="-6" r="11"/></g>')


def _note(x, y, s=1.0, fill="#B9A3EC", op=0.85):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="{fill}" opacity="{op}">'
            '<ellipse cx="0" cy="0" rx="7" ry="5" transform="rotate(-20)"/>'
            '<rect x="5" y="-26" width="2.6" height="26" rx="1.3"/>'
            '<path d="M7.6-26 q12 2 10 14 q-3 -8 -10 -8z"/></g>')


def _tree(x, y, s=1.0, leaf="#A9D8C2", trunk="#CDB8A3"):
    return (f'<g transform="translate({x} {y}) scale({s})"><rect x="-2.5" y="-6" width="5" height="16" rx="2" '
            f'fill="{trunk}"/><circle cx="0" cy="-16" r="13" fill="{leaf}"/><circle cx="-8" cy="-9" r="9" '
            f'fill="{leaf}"/><circle cx="8" cy="-9" r="9" fill="{leaf}"/></g>')


def hero_scene() -> str:
    """Wide banner: dusk sky, crescent moon, clouds, floating notes and rolling pastel hills."""
    a, b, c = SKY
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 260" preserveAspectRatio="xMidYMid slice">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/>'
        f'<stop offset="0.55" stop-color="{b}"/><stop offset="1" stop-color="{c}"/></linearGradient>'
        '<radialGradient id="m" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#FFF6D6" stop-opacity="0.95"/>'
        '<stop offset="1" stop-color="#FFF6D6" stop-opacity="0"/></radialGradient></defs>'
        '<rect width="900" height="260" fill="url(#g)"/>'
        '<circle cx="735" cy="82" r="78" fill="url(#m)"/>'
        '<path d="M735 48a34 34 0 1 0 0 68a27 27 0 1 1 0-68z" fill="#FFFBEA"/>'
        + _spark(640, 52, 1.1) + _spark(810, 40, 0.9) + _spark(560, 96, 0.7) + _spark(860, 120, 0.8)
        + _spark(470, 40, 0.8, "#FFF3C9") + _spark(330, 70, 0.6)
        + _cloud(80, 40, 0.8, op=0.55) + _cloud(600, 120, 1.0, op=0.8) + _cloud(850, 168, 0.7, op=0.7)
        + _note(590, 58, 0.9, "#F4A9C4") + _note(665, 150, 0.75, "#9ED4EA") + _note(640, 168, 0.7, "#B9A3EC")
        + '<path d="M0 222 C120 176 260 186 400 214 S700 184 900 210 V260 H0Z" fill="#CFE8DF"/>'
        '<path d="M0 238 C140 206 300 218 450 236 S760 212 900 232 V260 H0Z" fill="#BFD6F0" opacity="0.9"/>'
        '<path d="M0 252 C180 238 330 246 520 253 S780 243 900 251 V260 H0Z" fill="#D9CCF3"/>'
        + _tree(740, 222, 0.8, "#C9BDF0") + _tree(785, 228, 0.6) + _tree(845, 224, 0.85, "#B7DDF0")
        + _tree(40, 230, 0.7) + '</svg>'
    )


def mood_scene(kind: str) -> str:
    """Small square illustration for a mood: moon, sun, rain, heart, bolt, leaf or note."""
    bg = PALETTE.get(kind, PALETTE["note"])
    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><rect width="120" height="120" rx="26" fill="{bg}"/>'
    if kind == "moon":
        body = ('<circle cx="60" cy="60" r="34" fill="#FFF6D6" opacity="0.6"/>'
                '<path d="M66 28a32 32 0 1 0 22 54a26 26 0 1 1-22-54z" fill="#FFF3C0"/>'
                + _spark(30, 34, 0.9) + _spark(96, 30, 0.7) + _spark(92, 88, 0.8, "#FFFFFF") + _cloud(44, 92, 0.6))
    elif kind == "sun":
        rays = "".join(
            f'<line x1="60" y1="14" x2="60" y2="24" stroke="#FFC978" stroke-width="5" stroke-linecap="round" '
            f'transform="rotate({a} 60 60)"/>' for a in range(0, 360, 45))
        body = (rays + '<circle cx="60" cy="60" r="21" fill="#FFD98F"/>' + _cloud(78, 92, 0.7))
    elif kind == "rain":
        drops = "".join(f'<ellipse cx="{x}" cy="{y}" rx="3" ry="6" fill="#9CC4EB" transform="rotate(15 {x} {y})"/>'
                        for x, y in ((40, 86), (58, 96), (76, 86), (94, 96)))
        body = _cloud(62, 58, 1.35) + drops
    elif kind == "heart":
        body = ('<path d="M60 92 C26 66 28 38 46 36 C54 35 59 40 60 46 C61 40 66 35 74 36 C92 38 94 66 60 92Z" '
                'fill="#F7A8C0"/>' + _spark(30, 30, 0.9) + _spark(92, 34, 0.7) + _spark(94, 90, 0.8))
    elif kind == "bolt":
        body = ('<circle cx="60" cy="60" r="36" fill="#FFF1E8" opacity="0.7"/>'
                '<path d="M68 22 L40 66 H58 L50 98 L84 52 H64Z" fill="#FFC27A"/>' + _spark(28, 32, 0.8) + _spark(96, 86, 0.8))
    elif kind == "leaf":
        body = ('<path d="M30 88 C28 52 52 28 90 30 C92 66 68 90 30 88Z" fill="#A7D9BF"/>'
                '<path d="M32 86 C50 66 64 52 84 36" stroke="#F4FBF7" stroke-width="3" fill="none" stroke-linecap="round"/>'
                + _spark(96, 90, 0.7) + _spark(24, 34, 0.7))
    else:
        body = _note(54, 78, 2.2, "#B9A3EC", 0.95) + _spark(92, 32, 0.9) + _spark(26, 40, 0.7)
    return head + body + '</svg>'
