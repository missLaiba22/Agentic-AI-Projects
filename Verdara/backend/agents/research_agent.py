from backend.config import tavily_client
from backend.models.debate_state import DebateState


def researcher(state: DebateState):
    question = state.get("question", "").strip()

    if not question:
        return {"research": "No question provided for research."}

    response = tavily_client.search(
        query=question,
        max_results=5,
        search_depth="basic",
    )

    results = response.get("results", [])
    if not results:
        return {"research": "No web evidence found."}

    evidence_lines = []
    for i, item in enumerate(results, start=1):
        title = item.get("title", "Untitled source")
        content = item.get("content", "").replace("\n", " ").strip()
        url = item.get("url", "")

        snippet = content[:300]
        if len(content) > 300:
            snippet += "..."

        evidence_lines.append(f"{i}. {title} | {snippet} | Source: {url}")

    research_text = "Evidence collected:\n" + "\n".join(evidence_lines)
    return {"research": research_text}