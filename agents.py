from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

# Primary Model: openai/gpt-oss-120b
# Fallback Model: qwen/qwen3.8-27b (activated automatically on 429/500/rate limits)
primary_model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

fallback_model = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0
)

# Resilient LLM with automatic fallback routing
llm = primary_model.with_fallbacks([fallback_model])


def build_search_agent():
    """Agent that searches the web for a given topic using Tavily."""
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=(
            "You are a research assistant. Use the web_search tool to find recent, "
            "reliable information on the given topic."
        ),
    )


def build_reader_agent():
    """Agent that scrapes a URL and returns its cleaned text content."""
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=(
            "You are a web reader. Use the scrape_url tool to fetch and return the "
            "full text content of a given URL."
        ),
    )


# ── Writer chain (Draft) ──────────────────────────────────────────────────────
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered from Multi-Source Deep Reading:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points with comparative insights)
- Conclusion
- Sources (list all URLs cited in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# ── Writer chain (Revision based on Critic feedback) ──────────────────────────
revision_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer improving an existing draft based on rigorous critique."),
    ("human", """Improve and revise the research report below based on the reviewer's feedback.

Topic: {topic}

Original Multi-Source Research Gathered:
{research}

Current Draft:
{report}

Critic's Feedback:
{feedback}

Please produce a thoroughly revised and polished version of the report addressing all areas to improve.
Maintain proper structure:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs cited in the research)"""),
])

revision_chain = revision_prompt | llm | StrOutputParser()


# ── Critic chain ──────────────────────────────────────────────────────────────
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
