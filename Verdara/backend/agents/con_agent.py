from backend.models.debate_state import DebateState
from backend.config import gemini_client, GEMINI_MODEL
def con_arguer(state: DebateState):
    # Generate con arguments based on the research
    research = state.get("research", "").strip()
    if not research:
        return {"con_arguments": "No research provided for argument generation."}

    prompt = (
        "You are an expert debater arguing AGAINST the topic.\n"
        "Use the research evidence below to build a strong, logical con argument.\n"
        "Be specific and concise.\n"
        "Keep total output under 160 words.\n"
        "Use short lines only.\n\n"
        f"Question: {state.get('question', '').strip()}\n\n"
        f"Research Evidence:\n{research}\n\n"
        "Output format:\n"
        "Main claim: one sentence\n"
        "Supporting points:\n"
        "1) ...\n"
        "2) ...\n"
        "3) ... (optional)\n"
        "Conclusion: one short sentence"
    )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    con_text = (response.text or "").strip()
    if not con_text:
        con_text = "Con argument generation failed."

    return {"con_arguments": con_text}