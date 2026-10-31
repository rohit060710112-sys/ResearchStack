# ResearchStack 🔬

An autonomous multi-agent research assistant built with **LangChain**, **Groq**, **Tavily**, and **Streamlit**.

ResearchStack coordinates four specialized AI agents sequentially to discover, deep-read, synthesize, and rigorously critique research on any topic:

1. **Search Agent (Tavily)**: Gathers fresh, authoritative web search results, titles, URLs, and snippets.
2. **Reader Agent (Web Scraper)**: Inspects search results, identifies the most relevant URL, and extracts in-depth text content.
3. **Writer Chain**: Synthesizes the gathered intelligence into a well-structured research report (Introduction, Key Findings, Conclusion, Sources).
4. **Critic Chain**: Evaluates and scores the drafted report with constructive feedback and strengths/improvements breakdown.

---

## 🚀 Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/rohit060710112-sys/ResearchStack.git
cd ResearchStack
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 4. Run the application

#### Web UI (Streamlit)
```bash
streamlit run app.py
```

#### Terminal / CLI mode
```bash
python pipeline.py
```

