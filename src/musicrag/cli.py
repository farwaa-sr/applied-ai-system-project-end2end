"""Command-line interface: ask the 5 questions, run the agent, collect human review.

  python -m musicrag.cli                      interactive
  python -m musicrag.cli --answers a,a,b,a,b  non-interactive (one letter per question)
  python -m musicrag.cli --offline            rule-based only: no Gemini, fixture web results
  python -m musicrag.cli --no-rag             ablation: skip retrieval
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .agent import MusicAgent, Result
from .catalog import load_catalog
from .llm import GeminiClient
from .questions import QUESTIONS, InvalidAnswers
from .retriever import Retriever, load_archetypes
from .web import FixtureClient, MusicBrainzClient, SpotifyClient

ROOT = Path(__file__).resolve().parents[2]
FEEDBACK_FILE = ROOT / "logs" / "feedback.jsonl"
TRACE_FILE = ROOT / "ai_interactions.md"


def build_agent(offline: bool) -> MusicAgent:
    songs = load_catalog()
    retriever = Retriever(load_archetypes(), songs)
    if offline:
        return MusicAgent(retriever, songs, llm=None, web_clients=[], fallback_web=FixtureClient())
    return MusicAgent(retriever, songs, llm=GeminiClient(), web_clients=[SpotifyClient(), MusicBrainzClient()])


def ask_interactively() -> dict:
    answers = {}
    for q in QUESTIONS:
        print(f"\n{q.prompt}")
        for letter, opt in q.options.items():
            print(f"  {letter}) {opt.label}")
        for _ in range(3):
            choice = input("> ").strip().lower()
            if choice in q.options:
                answers[q.id] = choice
                break
            print(f"Please choose one of: {', '.join(q.options)}")
        else:
            raise InvalidAnswers(f"No valid answer for '{q.id}'")
    return answers


def format_result(r: Result) -> str:
    p = r.profile
    lines = [
        f"Taste profile ({p.source}): {p.genre} / {p.mood}, energy {p.energy}, valence {p.valence}, "
        f"acousticness {p.acousticness}",
        f"Why: {p.rationale}",
        f"Overall confidence: {r.confidence}   Flags: {', '.join(r.flags) or 'none'}",
        "", "Recommendations:",
    ]
    for i, pick in enumerate(r.picks, 1):
        tag = f"web:{pick.source}" if pick.kind == "web" else f"catalog {pick.score:.1f}/13"
        lines.append(f"  {i}. {pick.title} - {pick.artist}  [{tag}]")
        lines.append(f"     {pick.explanation}")
        if pick.url:
            lines.append(f"     {pick.url}")
    return "\n".join(lines)


def save_trace(r: Result, label: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = (f"\n## Run: {label} ({stamp})\n\nAnswers: `{r.answers}`\n\n### Reasoning trace\n\n"
             f"{r.trace.to_markdown()}\n\n### Output\n\n```\n{format_result(r)}\n```\n")
    if not TRACE_FILE.exists():
        TRACE_FILE.write_text("# AI interaction and reasoning traces\n", encoding="utf-8")
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(block)


def human_review(r: Result, answers: dict) -> None:
    reply = input("\nDo these picks make sense? [y = approve / n = flag] > ").strip().lower()
    verdict = "approved" if reply.startswith("y") else "flagged"
    note = input("Optional note: ").strip() if verdict == "flagged" else ""
    FEEDBACK_FILE.parent.mkdir(exist_ok=True)
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "answers": answers,
                            "verdict": verdict, "note": note,
                            "picks": [p.title for p in r.picks]}) + "\n")
    print("Thanks, feedback saved." if verdict == "approved" else "Flagged for review. Thanks.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Agentic RAG music recommender")
    ap.add_argument("--answers", help="comma-separated letters, one per question (e.g. a,a,b,a,b)")
    ap.add_argument("--offline", action="store_true", help="no Gemini, no live web (fixtures only)")
    ap.add_argument("--no-rag", action="store_true", help="disable retrieval (ablation)")
    ap.add_argument("--trace", action="store_true", help="append the reasoning trace to ai_interactions.md")
    ap.add_argument("--no-review", action="store_true", help="skip the human review prompt")
    args = ap.parse_args(argv)

    try:
        agent = build_agent(args.offline)
        if args.answers:
            letters = [x.strip() for x in args.answers.split(",")]
            answers = dict(zip((q.id for q in QUESTIONS), letters))
        else:
            answers = ask_interactively()
        result = agent.run(answers, use_rag=not args.no_rag)
    except InvalidAnswers as exc:
        print(f"Sorry, I couldn't use those answers: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"Setup problem: {exc}", file=sys.stderr)
        return 1

    print("\n" + format_result(result))
    if args.trace:
        save_trace(result, "retrieval off" if args.no_rag else "retrieval on")
    if not args.answers and not args.no_review:
        human_review(result, result.answers)
    elif result.needs_review:
        print("\nNote: low confidence, a human should review this result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
