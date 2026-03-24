from backend.config import GEMINI_MODEL, gemini_client
from backend.models.debate_state import DebateState


def judge_arguments(state: DebateState):
    question = state.get("question", "").strip()
    pro_arguments = state.get("pro_arguments", "").strip()
    con_arguments = state.get("con_arguments", "").strip()

    if not question:
        return {"verdict": "No debate question provided for judging."}

    if not pro_arguments or not con_arguments:
        return {"verdict": "Cannot judge because one or both arguments are missing."}

    prompt = (
        "You are an impartial debate judge.\n"
        "Evaluate both sides fairly using clarity, evidence use, logic, and relevance.\n"
        "Do not pick a side without explanation.\n\n"
        f"Question: {question}\n\n"
        f"Pro Argument:\n{pro_arguments}\n\n"
        f"Con Argument:\n{con_arguments}\n\n"
        "Output format:\n"
        "- Strong points from Pro\n"
        "- Strong points from Con\n"
        "- Weaknesses on each side\n"
        "- Final verdict (which side is currently stronger and why)"
    )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    verdict_text = (response.text or "").strip()
    if not verdict_text:
        verdict_text = "Judge could not produce a verdict."

    return {"verdict": verdict_text}