export type SessionStatus =
  | "created"
  | "running"
  | "awaiting_review"
  | "awaiting_human_verdict"
  | "completed"
  | "failed"
  | "cancelled";

export type StageStatusMap = {
  research: string;
  pro_con: string;
  review: string;
  judge: string;
  done: string;
};

export type SessionInfo = {
  session_id: string;
  question: string;
  start_time: string;
  end_time: string | null;
  status: SessionStatus;
};

export type SessionSummary = {
  session: SessionInfo;
  stage_status: StageStatusMap;
  metrics: {
    sources: number;
    arguments_points: number;
    runtime_sec: number | null;
  };
  next_nodes: string[];
  state: {
    question: string;
    research: string;
    pro_arguments: string;
    con_arguments: string;
    verdict: string;
  };
};

export type TabKey = "agents" | "research" | "debate" | "verdict" | "audit";

export type HumanDecisionResponse = {
  action: "approve" | "edit" | "reject";
  session: SessionInfo;
  stage_status: StageStatusMap;
  verdict: string;
};

export type TabPayloadResponse<T = any> = {
  payload: T;
};
