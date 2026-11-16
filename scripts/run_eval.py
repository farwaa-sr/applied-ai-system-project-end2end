"""Reliability harness: runs fixed inputs through the agent and prints a pass/fail summary.

Deterministic by default (offline: rule-based profile, recorded web fixtures, no network).
Usage:  python scripts/run_eval.py            -> prints tables and writes eval_results.md
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from musicrag.agent import MusicAgent  # noqa: E402
from musicrag.catalog import load_catalog  # noqa: E402
from musicrag.llm import LLMError  # noqa: E402
from musicrag.questions import QUESTIONS, InvalidAnswers  # noqa: E402
from musicrag.retriever import Retriever, load_archetypes  # noqa: E402
from musicrag.web import FixtureClient, WebSearchError  # noqa: E402

KEYS = [q.id for q in QUESTIONS]


def ans(letters: str) -> dict:
    return dict(zip(KEYS, letters.split(",")))


# name, answers, genres that a sensible top-1 catalog pick should belong to
TASTE_CASES = [
    ("Late-night study", "a,a,b,a,b", {"lofi", "ambient"}),
    ("Gym workout", "b,c,d,c,a", {"rock", "metal", "edm", "pop"}),
    ("Sad evening at home", "d,a,c,a,a", {"soul", "blues", "classical", "folk"}),
    ("Party night", "e,c,a,c,c", {"pop", "edm", "indie pop", "reggae"}),
    ("Moody night drive", "c,b,f,c,b", {"synthwave", "alt pop"}),
    ("Romantic date night", "d,b,e,b,a", {"r&b", "soul", "jazz"}),
]


class DownLLM:
    available = True

    def generate_json(self, prompt, retries=1):
        raise LLMError("simulated outage")


class DownWeb:
    name, available = "down", True

    def search_tracks(self, q, limit=10):
        raise WebSearchError("simulated outage")

    def lookup(self, t, a):
        raise WebSearchError("simulated outage")


def main() -> int:
    songs = load_catalog()
    retriever = Retriever(load_archetypes(), songs)
    agent = MusicAgent(retriever, songs, llm=None, web_clients=[], fallback_web=FixtureClient())
    catalog_titles = {s.title.lower() for s in songs}
    rows, passed = [], 0

    def record(name, expectation, ok, detail):
        nonlocal passed
        passed += ok
        rows.append((name, expectation, "Pass" if ok else "Fail", detail))

    # 1. taste cases, retrieval ON vs OFF
    ablation = []
    for name, letters, genres in TASTE_CASES:
        on, off = agent.run(ans(letters)), agent.run(ans(letters), use_rag=False)
        top_on = next(p for p in on.picks if p.kind == "catalog")
        top_off = next(p for p in off.picks if p.kind == "catalog")
        ok = (top_on.title and len(on.picks) == 5
              and any(s.title == top_on.title and s.genre in genres for s in songs))
        record(f"Taste: {name}", f"top pick genre in {sorted(genres)}; 5 picks", ok,
               f"top = {top_on.title}; conf {on.confidence}")
        hit_off = any(s.title == top_off.title and s.genre in genres for s in songs)
        overlap = len({p.title for p in on.picks if p.kind == "catalog"} & {p.title for p in off.picks if p.kind == "catalog"})
        ablation.append((name, on.confidence, off.confidence, bool(ok), hit_off,
                         f"{on.profile.genre}/{on.profile.valence}", f"{off.profile.genre}/{off.profile.valence}", overlap))

    # 2. web picks are verified
    r = agent.run(ans("b,c,d,c,c"))
    web = [p for p in r.picks if p.kind == "web"]
    record("Web picks verified", "2 web picks, none in catalog, all have a source",
           len(web) == 2 and all(p.title.lower() not in catalog_titles and p.source for p in web),
           f"web = {[p.title for p in web]}")

    # 3. familiar novelty -> no web
    r = agent.run(ans("a,a,b,a,a"))
    record("Novelty 'familiar'", "catalog only", all(p.kind == "catalog" for p in r.picks), "no web call made")

    # 4. conflicting answers still produce a flagged-or-confident, complete result
    r = agent.run(ans("a,c,a,a,a"))
    record("Conflicting answers", "5 picks, confidence reported in [0,1]",
           len(r.picks) == 5 and 0 <= r.confidence <= 1, f"conf {r.confidence}, flags {r.flags or 'none'}")

    # 5. guardrails
    for name, bad in [("Empty answers", {}), ("Missing questions", {"setting": "a"}),
                      ("Invalid choice", {**ans("a,a,b,a,a"), "mood": "z"})]:
        try:
            agent.run(bad)
            record(f"Guardrail: {name}", "rejected with InvalidAnswers", False, "accepted")
        except InvalidAnswers as exc:
            record(f"Guardrail: {name}", "rejected with InvalidAnswers", True, str(exc)[:60])

    r = MusicAgent(retriever, songs, llm=DownLLM(), web_clients=[], fallback_web=FixtureClient()).run(ans("a,a,b,a,b"))
    record("Guardrail: LLM outage", "falls back, flag set, 5 picks",
           "llm_unavailable" in r.flags and len(r.picks) == 5, f"flags {r.flags}")
    r = MusicAgent(retriever, songs, llm=None, web_clients=[DownWeb()], fallback_web=FixtureClient()).run(ans("b,c,d,c,c"))
    record("Guardrail: web outage", "falls back to recorded fixtures",
           "web_fallback_fixture" in r.flags and len(r.picks) == 5, f"flags {r.flags}")

    # report
    total = len(rows)
    out = [f"# Evaluation results ({date.today()}, offline deterministic mode)", "",
           f"**{passed}/{total} checks passed**", "",
           "| Test | Expectation | Result | Detail |", "|---|---|---|---|"]
    out += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    on_hits = sum(1 for row in ablation if row[3])
    off_hits = sum(1 for row in ablation if row[4])
    out += ["", "## RAG on vs off", "",
            "| Scenario | Profile genre/valence (on) | Profile genre/valence (off) | Shared catalog picks | "
            "Top pick in expected genres (on / off) |", "|---|---|---|---|---|"]
    out += [f"| {r[0]} | {r[5]} | {r[6]} | {r[7]} | {'yes' if r[3] else 'no'} / {'yes' if r[4] else 'no'} |"
            for r in ablation]
    avg = lambda xs: round(sum(xs) / len(xs), 2)  # noqa: E731
    out += ["", f"Top pick in expected genres: RAG on {on_hits}/{len(ablation)}, RAG off {off_hits}/{len(ablation)}. "
                f"Average shared catalog picks (of 5): {avg([r[7] for r in ablation])}. "
                f"Average reported confidence: on {avg([a[1] for a in ablation])}, off {avg([a[2] for a in ablation])} "
                "(not a like-for-like score: the no-retrieval profile uses a fixed prior of 0.4)."]
    text = "\n".join(out)
    print(text)
    (ROOT / "eval_results.md").write_text(text + "\n", encoding="utf-8")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
