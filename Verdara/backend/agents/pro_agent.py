from backend.config import GEMINI_MODEL, gemini_client
from backend.models.debate_state import DebateState

def pro_arguer(state: DebateState):
    # Generate pro arguments based on the research
    question = state.get("question", "").strip()
    research = state.get("research", "").strip()
    if not question:
        return {"pro_arguments": "No question provided for argument generation."}
    if not research:
        return {"pro_arguments": "No research provided for argument generation."}
    prompt = (
        "You are an expert debater arguing in FAVOR of the topic.\n"
        "Use the research evidence below to build a strong, logical pro argument.\n"
        "Be specific and concise.\n"
        "Keep total output under 160 words.\n"
        "Use short lines only.\n\n"
        f"Question: {question}\n\n"
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

    pro_text = (response.text or "").strip()
    if not pro_text:
        pro_text = "Pro argument generation failed."

    return {"pro_arguments": pro_text}