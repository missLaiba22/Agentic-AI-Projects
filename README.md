# Agentic AI Projects

Collection of AI-powered applications leveraging agentic workflows and LLMs.

## Projects

### Verdara
AI-powered debate platform where multiple agents discuss topics and reach verdicts.
- **Path**: `./Verdara`
- **Tech**: FastAPI, LangGraph, React, TypeScript
- [Verdara README](./Verdara/README.md)

### Cognara
Streamlit-based research assistant that uses web search and LLM synthesis.
- **Path**: `./cognara`
- **Tech**: Streamlit, LangGraph, Gemini, Tavily
- [Cognara README](./cognara/README.md)

## Quick Start

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\cognara\requirements.txt
Copy-Item .\cognara\.env.example .\cognara\.env
python -m streamlit run .\cognara\app.py
```

Then open the local Streamlit URL shown in the terminal, usually `http://localhost:8501`.

## CLI Mode

```powershell
python -m cognara.main
```

## Environment Variables

Create `cognara/.env` from `cognara/.env.example` and fill in:

- `GEMINI_API_KEY` 
- `TAVILY_API_KEY`

## Repository Scope

This repository is currently scoped to publish Cognara only. Other local experiments in the workspace are intentionally excluded from git tracking.

## Project Structure

```text
cognara/
	app.py
	graph.py
	main.py
	nodes.py
	requirements.txt
	state.py
```
