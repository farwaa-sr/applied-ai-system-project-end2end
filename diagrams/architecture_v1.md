# System Diagram, Version 1

Planned architecture: RAG music concierge with a reliability layer.

```mermaid
flowchart TD
    U[User types a request<br/>'calm music for studying at 2am'] --> V[Input validation<br/>and guardrails]
    V -->|invalid or empty| E[Friendly error message]
    V -->|valid| R[Retriever]

    subgraph Data
        C[(songs.csv<br/>song catalog)]
        K[(Mood and genre<br/>knowledge notes)]
    end

    C --> R
    K --> R

    R -->|top matching songs<br/>and context| L[LLM<br/>builds taste profile<br/>from request + retrieved data]
    L -->|API failure| F[Fallback:<br/>default profile]
    L --> P[Taste profile<br/>genre, mood, energy,<br/>valence, acousticness]
    F --> P

    P --> S[score_song and<br/>recommend_songs<br/>existing rule-based scorer]
    S --> G[LLM writes explanations<br/>grounded in retrieved songs]
    G --> O[Top 5 recommendations<br/>with reasons]

    V -.-> LOG[(Logging)]
    R -.-> LOG
    L -.-> LOG
    S -.-> LOG
    G -.-> LOG

    T[Reliability tests<br/>fixed prompts and edge cases] -.->|runs the pipeline and checks| O
    T --> TR[Test report<br/>pass rate and failures]

    O --> H{Human review<br/>do the picks and<br/>reasons make sense?}
    TR --> H
    H -->|approve| D[Result shown to user]
    H -->|reject or flag| FB[Feedback notes<br/>used to adjust prompts,<br/>weights, and test cases]
    FB -.-> L
    FB -.-> T
    LOG -.->|reviewed for errors| H
```

## Flow summary

1. The user describes what they want in plain language.
2. Guardrails validate the input.
3. The retriever finds relevant songs and mood notes from the data.
4. The LLM uses the retrieved data to build a taste profile.
5. The existing scorer ranks songs against that profile.
6. The LLM explains each pick using only the retrieved song data.
7. Every step is logged, and a test script checks the pipeline for consistency.
8. A human reviews the recommendations, the test report and the logs. Approved results go to the user. Flagged results produce feedback that improves the prompts, scoring weights and test cases.

## Where checking happens

| Check | Type | What it catches |
|---|---|---|
| Input validation | Automated guardrail | Empty or invalid requests |
| API fallback | Automated guardrail | LLM failures |
| Reliability tests | Automated testing | Inconsistent answers, songs not in the catalog |
| Human review | Human in the loop | Picks or explanations that look wrong or unhelpful |
