"""Pastel look and feel for the Streamlit UI: one CSS block plus small HTML builders."""
from html import escape

from .illustrations import data_uri, hero_scene, mood_scene, scene_for

INK, MUTED = "#4B4668", "#8A84A6"
# (card tint, card border) cycled across the five song cards
TINTS = [("#FFF0E7", "#FFD7C4"), ("#E9F6EF", "#CBE9D8"), ("#E8F2FC", "#CADFF6"),
         ("#F2ECFC", "#DDD0F3"), ("#FDECF1", "#F8CDDA")]
METER_COLORS = {"energy": "#F7B89B", "valence": "#F4D58D", "acousticness": "#9ED4B8"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
html, body, .stApp, [class*="css"], button, input, textarea { font-family: 'Nunito', 'Segoe UI', system-ui, sans-serif; }
.stApp { background: linear-gradient(180deg, #FFF6F0 0%, #F8F2FF 42%, #EAF4FB 100%); color: #4B4668; }
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; height: 0; }
.block-container { max-width: 860px; padding-top: 1.4rem; padding-bottom: 4rem; }
.stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp button, .stApp input,
.stMarkdown, [data-testid="stWidgetLabel"], .hero-text *, .song *, .summary *, .meter * {
  font-family: 'Nunito', 'Segoe UI', system-ui, sans-serif !important; }
h1, h2, h3 { color: #4B4668; letter-spacing: -0.01em; }
p, label, span, li { color: #4B4668; }

.hero { position: relative; border-radius: 30px; overflow: hidden; height: 230px; margin-bottom: 1.2rem;
        box-shadow: 0 10px 30px rgba(155, 131, 224, 0.18); }
.hero .hero-art { position: absolute; inset: 0; width: 100% !important; height: 100% !important; max-width: none !important; object-fit: cover; margin: 0; }
.hero-text { position: relative; padding: 26px 32px; max-width: 66%; }
.hero-kicker { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; color: #8F78D6; }
.hero-text h1 { font-size: 1.95rem; line-height: 1.15; margin: 0.35rem 0 0.5rem; font-weight: 800; padding: 0; }
.hero-text p { font-size: 1rem; margin: 0; color: #5E5878; }

.section-title { font-size: 1.15rem; font-weight: 800; margin: 1.4rem 0 0.2rem; }
.section-sub { color: #8A84A6; margin: 0 0 0.6rem; font-size: 0.95rem; }

[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 24px; border-color: #E8DDF6;
        background: rgba(255, 255, 255, 0.72); box-shadow: 0 4px 18px rgba(155, 131, 224, 0.08); }
[data-testid="stForm"] { border: none; padding: 0; background: transparent; }
.q-label { font-weight: 800; font-size: 1.02rem; margin-bottom: 0.2rem; }

button[kind="primary"], button[kind="primaryFormSubmit"] { background: linear-gradient(135deg, #B9A3EC, #F4A9C4);
        color: #fff; border: none; border-radius: 999px; padding: 0.6rem 1.6rem; font-weight: 800;
        box-shadow: 0 6px 16px rgba(185, 163, 236, 0.45); }
button[kind="primary"] p, button[kind="primaryFormSubmit"] p { color: #fff !important; font-weight: 800; }
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover { filter: brightness(1.05); color: #fff; border: none; }
button[kind="secondary"], button[kind="secondaryFormSubmit"] { background: #fff; color: #6C58B5; border: 1.5px solid #D9CCF3;
        border-radius: 999px; font-weight: 700; }
button[kind="secondary"]:hover { border-color: #B9A3EC; color: #6C58B5; background: #FAF7FF; }
button[kind="pills"], button[kind="pillsActive"] { border-radius: 999px; font-weight: 700; }
button[kind="pills"] { background: #fff; border: 1.5px solid #E5DAF5; color: #5E5878; }
button[kind="pillsActive"] { background: #EBE2FB; border: 1.5px solid #B9A3EC; color: #5B47A8; }

.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0.2rem 0 0.8rem; }
.chip { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.82rem; font-weight: 700;
        background: #EFE8FB; color: #5B47A8; }
.chip.mint { background: #DDF2E7; color: #2F7A58; } .chip.peach { background: #FFE5D6; color: #A8613A; }
.chip.sky { background: #DCEBFA; color: #3A6EA5; } .chip.rose { background: #FBDDE7; color: #A8475F; }

.summary { display: flex; gap: 18px; align-items: center; }
.summary img { width: 92px; height: 92px; border-radius: 24px; flex: none; }
.summary h3 { margin: 0 0 4px; font-size: 1.25rem; }
.summary p { margin: 0 0 8px; color: #6A6485; font-size: 0.95rem; }
.meter { display: flex; align-items: center; gap: 10px; font-size: 0.82rem; color: #6A6485; margin: 3px 0; }
.meter .name { width: 96px; font-weight: 700; } .meter .val { width: 34px; text-align: right; }
.meter .track { flex: 1; height: 9px; border-radius: 99px; background: #EFE9F8; overflow: hidden; }
.meter .fill { height: 100%; border-radius: 99px; }

.song { display: flex; gap: 16px; align-items: flex-start; }
.song-art { width: 74px; height: 74px; border-radius: 20px; flex: none; }
.song-body { flex: 1; min-width: 0; }
.song-top { display: flex; align-items: center; gap: 10px; }
.rank { flex: none; width: 26px; height: 26px; border-radius: 50%; background: #fff; color: #7B66C4; font-weight: 800;
        font-size: 0.85rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,.06); }
.song-title { font-size: 1.12rem; font-weight: 800; line-height: 1.2; }
.song-artist { color: #7A7496; font-size: 0.95rem; margin: 2px 0 8px 36px; }
.song .song-why { margin: 8px 0 12px 36px !important; font-size: 0.93rem; line-height: 1.45; color: #5A5474; }
.song-body .chip { margin-left: 36px; }
@media (max-width: 640px) {
  .hero { height: auto; min-height: 210px; } .hero-text { max-width: 100%; padding: 20px 20px 70px; }
  .hero-text h1 { font-size: 1.45rem; } .hero-text p { font-size: 0.92rem; }
  .song-art { width: 56px; height: 56px; } .summary img { width: 64px; height: 64px; }
  .song-artist, .song-body .chip { margin-left: 0; } .song .song-why { margin-left: 0 !important; }
}
%CARD_KEYS%
iframe { border-radius: 14px; }
.soft-note { font-size: 0.82rem; color: #8A84A6; text-align: center; margin-top: 1.4rem; }
</style>
"""


def _card_key_css() -> str:
    return "\n".join(
        f".st-key-pick{i} {{ background: {bg}; border: 1.5px solid {bd}; border-radius: 26px; padding: 1rem 1.1rem 0.7rem; "
        f"margin-bottom: 0.9rem; box-shadow: 0 6px 20px rgba(120,100,170,0.08); }}"
        for i, (bg, bd) in enumerate(TINTS))


def theme_css() -> str:
    return CSS.replace("%CARD_KEYS%", _card_key_css())


def hero_html() -> str:
    return (
        f'<div class="hero"><img class="hero-art" alt="" src="{data_uri(hero_scene())}"/>'
        '<div class="hero-text"><div class="hero-kicker">Music concierge</div>'
        "<h1>Music for the mood you're in</h1>"
        "<p>Answer five gentle questions. An agent finds songs that fit and checks that they're real.</p>"
        "</div></div>"
    )


def section_html(title: str, sub: str = "") -> str:
    return f'<div class="section-title">{escape(title)}</div>' + (f'<p class="section-sub">{escape(sub)}</p>' if sub else "")


def _meter(name: str, value: float) -> str:
    return (f'<div class="meter"><span class="name">{name}</span><div class="track"><div class="fill" '
            f'style="width:{max(0, min(1, value)) * 100:.0f}%;background:{METER_COLORS[name]}"></div></div>'
            f'<span class="val">{value:.2f}</span></div>')


def summary_html(profile, confidence: float, set_no: int, flags: list) -> str:
    chips = [f'<span class="chip">{escape(profile.genre)}</span>', f'<span class="chip rose">{escape(profile.mood)}</span>',
             f'<span class="chip mint">confidence {confidence:.0%}</span>', f'<span class="chip sky">set {set_no}</span>']
    chips += [f'<span class="chip peach">{escape(f.replace("_", " "))}</span>' for f in flags]
    meters = "".join(_meter(n, getattr(profile, n)) for n in ("energy", "valence", "acousticness"))
    return (f'<div class="summary"><img alt="" src="{data_uri(mood_scene(scene_for(profile.mood)))}"/><div>'
            f'<h3>Your vibe</h3><p>{escape(profile.rationale)}</p><div class="chips">{"".join(chips)}</div>{meters}</div></div>')


def song_html(rank: int, pick) -> str:
    art = data_uri(mood_scene(scene_for(getattr(pick, "mood", ""))))
    if pick.kind == "web":
        chip = f'<span class="chip sky">new find · verified on {escape(pick.source)}</span>'
    else:
        chip = '<span class="chip mint">from the catalog</span>'
    return (f'<div class="song"><img class="song-art" alt="" src="{art}"/><div class="song-body">'
            f'<div class="song-top"><span class="rank">{rank}</span><span class="song-title">{escape(pick.title)}</span></div>'
            f'<div class="song-artist">{escape(pick.artist)}</div>{chip}'
            f'<p class="song-why">{escape(pick.explanation)}</p></div></div>')
