# Agentic RAG Music Concierge

An applied-AI extension of my **Music Recommender Simulation** (Modules 1-3). You answer five
multiple-choice questions; an agent retrieves matching taste-profile documents (RAG), builds a taste
profile, ranks a song catalog, decides whether to look for new songs on the web, **verifies** every web
song actually exists, and explains each pick with a confidence score.

## Original project

**Music Recommender Simulation** (kept in [`musicrecommendersimulation-starter/`](musicrecommendersimulation-starter/)).
It was a small content-based recommender: a 23-song `songs.csv`, a hand-written user taste profile
(favorite genre and mood, target energy, acoustic preference), and a weighted scoring rule that rewarded
songs for being *close* to the target (energy 7.0, valence 2.5, acousticness 1.0, mood 2.0, genre 0.5 points).
It had no AI components and no way to find songs outside its tiny catalog. This project keeps that scorer
unchanged (`src/musicrag/scorer.py`) and wraps it in retrieval, an agent loop, web discovery and a
reliability layer.

## What the AI parts do

| Feature | Where | How it changes behaviour |
|---|---|---|
| **RAG** | `retriever.py`, `data/profiles/` | TF-IDF search over 10 archetype documents and the song catalog. Retrieved archetypes set the profile's genre, valence and (partly) energy/acousticness, and supply the web search hints. Without retrieval the profile falls back to answers only. |
| **Agentic workflow** | `agent.py` | One agent picks tools and branches on what it finds: widens retrieval on low confidence, skips or runs web search depending on the novelty answer and a "catalog gap" check, tries the next candidate or source when verification fails, flags low confidence for human review. Every step is written to a trace. |
| **Reliability / guardrails** | `questions.py`, `web.py`, `profile.py`, `scripts/run_eval.py` | MCQ validation, LLM output validation, web-result verification, API fallbacks, a circuit breaker, logging, 24 unit tests and a 14-check harness. |

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
8. **Human in the loop**: the CLI asks you to approve or flag the result; flags go to `logs/feedback.jsonl`.

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

```bash
# interactive (asks the 5 questions, then asks for your review)
PYTHONPATH=src python -m musicrag

# non-interactive: one letter per question (setting, energy, mood, texture, novelty)
PYTHONPATH=src python -m musicrag --answers a,a,b,a,b --trace

# no keys, no network: rule-based + recorded web results
PYTHONPATH=src python -m musicrag --answers a,a,b,a,b --offline

# ablation: turn retrieval off
PYTHONPATH=src python -m musicrag --answers a,a,b,a,b --no-rag

# tests and reliability harness
python -m pytest tests -q
python scripts/run_eval.py
```

On PowerShell use `$env:PYTHONPATH="src"` before the commands.

## Sample interactions (real runs, live Gemini + Spotify)

Question letters: `setting, energy, mood, texture, novelty`. Full reasoning traces for these runs are in
[`ai_interactions.md`](ai_interactions.md).

**1. Late-night study** `--answers a,a,b,a,b` (studying, low energy, calm, acoustic, one new find)

```
Taste profile (llm): lofi / focused, energy 0.35, valence 0.55, acousticness 0.85
Why: The listener's preference for studying and organic, calm sounds aligns perfectly with the 'Late-night study listener' archetype's focus on instrumental-leaning, low-energy music.
Overall confidence: 0.96   Flags: none

  1. Focus Flow - LoRoom  [catalog 12.5/13]
     This track provides a steady, rhythmic backdrop that perfectly complements your need for deep concentration and focused work.
  2. Library Rain - Paper Lanterns  [catalog 10.9/13]
  3. Midnight Coding - LoRoom  [catalog 10.3/13]
  4. Wildflower Road - Juniper Lane  [catalog 10.2/13]
  5. A Walk - Tycho  [web:spotify]
     https://open.spotify.com/track/0sQNqu37YQQSI3K0ueswyA
```

**2. Workout** `--answers b,c,d,c,c` (working out, high energy, intense, electronic, surprise me)

```
Taste profile (llm): edm / intense, energy 0.95, valence 0.5, acousticness 0.08
Why: ... aligns with the 'Gym and high-energy workout listener' archetype, while the desire for aggression incorporates elements of the 'Rage and release listener' profile.
Overall confidence: 0.94   Flags: none

  1. Storm Runner - Voltline  [catalog 12.2/13]
  2. Gym Hero - Max Pulse  [catalog 11.7/13]
  3. Neon Pulse - Voltage Kid  [catalog 10.1/13]
  4. Animals - Martin Garrix  [web:spotify]
     https://open.spotify.com/track/0A9mHc7oYUoCECqByV8cQR
  5. LRAD - Knife Party  [web:musicbrainz]
     https://musicbrainz.org/recording/9afa8762-2e09-4e2c-ad04-2e6dc1047e32
```

The retriever blended **two** archetypes (gym and rage). Spotify confirmed only 1 of Gemini's 5 proposed
songs, so the agent moved to MusicBrainz for the second pick (see the trace; it also rejected a duplicate).
Several of the unconfirmed songs are real, so the strict title/artist match produces false negatives
(see Limitations).

**3. Sad evening at home** `--answers d,a,c,a,b`

```
Taste profile (llm): folk / sad, energy 0.35, valence 0.25, acousticness 0.85
Overall confidence: 0.92   Flags: none

  1. Rainy Window Blues - Delta Hollis  [catalog 12.1/13]
  2. Jealous - Labrinth  [catalog 10.2/13]
  3. Someone Like You - Adele  [catalog 10.0/13]
  4. Wildflower Road - Juniper Lane  [catalog 10.0/13]
  5. Holocene - Bon Iver  [web:spotify]
     https://open.spotify.com/track/35KiiILklye1JRRctaLUb4
```

**4. Guardrail: bad input**

```
$ python -m musicrag --answers a,a,z,a
Sorry, I couldn't use those answers: 'mood': 'z' is not one of ['a', 'b', 'c', 'd', 'e', 'f']; 'novelty' is missing
```

## Reliability and evaluation

Full output: [`eval_results.md`](eval_results.md). Summary:

| Check group | Result |
|---|---|
| Unit tests (`pytest`): catalog loading, MCQ validation, retrieval, agent, web verification | **24 / 24 passed** |
| Harness (`scripts/run_eval.py`, offline and deterministic): 6 taste scenarios, web verification, novelty rule, conflicting answers, 3 invalid-input cases, simulated LLM outage, simulated web outage | **14 / 14 passed** |

**RAG on vs off** (6 scenarios, from the harness):

| Observation | Finding |
|---|---|
| Top catalog pick in expected genres | Retrieval on 6/6, retrieval off 6/6. **No accuracy gain on this small catalog.** |
| Top-5 overlap between the two modes | 3.3 of 5 on average: retrieval changes about a third of the list |
| Profile genre | Retrieval changed it in 3/6 cases (e.g. party night: `edm` vs `pop`; moody drive: `synthwave` vs `alt pop`) |
| Where retrieval hurt | "Sad evening at home": retrieval chose `jazz` (cozy archetype dominated by "relaxing at home"); answers-only chose `blues`, which fits "sad" better |

So the honest claim is that retrieval makes the profile and the web search hints more specific and explainable,
not that it is more accurate on a 23-song catalog.

**Failures seen in live use** (all handled by fallbacks, none crashed): Gemini 2.5 model names returned 404 and
`gemini-flash-latest` timed out for my key; MusicBrainz returned HTTP 503 several times (retry with backoff,
then the next source); Spotify returned 403 until the account had Premium. After the first Gemini failure the
agent stops calling it for that run (circuit breaker), instead of waiting through repeated timeouts.

## Design decisions and trade-offs

- **Multiple choice instead of free text.** Cheap to validate, testable, and nothing to prompt-inject. The cost
  is expressiveness: you cannot say "calm music for studying at 2am" and have it understood.
- **One agent with tools, not several LLM "agents".** A chain of one-call agents is a pipeline. A single loop that
  branches on results is easier to trace and test.
- **LLM proposes, the web verifies.** Asking an LLM for songs invites invented titles. A candidate is only shown
  if Spotify/MusicBrainz confirms it exists. Trade-off: real songs with accents or alternate spellings can be
  rejected (a false negative, seen in the trace for "Gymnopédie No. 1").
- **Pure-Python TF-IDF, not embeddings.** Zero setup and fully reproducible. Trade-off: it matches words, not
  meaning, so it depends on the archetype documents containing the vocabulary users' answers produce.
- **Deterministic baseline plus LLM refinement.** The system works with no key, and the LLM can never put an
  invalid genre or number into the scorer.
- **Original scorer kept as-is.** The weights from the first project are unchanged so differences come from the
  new components.

## Limitations

See [`model_card.md`](model_card.md) for limitations, bias, misuse and reflection.

## Project layout

```
src/musicrag/   catalog.py questions.py retriever.py profile.py scorer.py llm.py web.py explain.py agent.py cli.py
data/           songs.csv, profiles/ (10 archetype documents)
tests/          unit tests + fixtures/web_tracks.json (33 recorded, verified tracks)
scripts/        run_eval.py (harness), record_fixtures.py
diagrams/       architecture.mmd (source), architecture.md, architecture_v1.md
assets/         diagram images
ai_interactions.md   reasoning traces     eval_results.md   harness output     model_card.md   reflection
```

## Demo

Loom walkthrough: _add link here_
