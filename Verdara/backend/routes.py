from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas.schemas import (
    CreateSessionRequest,
    HumanDecisionRequest,
    HumanDecisionResponse,
    SessionListResponse,
    SessionStatusResponse,
    SessionSummaryResponse,
    TabPayloadResponse,
)
from backend.services.session_orchestrator import (
    apply_human_decision,
    create_debate_session,
    get_session_summary,
    get_tab_payload,
    list_debate_sessions,
    run_judge,
    run_to_review,
)

app = FastAPI(
    title="Verdara API",
    version="0.1.0",
    description="Debate orchestration API for Verdara frontend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/sessions")
def create_session(payload: CreateSessionRequest) -> SessionSummaryResponse:
    try:
        return create_debate_session(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/sessions")
def get_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
) -> SessionListResponse:
    sessions = list_debate_sessions(limit=limit, status=status)
    return {"sessions": sessions, "count": len(sessions)}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> SessionSummaryResponse:
    try:
        return get_session_summary(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/run-to-review")
def execute_to_review(session_id: str) -> SessionSummaryResponse:
    try:
        return run_to_review(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Execution failed: {exc}") from exc


@app.post("/api/sessions/{session_id}/run-judge")
def execute_judge(session_id: str) -> SessionSummaryResponse:
    try:
        return run_judge(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Judge run failed: {exc}") from exc


@app.post("/api/sessions/{session_id}/decision")
def decide(session_id: str, payload: HumanDecisionRequest) -> HumanDecisionResponse:
    try:
        return apply_human_decision(
            session_id=session_id,
            action=payload.action,
            user_opinion=payload.user_opinion,
            edit_summary=payload.edit_summary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Decision failed: {exc}") from exc


@app.get("/api/sessions/{session_id}/status")
def get_status(session_id: str) -> SessionStatusResponse:
    try:
        summary = get_session_summary(session_id)
        return {
            "session": summary["session"],
            "stage_status": summary["stage_status"],
            "metrics": summary["metrics"],
            "next_nodes": summary["next_nodes"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/sessions/{session_id}/tabs/{tab_name}")
def get_tab(session_id: str, tab_name: str) -> TabPayloadResponse:
    valid_tabs = {"agents", "research", "debate", "verdict", "audit"}
    if tab_name not in valid_tabs:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tab '{tab_name}'. Valid tabs: {sorted(valid_tabs)}",
        )

    try:
        return {"payload": get_tab_payload(session_id, tab_name)}  # type: ignore[arg-type]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
