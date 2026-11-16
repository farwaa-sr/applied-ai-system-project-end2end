"""Streamlit web UI for the Agentic RAG Music Concierge.

Run:  streamlit run app.py
Same agent as the CLI; adds clickable questions, cards, the reasoning trace and human review buttons.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

from musicrag.cli import build_agent, save_feedback  # noqa: E402
from musicrag.questions import QUESTIONS, InvalidAnswers  # noqa: E402

st.set_page_config(page_title="Music Concierge", page_icon="🎵", layout="centered")


@st.cache_resource(show_spinner=False)
def get_agent(offline: bool):
    return build_agent(offline)


st.title("🎵 Agentic RAG Music Concierge")
st.caption("Answer five questions. An agent retrieves matching taste profiles, ranks songs, "
           "finds a new one on the web, and verifies it exists.")

with st.sidebar:
    st.header("Settings")
    offline = st.checkbox("Offline mode", value=False,
                          help="No Gemini and no live web: rule-based profile and recorded web results.")
    use_rag = st.checkbox("Use retrieval (RAG)", value=True,
                          help="Turn off to see what the profile looks like from your answers alone.")
    st.markdown("**Confidence** blends retrieval similarity, agreement with your mood answer, "
                "and the best catalog score. It is a heuristic, not a probability.")

with st.form("questions"):
    answers = {}
    for q in QUESTIONS:
        letters = list(q.options)
        answers[q.id] = st.radio(
            q.prompt, letters, index=None, format_func=lambda k, q=q: q.options[k].label, key=f"q_{q.id}")
    submitted = st.form_submit_button("Get recommendations", type="primary")

if submitted:
    try:
        with st.spinner("Retrieving profiles, scoring songs, checking the web..."):
            st.session_state["result"] = get_agent(offline).run(
                {k: v for k, v in answers.items() if v}, use_rag=use_rag)
        st.session_state["reviewed"] = False
    except InvalidAnswers as exc:
        st.session_state.pop("result", None)
        st.error(f"Please answer every question. ({exc})")

result = st.session_state.get("result")
if result:
    p = result.profile
    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence", f"{result.confidence:.2f}")
    c2.metric("Profile", f"{p.genre} / {p.mood}")
    c3.metric("Profile source", p.source.split(" ")[0])
    st.caption(f"Energy {p.energy} · valence {p.valence} · acousticness {p.acousticness}")
    st.info(p.rationale)
    for flag in result.flags:
        st.warning(f"Flag: {flag.replace('_', ' ')}")

    st.subheader("Recommendations")
    for i, pick in enumerate(result.picks, 1):
        with st.container(border=True):
            badge = f"🌐 found on the web ({pick.source})" if pick.kind == "web" else f"📚 catalog · {pick.score:.1f}/13"
            st.markdown(f"**{i}. {pick.title}** — {pick.artist}  \n:gray[{badge}]")
            st.write(pick.explanation)
            if pick.url:
                st.link_button("Open", pick.url)

    with st.expander("Reasoning trace (what the agent did)"):
        st.markdown(result.trace.to_markdown())

    st.subheader("Do these picks make sense?")
    if st.session_state.get("reviewed"):
        st.success("Thanks, your review was saved.")
    else:
        note = st.text_input("Optional note")
        a, b = st.columns(2)
        if a.button("👍 Approve"):
            save_feedback(result, "approved", note)
            st.session_state["reviewed"] = True
            st.rerun()
        if b.button("🚩 Flag"):
            save_feedback(result, "flagged", note)
            st.session_state["reviewed"] = True
            st.rerun()
