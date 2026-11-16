"""Grounded explanations: the LLM may only describe songs it was given, and every
returned explanation is checked against that set before being shown."""
from .llm import GeminiClient, LLMError
from .log import get_logger

log = get_logger("explain")


def template_explanation(song, score: float, max_score: float, reasons: list[str]) -> str:
    matches = [r.split(" (")[0] for r in reasons if "match" in r]
    close = [r.split(" gap")[0] for r in reasons if "gap" in r and float(r.split("gap ")[1].split(" ")[0]) <= 0.15]
    bits = matches + [f"close {c}" for c in close]
    why = ", ".join(bits) if bits else "overall closest audio profile"
    return f"{song.genre}/{song.mood} track; {why} ({score / max_score:.0%} match)."


def llm_explanations(llm: GeminiClient, profile, archetype_text: str, picks: list) -> dict[str, str]:
    """Return {title: explanation} for the given (song, score, reasons) picks.

    Raises LLMError on failure. Titles the model invents are dropped (grounding check).
    """
    allowed = {s.title for s, _, _ in picks}
    songs = "\n".join(
        f"- {s.title} by {s.artist} ({s.genre}, {s.mood}, energy {s.energy}, acousticness {s.acousticness}); "
        f"scoring notes: {', '.join(r)}" for s, _, r in picks
    )
    prompt = (
        "Explain, in one friendly sentence each, why these songs suit the listener.\n"
        f"Listener profile: {profile.as_dict()}\n"
        f"Retrieved archetype evidence:\n{archetype_text}\n\n"
        f"Songs (use ONLY this data; do not add facts about the songs):\n{songs}\n\n"
        "Return a JSON object mapping each exact song title to its one-sentence explanation."
    )
    data = llm.generate_json(prompt)
    clean = {t: str(e).strip() for t, e in data.items() if t in allowed and str(e).strip()}
    dropped = set(data) - allowed
    if dropped:
        log.warning("Dropped explanations for titles not in the picks: %s", sorted(dropped))
    return clean


__all__ = ["template_explanation", "llm_explanations", "LLMError"]
