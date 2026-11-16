# Model Card: Agentic RAG Music Concierge

Base project: **Music Recommender Simulation** (my Module 1-3 project).

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
- **Web verification can still have false negatives.** A suggestion is accepted only if Spotify/MusicBrainz returns
  the same cleaned title with the lead artist credited. An earlier, stricter version rejected real songs
  ("Bangarang", "Tsunami", "Turn Down for What") because of "(feat. ...)" suffixes and credit order; I fixed that
  after the "Show me new ones" test exposed it (see What surprised me). Remixes, live versions and unusual
  spellings can still be missed. Safe but wasteful.
- **Playback depends on Spotify.** Each player is a Spotify embed: a short preview unless the listener is signed in
  to Spotify. Songs without a known Spotify id get a search link instead of a player.
- **Web results are not curated.** MusicBrainz fallback results can be obscure; Spotify popularity is not used
  for ranking proposals. Explicit content is not filtered.
- **Dependence on third parties.** Gemini model availability and Spotify access changed during development
  (404s, timeouts, a 403 until Premium was active). The fallbacks keep the system running at lower quality.

## Could it be misused, and how is that prevented?

- **Prompt injection:** the user never types free text, so there is no text field to inject into. LLM output is
  validated (genre/mood against the catalog vocabulary, numbers clamped to 0-1) before it reaches the scorer,
  and explanations naming songs outside the picks are dropped.
- **Hallucinated songs:** no web song is shown unless a web source confirms it exists. (The offline fallback shows
  recorded tracks that were each confirmed on MusicBrainz when recorded, and the result is flagged.)
- **Secrets:** keys live in a gitignored `.env`; `.env.example` has placeholders only. Because a key was pasted
  into a chat during development it should be rotated.
- **Residual risk:** low for a music demo. Possible misuse is bulk calls against the Spotify/MusicBrainz APIs;
  MusicBrainz calls are rate-limited to about one per second in code. A deployed version would need request limits.

## What surprised me while testing

- Retrieval's accuracy gain was small: top pick in an expected genre 6/6 with retrieval, 5/6 without (the
  one miss was the romantic-date scenario). It changed about two of the five songs and the profile's genre in
  4 of 6 cases. I expected a larger gain.
- One scenario got **worse** with retrieval (see Limitations), which a confidence number alone would not reveal.
- **My own human-review step caught the biggest problem.** I ran the CLI, and when it asked whether the picks made
  sense I flagged them with "none are familiar". The cause: most catalog songs were invented starter data, so a
  recommender that sounded fine was recommending songs that do not exist. I replaced them with 39 real songs.
- The verification step rejected songs that exist. I expected it to catch invented songs, and it does, but it
  also needed fuzzier matching. Building "Show me new ones" made this obvious: in set 2 every Gemini proposal was
  rejected, and the fallback search returned filler tracks ("Gym Workout" by "EDM MUSIC"). Cleaning titles and
  artists before comparing fixed it.
- External services were the main source of failures, not my code; the circuit breaker and fallback chain mattered
  more than prompt wording.
- While re-checking my numbers I found the RAG-off comparison changed between runs: ties between genres were broken
  by Python's randomized set order. I made the tie-break alphabetical and confirmed identical output across six hash
  seeds, so the harness is now truly deterministic.
- The first version of the harness hardcoded the "RAG on" result as a pass, so its comparison proved nothing.
  Claude caught this while re-reading the output and fixed it to compute real values, which is how it became
  clear that retrieval's effect was small and mixed.

## Testing results

| Test | Evaluation criteria | Result |
|---|---|---|
| 33 pytest tests | Catalog loading, MCQ validation, retrieval ranking, agent fallbacks, web verification, new-set logic, Streamlit UI (headless) | 33 / 33 pass |
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

I used Claude Code as a pair programmer. The idea was mine: multiple-choice questions, agents that work out a
taste profile, RAG to fetch similar profiles, and a web search for a song to recommend. Claude helped turn that
into a concrete design and wrote most of the code and tests. I ran the system, reviewed the output, and made the
decisions about what to keep.

**Suggestion I accepted:** Claude proposed one agent with tools (retrieve, score, web search, verify) instead of
several separate LLM "agents", and "the LLM proposes songs, the web source must confirm they exist". I accepted it
because it kept my idea but removed the risk of recommending invented songs. In the live traces, the agent
rejects songs that Spotify or MusicBrainz cannot confirm.

**Suggestions I rejected or changed:**
- Claude suggested iTunes Search for the web step. I preferred Spotify. Spotify later returned 403 until my account
  had Premium, so the final design uses Spotify first, with MusicBrainz and recorded fixtures as fallbacks.
- When my review flagged "none are familiar", Claude suggested only documenting the invented-songs problem as a
  limitation. I asked for it to be fixed, so the catalog was replaced with 39 real songs. The cost is that the
  audio features are now my estimates (see Limitations).
- Claude told me the starter project had no web UI. That was wrong: I pointed it to my original repo, whose
  history shows a course-template Streamlit form that was later removed. We built a new `app.py` that extends it.
- Claude's first evaluation harness hardcoded a passing result for the "retrieval on" case, which made the RAG
  comparison meaningless. Claude caught it on re-reading the output and replaced it with a computed value, which
  is how the small, mixed effect of retrieval showed up.

What I took from this: AI was fast at scaffolding and I could move quickly, but it was confidently wrong more than
once (the UI claim, the harness), so I had to check its claims against the real repo and the real output.
