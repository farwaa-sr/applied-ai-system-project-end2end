# Evaluation results (2026-11-15, offline deterministic mode)

**14/14 checks passed**

| Test | Expectation | Result | Detail |
|---|---|---|---|
| Taste: Late-night study | top pick genre in ['ambient', 'lofi']; 5 picks | Pass | top = Aruarian Dance; conf 0.92 |
| Taste: Gym workout | top pick genre in ['edm', 'metal', 'pop', 'rock']; 5 picks | Pass | top = Physical; conf 0.92 |
| Taste: Sad evening at home | top pick genre in ['blues', 'classical', 'folk', 'soul']; 5 picks | Pass | top = Stormy Monday; conf 0.82 |
| Taste: Party night | top pick genre in ['edm', 'indie pop', 'pop', 'reggae']; 5 picks | Pass | top = Happy; conf 0.83 |
| Taste: Moody night drive | top pick genre in ['alt pop', 'synthwave']; 5 picks | Pass | top = bad guy; conf 0.92 |
| Taste: Romantic date night | top pick genre in ['jazz', 'r&b', 'soul']; 5 picks | Pass | top = Best Part; conf 0.85 |
| Web picks verified | 2 web picks, none in catalog, all have a source | Pass | web = ['Levitating', 'Blinding Lights'] |
| Novelty 'familiar' | catalog only | Pass | no web call made |
| Conflicting answers | 5 picks, confidence reported in [0,1] | Pass | conf 0.7, flags ['llm_unavailable'] |
| Guardrail: Empty answers | rejected with InvalidAnswers | Pass | No answers were provided. |
| Guardrail: Missing questions | rejected with InvalidAnswers | Pass | 'energy' is missing; 'mood' is missing; 'texture' is missing |
| Guardrail: Invalid choice | rejected with InvalidAnswers | Pass | 'mood': 'z' is not one of ['a', 'b', 'c', 'd', 'e', 'f'] |
| Guardrail: LLM outage | falls back, flag set, 5 picks | Pass | flags ['llm_unavailable', 'web_fallback_fixture'] |
| Guardrail: web outage | falls back to recorded fixtures | Pass | flags ['llm_unavailable', 'web_fallback_fixture'] |

## RAG on vs off

| Scenario | Profile genre/valence (on) | Profile genre/valence (off) | Shared catalog picks | Top pick in expected genres (on / off) |
|---|---|---|---|---|
| Late-night study | lofi/0.59 | lofi/0.47 | 3 | yes / yes |
| Gym workout | pop/0.52 | pop/0.73 | 2 | yes / yes |
| Sad evening at home | jazz/0.5 | blues/0.38 | 2 | yes / yes |
| Party night | edm/0.79 | pop/0.95 | 2 | yes / yes |
| Moody night drive | synthwave/0.51 | synthwave/0.48 | 3 | yes / yes |
| Romantic date night | r&b/0.63 | pop/0.48 | 4 | yes / no |

Top pick in expected genres: RAG on 6/6, RAG off 5/6. Average shared catalog picks (of 5): 2.67. Average reported confidence: on 0.88, off 0.67 (not a like-for-like score: the no-retrieval profile uses a fixed prior of 0.4).
