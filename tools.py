from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
import re
from dotenv import load_dotenv

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns Titles, URLs and Snippets."""
    results = tavily.search(query=query, max_results=5)

    out = []
    for r in results.get('results', []):
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
        )

    return "\n-------\n".join(out)


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"


def extract_top_urls(search_results_str: str, max_urls: int = 4) -> list:
    """Regex extractor to pull clean URLs from search results string."""
    found = re.findall(r"URL:\s*(https?://[^\s\n]+)", search_results_str)
    seen = set()
    unique_urls = []
    for u in found:
        cleaned = u.strip()
        if cleaned not in seen:
            seen.add(cleaned)
            unique_urls.append(cleaned)
        if len(unique_urls) >= max_urls:
            break
    return unique_urls


def batch_extract_and_rank(topic: str, urls: list, max_chunks: int = 8) -> str:
    """
    Parallel multi-URL extraction using Tavily's native batch extract.
    Chunks retrieved text and ranks chunks semantically by relevance to the research topic.
    """
    if not urls:
        return "(No valid URLs available for extraction)"

    extracted_blocks = []

    try:
        # Batch extract across multiple URLs in parallel
        response = tavily.extract(urls=urls)
        results = response.get("results", [])

        for item in results:
            url = item.get("url", "")
            raw = item.get("raw_content", "") or ""
            cleaned = re.sub(r"\s+", " ", raw).strip()
            if cleaned:
                extracted_blocks.append({"url": url, "text": cleaned})

    except Exception:
        # Fallback to local requests if Tavily extract encounters issues
        for u in urls[:2]:
            text = scrape_url.invoke(u)
            if not text.startswith("Could not scrape"):
                extracted_blocks.append({"url": u, "text": text})

    if not extracted_blocks:
        return "(Deep extraction yielded no text - utilizing search summaries)"

    # Semantic Chunking & Relevance Scoring
    all_chunks = []
    topic_words = set(re.findall(r"\w+", topic.lower()))

    for block in extracted_blocks:
        url = block["url"]
        text = block["text"]
        words = text.split(" ")
        step = 80
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + step + 20])
            if len(chunk) > 120:
                chunk_words = set(re.findall(r"\w+", chunk.lower()))
                overlap = len(topic_words.intersection(chunk_words))
                all_chunks.append({
                    "url": url,
                    "chunk": chunk,
                    "score": overlap
                })

    all_chunks.sort(key=lambda x: x["score"], reverse=True)
    selected_chunks = all_chunks[:max_chunks]

    formatted_output = []
    for i, item in enumerate(selected_chunks, 1):
        formatted_output.append(
            f"[Source {i} | {item['url']}]\n{item['chunk']}"
        )

    return "\n\n---\n\n".join(formatted_output)







