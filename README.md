# Agentic AI Projects

This repository currently contains Cognara, a small research-agent project built while learning agentic AI workflows.

## Cognara

Cognara is a Streamlit-based research assistant that:

- searches the web with Tavily
- synthesizes findings with Gemini
- orchestrates execution with LangGraph
- provides both a UI mode and a CLI mode

Project folder: `cognara/`

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
