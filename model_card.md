# Model Card: Agentic RAG Music Concierge

Base project: **Music Recommender Simulation**. Draft written with Claude Code during the project; edit
anything here so it is in your own words before submitting.

## Intended use

A demo recommender that turns five multiple-choice answers into five song picks with explanations and a
confidence score. It is a learning project, not a production recommender.

## Limitations and biases

- **Tiny catalog with estimated features.** 39 real songs and 10 archetype documents that I wrote myself. Spotify
  no longer provides audio features to new apps, so each song's energy, valence, danceability, acousticness and
  tempo are **my approximate hand estimates**, not measured values; a different listener would rate some of them
  differently, and the scorer inherits that error. The archetypes encode my own
  assumptions about what "studying" or "romantic" music sounds like, so the system reflects one person's
  taste and mostly Western genres. Genres not in the catalog (K-pop, Latin, Afrobeats, etc.) can only reach the
  user through the web step.
- **Coarse input.** Five fixed questions cannot express taste beyond them. Conflicting answers (for example
  studying + high energy) still produce a confident-looking result.
- **Keyword retrieval.** TF-IDF matches words, not meaning. If a user's answers do not share vocabulary with
  an archetype, retrieval can miss it.
- **Retrieval can hurt.** In the "sad evening at home" test, retrieval chose the cozy-acoustic archetype
  (jazz) because "relaxing at home" outweighed "sad", while the answers-only profile chose blues, a better fit.
- **Confidence is a heuristic**, built from retrieval similarity, agreement with the mood answer, and the
  best catalog score. It is not a calibrated probability.
- **Web verification has false negatives.** A suggestion is accepted only if Spotify/MusicBrainz returns an
  exact title match with the artist. Real songs were rejected because of accents ("Gymnopédie"), featured-artist
  strings, or search ranking (for example "Turn Down for What"). Safe but wasteful.
- **Web results are not curated.** MusicBrainz fallback results can be obscure; Spotify popularity is not used
  for ranking proposals. Explicit content is not filtered.
- **Dependence on third parties.** Gemini model availability and Spotify access changed during development
  (404s, timeouts, a 403 until Premium was active). The fallbacks keep the system running at lower quality.

## Could it be misused, and how is that prevented?

- **Prompt injection:** the user never types free text, so there is no text field to inject into. LLM output is
  validated (genre/mood against the catalog vocabulary, numbers clamped to 0-1) before it reaches the scorer,
  and explanations naming songs outside the picks are dropped.
- **Hallucinated songs:** no web song is shown unless a web source confirms it exists.
- **Secrets:** keys live in a gitignored `.env`; `.env.example` has placeholders only. Because a key was pasted
  into a chat during development it should be rotated.
- **Residual risk:** low for a music demo. Possible misuse is bulk calls against the Spotify/MusicBrainz APIs;
  MusicBrainz calls are rate-limited to about one per second in code. A deployed version would need request limits.

## What surprised me while testing

- Retrieval's accuracy gain was small: top pick in an expected genre 6/6 with retrieval, 5/6 without (the
  one miss was the romantic-date scenario). It changed about half of the top-5 list and the profile's genre in
  3 of 6 cases. I expected a larger gain.
- One scenario got **worse** with retrieval (see Limitations), which a confidence number alone would not reveal.
- **My own human-review step caught the biggest problem.** I ran the CLI, and when it asked whether the picks made
  sense I flagged them with "none are familiar". The cause: most catalog songs were invented starter data, so a
  recommender that sounded fine was recommending songs that do not exist. I replaced them with 39 real songs.
- The verification step rejected songs that exist. I expected it to catch invented songs, and it does, but it
  also needs fuzzier matching.
- External services were the main source of failures, not my code; the circuit breaker and fallback chain mattered
  more than prompt wording.
- The first version of the harness hardcoded the "RAG on" result as a pass, so its comparison proved nothing.
  Claude caught this while re-reading the output and fixed it to compute real values, which is how the
  no-accuracy-gain result surfaced.

## Testing results

| Test | Evaluation criteria | Result |
|---|---|---|
| 27 pytest tests | Catalog loading, MCQ validation, retrieval ranking, agent fallbacks, web verification, Streamlit UI (headless) | 27 / 27 pass |
| 6 taste scenarios (harness) | Top pick's genre in an expected set; 5 picks | 6 / 6 pass |
| Web picks | 2 picks, none already in catalog, source recorded | Pass |
| Empty / missing / invalid answers | Rejected with a clear message | 3 / 3 pass |
| LLM outage (injected) | Falls back, flag set, 5 picks | Pass |
| Web outage (injected) | Falls back to recorded fixtures, flag set | Pass |
| Live run, study scenario | Gemini profile and explanations, Spotify-verified pick | Pass (see README) |

### Human evaluation (my review of live runs)

| Test input (answers) | Evaluation criteria | Result |
|---|---|---|
| a,b,e,a,b (study, medium energy, romantic, acoustic, one new find), first catalog | Picks are real songs I recognise | **Fail**: flagged "none are familiar" (invented starter songs) |
| a,b,e,a,b, after replacing the catalog with 39 real songs | Picks are real songs I recognise | Pass: Fly Me to the Moon, Perfect, Tennessee Whiskey, Best Part, plus Spotify-verified Come Away With Me |

Details in `eval_results.md`; reasoning traces in `ai_interactions.md`. Human review in the CLI records an
approve/flag verdict to `logs/feedback.jsonl`; I have not collected enough reviews to report numbers.

## Collaboration with AI

I used Claude Code as a pair programmer for design discussion and implementation.

**Suggestion I accepted:** Claude proposed one agent with tools (retrieve, score, web search, verify) instead of
several separate LLM "agents", and "LLM proposes, the web confirms" for song discovery. It kept the design
traceable and testable, and the verification step caught invented songs in live runs.

**Suggestions I rejected or changed:**
- Claude suggested only documenting the invented-songs problem as a limitation. I asked for it to be fixed, and the
  catalog was replaced with real songs, with the extra cost that the features are estimates (see Limitations).
- Claude first said the starter project's web UI did not exist, then guessed it had been removed in my own
  commit. Both were wrong: I pointed to my original repo, and its history shows a course-template `src/app.py`
  Streamlit form added and then removed by the template's author. The new `app.py` extends that idea.
- Claude first suggested iTunes Search for the web step. I preferred Spotify. Spotify later returned 403 (it
  needs a Premium account on the app owner), so the final design uses Spotify first with MusicBrainz and recorded
  fixtures as fallbacks.
- Claude's first RAG pitch assumed scikit-learn or embeddings; the implementation uses a small pure-Python TF-IDF
  instead, to avoid extra dependencies and keep runs reproducible, at the cost of semantic matching.
- Claude's first harness hardcoded a passing result for the RAG-on case. Claude spotted it on review and
  replaced it with a computed value, which exposed that retrieval gave no accuracy gain. (An example of an AI
  suggestion that was wrong as first written.)

_Reviewer note: replace these with your own recollection of what you accepted and rejected if it differs._
