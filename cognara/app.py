import streamlit as st
import time
import html
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

# Make package imports work even when Streamlit executes this file from
# inside the cognara directory (common on hosted deployments).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cognara.graph import create_graph

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cognara — Deep Research AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "last_run_result" not in st.session_state:
    st.session_state["last_run_result"] = None

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Sora:wght@600;700&display=swap');

:root {
    --bg: #f1f1f6;
    --surface: #ffffff;
    --ink: #17152f;
    --muted: #72758b;
    --line: #e3e4ee;
    --accent: #534ab7;
    --accent-soft: #eeedfe;
    --success: #1d9e75;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1640 0%, #171239 100%) !important;
    padding: 1rem 0.75rem;
    min-width: 200px !important;
    max-width: 240px !important;
}
[data-testid="stSidebar"] * { color: #CECBF6 !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 0.8rem !important; }
[data-testid="stSidebar"] hr { border-color: #3C3489 !important; }

/* ── App background ── */
.stApp {
    background:
        radial-gradient(circle at 95% 0%, rgba(83,74,183,0.08), transparent 24%),
        linear-gradient(180deg, #f5f5fa 0%, #f1f1f6 100%);
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.block-container {
    padding-top: 2.5rem !important;
    padding-left: clamp(0.75rem, 3vw, 2rem) !important;
    padding-right: clamp(0.75rem, 3vw, 2rem) !important;
    max-width: 100% !important;
    overflow-x: hidden;
}
/* Remove default Streamlit header spacing issues */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
}

/* ── Topbar ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    background: var(--surface);
    border: 0.5px solid var(--line);
    border-radius: 14px;
    padding: 0.75rem 1.25rem;
    margin-bottom: 0.85rem;
}
.topbar-title {
    font-size: clamp(0.85rem, 2vw, 1rem);
    font-weight: 700;
    color: var(--ink);
    font-family: 'Sora', sans-serif;
    white-space: nowrap;
}
.topbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.model-badge {
    background: var(--accent-soft);
    color: var(--accent);
    font-size: clamp(0.6rem, 1.2vw, 0.68rem);
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 99px;
    white-space: nowrap;
}
.status-live { color: var(--success); font-size: 0.72rem; font-weight: 600; white-space: nowrap; }

/* ── Text input ── */
[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    border: 0.5px solid var(--line) !important;
    font-size: clamp(0.8rem, 1.5vw, 0.9rem) !important;
    background: var(--surface) !important;
    min-height: 44px;
    width: 100% !important;
}

/* ── Run button ── */
div.stButton > button {
    background-color: var(--accent) !important;
    color: #EEEDFE !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100%;
    padding: 0.62rem 1.25rem !important;
    white-space: nowrap;
    min-height: 44px;
    transition: background .15s;
    font-size: clamp(0.78rem, 1.5vw, 0.875rem) !important;
}
div.stButton > button:hover { background-color: #3C3489 !important; }

/* ── Download button ── */
div.stDownloadButton > button {
    background-color: #ffffff !important;
    color: var(--accent) !important;
    border: 0.5px solid var(--accent) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100%;
    font-size: clamp(0.78rem, 1.5vw, 0.875rem) !important;
}

/* ── Metric cards — dark ── */
[data-testid="stMetric"] {
    background: #1a1640;
    border: 0.5px solid #2d2660;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    box-shadow: 0 4px 20px rgba(23,21,47,0.18);
    height: 100%;
}
[data-testid="stMetricValue"] {
    color: #EEEDFE !important;
    font-size: clamp(1.2rem, 3vw, 1.6rem) !important;
    font-family: 'Sora', sans-serif;
}
[data-testid="stMetricLabel"] {
    color: #9b96d9 !important;
    font-size: clamp(0.62rem, 1.2vw, 0.72rem) !important;
}
[data-testid="stMetricDelta"] {
    color: #5DCAA5 !important;
    font-size: 0.7rem !important;
}

/* ── Output cards ── */
.cog-card {
    background: var(--surface);
    border: 0.5px solid var(--line);
    border-radius: 14px;
    padding: clamp(0.75rem, 2vw, 1.4rem);
    margin-bottom: 0.9rem;
    box-shadow: 0 4px 16px rgba(23,21,47,0.04);
    overflow-wrap: break-word;
    word-break: break-word;
}
.cog-card-label {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.1rem;
}
.label-purple { color: #534AB7; }
.label-green  { color: #1D9E75; }
.label-orange { color: #D85A30; }
.label-gray   { color: #888888; }

/* Summary body — style the rendered markdown */
.summary-body p,
.summary-body li,
.summary-body span {
    font-size: clamp(0.82rem, 1.5vw, 0.9rem) !important;
    color: #1e1c35 !important;
    line-height: 1.8 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.summary-body h1, .summary-body h2, .summary-body h3 {
    font-family: 'Sora', sans-serif !important;
    color: #17152f !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    margin: 1rem 0 0.4rem 0 !important;
}
.summary-body strong {
    color: #17152f !important;
    font-weight: 700 !important;
}
.summary-body ul, .summary-body ol {
    padding-left: 1.4rem !important;
    margin: 0.5rem 0 !important;
}
.summary-body li {
    margin-bottom: 0.3rem !important;
}
/* Divider between label and body */
.summary-body {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 0.5px solid var(--line);
}

/* ── Source chips ── */
.source-row { display: flex; flex-wrap: wrap; gap: 6px; }
.source-chip {
    background: var(--accent-soft);
    color: #3c3489;
    font-size: clamp(0.6rem, 1.2vw, 0.68rem);
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 99px;
    text-decoration: none;
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;
}
.source-chip:hover { background: #CECBF6; }

/* ── Step pills ── */
.steps-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 1rem; }
.step-pill {
    display: flex; align-items: center; gap: 5px;
    background: #f8f8fc; border: 0.5px solid #e4e3f3;
    border-radius: 99px;
    padding: 4px 12px;
    font-size: clamp(0.62rem, 1.2vw, 0.72rem);
    color: #555;
    white-space: nowrap;
}
.step-pill.active { background:#EEEDFE; border-color:#AFA9EC; color:#3C3489; font-weight:600; }
.step-pill.done   { background:#E1F5EE; border-color:#9FE1CB; color:#0F6E56; }
.pip { width:7px; height:7px; border-radius:50%; display:inline-block; flex-shrink:0; }
.pip-done   { background:#1D9E75; }
.pip-active { background:#534AB7; }
.pip-idle   { background:#cccccc; }

/* ── Sidebar nav ── */
.nav-item {
    padding: 0.5rem 0.65rem;
    border-radius: 10px;
    margin-bottom: 0.35rem;
    font-size: 0.9rem;
    font-weight: 600;
}
.nav-item.active { background: rgba(83,74,183,0.32); color: #ffffff !important; }
.nav-item.ghost  { color: #9b96d9 !important; font-size: 0.75rem; font-weight: 400; line-height: 1.5; }

/* ── Column gap ── */
[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; align-items: flex-end; }

/* ── Empty state ── */
.empty-state { text-align:center; padding:4rem 1rem; }
.empty-state .icon { font-size:2.5rem; margin-bottom:0.5rem; }
.empty-state .title { font-size:1rem; font-weight:600; color:#555; }
.empty-state .sub { font-size:0.8rem; margin-top:0.3rem; color:#999; }

/* ── Error box ── */
.error-box {
    background:#FFF5F5; border:0.5px solid #F09595;
    border-radius:10px; padding:0.75rem 1rem;
    font-size:0.85rem; color:#A32D2D;
}

/* ── Small screen tweaks ── */
@media (max-width: 640px) {
    [data-testid="stMetric"] { padding: 0.6rem 0.75rem; }
    .topbar { padding: 0.6rem 0.9rem; }
    .cog-card { padding: 0.75rem 0.9rem; }
    .step-pill { padding: 3px 8px; }
    /* Stack search + button vertically */
    [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
    [data-testid="stHorizontalBlock"] > div { width: 100% !important; flex: unset !important; }
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def render_steps(stage: str) -> str:
    stages = ["search", "synthesize", "done"]
    idx = stages.index(stage) if stage in stages else 0
    labels = [("🔍 Web search (Tavily)", 0), ("🧠 Synthesizing (Gemini)", 1), ("✅ Complete", 2)]
    pills = []
    for label, i in labels:
        if i < idx:   cls, pip = "done",   "pip-done"
        elif i == idx: cls, pip = "active", "pip-active"
        else:          cls, pip = "",       "pip-idle"
        pills.append(f'<div class="step-pill {cls}"><span class="pip {pip}"></span>{label}</div>')
    return f'<div class="steps-row">{"".join(pills)}</div>'


def build_report(topic, summary, sources):
    src_text = "\n".join(f"  - {s}" for s in sources)
    return (
        f"COGNARA RESEARCH REPORT\n{'='*50}\n"
        f"Topic: {topic}\n\nSUMMARY\n{'-'*30}\n{summary}\n\n"
        f"SOURCES\n{'-'*30}\n{src_text}\n"
    )


def render_output(summary, sources):
    source_count = len(sources)

    # Summary card — label via HTML, body via st.markdown so **bold** and * bullets render
    st.markdown("""
        <div class="cog-card">
            <span class="cog-card-label label-purple">Research summary</span>
        </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="summary-body">', unsafe_allow_html=True)
        st.markdown(summary)
        st.markdown('</div>', unsafe_allow_html=True)

    # Sources card
    chips = "".join(
        f'<a class="source-chip" href="{html.escape(url)}" target="_blank">'
        f'{html.escape(url[:50])}{"…" if len(url)>50 else ""}</a>'
        for url in sources
    ) if sources else '<span style="font-size:0.8rem;color:#aaa;">No sources returned.</span>'

    st.markdown(f"""
        <div class="cog-card">
            <span class="cog-card-label label-green">Sources ({source_count})</span>
            <div class="source-row" style="margin-top:0.6rem;">{chips}</div>
        </div>
    """, unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:1rem;padding-bottom:0.75rem;border-bottom:0.5px solid #3C3489;">
        <div style="width:32px;height:32px;background:#534AB7;border-radius:8px;
                    display:flex;align-items:center;justify-content:center;margin-bottom:6px;">
            <span style="color:#EEEDFE;font-size:18px;line-height:1;">✦</span>
        </div>
        <div style="font-size:15px;font-weight:700;color:#EEEDFE;letter-spacing:.01em;">Cognara</div>
        <div style="font-size:10px;color:#7F77DD;margin-top:2px;">Deep research AI</div>
    </div>
    <div style="font-size:9px;color:#534AB7;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">Navigation</div>
    <div class="nav-item active">✦ Research</div>
    <div class="nav-item ghost">History and settings coming soon.</div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <hr style="border-color:#3C3489;margin-bottom:12px;">
    <div style="text-align:center;">
        <div style="width:30px;height:30px;border-radius:50%;background:#3C3489;
                    display:flex;align-items:center;justify-content:center;
                    font-size:12px;font-weight:600;color:#CECBF6;margin:0 auto;">L</div>
        <div style="font-size:10px;color:#7F77DD;margin-top:4px;">Laiba</div>
    </div>
    """, unsafe_allow_html=True)


# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="topbar-title">New research</div>
    <div class="topbar-right">
        <span class="model-badge">Gemini 2.5 Flash + LangGraph</span>
        <span class="status-live">● Ready</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_q, col_btn = st.columns([5, 1])
with col_q:
    question = st.text_input(
        label="q",
        placeholder="e.g. What is quantum entanglement and how is it used in computing?",
        label_visibility="collapsed",
    )
with col_btn:
    run = st.button("Run Cognara")


@st.cache_resource
def get_graph():
    return create_graph()


# ── Execute ────────────────────────────────────────────────────────────────────
if run and question.strip():
    graph      = get_graph()
    steps_ph   = st.empty()
    metrics_ph = st.empty()

    steps_ph.markdown(render_steps("search"), unsafe_allow_html=True)

    try:
        result   = graph.invoke({"topic": question})
        summary  = result.get("summary", "No summary generated.")
        sources  = result.get("sources", [])
        notes    = result.get("research_notes", "")

        st.session_state["last_run_result"] = {
            "summary": summary, "sources": sources,
            "notes": notes, "question": question,
        }

        steps_ph.markdown(render_steps("synthesize"), unsafe_allow_html=True)
        time.sleep(0.4)
        steps_ph.markdown(render_steps("done"), unsafe_allow_html=True)

        word_count    = len(summary.split())
        source_count  = len(sources)
        concept_count = min(source_count + 2, 10)

        with metrics_ph.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("Sources found",  str(source_count),  "via Tavily")
            m2.metric("Summary length", f"{word_count}w",   "Gemini output")
            m3.metric("Concepts",       str(concept_count), "extracted")

        render_output(summary, sources)

        if notes:
            with st.expander("📋 View raw research notes"):
                st.text(notes[:3000] + ("…" if len(notes) > 3000 else ""))

        st.download_button(
            label="⬇ Export report as .txt",
            data=build_report(question, summary, sources),
            file_name="cognara_report.txt",
            mime="text/plain",
        )

    except Exception as e:
        steps_ph.empty()
        st.markdown(f'<div class="error-box">⚠️ Agent error: {e}</div>', unsafe_allow_html=True)

elif run and not question.strip():
    st.warning("Please enter a research question first.")

else:
    last = st.session_state.get("last_run_result")
    if last:
        summary       = last["summary"]
        sources       = last["sources"]
        notes         = last["notes"]
        question      = last["question"]
        word_count    = len(summary.split())
        source_count  = len(sources)
        concept_count = min(source_count + 2, 10)

        m1, m2, m3 = st.columns(3)
        m1.metric("Sources found",  str(source_count),  "via Tavily")
        m2.metric("Summary length", f"{word_count}w",   "Gemini output")
        m3.metric("Concepts",       str(concept_count), "extracted")

        render_output(summary, sources)

        if notes:
            with st.expander("📋 View raw research notes"):
                st.text(notes[:3000] + ("…" if len(notes) > 3000 else ""))

        st.download_button(
            label="⬇ Export report as .txt",
            data=build_report(question, summary, sources),
            file_name="cognara_report.txt",
            mime="text/plain",
        )
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">✦</div>
            <div class="title">Ask Cognara anything</div>
            <div class="sub">Type a topic above and click <strong>Run Cognara</strong> to start</div>
        </div>
        """, unsafe_allow_html=True)