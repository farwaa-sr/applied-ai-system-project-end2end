# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**  

---

## 2. Goal and Intended Use  

**Goal:** VibeMatch suggests songs that fit a listener's taste right now. It picks the top five songs from a small catalog. It scores each song and shows why.

**Intended use:**
- Classroom learning about how recommenders work.
- Testing ideas like weights and edge cases.
- Running from the command line with a hand-written taste profile.

**Assumptions about the user:**
- They can describe their taste with one genre, one mood, and three numbers.
- Their taste stays the same for one session.

**Not intended for:**
- Real music apps or real users.
- Making decisions about artists, money, or playlists that matter.
- Judging a person's taste. The system only matches labels and numbers.
- Any use that needs fair exposure for all genres. The catalog is too small and uneven.

---

## 3. How the Model Works  

The model compares each song to a taste profile. Each song gets a score. Then it sorts the songs and shows the top five.

A profile has a favorite genre and mood. It also has target levels for energy, valence (how happy a song sounds), and acousticness (how acoustic it is).

For the three number traits, closer is better. A song far above or far below the target loses points. A song right at the target gets full points.

Mood and genre are all or nothing. A match adds points. No match adds nothing.

**Current weights (out of 13 points):**
- Energy: up to 7.0
- Valence: up to 2.5
- Mood match: 2.0
- Acousticness: up to 1.0
- Genre match: 0.5

**Original weights (out of 10 points):** energy 3.5, valence 2.5, mood 2.0, acousticness 1.0, genre 1.0.

I changed the weights after an experiment. I doubled energy and halved genre. This fixed two odd results for strange profiles.

Ties go to the song closer on energy. Every result lists its reasons, like "mood match (+2.0)".

**Changes from the starter:**
- I added valence and acousticness.
- I left out tempo and danceability. They mostly repeat energy.
- Mood now counts for more than genre.

---

## 4. Data Used  

- The catalog has 23 songs in `data/songs.csv`.
- The starter had 10 songs. I added 13 more.
- Each song has a title, artist, genre, mood, and five numbers: energy, tempo, valence, danceability, and acousticness.
- Numbers run from 0 to 1, except tempo, which is in BPM.
- There are 18 genres and 18 moods.
- Four added songs are by real artists. Their numbers are my estimates, not real audio data.
- I made up the other added songs and their numbers.

**Limits:**
- Most genres and moods appear on only one song.
- Only one song is rock.
- The catalog has no lyrics, language, year, or popularity.
- It is far too small to cover real taste.

---

## 5. Strengths  

- Clear listeners get the songs I would pick. Pop gets Sunrise City. Lofi gets Library Rain. Rock gets Storm Runner.
- Opposite profiles share almost no songs. Lofi and Rock have no overlap.
- Every result explains itself. Users can see which rules gave points.
- A missing genre does not break it. The K-pop profile fell back on mood and numbers and still got sensible songs.
- It is simple. I can check any score by hand.

---

## 6. Limitations and Bias 

The biggest weakness I found is that the exact-match mood and genre bonuses can outweigh how a song actually sounds. With my original weights, the "high energy but sad" test profile (energy 0.9, valence 0.2) ranked Rainy Window Blues first even though its energy is 0.38, because matching "sad" and "blues" added 3 of the 10 points; Iron Cathedral, which is far closer on energy and valence, came second only because its labels did not match. The same thing happened for a "loud and fully acoustic" profile, where a song with an energy gap of 0.62 won on labels alone. This is made worse by the small catalog: 14 of its 18 genres and 14 of its 18 moods appear on only one song, so a listener's favorite label usually matches at most one track, and a near-synonym such as "aggressive" versus "intense" earns nothing. Doubling the energy weight and halving the genre weight fixed both cases, but it made energy over half of every score, so the real fix is probably softer label matching rather than just shifting weights. The energy gap itself is not biased against any group of listeners, since the catalog is fairly balanced (8 low, 7 mid and 8 high energy songs).

---

## 7. Evaluation  

### Profiles I tested
I ran seven listener profiles against the 23-song catalog and looked at the top five songs for each (full outputs are in the README). All results below use my original weights; I describe what happened when I changed them at the end.

- **High-Energy Pop (Pop):** loves pop, happy, lively, bright-sounding songs.
- **Chill Lofi (Lofi):** loves lofi, chill, calm and acoustic songs.
- **Deep Intense Rock (Rock):** loves rock, intense, very loud songs with a darker feel.
- **Conflicting: high energy but sad (Sad):** wants blues and sad moods but also very high energy, which rarely go together.
- **Genre not in catalog (K-pop):** wants K-pop, which has no songs at all, with a happy, high-energy feel.
- **Impossible: loud and fully acoustic (Impossible):** wants very high energy and almost entirely acoustic sound, a combination no song has.
- **Neutral (Neutral):** every number set to the middle, jazz and relaxed.

I was checking two things: do ordinary listeners get the songs I would pick for them, and what happens when a listener asks for something the catalog cannot give.

### What surprised me
1. **"Gym Hero" kept turning up.** It showed up for Pop, Rock, K-pop and Impossible. In plain terms: Gym Hero is a pop song that is very energetic and fairly cheerful. A "happy pop" listener wants exactly that mix of lively and upbeat, and the system checks the song's numbers and its genre label, not whether it is actually a "happy" song. Its mood is "intense", so it loses the points for mood, but it is so close on energy, cheerfulness and genre that it still lands third. It is not a bug, but it is not what a happy-pop listener would call a perfect match either. The same song shows up for rock fans because it is just as loud and "intense" as a rock song.
2. **Labels can beat the sound.** For the Sad profile, a quiet blues song (Rainy Window Blues) beat louder songs that matched the energy the listener asked for, just because its mood and genre words matched.
3. **A missing genre barely hurt.** The K-pop profile got nearly the same results as Pop, because the system fell back on mood and the numbers, which is a good sign.
4. **The Impossible profile hid its problem.** The top song scored 7.61 out of 10 even though nothing in the catalog fits, so a weak match looks like a decent one.
5. **The Neutral profile gave a one-song answer.** Coffee Shop Stories (jazz, relaxed) scored far above everything else, and the other four places were separated by less than 0.3 points, so their order is close to arbitrary.

### Comparing every pair of profiles
- **Pop vs Lofi:** no songs in common. Pop gets lively, bright songs; Lofi gets slow, acoustic, calm ones. Makes sense, since they are almost opposites on energy and acousticness.
- **Pop vs Rock:** they share Gym Hero and Concrete Crown. Both want loud songs, but Pop gets cheerful ones and Rock gets darker, "intense" ones; Gym Hero is the bridge because it is loud and bright.
- **Pop vs Sad:** only Concrete Crown in common. Both want high energy, but Sad asks for a gloomy feel, so Pop gets happy songs and Sad gets blues and metal. This shows the cheerfulness setting does real work.
- **Pop vs K-pop:** almost identical lists (same top two and the same five songs apart from order). The only difference is that K-pop has no genre bonus to give, so Gym Hero drops from third to fourth. Makes sense.
- **Pop vs Impossible:** only Gym Hero in common. Impossible's acoustic request pulls a folk song to first place, while Pop's lively request does not.
- **Pop vs Neutral:** nothing in common. Neutral wants mid-level everything, so it gets jazz, country and R&B, while Pop gets loud pop and dance songs.
- **Lofi vs Rock:** completely different lists, the cleanest test. One wants quiet and acoustic, the other loud and electric, and the songs flip accordingly.
- **Lofi vs Sad:** no overlap. Lofi gets calm, mellow songs; Sad gets high-energy dark ones. The system respects the energy request.
- **Lofi vs K-pop:** no overlap. Calm and acoustic against loud and bright, as expected.
- **Lofi vs Impossible:** they share Wildflower Road (a folk song). It is Lofi's fifth pick on its numbers, but Impossible's first pick on its labels (folk, dreamy), so the same song ranks high for two different reasons.
- **Lofi vs Neutral:** only Midnight Coding in common. It sits at medium-low energy, so it satisfies a calm listener and a middle-of-the-road one.
- **Rock vs Sad:** four of five songs shared (Storm Runner, Iron Cathedral, Night Drive Loop, Concrete Crown). Both want loud songs, so that overlap is right. The difference is the first place: Rock's is a rock song, Sad's is a quiet blues song, which came from labels.
- **Rock vs K-pop:** Gym Hero and Concrete Crown in common. Rock gets darker, harder songs and K-pop gets brighter ones.
- **Rock vs Impossible:** four songs shared, because both want very loud songs. The difference is that Impossible's acoustic request pushes a gentle folk song to the top.
- **Rock vs Neutral:** nothing in common. Very loud against middle-of-everything.
- **Sad vs K-pop:** only Concrete Crown in common. Same loudness, opposite mood, so one list is gloomy and the other cheerful.
- **Sad vs Impossible:** three songs shared (Storm Runner, Iron Cathedral, Night Drive Loop). Both ask for something the catalog cannot fully offer, and in both a song winning on labels beat songs that fit the loudness better.
- **Sad vs Neutral:** nothing in common. Loud and gloomy against middle of the road.
- **K-pop vs Impossible:** only Gym Hero in common. K-pop is bright and loud; Impossible wants loud and acoustic.
- **K-pop vs Neutral:** nothing in common. Bright and loud against a middle-ground jazz listener.
- **Impossible vs Neutral:** nothing in common. One asks for the extremes, the other for the exact middle.

### Does the output make sense?
For the three realistic profiles, yes: the top pick is what I would choose by hand (Sunrise City, Library Rain, Storm Runner). The profiles that disagree the most (Lofi against Rock) share no songs, which is what I hoped to see. Where it breaks is the strange requests, where the system always gives a confident-looking answer.

### Weight experiment
I doubled the energy weight and halved the genre weight. Ordinary profiles barely changed, but the Sad profile moved Rainy Window Blues from first to fourth and the Impossible profile moved Wildflower Road from first to fifth, which looked more accurate. The cost is that energy then makes up over half of every score.

---

## 8. Ideas for Improvement  

1. **Softer label matching.** Give partial credit for close moods and genres, like "aggressive" and "intense", or "indie pop" and "pop". This would fix the exact-match problem.
2. **A weak-match warning.** If no song fits well, say so. Today a poor match still looks like a good score.
3. **More songs and more variety.** Add several songs per genre. Add a repeat-artist limit so the top five are not all alike.
4. **Better profiles.** Let a user pick more than one mood or genre, and name genres to avoid.

---

## 9. Personal Reflection  

**Biggest learning moment.** A recommender is a set of choices, not magic. I picked the features and the weights, and those choices decided every result. The moment it clicked was the "high energy but sad" test. A quiet blues song ranked first for someone who asked for very loud music, because its mood and genre labels matched. Nothing was broken. I had simply decided that labels were worth 3 of 10 points. Seeing a weight turn into a wrong answer showed me what a weight really does.

**How AI helped, and when I had to double-check it.** AI helped me move fast. It suggested the scoring recipe, wrote the CSV loader and scoring code, expanded the dataset, and drafted the documents. But I still had to check its work. Three examples:
- The AI said `python -m src.main` would work, but it crashed on an import error until the import was fixed.
- After I changed the weights, the output still said "out of 10" when the real maximum was 13. I had to ask whether the math was still valid.
- The numbers for the songs by real artists are estimates, not real audio data. I should not treat them as facts.

The AI also suggested that mood should count for more than genre. I treated that as a guess and tested it with experiments instead of trusting it.

**What surprised me.** Simple rules can feel like real recommendations. The system only subtracts and adds. Yet Sunrise City for a happy pop listener, and Library Rain for a lofi listener, felt right. Showing the reasons for each score helped a lot, because I could see why a song was picked. The other surprise was Gym Hero. It kept showing up for happy pop listeners. It is loud and cheerful, so the numbers fit, even though its mood is "intense". That showed me how a system can feel smart and still be matching only a few numbers.

**What I would try next.**
- Give partial credit for close moods and genres, like "aggressive" and "intense".
- Add a warning when no song is a good match.
- Add many more songs, with real audio data, and limit repeat artists in the top five.
- Let a profile hold more than one mood or genre.
