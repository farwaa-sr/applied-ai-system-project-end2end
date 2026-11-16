# Agentic RAG Music Concierge

An applied-AI extension of my **Music Recommender Simulation** (Modules 1-3). You answer five
multiple-choice questions; an agent retrieves matching taste-profile documents (RAG), builds a taste
profile, ranks a song catalog, decides whether to look for new songs on the web, **verifies** every web
song actually exists, and explains each pick with a confidence score.

## Original project

**Music Recommender Simulation** (kept in [`musicrecommendersimulation-starter/`](musicrecommendersimulation-starter/)).
It was a small content-based recommender: a 23-song `songs.csv` (mostly invented songs), a hand-written user taste profile
(favorite genre and mood, target energy, acoustic preference), and a weighted scoring rule that rewarded
songs for being *close* to the target (energy 7.0, valence 2.5, acousticness 1.0, mood 2.0, genre 0.5 points).
It had no AI components and no way to find songs outside its tiny catalog. This project keeps that scorer
unchanged (`src/musicrag/scorer.py`) and wraps it in retrieval, an agent loop, web discovery and a
reliability layer. The course starter also shipped a basic Streamlit form (free-text genre and mood, an
energy slider; its `src/app.py`, visible in that repo's early history); this project's [`app.py`](app.py)
extends that idea.

## What the AI parts do

| Feature | Where | How it changes behaviour |
|---|---|---|
| **RAG** | `retriever.py`, `data/profiles/` | TF-IDF search over 10 archetype documents and the song catalog. Retrieved archetypes set the profile's genre, valence and (partly) energy/acousticness, and supply the web search hints. Without retrieval the profile falls back to answers only. |
| **Agentic workflow** | `agent.py` | One agent picks tools and branches on what it finds: widens retrieval on low confidence, skips or runs web search depending on the novelty answer and a "catalog gap" check, tries the next candidate or source when verification fails, flags low confidence for human review. Every step is written to a trace. |
| **Reliability / guardrails** | `questions.py`, `web.py`, `profile.py`, `scripts/run_eval.py` | MCQ validation, LLM output validation, web-result verification, API fallbacks, a circuit breaker, logging, 27 unit tests and a 14-check harness. |

## Architecture overview

Full diagram: [`diagrams/architecture.md`](diagrams/architecture.md) (renders on GitHub), Mermaid source in
[`diagrams/architecture.mmd`](diagrams/architecture.mmd). An older v1 plan is in `diagrams/architecture_v1.md`.

1. **Input**: five fixed-choice questions, validated before anything runs.
2. **Retrieve**: the answers become a query; a TF-IDF retriever returns the closest taste archetypes.
3. **Profile**: a rule-based baseline blends the answers with the retrieved archetypes. Gemini then refines it
   from the retrieved text; every field is checked against the catalog's genres/moods and numeric ranges.
4. **Score**: the original weighted scorer ranks the catalog.
5. **Decide**: the agent decides how many web songs to fetch (novelty answer, or a weak best match).
6. **Web discovery**: Gemini proposes songs, then Spotify (or MusicBrainz as a fallback) must *confirm each one
   exists*. Songs already in the catalog or already picked are rejected. If every source fails, recorded
   fixtures are used and the result is flagged.
7. **Explain**: Gemini explains each catalog pick using only the supplied song data; titles it invents are dropped.
8. **Human in the loop**: the CLI and the web UI ask you to approve or flag the result; verdicts go to
   `logs/feedback.jsonl` (gitignored).

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1      macOS/Linux/Git Bash: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys (optional, see below)
```

| Key in `.env` | Needed for | Without it |
|---|---|---|
| `GEMINI_API_KEY` (and optional `GEMINI_MODEL`) | LLM profile refinement, song proposals, explanations | Rule-based profile and template explanations |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | Primary web source (Spotify Search API) | MusicBrainz (no account), then recorded fixtures |

Spotify's Web API currently requires an active Premium subscription on the app owner's account. `.env` is
gitignored; never commit real keys.

## Run it

**Web UI** (Streamlit): five clickable questions, result cards with Spotify links, the agent's
reasoning trace, and approve/flag buttons. Sidebar toggles for offline mode and retrieval on/off.

```bash
streamlit run app.py
```

**Command line:**

```bash
# interactive (asks the 5 questions, then asks for your review)
python run.py

# non-interactive: one letter per question (setting, energy, mood, texture, novelty)
python run.py --answers a,a,b,a,b --trace

# no keys, no network: rule-based + recorded web results
python run.py --answers a,a,b,a,b --offline

# ablation: turn retrieval off
python run.py --answers a,a,b,a,b --no-rag

# tests and reliability harness
python -m pytest tests -q
python scripts/run_eval.py
```

Run everything from the project root. No `PYTHONPATH` setup is needed.

## Sample interactions (real runs, live Gemini + Spotify)

Question letters: `setting, energy, mood, texture, novelty`. Full reasoning traces for these runs are in
[`ai_interactions.md`](ai_interactions.md).

**1. Late-night study** `--answers a,a,b,a,b` (studying, low energy, calm, acoustic, one new find)

```
Taste profile (llm): lofi / focused, energy 0.35, valence 0.55, acousticness 0.85
Why: The listener's preference for studying and organic, calm sounds aligns perfectly with the 'Late-night study listener' archetype, which emphasizes focused, low-energy instrumental music.
Overall confidence: 0.95   Flags: none

  1. Affection - Jinsang  [catalog 12.5/13]
     This track provides a steady, low-energy rhythm that creates the perfect background atmosphere for your deep study sessions.
  2. Aruarian Dance - Nujabes  [catalog 10.7/13]
  3. Fly Me to the Moon - Frank Sinatra  [catalog 10.4/13]
  4. Feather - Nujabes  [catalog 10.2/13]
  5. Gymnopédie No. 1 - Erik Satie, Philippe Entremont  [web:spotify]
     https://open.spotify.com/track/5NGtFXVpXSvwunEIGeviY3
```

**2. Workout** `--answers b,c,d,c,c` (working out, high energy, intense, electronic, surprise me)

```
Taste profile (llm): edm / intense, energy 0.95, valence 0.45, acousticness 0.08
Why: The profile relies on the 'Gym and high-energy workout listener' archetype ... while incorporating elements of the 'Rage and release' archetype to satisfy the preference for an intense and aggressive mood.
Overall confidence: 0.92   Flags: none

  1. Smells Like Teen Spirit - Nirvana  [catalog 11.5/13]
  2. Physical - Dua Lipa  [catalog 10.9/13]
  3. Levels - Avicii  [catalog 10.5/13]
  4. Sandstorm - Darude  [web:spotify]
     https://open.spotify.com/track/6Sy9BUbgFse0n0LPA5lwy5
  5. Animals - Martin Garrix  [web:spotify]
     https://open.spotify.com/track/0A9mHc7oYUoCECqByV8cQR
```

The retriever blended **two** archetypes (gym and rage), which is why a rock song leads a workout list.

**3. Sad evening at home** `--answers d,a,c,a,b`

```
Taste profile (llm): folk / sad, energy 0.35, valence 0.25, acousticness 0.85
Overall confidence: 0.87   Flags: none

  1. Stormy Monday - T-Bone Walker  [catalog 11.7/13]
  2. Holocene - Bon Iver  [catalog 10.7/13]
  3. Jealous - Labrinth  [catalog 10.2/13]
  4. Someone You Loved - Lewis Capaldi  [catalog 10.0/13]
  5. The Night We Met - Lord Huron  [web:spotify]
     https://open.spotify.com/track/5yJaXWIErrrsjQ3J0eR5aK
```

**4. Guardrail: bad input**

```
$ python run.py --answers a,a,z,a
Sorry, I couldn't use those answers: 'mood': 'z' is not one of ['a', 'b', 'c', 'd', 'e', 'f']; 'novelty' is missing
```

## Reliability and evaluation

Full output: [`eval_results.md`](eval_results.md). Summary:

| Check group | Result |
|---|---|
| Unit tests (`pytest`): catalog loading, MCQ validation, retrieval, agent, web verification, Streamlit UI (headless) | **27 / 27 passed** |
| Harness (`scripts/run_eval.py`, offline and deterministic): 6 taste scenarios, web verification, novelty rule, conflicting answers, 3 invalid-input cases, simulated LLM outage, simulated web outage | **14 / 14 passed** |

**RAG on vs off** (6 scenarios, from the harness; full table in `eval_results.md`):

| Observation | Finding |
|---|---|
| Top catalog pick in expected genres | Retrieval on **6/6**, retrieval off **5/6** (off picked `pop` for the romantic-date scenario) |
| Top-5 overlap between the two modes | 2.7 of 5 on average: retrieval changes about half the list |
| Profile genre | Retrieval changed it in 3/6 cases (sad evening, party night, romantic date) |
| Where retrieval hurt | "Sad evening at home": retrieval chose `jazz` (cozy archetype dominated by "relaxing at home"); answers-only chose `blues`, which fits "sad" better |

So retrieval helped in one scenario, hurt the genre guess in another, and mostly makes the profile and the
web-search hints more specific and explainable. That is a small, mixed effect on a 39-song catalog, and I
would not claim more than that.

**Failures seen in live use** (all handled by fallbacks, none crashed): Gemini 2.5 model names returned 404 and
`gemini-flash-latest` timed out for my key; MusicBrainz returned HTTP 503 several times (retry with backoff,
then the next source); Spotify returned 403 until the account had Premium. After the first Gemini failure the
agent stops calling it for that run (circuit breaker), instead of waiting through repeated timeouts.

### Sample command execution: reliability harness

```
$ python scripts/run_eval.py
**14/14 checks passed**

| Test | Expectation | Result |
|---|---|---|
| Taste: Late-night study | top pick genre in ['ambient', 'lofi']; 5 picks | Pass |
| Taste: Gym workout | top pick genre in ['edm', 'metal', 'pop', 'rock']; 5 picks | Pass |
| Taste: Sad evening at home | top pick genre in ['blues', 'classical', 'folk', 'soul']; 5 picks | Pass |
| Web picks verified | 2 web picks, none in catalog, all have a source | Pass |
| Guardrail: Invalid choice | rejected with InvalidAnswers | Pass |
| Guardrail: LLM outage | falls back, flag set, 5 picks | Pass |
| Guardrail: web outage | falls back to recorded fixtures | Pass |
(6 taste scenarios and 3 invalid-input cases in the full table: eval_results.md)
```

### Testing summary

- **Worked:** input validation, the fallback chain (LLM outage, web outage), and web verification, which
  rejected songs a source could not confirm. 27 unit tests and 14 harness checks pass, and the live runs
  completed with real Gemini and Spotify calls.
- **Did not work as hoped:** retrieval gave only a small, mixed gain (see the RAG table), and one scenario got
  worse. Verification rejects some real songs because it matches titles and artists strictly. Gemini model names
  and Spotify access failed at various points during development.
- **Learned:** the failures that mattered came from outside services and from the data (invented songs, found
  by my own review step), not from the model's wording. Testing the failure paths mattered as much as testing
  the happy path.

## Design decisions and trade-offs

- **Multiple choice instead of free text.** Cheap to validate, testable, and nothing to prompt-inject. The cost
  is expressiveness: you cannot say "calm music for studying at 2am" and have it understood.
- **One agent with tools, not several LLM "agents".** A chain of one-call agents is a pipeline. A single loop that
  branches on results is easier to trace and test.
- **LLM proposes, the web verifies.** Asking an LLM for songs invites invented titles. A candidate is only shown
  if Spotify/MusicBrainz confirms it exists. Trade-off: real songs with accents or alternate spellings can be
  rejected (false negatives: "Bangarang" and "Tsunami" are real songs but were not confirmed in the workout
  trace in `ai_interactions.md`, probably because Spotify's titles carry "(feat. ...)" suffixes).
- **Pure-Python TF-IDF, not embeddings.** Zero setup and fully reproducible. Trade-off: it matches words, not
  meaning, so it depends on the archetype documents containing the vocabulary users' answers produce.
- **Deterministic baseline plus LLM refinement.** The system works with no key, and the LLM can never put an
  invalid genre or number into the scorer.
- **Real songs, estimated features.** My first catalog was the starter's mostly invented songs. When I tried
  the CLI, I flagged the result in the review step with the note "none are familiar", which is how I found
  the problem. The catalog is now 39 real songs. Spotify no longer exposes audio features to new apps, so
  the energy, valence, acousticness and tempo values are **my own approximate estimates**, not measured data.
- **Original scorer kept as-is.** The weights from the first project are unchanged so differences come from the
  new components.

## Limitations

- The catalog is 39 songs, and each song's audio features are my own estimates, not measured data.
- Retrieval gave a small, mixed gain, and keyword matching can miss meaning.
- Web verification is strict and rejects some real songs; MusicBrainz results can be obscure.
- Confidence is a heuristic, not a calibrated probability.

See [`model_card.md`](model_card.md) for the full limitations, bias, misuse and reflection.

## Project layout

```
app.py          Streamlit web UI              run.py   CLI launcher
src/musicrag/   catalog.py questions.py retriever.py profile.py scorer.py llm.py web.py explain.py agent.py cli.py env.py
data/           songs.csv (39 real songs, hand-estimated features), profiles/ (10 archetype documents)
tests/          unit tests + fixtures/web_tracks.json (33 recorded, verified tracks)
scripts/        run_eval.py (harness), record_fixtures.py
diagrams/       architecture.mmd (source), architecture.md, architecture_v1.md
assets/         earlier (v1) diagram images
ai_interactions.md   reasoning traces     eval_results.md   harness output     model_card.md   reflection
```

## Reflection

Building this taught me that the model call is the smallest part of an AI system. My idea was simple: ask five
multiple-choice questions, let an agent work out which taste profile fits, retrieve similar profiles with RAG, and
search the web for a new song. Most of the work was making that trustworthy: validating what Gemini returns,
making Spotify confirm that every recommended song really exists, and deciding what happens when a service
fails. Services did fail while I built it (Gemini model errors and timeouts, MusicBrainz 503s, Spotify 403s), so
testing the failure paths mattered as much as testing the happy path.

Two results surprised me. Retrieval helped less than I expected: it improved one scenario and made another
worse. And when I ran the CLI myself and flagged the result with "none are familiar", I found that most of the
catalog was invented starter data, a problem none of my automated tests had checked for. I replaced it with real
songs. The lasting lessons are to measure before claiming a feature works, to keep a human check in the loop,
and to verify what an AI tells me instead of taking it at face value.
