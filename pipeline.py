"""
pipeline.py
-----------
Multi-agent research pipeline implemented using a cyclic LangGraph state machine.
Enhanced with:
- Parallel Multi-URL Extraction & Semantic Chunk Ranking
- Autonomous Critic -> Writer Revision Loop
- Automatic Groq Model Fallbacks
"""

import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

import agents
import tools
from tools import web_search, extract_top_urls, batch_extract_and_rank


# ── Error sentinel ────────────────────────────────────────────────────────────
class PipelineStepError(Exception):
    """Raised when a pipeline step produces unusable output."""


def _validate(value: str, step_name: str, min_len: int = 50) -> str:
    """Validate string output from a step."""
    if not value or not value.strip():
        raise PipelineStepError(f"[{step_name}] produced empty output.")
    if value.strip().lower().startswith("could not"):
        raise PipelineStepError(f"[{step_name}] reported a tool error: {value[:200]}")
    if len(value.strip()) < min_len:
        raise PipelineStepError(
            f"[{step_name}] output is suspiciously short ({len(value)} chars): {value[:200]}"
        )
    return value


def extract_score(feedback: str) -> int:
    """Extract integer score out of 10 from the Critic's output."""
    match = re.search(r"score\s*:\s*(\d{1,2})\s*(?:/\s*10)?", feedback, re.IGNORECASE)
    if match:
        try:
            score = int(match.group(1))
            return min(max(score, 0), 10)
        except ValueError:
            pass
    return 7


# ── State Schema ──────────────────────────────────────────────────────────────
class ResearchState(TypedDict):
    topic: str
    search_results: str
    scraped_content: str
    report: str
    feedback: str
    score: int
    revision_count: int
    revision_history: List[dict]


# ── Graph Node Functions ──────────────────────────────────────────────────────
def search_node(state: ResearchState) -> dict:
    """Step 1: Search Agent discovers fresh web sources via Tavily."""
    topic = state["topic"]
    raw_search = web_search.invoke(topic)
    validated = _validate(raw_search, "Search Agent")
    return {"search_results": validated}


def reader_node(state: ResearchState) -> dict:
    """
    Step 2: Parallel Multi-URL Deep Scraping & Semantic Chunk Ranking.
    Extracts top 3-4 URLs simultaneously from search results, then ranks
    semantically relevant chunks to provide rich multi-perspective context.
    """
    topic = state["topic"]
    search_results = state.get("search_results", "")

    # Pull top 4 URLs from search results
    urls = extract_top_urls(search_results, max_urls=4)

    if urls:
        # Parallel extraction and semantic ranking across all top URLs
        ranked_context = batch_extract_and_rank(topic=topic, urls=urls, max_chunks=8)
        validated = _validate(ranked_context, "Reader Agent", min_len=80)
    else:
        validated = "(No explicit URLs extracted - relying on search snippets)"

    return {"scraped_content": validated}


def writer_node(state: ResearchState) -> dict:
    """Step 3: Writer drafts or revises the report using multi-source intelligence."""
    topic = state["topic"]
    research_combined = (
        f"SEARCH RESULTS:\n{state.get('search_results', '')}\n\n"
        f"MULTI-SOURCE DEEP CONTEXT:\n{state.get('scraped_content', '')}"
    )

    current_draft = state.get("report")
    previous_feedback = state.get("feedback")
    revision_count = state.get("revision_count", 0)

    # Initial Draft vs. Targeted Revision
    if not current_draft:
        report_raw = agents.writer_chain.invoke({
            "topic": topic,
            "research": research_combined,
        })
        new_revision_count = 0
    else:
        new_revision_count = revision_count + 1
        report_raw = agents.revision_chain.invoke({
            "topic": topic,
            "research": research_combined,
            "report": current_draft,
            "feedback": previous_feedback,
        })

    validated = _validate(report_raw, "Writer Chain", min_len=200)
    return {
        "report": validated,
        "revision_count": new_revision_count
    }


def critic_node(state: ResearchState) -> dict:
    """Step 4: Critic reviews, scores, and triggers autonomous refinement."""
    report = state.get("report", "")
    feedback_raw = agents.critic_chain.invoke({"report": report})
    validated_feedback = _validate(feedback_raw, "Critic Chain", min_len=30)
    score = extract_score(validated_feedback)

    history_entry = {
        "revision": state.get("revision_count", 0),
        "score": score,
        "feedback": validated_feedback,
    }

    history = list(state.get("revision_history") or [])
    history.append(history_entry)

    return {
        "feedback": validated_feedback,
        "score": score,
        "revision_history": history
    }


# ── Conditional Routing Edge ──────────────────────────────────────────────────
def evaluate_critique(state: ResearchState) -> str:
    """
    Autonomous refinement decision:
    Score < 7 and revisions < 2 -> loop back to 'writer'
    Otherwise -> route to END
    """
    score = state.get("score", 0)
    revision_count = state.get("revision_count", 0)
    max_revisions = 2

    if score < 7 and revision_count < max_revisions:
        return "revise"
    return "finish"


# ── Graph Builder ─────────────────────────────────────────────────────────────
def build_research_graph():
    """Build and compile the cyclic LangGraph workflow."""
    workflow = StateGraph(ResearchState)

    workflow.add_node("search", search_node)
    workflow.add_node("reader", reader_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("critic", critic_node)

    workflow.add_edge(START, "search")
    workflow.add_edge("search", "reader")
    workflow.add_edge("reader", "writer")
    workflow.add_edge("writer", "critic")

    workflow.add_conditional_edges(
        "critic",
        evaluate_critique,
        {
            "revise": "writer",
            "finish": END
        }
    )

    return workflow.compile()


# Compiled singleton graph
research_app = build_research_graph()


# ── Pipeline Runner API ───────────────────────────────────────────────────────
def run_research_pipeline(topic: str, verbose: bool = True) -> dict:
    """Execute the multi-agent graph with automatic fallbacks and deep scraping."""
    def log(msg: str):
        if verbose:
            print(msg)

    log("\n" + "=" * 55)
    log(f"⚡ Starting Autonomous Multi-Agent Research Graph: {topic}")
    log("=" * 55)

    initial_state: ResearchState = {
        "topic": topic,
        "search_results": "",
        "scraped_content": "",
        "report": "",
        "feedback": "",
        "score": 0,
        "revision_count": 0,
        "revision_history": [],
    }

    final_state = research_app.invoke(initial_state)

    log("\n" + "=" * 55)
    log(f"✓ Complete! Quality Score: {final_state.get('score')}/10 | Revisions: {final_state.get('revision_count')}")
    log("=" * 55)

    return final_state


if __name__ == "__main__":
    topic_in = input("\nEnter a research topic: ").strip()
    if not topic_in:
        print("No topic entered. Exiting.")
    else:
        try:
            res = run_research_pipeline(topic_in, verbose=True)
            print("\nFinal Report:\n", res["report"][:500], "...\n")
            print("Final Feedback:\n", res["feedback"])
        except Exception as err:
            print(f"\n❌ Pipeline failed: {err}")
