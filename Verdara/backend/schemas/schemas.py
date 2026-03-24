from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class HumanDecisionRequest(BaseModel):
    action: Literal["approve", "edit", "reject"]
    user_opinion: Optional[str] = None
    edit_summary: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    question: str
    start_time: str
    end_time: Optional[str] = None
    status: str


class StageStatusMap(BaseModel):
    research: str
    pro_con: str
    review: str
    judge: str
    done: str


class SessionMetrics(BaseModel):
    sources: int
    arguments_points: int
    runtime_sec: Optional[int] = None


class SessionState(BaseModel):
    question: str
    research: str
    pro_arguments: str
    con_arguments: str
    verdict: str


class SessionSummaryResponse(BaseModel):
    session: SessionInfo
    stage_status: StageStatusMap
    metrics: SessionMetrics
    next_nodes: List[str]
    state: SessionState


class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
    count: int


class HumanDecisionResponse(BaseModel):
    action: Literal["approve", "edit", "reject"]
    session: SessionInfo
    stage_status: StageStatusMap
    verdict: str


class SessionStatusResponse(BaseModel):
    session: SessionInfo
    stage_status: StageStatusMap
    metrics: SessionMetrics
    next_nodes: List[str]


class TabPayloadResponse(BaseModel):
    # Tab payload is intentionally flexible while UI contracts evolve.
    payload: Dict[str, Any]
