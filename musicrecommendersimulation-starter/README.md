# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders like Spotify or YouTube work in two stages. First, they score each item by predicting how relevant it is to a specific user, using signals such as what the user has played, skipped, or saved, along with the item's own features (genre, mood, energy, tempo). Then they rank all of those scored items, apply extra rules like removing songs already heard or keeping the list varied, and show only the top few. My version is a much smaller, content-based take on that idea: instead of learning from listening history, it compares each song's attributes directly against a user's stated taste. I score every song on how close it is to the user's target rather than rewarding higher or lower values, so a user who wants energy 0.4 is not handed a 0.9 song. I prioritize energy first, then valence, then mood, with acousticness and genre as smaller nudges, because energy and valence capture how a song feels and mood captures what the listener wants right now. I chose to weight mood above genre because genre labels are too sparse in my small dataset to carry much weight. After scoring, I rank songs from highest to lowest and return the top results.

### Features used

**`Song`** (one row of `data/songs.csv`)

| Feature | Type | Used in scoring? |
|---|---|---|
| `id`, `title`, `artist` | int / str | No, identification and display only |
| `genre` | str | Yes, exact match bonus (max 1.0 pt) |
| `mood` | str | Yes, exact match bonus (max 2.0 pts) |
| `energy` | float 0-1 | Yes, closeness to target (max 3.5 pts) |
| `valence` | float 0-1 | Yes, closeness to target (max 2.5 pts) |
| `acousticness` | float 0-1 | Yes, closeness to target (max 1.0 pt) |
| `tempo_bpm` | float | No, mostly redundant with energy |
| `danceability` | float 0-1 | No, mostly redundant with energy |

**`UserProfile`** (the listener's taste)

| Feature | Type | Compared against |
|---|---|---|
| `favorite_genre` | str | `Song.genre` |
| `favorite_mood` | str | `Song.mood` |
| `target_energy` | float 0-1 | `Song.energy` |
| `target_valence` | float 0-1 | `Song.valence` (to be added to the starter profile) |
| `likes_acoustic` | bool | `Song.acousticness`, mapped to a target of about 0.8 if true and 0.2 if false |

### Algorithm Recipe

Each song is scored out of 10 points against the user's profile:

| Rule | Max points | How it is computed |
|---|---|---|
| Energy | 3.5 | `3.5 * (1 - abs(song.energy - target_energy))` |
| Valence | 2.5 | `2.5 * (1 - abs(song.valence - target_valence))` |
| Mood match | 2.0 | `2.0` if `song.mood == favorite_mood`, else `0` |
| Acousticness | 1.0 | `1.0 * (1 - abs(song.acousticness - acoustic_target))` |
| Genre match | 1.0 | `1.0` if `song.genre == favorite_genre`, else `0` |

The weights above are the original recipe. The current code uses an experimental setting (energy 7.0, genre 0.5, so scores are out of 13), compared in the two Sample Recommendation Output sections below.

Numeric features reward closeness to the user's target, not higher or lower values. Mood is weighted above genre because genre labels are sparse in the catalog and mood better describes what the listener wants right now.

**Ranking rule:** sort all songs by score (highest first), break ties by smaller energy distance and then lower `id`, and return the top K with a short "because" explanation.

**Data flow**

```
songs.csv -> load_songs -> list of song dicts
user_prefs ----------------------------+
                                        v
for each song: score_song(prefs, song) -> (song, score, reasons)
                                        v
sort by score, break ties, keep top K -> printed recommendations
```

**Example profiles** (in `src/main.py`)

- `chill_lofi`: genre lofi, mood chill, energy 0.40, valence 0.60, acousticness 0.80
- `intense_rock`: genre rock, mood intense, energy 0.90, valence 0.45, acousticness 0.10

### Expected biases and limits

- **Exact-match categories:** mood and genre need identical strings, so "indie pop" earns nothing against "pop" and "chill" earns nothing against "relaxed", even though they are close.
- **Mood over genre:** a user who cares mostly about genre may be shown songs from other genres that match their mood.
- **Energy dominance:** energy carries the most points, so the system can favor songs that match on energy while differing in feel.
- **Sparse catalog:** with 23 songs and most genres appearing once, a profile may have no close match (for example, only one rock song), and the top results will be filled by numeric similarity alone.
- **Single taste:** a profile holds one genre and one mood, so it cannot express "chill or focused", and it has no way to exclude genres.
- **Hand-picked weights and data:** the weights are my judgment, not fitted to data, and the feature values of the added songs are estimates.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
- What information does your `UserProfile` store
- How does your `Recommender` compute a score for each song
- How do you choose which songs to recommend

You can include a simple diagram or bullet list if helpful.

---

## Sample Recommendation Output (original weights)

These results use the original weights (energy 3.5, valence 2.5, mood 2.0, acousticness 1.0, genre 1.0, out of 10). Terminal output of `python -m src.main`, which runs all seven profiles defined in `src/main.py` (three realistic listeners, then four adversarial edge cases). Each block shows the top 5 results with their scores and reasons.

### High-Energy Pop

```text
  pop / happy, energy 0.85, valence 0.80, acousticness 0.15
============================================================
1. Sunrise City by Neon Echo  [pop, happy]
   Score: 9.77 / 10  (energy gap 0.03 (+3.40), valence gap 0.04 (+2.40), acousticness gap 0.03 (+0.97), mood match (+2.0), genre match (+1.0))
2. Rooftop Lights by Indigo Parade  [indie pop, happy]
   Score: 8.46 / 10  (energy gap 0.09 (+3.19), valence gap 0.01 (+2.48), acousticness gap 0.20 (+0.80), mood match (+2.0))
3. Gym Hero by Max Pulse  [pop, intense]
   Score: 7.54 / 10  (energy gap 0.08 (+3.22), valence gap 0.03 (+2.42), acousticness gap 0.10 (+0.90), genre match (+1.0))
4. Neon Pulse by Voltage Kid  [edm, euphoric]
   Score: 6.50 / 10  (energy gap 0.11 (+3.12), valence gap 0.00 (+2.50), acousticness gap 0.12 (+0.88))
5. Concrete Crown by Kid Marlow  [hip hop, confident]
   Score: 6.27 / 10  (energy gap 0.07 (+3.26), valence gap 0.18 (+2.05), acousticness gap 0.03 (+0.97))
```

### Chill Lofi

```text
  lofi / chill, energy 0.40, valence 0.60, acousticness 0.80
============================================================
1. Library Rain by Paper Lanterns  [lofi, chill]
   Score: 9.77 / 10  (energy gap 0.05 (+3.32), valence gap 0.00 (+2.50), acousticness gap 0.06 (+0.94), mood match (+2.0), genre match (+1.0))
2. Midnight Coding by LoRoom  [lofi, chill]
   Score: 9.74 / 10  (energy gap 0.02 (+3.43), valence gap 0.04 (+2.40), acousticness gap 0.09 (+0.91), mood match (+2.0), genre match (+1.0))
3. Spacewalk Thoughts by Orbit Bloom  [ambient, chill]
   Score: 8.34 / 10  (energy gap 0.12 (+3.08), valence gap 0.05 (+2.38), acousticness gap 0.12 (+0.88), mood match (+2.0))
4. Focus Flow by LoRoom  [lofi, focused]
   Score: 7.96 / 10  (energy gap 0.00 (+3.50), valence gap 0.01 (+2.48), acousticness gap 0.02 (+0.98), genre match (+1.0))
5. Wildflower Road by Juniper Lane  [folk, dreamy]
   Score: 6.58 / 10  (energy gap 0.07 (+3.25), valence gap 0.02 (+2.45), acousticness gap 0.13 (+0.87))
```

### Deep Intense Rock

```text
  rock / intense, energy 0.92, valence 0.45, acousticness 0.08
============================================================
1. Storm Runner by Voltline  [rock, intense]
   Score: 9.87 / 10  (energy gap 0.01 (+3.46), valence gap 0.03 (+2.42), acousticness gap 0.02 (+0.98), mood match (+2.0), genre match (+1.0))
2. Gym Hero by Max Pulse  [pop, intense]
   Score: 8.13 / 10  (energy gap 0.01 (+3.46), valence gap 0.32 (+1.70), acousticness gap 0.03 (+0.97), mood match (+2.0))
3. Iron Cathedral by Black Ember  [metal, aggressive]
   Score: 6.29 / 10  (energy gap 0.05 (+3.33), valence gap 0.20 (+2.00), acousticness gap 0.04 (+0.96))
4. Night Drive Loop by Neon Echo  [synthwave, moody]
   Score: 6.17 / 10  (energy gap 0.17 (+2.90), valence gap 0.04 (+2.40), acousticness gap 0.14 (+0.86))
5. Concrete Crown by Kid Marlow  [hip hop, confident]
   Score: 6.04 / 10  (energy gap 0.14 (+3.01), valence gap 0.17 (+2.08), acousticness gap 0.04 (+0.96))
```

### Conflicting: high energy but sad

```text
  blues / sad, energy 0.90, valence 0.20, acousticness 0.10
============================================================
1. Rainy Window Blues by Delta Hollis  [blues, sad]
   Score: 7.49 / 10  (energy gap 0.52 (+1.68), valence gap 0.02 (+2.45), acousticness gap 0.64 (+0.36), mood match (+2.0), genre match (+1.0))
2. Iron Cathedral by Black Ember  [metal, aggressive]
   Score: 6.57 / 10  (energy gap 0.07 (+3.26), valence gap 0.05 (+2.38), acousticness gap 0.06 (+0.94))
3. Storm Runner by Voltline  [rock, intense]
   Score: 6.26 / 10  (energy gap 0.01 (+3.46), valence gap 0.28 (+1.80), acousticness gap 0.00 (+1.00))
4. Night Drive Loop by Neon Echo  [synthwave, moody]
   Score: 5.63 / 10  (energy gap 0.15 (+2.98), valence gap 0.29 (+1.77), acousticness gap 0.12 (+0.88))
5. Concrete Crown by Kid Marlow  [hip hop, confident]
   Score: 5.51 / 10  (energy gap 0.12 (+3.08), valence gap 0.42 (+1.45), acousticness gap 0.02 (+0.98))
```

### Genre not in catalog

```text
  k-pop / happy, energy 0.80, valence 0.85, acousticness 0.15
============================================================
1. Sunrise City by Neon Echo  [pop, happy]
   Score: 8.88 / 10  (energy gap 0.02 (+3.43), valence gap 0.01 (+2.48), acousticness gap 0.03 (+0.97), mood match (+2.0))
2. Rooftop Lights by Indigo Parade  [indie pop, happy]
   Score: 8.56 / 10  (energy gap 0.04 (+3.36), valence gap 0.04 (+2.40), acousticness gap 0.20 (+0.80), mood match (+2.0))
3. Concrete Crown by Kid Marlow  [hip hop, confident]
   Score: 6.32 / 10  (energy gap 0.02 (+3.43), valence gap 0.23 (+1.93), acousticness gap 0.03 (+0.97))
4. Gym Hero by Max Pulse  [pop, intense]
   Score: 6.25 / 10  (energy gap 0.13 (+3.04), valence gap 0.08 (+2.30), acousticness gap 0.10 (+0.90))
5. Neon Pulse by Voltage Kid  [edm, euphoric]
   Score: 6.20 / 10  (energy gap 0.16 (+2.94), valence gap 0.05 (+2.38), acousticness gap 0.12 (+0.88))
```

### Impossible: loud and fully acoustic

```text
  folk / dreamy, energy 0.95, valence 0.50, acousticness 0.95
============================================================
1. Wildflower Road by Juniper Lane  [folk, dreamy]
   Score: 7.61 / 10  (energy gap 0.62 (+1.33), valence gap 0.08 (+2.30), acousticness gap 0.02 (+0.98), mood match (+2.0), genre match (+1.0))
2. Storm Runner by Voltline  [rock, intense]
   Score: 5.96 / 10  (energy gap 0.04 (+3.36), valence gap 0.02 (+2.45), acousticness gap 0.85 (+0.15))
3. Night Drive Loop by Neon Echo  [synthwave, moody]
   Score: 5.54 / 10  (energy gap 0.20 (+2.80), valence gap 0.01 (+2.48), acousticness gap 0.73 (+0.27))
4. Iron Cathedral by Black Ember  [metal, aggressive]
   Score: 5.39 / 10  (energy gap 0.02 (+3.43), valence gap 0.25 (+1.88), acousticness gap 0.91 (+0.09))
5. Gym Hero by Max Pulse  [pop, intense]
   Score: 5.36 / 10  (energy gap 0.02 (+3.43), valence gap 0.27 (+1.82), acousticness gap 0.90 (+0.10))
```

### Neutral: everything in the middle

```text
  jazz / relaxed, energy 0.50, valence 0.50, acousticness 0.50
============================================================
1. Coffee Shop Stories by Slow Stereo  [jazz, relaxed]
   Score: 8.63 / 10  (energy gap 0.13 (+3.04), valence gap 0.21 (+1.98), acousticness gap 0.39 (+0.61), mood match (+2.0), genre match (+1.0))
2. bad guy by Billie Eilish  [alt pop, moody]
   Score: 6.43 / 10  (energy gap 0.07 (+3.25), valence gap 0.06 (+2.35), acousticness gap 0.17 (+0.83))
3. Midnight Coding by LoRoom  [lofi, chill]
   Score: 6.36 / 10  (energy gap 0.08 (+3.22), valence gap 0.06 (+2.35), acousticness gap 0.21 (+0.79))
4. Velvet Hours by Amara Fields  [r&b, romantic]
   Score: 6.33 / 10  (energy gap 0.05 (+3.32), valence gap 0.16 (+2.10), acousticness gap 0.10 (+0.90))
5. Dusty Porch Swing by Hollow Creek  [country, nostalgic]
   Score: 6.18 / 10  (energy gap 0.02 (+3.43), valence gap 0.18 (+2.05), acousticness gap 0.30 (+0.70))
```

### What the outputs show

- The three realistic profiles each get the song you would expect first (Sunrise City, Library Rain, Storm Runner).
- **Conflicting (high energy but sad):** Rainy Window Blues wins at 7.49 even though its energy gap is 0.52, because the mood and genre matches add 3.0 points. Iron Cathedral fits the energy and valence better but has no matching label.
- **Genre not in catalog:** the genre bonus never fires, so mood and the numbers decide, and the results stay sensible.
- **Impossible (loud and fully acoustic):** no song fits, yet Wildflower Road scores 7.61 on label matches alone, which makes a weak match look good.
- **Neutral:** scores for places 2 to 5 sit within 0.25 of each other, so their order is close to arbitrary.

---

## Sample Recommendation Output (experimental weights)

Weight-shift experiment: energy doubled from 3.5 to 7.0 and genre halved from 1.0 to 0.5, so scores are now out of 13. These weights are the current setting in `src/recommender.py`; the original weights are listed in the section above if you want to switch back. Terminal output of `python -m src.main`:

### High-Energy Pop

```text
  pop / happy, energy 0.85, valence 0.80, acousticness 0.15
============================================================
1. Sunrise City by Neon Echo  [pop, happy]
   Score: 12.66 / 13  (energy gap 0.03 (+6.79), valence gap 0.04 (+2.40), acousticness gap 0.03 (+0.97), mood match (+2.0), genre match (+0.5))
2. Rooftop Lights by Indigo Parade  [indie pop, happy]
   Score: 11.65 / 13  (energy gap 0.09 (+6.37), valence gap 0.01 (+2.48), acousticness gap 0.20 (+0.80), mood match (+2.0))
3. Gym Hero by Max Pulse  [pop, intense]
   Score: 10.26 / 13  (energy gap 0.08 (+6.44), valence gap 0.03 (+2.42), acousticness gap 0.10 (+0.90), genre match (+0.5))
4. Neon Pulse by Voltage Kid  [edm, euphoric]
   Score: 9.61 / 13  (energy gap 0.11 (+6.23), valence gap 0.00 (+2.50), acousticness gap 0.12 (+0.88))
5. Concrete Crown by Kid Marlow  [hip hop, confident]
   Score: 9.53 / 13  (energy gap 0.07 (+6.51), valence gap 0.18 (+2.05), acousticness gap 0.03 (+0.97))
```

### Chill Lofi

```text
  lofi / chill, energy 0.40, valence 0.60, acousticness 0.80
============================================================
1. Midnight Coding by LoRoom  [lofi, chill]
   Score: 12.67 / 13  (energy gap 0.02 (+6.86), valence gap 0.04 (+2.40), acousticness gap 0.09 (+0.91), mood match (+2.0), genre match (+0.5))
2. Library Rain by Paper Lanterns  [lofi, chill]
   Score: 12.59 / 13  (energy gap 0.05 (+6.65), valence gap 0.00 (+2.50), acousticness gap 0.06 (+0.94), mood match (+2.0), genre match (+0.5))
3. Spacewalk Thoughts by Orbit Bloom  [ambient, chill]
   Score: 11.42 / 13  (energy gap 0.12 (+6.16), valence gap 0.05 (+2.38), acousticness gap 0.12 (+0.88), mood match (+2.0))
4. Focus Flow by LoRoom  [lofi, focused]
   Score: 10.96 / 13  (energy gap 0.00 (+7.00), valence gap 0.01 (+2.48), acousticness gap 0.02 (+0.98), genre match (+0.5))
5. Coffee Shop Stories by Slow Stereo  [jazz, relaxed]
   Score: 9.93 / 13  (energy gap 0.03 (+6.79), valence gap 0.11 (+2.23), acousticness gap 0.09 (+0.91))
```

### Deep Intense Rock

```text
  rock / intense, energy 0.92, valence 0.45, acousticness 0.08
============================================================
1. Storm Runner by Voltline  [rock, intense]
   Score: 12.84 / 13  (energy gap 0.01 (+6.93), valence gap 0.03 (+2.42), acousticness gap 0.02 (+0.98), mood match (+2.0), genre match (+0.5))
2. Gym Hero by Max Pulse  [pop, intense]
   Score: 11.60 / 13  (energy gap 0.01 (+6.93), valence gap 0.32 (+1.70), acousticness gap 0.03 (+0.97), mood match (+2.0))
3. Iron Cathedral by Black Ember  [metal, aggressive]
   Score: 9.61 / 13  (energy gap 0.05 (+6.65), valence gap 0.20 (+2.00), acousticness gap 0.04 (+0.96))
4. Neon Pulse by Voltage Kid  [edm, euphoric]
   Score: 9.29 / 13  (energy gap 0.04 (+6.72), valence gap 0.35 (+1.62), acousticness gap 0.05 (+0.95))
5. Night Drive Loop by Neon Echo  [synthwave, moody]
   Score: 9.07 / 13  (energy gap 0.17 (+5.81), valence gap 0.04 (+2.40), acousticness gap 0.14 (+0.86))
```

### Conflicting: high energy but sad

```text
  blues / sad, energy 0.90, valence 0.20, acousticness 0.10
============================================================
1. Iron Cathedral by Black Ember  [metal, aggressive]
   Score: 9.83 / 13  (energy gap 0.07 (+6.51), valence gap 0.05 (+2.38), acousticness gap 0.06 (+0.94))
2. Storm Runner by Voltline  [rock, intense]
   Score: 9.73 / 13  (energy gap 0.01 (+6.93), valence gap 0.28 (+1.80), acousticness gap 0.00 (+1.00))
3. Gym Hero by Max Pulse  [pop, intense]
   Score: 8.81 / 13  (energy gap 0.03 (+6.79), valence gap 0.57 (+1.07), acousticness gap 0.05 (+0.95))
4. Rainy Window Blues by Delta Hollis  [blues, sad]
   Score: 8.67 / 13  (energy gap 0.52 (+3.36), valence gap 0.02 (+2.45), acousticness gap 0.64 (+0.36), mood match (+2.0), genre match (+0.5))
5. Night Drive Loop by Neon Echo  [synthwave, moody]
   Score: 8.61 / 13  (energy gap 0.15 (+5.95), valence gap 0.29 (+1.77), acousticness gap 0.12 (+0.88))
```

### Genre not in catalog

```text
  k-pop / happy, energy 0.80, valence 0.85, acousticness 0.15
============================================================
1. Sunrise City by Neon Echo  [pop, happy]
   Score: 12.31 / 13  (energy gap 0.02 (+6.86), valence gap 0.01 (+2.48), acousticness gap 0.03 (+0.97), mood match (+2.0))
2. Rooftop Lights by Indigo Parade  [indie pop, happy]
   Score: 11.92 / 13  (energy gap 0.04 (+6.72), valence gap 0.04 (+2.40), acousticness gap 0.20 (+0.80), mood match (+2.0))
3. Concrete Crown by Kid Marlow  [hip hop, confident]
   Score: 9.76 / 13  (energy gap 0.02 (+6.86), valence gap 0.23 (+1.93), acousticness gap 0.03 (+0.97))
4. Gym Hero by Max Pulse  [pop, intense]
   Score: 9.29 / 13  (energy gap 0.13 (+6.09), valence gap 0.08 (+2.30), acousticness gap 0.10 (+0.90))
5. Night Drive Loop by Neon Echo  [synthwave, moody]
   Score: 9.18 / 13  (energy gap 0.05 (+6.65), valence gap 0.36 (+1.60), acousticness gap 0.07 (+0.93))
```

### Impossible: loud and fully acoustic

```text
  folk / dreamy, energy 0.95, valence 0.50, acousticness 0.95
============================================================
1. Storm Runner by Voltline  [rock, intense]
   Score: 9.32 / 13  (energy gap 0.04 (+6.72), valence gap 0.02 (+2.45), acousticness gap 0.85 (+0.15))
2. Iron Cathedral by Black Ember  [metal, aggressive]
   Score: 8.82 / 13  (energy gap 0.02 (+6.86), valence gap 0.25 (+1.88), acousticness gap 0.91 (+0.09))
3. Gym Hero by Max Pulse  [pop, intense]
   Score: 8.79 / 13  (energy gap 0.02 (+6.86), valence gap 0.27 (+1.82), acousticness gap 0.90 (+0.10))
4. Neon Pulse by Voltage Kid  [edm, euphoric]
   Score: 8.76 / 13  (energy gap 0.01 (+6.93), valence gap 0.30 (+1.75), acousticness gap 0.92 (+0.08))
5. Wildflower Road by Juniper Lane  [folk, dreamy]
   Score: 8.44 / 13  (energy gap 0.62 (+2.66), valence gap 0.08 (+2.30), acousticness gap 0.02 (+0.98), mood match (+2.0), genre match (+0.5))
```

### Neutral: everything in the middle

```text
  jazz / relaxed, energy 0.50, valence 0.50, acousticness 0.50
============================================================
1. Coffee Shop Stories by Slow Stereo  [jazz, relaxed]
   Score: 11.17 / 13  (energy gap 0.13 (+6.09), valence gap 0.21 (+1.98), acousticness gap 0.39 (+0.61), mood match (+2.0), genre match (+0.5))
2. bad guy by Billie Eilish  [alt pop, moody]
   Score: 9.69 / 13  (energy gap 0.07 (+6.51), valence gap 0.06 (+2.35), acousticness gap 0.17 (+0.83))
3. Velvet Hours by Amara Fields  [r&b, romantic]
   Score: 9.65 / 13  (energy gap 0.05 (+6.65), valence gap 0.16 (+2.10), acousticness gap 0.10 (+0.90))
4. Dusty Porch Swing by Hollow Creek  [country, nostalgic]
   Score: 9.61 / 13  (energy gap 0.02 (+6.86), valence gap 0.18 (+2.05), acousticness gap 0.30 (+0.70))
5. Midnight Coding by LoRoom  [lofi, chill]
   Score: 9.58 / 13  (energy gap 0.08 (+6.44), valence gap 0.06 (+2.35), acousticness gap 0.21 (+0.79))
```

### What changed with the new weights

- **Conflicting (high energy but sad):** Rainy Window Blues drops from 1st to 4th. Iron Cathedral and Storm Runner, which are much closer on energy, take 1st and 2nd.
- **Impossible (loud and fully acoustic):** Wildflower Road drops from 1st to 5th, and Storm Runner takes 1st.
- **Chill Lofi:** Library Rain and Midnight Coding swap places (a near-tie), and Coffee Shop Stories replaces Wildflower Road at 5th.
- **High-Energy Pop, Genre not in catalog, Neutral:** the top picks do not change; only lower places reshuffle slightly.
- **Trade-off:** energy is now 7 of 13 points (54% of every score), so the system leans harder on one feature.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



