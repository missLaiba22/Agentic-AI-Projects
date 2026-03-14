import os
from google import genai
from tavily import TavilyClient

from .state import ResearchState

client = genai.Client(api_key=os.getenv("Gemini_api_key"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def research_node(state: ResearchState) -> ResearchState:
    print(f"--- Step 1: Web Search for '{state['topic']}' ---")

    results = tavily.search(query=state["topic"], max_results=5)

    extracted_text = ""
    source_urls = []

    for res in results.get("results", []):
        url = res.get("url", "")
        content = res.get("content", "")
        if not url and not content:
            continue

        extracted_text += f"Source ({url}):\n{content}\n\n"
        if url:
            source_urls.append(url)

    return {
        "research_notes": extracted_text,
        "sources": source_urls,
    }


def writer_node(state: ResearchState) -> ResearchState:
    print("--- Step 2: Synthesizing and Summarizing ---")

    notes = state["research_notes"]

    prompt = f"""
You are an expert synthesizer. Based on the following raw web search results,
extract the key concepts and write a comprehensive summary about the topic.

Raw Data:
{notes}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return {"summary": response.text}