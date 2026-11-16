"""The agent: plans a sequence of tool calls, checks its own work, and records a trace.

Decisions it makes (each one is written to the trace):
  * low retrieval confidence      -> widen retrieval and rebuild the profile
  * LLM call fails                -> keep the rule-based profile / template explanations
  * novelty answer / catalog gap  -> decide whether, and how many, web songs to fetch
  * web candidate fails the check -> try the next candidate, next strategy, next source
  * overall confidence is low     -> flag the result for human review
"""
from dataclasses import dataclass, field

from .catalog import Song
from .explain import llm_explanations, template_explanation
from .links import clean_title
from .llm import GeminiClient, LLMError
from .log import get_logger
from .profile import TasteProfile, answers_only_profile, baseline_profile, refine_with_llm
from .questions import build_query, normalize_answers, option_for
from .retriever import Retriever
from .scorer import MAX_SCORE, rank_songs
from .web import FixtureClient, Track, WebSearchError, verify_candidate

log = get_logger("agent")

LOW_CONFIDENCE = 0.5
GAP_RATIO = 0.60          # best catalog score below this share of the maximum = "catalog gap"
N_WEB = {"familiar": 0, "mix": 1, "new": 2}
TOTAL_PICKS = 5


@dataclass
class Pick:
    title: str
    artist: str
    kind: str                 # "catalog" or "web"
    explanation: str
    score: float | None = None
    url: str = ""
    source: str = "catalog"
    mood: str = ""            # used by the UI to choose an illustration


@dataclass
class Trace:
    steps: list = field(default_factory=list)

    def add(self, name: str, detail: str) -> None:
        self.steps.append((name, detail))
        log.info("[trace] %s: %s", name, detail)

    def to_markdown(self) -> str:
        return "\n".join(f"{i}. **{n}**: {d}" for i, (n, d) in enumerate(self.steps, 1))


@dataclass
class Result:
    answers: dict
    profile: TasteProfile
    picks: list
    confidence: float
    flags: list
    trace: Trace

    @property
    def needs_review(self) -> bool:
        return "needs_human_review" in self.flags


class MusicAgent:
    def __init__(self, retriever: Retriever, songs: list[Song], llm: GeminiClient | None = None,
                 web_clients: list | None = None, fallback_web=None):
        self.retriever = retriever
        self.songs = songs
        self.llm = llm if llm is not None and llm.available else None
        self._llm_down = False   # circuit breaker: set after the first LLM failure in a run
        self.web_clients = web_clients or []
        self.fallback_web = fallback_web if fallback_web is not None else _safe_fixture()

    # ------------------------------------------------------------------ main loop
    def run(self, raw_answers: dict, use_rag: bool = True, exclude=None) -> Result:
        """Recommend songs. `exclude` is an iterable of titles already shown, never repeated (for "new set")."""
        trace, flags = Trace(), []
        self._llm_down = False
        answers = normalize_answers(raw_answers)
        trace.add("validate", "answers accepted: " + ", ".join(f"{k}={v}" for k, v in answers.items()))
        shown_titles = list(exclude or [])
        shown = {clean_title(t) for t in shown_titles}
        if shown:
            trace.add("exclude", f"{len(shown)} previously shown songs will not be repeated")
        pool = [s for s in self.songs if clean_title(s.title) not in shown]

        # 1. RAG: retrieve archetypes and build the profile
        hits = []
        if use_rag:
            query = build_query(answers)
            hits = self.retriever.archetypes_for(query, k=3)
            trace.add("retrieve", "top archetypes: " + ", ".join(f"{h.doc.name} ({h.score:.2f})" for h in hits))
        if hits:
            genres = {s.genre for s in self.songs}
            profile = baseline_profile(answers, hits, genres)
            if profile.confidence < LOW_CONFIDENCE:
                hits = self.retriever.archetypes_for(query, k=5)
                profile = baseline_profile(answers, hits, genres)
                trace.add("decide", f"confidence was low, widened retrieval to {len(hits)} archetypes "
                                    f"-> confidence {profile.confidence}")
            trace.add("profile", f"baseline {profile.genre}/{profile.mood}, energy {profile.energy}, "
                                 f"confidence {profile.confidence}")
            if self._llm_ready():
                try:
                    profile = refine_with_llm(self.llm, answers, hits, profile, self.songs)
                    trace.add("llm-refine", f"Gemini refined profile -> {profile.genre}/{profile.mood}, "
                                            f"energy {profile.energy}; {profile.rationale}")
                except LLMError as exc:
                    self._llm_down = True
                    flags.append("llm_unavailable")
                    trace.add("decide", f"LLM unavailable ({exc}); keeping rule-based profile, "
                                        "skipping the LLM for the rest of this run")
            else:
                flags.append("llm_unavailable")
                trace.add("decide", "no LLM configured; using rule-based profile")
        else:
            profile = answers_only_profile(answers, self.songs)
            trace.add("profile", "retrieval disabled; " + profile.rationale)

        # 2. Score the catalog
        ranked = rank_songs(profile, pool, k=TOTAL_PICKS)
        best_ratio = ranked[0][1] / MAX_SCORE if ranked else 0.0
        trace.add("score", f"best unseen catalog match {ranked[0][0].title} at {best_ratio:.0%} of max"
                  if ranked else "no unseen catalog songs left")

        # 3. Decide about the web
        novelty = option_for(answers, "novelty").value
        n_web = N_WEB[novelty]
        if best_ratio < GAP_RATIO:
            n_web = max(n_web, 1)
            flags.append("catalog_gap")
            trace.add("decide", f"catalog gap ({best_ratio:.0%} < {GAP_RATIO:.0%}); fetching a web song")
        else:
            trace.add("decide", f"novelty='{novelty}' -> fetch {n_web} web song(s)")

        web_picks = self._fetch_web(profile, hits, n_web, trace, flags, shown, shown_titles) if n_web else []
        n_catalog = TOTAL_PICKS - len(web_picks)
        catalog = ranked if n_catalog >= len(ranked) else rank_songs(profile, pool, k=n_catalog)
        if len(catalog) + len(web_picks) < TOTAL_PICKS:
            flags.append("catalog_exhausted")
            trace.add("decide", "ran out of unseen songs; returning fewer than 5 picks")

        # 4. Grounded explanations
        explanations = self._explain(profile, hits, catalog, trace, flags)
        picks = [Pick(s.title, s.artist, "catalog", explanations[s.title], score, mood=s.mood)
                 for s, score, _ in catalog] + web_picks

        # 5. Confidence and review flag
        confidence = round(0.5 * profile.confidence + 0.5 * min(1.0, best_ratio), 2)
        if confidence < LOW_CONFIDENCE:
            flags.append("needs_human_review")
        trace.add("finish", f"{len(picks)} picks, overall confidence {confidence}, flags {flags or 'none'}")
        return Result(answers, profile, picks, confidence, flags, trace)

    def _llm_ready(self) -> bool:
        return self.llm is not None and not self._llm_down

    # ------------------------------------------------------------------ web tool
    def _fetch_web(self, profile, hits, n_needed, trace, flags, shown=frozenset(), shown_titles=()) -> list[Pick]:
        found: list[Pick] = []
        seen: set = set()
        terms = list(hits[0].doc.search_terms) if hits else [f"{profile.genre} {profile.mood}"]
        clients = [c for c in self.web_clients if c.available] + [self.fallback_web]
        for client in [c for c in clients if c is not None]:
            if len(found) >= n_needed:
                break
            try:
                tracks = self._candidates(client, profile, terms, trace, shown_titles)
            except WebSearchError as exc:
                trace.add("web", f"{client.name} failed ({exc}); trying next source")
                continue
            for track in tracks:
                if clean_title(track.title) in shown:
                    trace.add("verify", f"rejected '{track.title}' (already shown in an earlier set)")
                    continue
                ok, why = verify_candidate(track, self.songs, seen)
                if not ok:
                    trace.add("verify", f"rejected '{track.title}' ({why})")
                    continue
                seen.add((" ".join(track.title.lower().split()), " ".join(track.artist.lower().split())))
                found.append(Pick(track.title, track.artist, "web", (
                    f"Web discovery matching your {profile.mood} {profile.genre} taste; "
                    f"existence verified via {track.source}."), None, track.url, track.source, profile.mood))
                trace.add("verify", f"accepted '{track.title}' by {track.artist} via {track.source}")
                if len(found) >= n_needed:
                    break
            if client.name == "fixture" and found:
                flags.append("web_fallback_fixture")
        if len(found) < n_needed:
            flags.append("web_shortfall")
            trace.add("decide", f"only {len(found)}/{n_needed} web songs found; filling with catalog songs")
        return found

    def _candidates(self, client, profile, terms, trace, avoid=()) -> list[Track]:
        """LLM proposes songs, the web source confirms they exist; tag search is the fallback."""
        out: list[Track] = []
        if self._llm_ready() and client.name != "fixture":
            try:
                prompt = (
                    "Suggest 5 real, well-known songs (title and artist) that fit this listener profile and "
                    f"are NOT in this list: {[s.title for s in self.songs] + list(avoid)}.\n"
                    f"Profile: {profile.as_dict()}\nStyle hints: {terms}\n"
                    'Return JSON: {"candidates": [{"title": "...", "artist": "..."}]}'
                )
                for c in self.llm.generate_json(prompt).get("candidates", [])[:5]:
                    track = client.lookup(str(c.get("title", "")), str(c.get("artist", "")))
                    trace.add("web", f"{client.name} lookup '{c.get('title')}' by {c.get('artist')}: "
                                     f"{'confirmed' if track else 'not found (possible hallucination)'}")
                    if track:
                        out.append(track)
            except LLMError as exc:
                self._llm_down = True
                trace.add("decide", f"LLM could not propose songs ({exc}); using tag search")
        if not out:
            for term in terms[:3]:
                tracks = client.search_tracks(f"{profile.genre} {term}")
                trace.add("web", f"{client.name} search '{profile.genre} {term}' -> {len(tracks)} result(s)")
                out.extend(sorted(tracks, key=lambda t: -t.popularity))
                if out:
                    break
        return out

    # ------------------------------------------------------------------ explanations
    def _explain(self, profile, hits, catalog, trace, flags) -> dict[str, str]:
        templates = {s.title: template_explanation(s, score, MAX_SCORE, reasons) for s, score, reasons in catalog}
        if not self._llm_ready():
            return templates
        try:
            evidence = "\n".join(h.doc.text.strip() for h in hits[:2])
            llm_text = llm_explanations(self.llm, profile, evidence, catalog)
            missing = [t for t in templates if t not in llm_text]
            if missing:
                trace.add("verify", f"LLM explanations missing for {missing}; used templates for those")
            trace.add("explain", f"Gemini explanations grounded in {len(llm_text)} retrieved songs")
            return {**templates, **llm_text}
        except LLMError as exc:
            self._llm_down = True
            if "llm_unavailable" not in flags:
                flags.append("llm_unavailable")
            trace.add("decide", f"LLM explanation failed ({exc}); used templates")
            return templates


def _safe_fixture():
    try:
        return FixtureClient()
    except (OSError, ValueError):
        log.warning("Web fixtures unavailable")
        return None
