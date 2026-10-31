import streamlit as st
import time
from pipeline import research_app, PipelineStepError, ResearchState
import storage
import exporters

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchStack · Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
storage.init_db()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #e8e4dc;
}

.stApp {
    background: #0a0a0f;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,140,50,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,80,30,0.08) 0%, transparent 55%);
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    color: #ff8c32 !important;
    background: rgba(255, 140, 50, 0.1) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebarCollapseButton"] {
    color: #ff8c32 !important;
}
section[data-testid="stSidebar"] {
    background: #0d0d15 !important;
    border-right: 1px solid rgba(255,140,50,0.15) !important;
}
.block-container { padding: 2rem 3rem 4rem; max-width: 1200px; }

/* ── Hero header ── */
.hero {
    text-align: center;
    padding: 2.5rem 0 1.8rem;
    position: relative;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #ff8c32;
    margin-bottom: 0.8rem;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.4rem, 5vw, 4.2rem);
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -0.03em;
    color: #f0ebe0;
    margin: 0 0 0.8rem;
}
.hero h1 span {
    color: #ff8c32;
}
.hero-sub {
    font-size: 1.02rem;
    font-weight: 300;
    color: #a09890;
    max-width: 580px;
    margin: 0 auto;
    line-height: 1.6;
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,140,50,0.3), transparent);
    margin: 1.8rem 0;
}

/* ── Input card ── */
.input-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,140,50,0.15);
    border-radius: 16px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(8px);
}

.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,140,50,0.25) !important;
    border-radius: 10px !important;
    color: #f0ebe0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #ff8c32 !important;
    box-shadow: 0 0 0 3px rgba(255,140,50,0.12) !important;
}
.stTextInput > label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #ff8c32 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #ff8c32 0%, #ff5a1a 100%) !important;
    color: #0a0a0f !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.7rem 2.2rem !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(255,140,50,0.3) !important;
    width: 100%;
}

section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #ded7ce !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.84rem !important;
    box-shadow: none !important;
    text-align: left !important;
    padding: 0.55rem 0.8rem !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 140, 50, 0.12) !important;
    border-color: rgba(255, 140, 50, 0.3) !important;
    color: #ff8c32 !important;
}

/* ── Step cards ── */
.step-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.9rem;
    position: relative;
    overflow: hidden;
}
.step-card.active {
    border-color: rgba(255,140,50,0.4);
    background: rgba(255,140,50,0.05);
}
.step-card.done {
    border-color: rgba(80,200,120,0.3);
    background: rgba(80,200,120,0.03);
}
.step-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: rgba(255,255,255,0.05);
}
.step-card.active::before { background: #ff8c32; }
.step-card.done::before { background: #50c878; }

.step-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}
.step-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    color: #ff8c32;
}
.step-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.92rem;
    font-weight: 700;
    color: #f0ebe0;
}
.step-status {
    margin-left: auto;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
}
.status-waiting { color: #555; }
.status-running { color: #ff8c32; }
.status-done { color: #50c878; }

.report-panel {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,140,50,0.2);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-top: 1rem;
}
.feedback-panel {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(80,200,120,0.2);
    border-radius: 16px;
    padding: 1.8rem 2.2rem;
    margin-top: 1rem;
}
.panel-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    padding-bottom: 0.7rem;
}
.panel-label.orange {
    color: #ff8c32;
    border-bottom: 1px solid rgba(255,140,50,0.15);
}
.panel-label.green {
    color: #50c878;
    border-bottom: 1px solid rgba(80,200,120,0.15);
}

.section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #f0ebe0;
    margin: 1.5rem 0 1rem;
}

.export-btn-group {
    display: flex;
    gap: 0.8rem;
    margin: 1.2rem 0;
}
</style>
""", unsafe_allow_html=True)


# ── Step Card Helper ──────────────────────────────────────────────────────────
def step_card(num: str, title: str, state: str, desc: str = ""):
    status_map = {
        "waiting": ("WAITING", "status-waiting"),
        "running": ("● RUNNING", "status-running"),
        "done":    ("✓ DONE",   "status-done"),
    }
    label, cls = status_map.get(state, ("", ""))
    card_cls = {"running": "active", "done": "done"}.get(state, "")
    st.markdown(f"""
    <div class="step-card {card_cls}">
        <div class="step-header">
            <span class="step-num">{num}</span>
            <span class="step-title">{title}</span>
            <span class="step-status {cls}">{label}</span>
        </div>
        {"<div style='font-size:0.8rem;color:#706860;margin-top:0.3rem;'>"+desc+"</div>" if desc else ""}
    </div>
    """, unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────────────────────
for key in ("results", "running", "done", "active_step"):
    if key not in st.session_state:
        st.session_state[key] = {} if key == "results" else (False if key in ("running", "done") else None)


# ── Sidebar: Past Research Runs ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:700;color:#ff8c32;margin-bottom:0.4rem;">
            📚 Research History
        </div>
        <div style="font-size:0.8rem;color:#807870;margin-bottom:1.2rem;">
            Local SQLite repository of past sessions.
        </div>
    """, unsafe_allow_html=True)

    past_reports = storage.list_reports(limit=25)

    if not past_reports:
        st.markdown("<div style='font-size:0.8rem;color:#555;'>No past reports found yet.</div>", unsafe_allow_html=True)
    else:
        for item in past_reports:
            score_badge = f"{item['score']}/10" if item['score'] else "N/A"
            btn_label = f"📄 {item['topic'][:24]}... ({score_badge})"
            if st.button(btn_label, key=f"hist_{item['id']}", use_container_width=True):
                full_item = storage.get_report_by_id(item["id"])
                if full_item:
                    st.session_state.results = {
                        "search": full_item["search_results"],
                        "reader": full_item["scraped_content"],
                        "writer": full_item["report"],
                        "critic": full_item["feedback"],
                        "score": full_item["score"],
                        "revisions": full_item["revisions"],
                        "history": full_item.get("history", []),
                        "topic": full_item["topic"],
                    }
                    st.session_state.done = True
                    st.session_state.running = False
                    st.rerun()

    if past_reports:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Active View", use_container_width=True):
            st.session_state.results = {}
            st.session_state.done = False
            st.rerun()


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Autonomous Multi-Agent System</div>
    <h1>Research<span>Stack</span></h1>
    <p class="hero-sub">
        Four specialized AI agents collaborate across search, deep scraping, drafting,
        and autonomous critique loops to create publish-ready research papers.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ── Layout: Input left, Agent Pipeline right ──────────────────────────────────
col_input, col_spacer, col_pipeline = st.columns([5, 0.5, 4])

with col_input:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    topic = st.text_input(
        "Research Topic",
        placeholder="e.g. Next-generation Solid State Batteries 2026",
        key="topic_input",
    )
    run_btn = st.button("⚡ Run Autonomous Research", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Example Chips
    st.markdown("""
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1.5rem;">
        <span style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#605850;letter-spacing:0.1em;">TRY →</span>
    """, unsafe_allow_html=True)
    examples = ["Solid state batteries 2026", "CRISPR in vivo trials", "Quantum error correction progress"]
    for ex in examples:
        st.markdown(f"""
        <span style="
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:6px;
            padding:0.25rem 0.7rem;
            font-size:0.75rem;
            color:#a09890;
            font-family:'DM Sans',sans-serif;
            cursor:default;
        ">{ex}</span>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_pipeline:
    st.markdown('<div class="section-heading">Agent Graph</div>', unsafe_allow_html=True)
    cards_container = st.empty()

    def render_pipeline_cards(active_name=None, completed_set=None):
        if completed_set is None:
            completed_set = set()
        with cards_container.container():
            def get_card_state(name):
                if st.session_state.done:
                    return "done"
                if active_name == name:
                    return "running"
                if name in completed_set or (st.session_state.results and name in st.session_state.results):
                    return "done"
                return "waiting"

            step_card("01", "Search Agent",  get_card_state("search"), "Discovers fresh web sources via Tavily")
            step_card("02", "Reader Agent",  get_card_state("reader"), "Extracts deep page content")
            step_card("03", "Writer Chain",  get_card_state("writer"), "Drafts and iteratively refines report")
            step_card("04", "Critic Chain",  get_card_state("critic"), "Evaluates score and loops until >= 8/10")

    render_pipeline_cards(active_name=st.session_state.active_step)


# ── Execution with Step-by-Step Streaming ─────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.running = True
        st.session_state.done = False
        st.session_state.active_step = "search"
        st.rerun()

if st.session_state.running and not st.session_state.done:
    topic_val = st.session_state.topic_input

    initial_state: ResearchState = {
        "topic": topic_val,
        "search_results": "",
        "scraped_content": "",
        "report": "",
        "feedback": "",
        "score": 0,
        "revision_count": 0,
        "revision_history": [],
    }

    live_container = st.container()
    
    with live_container:
        status_box = st.status("🧠 Agents executing research graph...", expanded=True)

        completed_nodes = set()
        try:
            # Stream the LangGraph node executions live
            for event in research_app.stream(initial_state, stream_mode="updates"):
                for node_name, node_update in event.items():
                    st.session_state.active_step = node_name
                    render_pipeline_cards(active_name=node_name, completed_set=completed_nodes)
                    completed_nodes.add(node_name)

                    if node_name == "search":
                        status_box.write("🔍 **Search Agent** discovered top web resources.")
                        initial_state["search_results"] = node_update["search_results"]
                    elif node_name == "reader":
                        status_box.write("📄 **Reader Agent** extracted deep article content.")
                        initial_state["scraped_content"] = node_update["scraped_content"]
                    elif node_name == "writer":
                        rev = node_update.get("revision_count", 0)
                        if rev == 0:
                            status_box.write("✍️ **Writer Chain** generated initial draft.")
                        else:
                            status_box.write(f"🔄 **Writer Chain** refined draft (Revision #{rev}) based on critique.")
                        initial_state["report"] = node_update["report"]
                        initial_state["revision_count"] = rev
                    elif node_name == "critic":
                        score = node_update.get("score", 0)
                        status_box.write(f"🧐 **Critic Chain** evaluated report: **{score}/10**")
                        initial_state["feedback"] = node_update["feedback"]
                        initial_state["score"] = score
                        initial_state["revision_history"] = node_update.get("revision_history", [])

            render_pipeline_cards(active_name=None, completed_set={"search", "reader", "writer", "critic"})
            status_box.update(label="✓ Research complete & quality verified!", state="complete", expanded=False)

            # Persist to local SQLite storage
            report_id = storage.save_report(
                topic=topic_val,
                score=initial_state["score"],
                revisions=initial_state["revision_count"],
                report=initial_state["report"],
                feedback=initial_state["feedback"],
                search_results=initial_state["search_results"],
                scraped_content=initial_state["scraped_content"],
                history=initial_state["revision_history"]
            )

            st.session_state.results = {
                "search": initial_state["search_results"],
                "reader": initial_state["scraped_content"],
                "writer": initial_state["report"],
                "critic": initial_state["feedback"],
                "score": initial_state["score"],
                "revisions": initial_state["revision_count"],
                "history": initial_state["revision_history"],
                "topic": topic_val,
            }

        except Exception as e:
            status_box.update(label=f"❌ Error: {e}", state="error")
            st.error(f"Pipeline error: {e}")
            st.session_state.results = {}

    st.session_state.running = False
    st.session_state.done = True
    st.session_state.active_step = None
    st.rerun()


# ── Results & Export View ─────────────────────────────────────────────────────
r = st.session_state.results

if r and r.get("writer"):
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Research Deliverable</div>', unsafe_allow_html=True)

    curr_topic = r.get("topic", topic)
    rev_cnt = r.get("revisions", 0)
    score_val = r.get("score", 0)

    # Quality & Revision Badges
    st.markdown(f"""
    <div style="display:flex;gap:1rem;margin-bottom:1.5rem;">
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(80,200,120,0.3);border-radius:10px;padding:0.7rem 1.4rem;">
            <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#50c878;letter-spacing:0.1em;text-transform:uppercase;">Critic Score</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:700;color:#f0ebe0;">{score_val}/10</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,140,50,0.3);border-radius:10px;padding:0.7rem 1.4rem;">
            <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#ff8c32;letter-spacing:0.1em;text-transform:uppercase;">Autonomous Revisions</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:700;color:#f0ebe0;">{rev_cnt} {'refinement' if rev_cnt == 1 else 'refinements'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1-Click Multi-Format Export Buttons
    col_md, col_pdf, col_docx, col_spacer_exp = st.columns([2, 2, 2, 4])
    
    with col_md:
        st.download_button(
            label="⬇  Markdown (.md)",
            data=r["writer"],
            file_name=f"report_{int(time.time())}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_pdf:
        try:
            pdf_bytes = exporters.export_to_pdf(curr_topic, r["writer"])
            st.download_button(
                label="⬇  PDF Document (.pdf)",
                data=pdf_bytes,
                file_name=f"report_{int(time.time())}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as err:
            st.warning(f"PDF export notice: {err}")

    with col_docx:
        try:
            docx_bytes = exporters.export_to_docx(curr_topic, r["writer"])
            st.download_button(
                label="⬇  Word Document (.docx)",
                data=docx_bytes,
                file_name=f"report_{int(time.time())}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as err:
            st.warning(f"DOCX export notice: {err}")

    # Final Report Panel
    st.markdown("""
    <div class="report-panel">
        <div class="panel-label orange">📝 Synthesized Research Report</div>
    """, unsafe_allow_html=True)
    st.markdown(r["writer"])
    st.markdown("</div>", unsafe_allow_html=True)

    # Critic Review Panel
    if r.get("critic"):
        st.markdown("""
        <div class="feedback-panel">
            <div class="panel-label green">🧐 Critic Evaluation & Scoring</div>
        """, unsafe_allow_html=True)
        st.markdown(r["critic"])
        st.markdown("</div>", unsafe_allow_html=True)

    # Raw Research Data (Collapsible)
    with st.expander("🔍 Search Results (raw)", expanded=False):
        st.text(r.get("search", ""))

    with st.expander("📄 Scraped Content (raw)", expanded=False):
        st.text(r.get("reader", ""))


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#605850;text-align:center;margin-top:3rem;letter-spacing:0.08em;">
    ResearchStack · LangGraph Cyclic Multi-Agent System · SQLite Session Persistence
</div>
""", unsafe_allow_html=True)
