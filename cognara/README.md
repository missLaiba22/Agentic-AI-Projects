# Cognara

Cognara is a learning project for building a research agent with a simple user interface.

## What It Does

- takes a research topic from the user
- searches the web with Tavily
- passes the gathered notes into Gemini
- returns a synthesized research summary in Streamlit or CLI

## Tech Stack

- Streamlit
- LangGraph
- Google Gemini via `google-genai`
- Tavily
- Python dotenv

## Run The UI

From the repository root:

```powershell
pip install -r .\cognara\requirements.txt
python -m streamlit run .\cognara\app.py
```

## Run The CLI

```powershell
python -m cognara.main
```

## Required Environment Variables

Create `cognara/.env` with:

```env
GEMINI_API_KEY=your_gemini_key_here
TAVILY_API_KEY=your_tavily_key_here
```

The current code also supports `Gemini_api_key` for compatibility.

## Main Files

- `app.py` - Streamlit UI
- `main.py` - CLI entry point
- `graph.py` - LangGraph workflow definition
- `nodes.py` - search and synthesis nodes
- `state.py` - shared graph state

## Current Limitations

- UI navigation is intentionally minimal
- output is a single synthesized summary rather than a deeply structured report
- history and persistence are not implemented yet
- the graph is currently linear, not iterative

## Good Next Steps

- break summary output into sections like overview, key concepts, and takeaways
- add report saving and a lightweight history view
- add validation and retry loops to improve answer quality
- add better source presentation and citations
