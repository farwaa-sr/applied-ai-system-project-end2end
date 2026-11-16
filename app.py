"""Streamlit web UI for the Agentic RAG Music Concierge.

Run:  streamlit run app.py
Same agent as the CLI, with a pastel interface, an in-page Spotify player for each pick,
a "show me new ones" button that never repeats songs, the reasoning trace and human review.
"""
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

from musicrag.cli import build_agent, save_feedback  # noqa: E402
from musicrag.links import embed_url, search_url, spotify_track_id  # noqa: E402
from musicrag.questions import QUESTIONS, InvalidAnswers  # noqa: E402
from musicrag.ui_theme import hero_html, section_html, song_html, summary_html, theme_css  # noqa: E402

st.set_page_config(page_title="Music Concierge", page_icon="🌙", layout="centered", initial_sidebar_state="collapsed")
st.markdown(theme_css(), unsafe_allow_html=True)

EMOJI = {
    "setting": {"a": "📚", "b": "🏃", "c": "🚗", "d": "🛋️", "e": "🎉"},
    "energy": {"a": "🌙", "b": "🌤️", "c": "⚡"},
    "mood": {"a": "☀️", "b": "🍃", "c": "🌧️", "d": "🔥", "e": "💗", "f": "🌌"},
    "texture": {"a": "🎸", "b": "🎛️", "c": "🎹"},
    "novelty": {"a": "🏠", "b": "🧭", "c": "✨"},
}
Q_KEYS = [f"q_{q.id}" for q in QUESTIONS]


@st.cache_resource(show_spinner=False)
def get_agent(offline: bool):
    return build_agent(offline)


with st.sidebar:
    st.header("Settings")
    offline = st.checkbox("Offline mode", value=False,
                          help="No Gemini and no live web: rule-based profile and recorded web results.")
    use_rag = st.checkbox("Use retrieval (RAG)", value=True,
                          help="Turn off to see what the profile looks like from your answers alone.")
    st.caption("Confidence blends retrieval similarity, agreement with your mood answer and the best catalog "
               "score. It is a heuristic, not a probability.")


def run_agent(answers: dict, exclude=()):
    return get_agent(offline).run(answers, use_rag=use_rag, exclude=list(exclude))


def start_over() -> None:
    for key in Q_KEYS:
        st.session_state[key] = None
    for key in ("result", "answers", "shown", "set_no", "reviewed"):
        st.session_state.pop(key, None)


def render_player(pick) -> None:
    track_id = spotify_track_id(pick.title, pick.artist, pick.url)
    if track_id:
        st.iframe(embed_url(track_id), height=80)
    else:
        st.link_button("▶ Find it on Spotify", search_url(pick.title, pick.artist))


def render_results(result) -> None:
    set_no = st.session_state.get("set_no", 1)
    st.markdown(section_html("Your songs", "Press play on any song. Each one is checked to be a real track."),
                unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(summary_html(result.profile, result.confidence, set_no, result.flags), unsafe_allow_html=True)
    if "catalog_exhausted" in result.flags:
        st.info("You've heard nearly everything I have for this vibe. Start over to try different answers.")

    for i, pick in enumerate(result.picks):
        with st.container(key=f"pick{i % 5}"):
            st.markdown(song_html(i + 1, pick), unsafe_allow_html=True)
            render_player(pick)

    left, right = st.columns(2)
    if left.button("🔄  Show me new ones", type="primary", use_container_width=True):
        with st.spinner("Finding fresh songs..."):
            new = run_agent(st.session_state["answers"], st.session_state["shown"])
        st.session_state["shown"] = st.session_state["shown"] + [p.title for p in new.picks]
        st.session_state.update(result=new, set_no=set_no + 1, reviewed=False)
        st.rerun()
    right.button("🌱  Start over", on_click=start_over, use_container_width=True)

    with st.expander("How the agent decided"):
        st.markdown(result.trace.to_markdown())

    st.markdown(section_html("Do these feel right?"), unsafe_allow_html=True)
    if st.session_state.get("reviewed"):
        st.success("Thank you, your review was saved.")
    else:
        note = st.text_input("Optional note", placeholder="Anything that felt off?")
        a, b = st.columns(2)
        if a.button("💜  Love these", use_container_width=True):
            save_feedback(result, "approved", note)
            st.session_state["reviewed"] = True
            st.rerun()
        if b.button("🚩  Not quite", use_container_width=True):
            save_feedback(result, "flagged", note)
            st.session_state["reviewed"] = True
            st.rerun()


def render_form() -> bool:
    """The five questions. Returns True when the form was submitted."""
    with st.form("questions", border=False):
        answers = {}
        for q in QUESTIONS:
            with st.container(border=True):
                st.markdown(f'<div class="q-label">{escape(q.prompt)}</div>', unsafe_allow_html=True)
                answers[q.id] = st.pills(
                    q.prompt, list(q.options), key=f"q_{q.id}", label_visibility="collapsed",
                    format_func=lambda k, q=q: f"{EMOJI[q.id][k]}  {q.options[k].label}")
        submitted = st.form_submit_button("✨ Find my music", type="primary")
    if submitted:
        try:
            with st.spinner("Listening to your vibe..."):
                res = run_agent({k: v for k, v in answers.items() if v})
            st.session_state.update(result=res, answers=res.answers, shown=[p.title for p in res.picks],
                                    set_no=1, reviewed=False)
            st.rerun()
        except InvalidAnswers:
            st.error("Please answer all five questions, then try again.")
    return submitted


# ----------------------------------------------------------------------------- page
st.markdown(hero_html(), unsafe_allow_html=True)

if st.session_state.get("result"):
    render_results(st.session_state["result"])
    with st.expander("✏️  Change my answers"):
        render_form()
else:
    st.markdown(section_html("Tell me about your vibe", "Pick one answer for each question, then press the button."),
                unsafe_allow_html=True)
    render_form()

st.markdown('<div class="soft-note">Players are Spotify embeds: you hear a short preview unless you are '
            'signed in to Spotify in this browser.</div>', unsafe_allow_html=True)
