from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from backend.models.debate_state import DebateState
from backend.session_store import (
    create_session,
    get_audit_log,
    get_session,
    init_db,
    list_sessions,
    log_human_decision,
    update_session_status,
)
from backend.services.verdict_decision_handler import apply_judge_human_action
from backend.services.session_response_builder import build_session_summary, build_tab_payload

SessionAction = Literal["approve", "edit", "reject"]
TabName = Literal["agents", "research", "debate", "verdict", "audit"]


def _get_graph():
    # Import lazily to avoid forcing LLM/API env setup for simple list/read endpoints.
    from backend.graphs.debate_graph import debate_graph

    return debate_graph


def _config(session_id: str) -> Dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def _initial_state(question: str, session_id: str) -> DebateState:
    return {
        "question": question,
        "research": "",
        "pro_arguments": "",
        "con_arguments": "",
        "verdict": "",
        "execution_id": session_id,
        "human_approved": False,
        "human_edits": {},
    }


def _safe_state_snapshot(session_id: str) -> Tuple[Dict[str, Any], Tuple[str, ...]]:
    try:
        graph = _get_graph()
        snapshot = graph.get_state(_config(session_id))
    except Exception:
        return {}, tuple()

    values = dict(snapshot.values) if snapshot and snapshot.values else {}
    next_nodes = tuple(snapshot.next) if snapshot and snapshot.next else tuple()
    return values, next_nodes


def _persist_state_update(session_id: str, values: Dict[str, Any]) -> None:
    graph = _get_graph()
    try:
        graph.update_state(_config(session_id), values)
    except Exception:
        # Non-fatal: audit/session persistence still captures user actions.
        pass


def _require_session(session_id: str) -> Dict[str, Any]:
    init_db()
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Session '{session_id}' not found")
    return session


def create_debate_session(question: str) -> Dict[str, Any]:
    question = question.strip()
    if not question:
        raise ValueError("Question is required")

    init_db()
    session_id = uuid4().hex[:8]
    create_session(session_id, question)
    return get_session_summary(session_id)


def list_debate_sessions(limit: int = 20, status: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    return list_sessions(limit=limit, status=status)


def get_session_summary(session_id: str) -> Dict[str, Any]:
    session = _require_session(session_id)
    state, next_nodes = _safe_state_snapshot(session_id)
    return build_session_summary(session=session, state=state, next_nodes=next_nodes)


def run_to_review(session_id: str) -> Dict[str, Any]:
    session = _require_session(session_id)
    graph = _get_graph()
    config = _config(session_id)

    update_session_status(session_id, "running")
    state, _ = _safe_state_snapshot(session_id)

    stream_input: Optional[Dict[str, Any]]
    if state:
        stream_input = None
    else:
        stream_input = _initial_state(session["question"], session_id)

    for _ in graph.stream(stream_input, config, stream_mode="values"):
        pass

    update_session_status(session_id, "awaiting_review")
    return get_session_summary(session_id)


def run_judge(session_id: str) -> Dict[str, Any]:
    _require_session(session_id)
    graph = _get_graph()
    config = _config(session_id)

    state, _ = _safe_state_snapshot(session_id)
    if not state.get("pro_arguments") or not state.get("con_arguments"):
        run_to_review(session_id)

    state, _ = _safe_state_snapshot(session_id)
    if not state.get("verdict"):
        for _ in graph.stream(None, config, stream_mode="values"):
            pass

    update_session_status(session_id, "awaiting_human_verdict")
    return get_session_summary(session_id)


def apply_human_decision(
    session_id: str,
    action: SessionAction,
    user_opinion: Optional[str] = None,
    edit_summary: Optional[str] = None,
) -> Dict[str, Any]:
    _require_session(session_id)
    state, _ = _safe_state_snapshot(session_id)

    if not state.get("verdict"):
        run_judge(session_id)
        state, _ = _safe_state_snapshot(session_id)

    decision_result = apply_judge_human_action(
        state=state,
        action=action,
        user_opinion=user_opinion,
        edit_summary=edit_summary,
    )

    for audit_event in decision_result["audit_events"]:
        log_human_decision(session_id, **audit_event)

    _persist_state_update(session_id, decision_result["state_update"])
    update_session_status(session_id, decision_result["session_status"])

    summary_payload = get_session_summary(session_id)
    return {
        "action": action,
        "session": summary_payload["session"],
        "stage_status": summary_payload["stage_status"],
        "verdict": summary_payload["state"].get("verdict", ""),
    }


def get_tab_payload(session_id: str, tab_name: TabName) -> Dict[str, Any]:
    summary = get_session_summary(session_id)
    audit_entries = get_audit_log(session_id)
    return build_tab_payload(
        summary=summary,
        tab_name=tab_name,
        audit_entries=audit_entries,
    )
