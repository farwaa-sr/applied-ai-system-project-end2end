"""Multiple-choice intake: the questions, answer validation and query building.

Using fixed choices (instead of free text) is the first guardrail: the agent only ever
sees a small, known set of inputs, so there is nothing to inject and every run is testable.
"""
from dataclasses import dataclass

from .log import get_logger

log = get_logger("questions")


@dataclass(frozen=True)
class Option:
    label: str
    keywords: str          # words added to the retrieval query
    value: object = None   # optional numeric / categorical hint used by the profile builder


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    options: dict  # letter -> Option


QUESTIONS: tuple[Question, ...] = (
    Question("setting", "What are you doing while you listen?", {
        "a": Option("Studying, coding or reading", "studying focus quiet library late night concentration"),
        "b": Option("Working out or running", "workout gym running motivation adrenaline training"),
        "c": Option("Driving or commuting", "driving commute night drive city headphones"),
        "d": Option("Relaxing at home", "relaxing home cozy evening unwinding coffee"),
        "e": Option("At a party or getting ready to go out", "party dancing club friends celebration"),
    }),
    Question("energy", "How much energy do you want?", {
        "a": Option("Low, calm and quiet", "low energy calm slow soft", 0.30),
        "b": Option("Medium, steady groove", "steady groove mid tempo", 0.55),
        "c": Option("High, fast and loud", "high energy fast loud driving", 0.88),
    }),
    Question("mood", "Which mood fits best right now?", {
        "a": Option("Happy and uplifting", "happy uplifting joy sunshine good vibes", "happy"),
        "b": Option("Calm and focused", "calm focused chill relaxed peaceful", "chill"),
        "c": Option("Sad or reflective", "sad heartbreak melancholic reflective lonely", "sad"),
        "d": Option("Intense or aggressive", "intense aggressive angry heavy release", "intense"),
        "e": Option("Romantic", "romantic love smooth intimate date night", "romantic"),
        "f": Option("Moody and dark", "moody dark brooding atmospheric neon", "moody"),
    }),
    Question("texture", "What sound do you prefer?", {
        "a": Option("Acoustic and organic", "acoustic organic guitar piano warm", 0.85),
        "b": Option("A mix of both", "balanced blend", 0.45),
        "c": Option("Electronic and produced", "electronic synth produced beats", 0.10),
    }),
    Question("novelty", "How adventurous are you feeling?", {
        "a": Option("Stick to what fits my taste (catalog only)", "familiar", "familiar"),
        "b": Option("Mostly familiar, one new find", "mix", "mix"),
        "c": Option("Surprise me with something new", "discover new", "new"),
    }),
)

QUESTION_BY_ID = {q.id: q for q in QUESTIONS}


class InvalidAnswers(ValueError):
    """Raised when the answers are incomplete or contain an unknown choice."""


def normalize_answers(raw: dict) -> dict:
    """Validate raw answers ({question_id: letter}) and return a clean copy.

    Unknown questions are ignored with a warning; missing or invalid choices raise
    InvalidAnswers listing every problem at once.
    """
    if not isinstance(raw, dict) or not raw:
        raise InvalidAnswers("No answers were provided.")
    problems, clean = [], {}
    for q in QUESTIONS:
        choice = str(raw.get(q.id, "")).strip().lower()
        if not choice:
            problems.append(f"'{q.id}' is missing")
        elif choice not in q.options:
            problems.append(f"'{q.id}': '{choice}' is not one of {sorted(q.options)}")
        else:
            clean[q.id] = choice
    for extra in set(raw) - set(QUESTION_BY_ID):
        log.warning("Ignoring unknown question id %r", extra)
    if problems:
        raise InvalidAnswers("; ".join(problems))
    return clean


def option_for(answers: dict, qid: str) -> Option:
    return QUESTION_BY_ID[qid].options[answers[qid]]


def build_query(answers: dict) -> str:
    """Turn validated answers into the text query used for retrieval."""
    return " ".join(option_for(answers, q.id).keywords for q in QUESTIONS)


def describe(answers: dict) -> str:
    """Human-readable summary of the answers, for prompts and logs."""
    return "; ".join(
        f"{q.prompt} -> {option_for(answers, q.id).label}" for q in QUESTIONS
    )
