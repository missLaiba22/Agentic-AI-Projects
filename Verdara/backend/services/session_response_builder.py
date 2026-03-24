from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


def _parse_research_sources(research_text: str) -> list[Dict[str, Any]]:
    if not research_text:
        return []

    lines = [line.strip() for line in research_text.splitlines() if line.strip()]
    parsed: list[Dict[str, Any]] = []

    pattern = re.compile(r"^(\d+)\.\s*(.*?)\s*\|\s*(.*?)\s*\|\s*Source:\s*(\S+)$")
    for line in lines:
        match = pattern.match(line)
        if not match:
            continue

        rank, title, snippet, url = match.groups()
        parsed.append(
            {
                "rank": int(rank),
                "title": title,
                "snippet": snippet,
                "url": url,
            }
        )

    return parsed


def _count_points(text: str) -> int:
    if not text:
        return 0

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    point_lines = [
        line
        for line in lines
        if line.startswith("-") or line.startswith("*") or re.match(r"^\d+[\.)]\s+", line)
    ]

    if point_lines:
        return len(point_lines)

    return min(max(len(lines) // 3, 1), 10)


def _runtime_seconds(start_time: Optional[str], end_time: Optional[str]) -> Optional[int]:
    if not start_time:
        return None

    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time) if end_time else datetime.now()
        return max(int((end_dt - start_dt).total_seconds()), 0)
    except ValueError:
        return None


def derive_stage_status(
    session_status: str,
    state: Dict[str, Any],
    next_nodes: Tuple[str, ...],
) -> Dict[str, str]:
    research_done = bool(state.get("research"))
    pro_done = bool(state.get("pro_arguments"))
    con_done = bool(state.get("con_arguments"))
    verdict_done = bool(state.get("verdict"))

    if session_status == "completed":
        return {
            "research": "completed",
            "pro_con": "completed",
            "review": "completed",
            "judge": "completed",
            "done": "completed",
        }

    review_status = "pending"
    judge_status = "pending"

    if research_done and pro_done and con_done:
        review_status = "completed"

    if "judge_arguments" in next_nodes:
        judge_status = "paused"
    elif verdict_done:
        judge_status = "completed"

    done_status = "pending"
    if session_status in {"failed", "cancelled"}:
        done_status = session_status

    return {
        "research": "completed" if research_done else "pending",
        "pro_con": "completed" if (pro_done and con_done) else "pending",
        "review": review_status,
        "judge": judge_status,
        "done": done_status,
    }


def build_session_summary(
    *,
    session: Dict[str, Any],
    state: Dict[str, Any],
    next_nodes: Tuple[str, ...],
) -> Dict[str, Any]:
    stage_status = derive_stage_status(session.get("status", "created"), state, next_nodes)

    sources = _parse_research_sources(state.get("research", ""))
    metrics = {
        "sources": len(sources),
        "arguments_points": _count_points(state.get("pro_arguments", ""))
        + _count_points(state.get("con_arguments", "")),
        "runtime_sec": _runtime_seconds(session.get("start_time"), session.get("end_time")),
    }

    return {
        "session": session,
        "stage_status": stage_status,
        "metrics": metrics,
        "next_nodes": list(next_nodes),
        "state": {
            "question": state.get("question", session.get("question", "")),
            "research": state.get("research", ""),
            "pro_arguments": state.get("pro_arguments", ""),
            "con_arguments": state.get("con_arguments", ""),
            "verdict": state.get("verdict", ""),
        },
    }


def build_tab_payload(
    *,
    summary: Dict[str, Any],
    tab_name: str,
    audit_entries: list[Dict[str, Any]],
) -> Dict[str, Any]:
    state = summary["state"]

    if tab_name == "research":
        sources = _parse_research_sources(state.get("research", ""))
        return {
            "question": state.get("question", ""),
            "sources": sources,
            "raw_research": state.get("research", ""),
            "count": len(sources),
        }

    if tab_name == "debate":
        pro_text = state.get("pro_arguments", "")
        con_text = state.get("con_arguments", "")
        return {
            "pro": {
                "text": pro_text,
                "points": _count_points(pro_text),
            },
            "con": {
                "text": con_text,
                "points": _count_points(con_text),
            },
        }

    if tab_name == "verdict":
        latest_action = audit_entries[-1]["action"] if audit_entries else None
        return {
            "verdict": state.get("verdict", ""),
            "human_approved": summary["session"].get("status") == "completed",
            "latest_action": latest_action,
        }

    if tab_name == "audit":
        return {
            "entries": audit_entries,
            "count": len(audit_entries),
        }

    if tab_name == "agents":
        status = summary["stage_status"]
        return {
            "agents": [
                {
                    "id": "researcher",
                    "name": "Researcher",
                    "status": status["research"],
                },
                {
                    "id": "pro_arguer",
                    "name": "Pro Agent",
                    "status": "completed" if state.get("pro_arguments") else "pending",
                },
                {
                    "id": "con_arguer",
                    "name": "Con Agent",
                    "status": "completed" if state.get("con_arguments") else "pending",
                },
                {
                    "id": "judge_arguments",
                    "name": "Judge",
                    "status": status["judge"],
                },
            ]
        }

    raise ValueError(f"Unsupported tab '{tab_name}'")