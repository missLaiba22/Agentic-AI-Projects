from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from backend.agents.judge_agent import judge_arguments
from backend.config import GEMINI_MODEL, gemini_client
from backend.models.debate_state import DebateState

SessionAction = Literal["approve", "edit", "reject"]


def _refine_verdict_with_human_opinion(
    *,
    question: str,
    pro_arguments: str,
    con_arguments: str,
    original_verdict: str,
    user_opinion: str,
) -> str:
    prompt = (
        "You are an impartial debate judge performing a FINAL verdict refinement.\n"
        "You are given a draft verdict and human reviewer opinion.\n"
        "Incorporate useful reviewer feedback while preserving evidence-based reasoning.\n"
        "If reviewer opinion is weakly supported, acknowledge uncertainty explicitly.\n"
        "Keep response concise (max 180 words).\n"
        "Output only the final verdict text.\n\n"
        f"Question:\n{question}\n\n"
        f"Pro arguments:\n{pro_arguments}\n\n"
        f"Con arguments:\n{con_arguments}\n\n"
        f"Draft verdict:\n{original_verdict}\n\n"
        f"Human reviewer opinion / edits:\n{user_opinion}\n"
    )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    refined = (response.text or "").strip()
    if not refined:
        refined = original_verdict
    return refined


def _regenerate_verdict(state: DebateState) -> str:
    regenerated = (judge_arguments(state).get("verdict") or "").strip()
    if not regenerated:
        regenerated = "Judge could not produce a regenerated verdict."
    return regenerated


def apply_judge_human_action(
    *,
    state: DebateState,
    action: SessionAction,
    user_opinion: Optional[str],
    edit_summary: Optional[str],
) -> Dict[str, Any]:
    original_verdict = (state.get("verdict") or "").strip()
    if not original_verdict:
        raise RuntimeError("No verdict available for human decision")

    if action == "approve":
        return {
            "session_status": "completed",
            "state_update": {"human_approved": True},
            "audit_events": [
                {
                    "action": "approve",
                    "original_verdict": original_verdict,
                }
            ],
            "verdict": original_verdict,
        }

    if action == "edit":
        opinion_text = (user_opinion or "").strip()
        if not opinion_text:
            raise ValueError("user_opinion is required when action is 'edit'")

        edited_clean = _refine_verdict_with_human_opinion(
            question=state.get("question", ""),
            pro_arguments=state.get("pro_arguments", ""),
            con_arguments=state.get("con_arguments", ""),
            original_verdict=original_verdict,
            user_opinion=opinion_text,
        )
        summary = edit_summary or "Verdict refined by LLM using human opinion"
        return {
            "session_status": "completed",
            "state_update": {
                "verdict": edited_clean,
                "human_approved": True,
                "human_edits": {
                    "original": original_verdict,
                    "opinion": opinion_text,
                    "edited": edited_clean,
                    "summary": summary,
                },
            },
            "audit_events": [
                {
                    "action": "edit",
                    "original_verdict": original_verdict,
                    "edited_verdict": edited_clean,
                    "edit_summary": summary,
                }
            ],
            "verdict": edited_clean,
        }

    if action == "reject":
        regenerated = _regenerate_verdict(state)
        return {
            "session_status": "awaiting_human_verdict",
            "state_update": {
                "verdict": regenerated,
                "human_approved": False,
            },
            "audit_events": [
                {
                    "action": "reject",
                    "original_verdict": original_verdict,
                },
                {
                    "action": "regenerate",
                    "original_verdict": original_verdict,
                    "edited_verdict": regenerated,
                    "edit_summary": "Judge regenerated after rejection",
                },
            ],
            "verdict": regenerated,
        }

    raise ValueError(f"Unsupported action '{action}'")