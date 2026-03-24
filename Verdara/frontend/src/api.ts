import axios from "axios";
import { HumanDecisionResponse, SessionSummary, TabKey, TabPayloadResponse } from "./types";

const api = axios.create({
  baseURL: "/",
});

export async function createSession(question: string): Promise<SessionSummary> {
  const { data } = await api.post<SessionSummary>("/api/sessions", { question });
  return data;
}

export async function getSession(sessionId: string): Promise<SessionSummary> {
  const { data } = await api.get<SessionSummary>(`/api/sessions/${sessionId}`);
  return data;
}

export async function listSessions() {
  const { data } = await api.get<{ sessions: Array<SessionSummary["session"]> }>("/api/sessions");
  return data.sessions;
}

export async function runToReview(sessionId: string): Promise<SessionSummary> {
  const { data } = await api.post<SessionSummary>(`/api/sessions/${sessionId}/run-to-review`);
  return data;
}

export async function runJudge(sessionId: string): Promise<SessionSummary> {
  const { data } = await api.post<SessionSummary>(`/api/sessions/${sessionId}/run-judge`);
  return data;
}

export async function decide(
  sessionId: string,
  action: "approve" | "edit" | "reject",
  userOpinion?: string,
  editSummary?: string
): Promise<HumanDecisionResponse> {
  const { data } = await api.post<HumanDecisionResponse>(`/api/sessions/${sessionId}/decision`, {
    action,
    user_opinion: userOpinion,
    edit_summary: editSummary,
  });
  return data;
}

export async function getTab(sessionId: string, tab: TabKey) {
  const { data } = await api.get<TabPayloadResponse>(`/api/sessions/${sessionId}/tabs/${tab}`);
  return data.payload;
}
