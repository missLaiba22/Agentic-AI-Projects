import { useEffect, useMemo, useState } from "react";
import {
  createSession,
  decide,
  getSession,
  getTab,
  listSessions,
  runJudge,
  runToReview,
} from "./api";
import { SessionSummary, TabKey } from "./types";

const tabs: TabKey[] = ["agents", "research", "debate", "verdict", "audit"];
const pipelineOrder: Array<keyof SessionSummary["stage_status"]> = [
  "research",
  "pro_con",
  "review",
  "judge",
  "done",
];

type VerdictSection = {
  decision: string;
  rationale: string;
  reasons: string[];
  weaknesses: string[];
  winner: "pro" | "con" | "balanced";
  raw: string;
};

function getArgumentLines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function extractMainClaim(text: string): string {
  const lines = getArgumentLines(text);
  if (!lines.length) return "No claim available.";

  const explicit = lines.find(
    (line) =>
      /^\*?\*?\s*main claim/i.test(line) ||
      /^\*?\*?\s*main argument/i.test(line) ||
      /^\*?\*?\s*thesis/i.test(line)
  );

  const base = explicit || lines[0];
  return base.replace(/^[-*\d.)\s]+/, "").replace(/^\*+|\*+$/g, "").trim();
}

function extractKeyPoints(text: string, limit = 4): string[] {
  const lines = getArgumentLines(text);
  const points = lines
    .filter((line) => /^[-*]|^\d+[.)]/.test(line) || /^\*\*.*\*\*$/.test(line))
    .map((line) => line.replace(/^[-*\d.)\s]+/, "").replace(/^\*+|\*+$/g, "").trim())
    .filter(Boolean);

  if (points.length) return points.slice(0, limit);

  const fallback = lines.slice(1, 1 + limit).map((line) => line.replace(/^\*+|\*+$/g, "").trim());
  return fallback.length ? fallback : ["No key points extracted."];
}

function compactText(text: string, maxChars = 220): string {
  const compact = text
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .replace(/#+\s*/g, "")
    .replace(/\s+/g, " ")
    .trim();
  if (!compact) return "";
  if (compact.length <= maxChars) return compact;
  return `${compact.slice(0, maxChars)}...`;
}

function normalizeBulletLine(line: string): string {
  return line
    .replace(/^[-*\d.)\s]+/, "")
    .replace(/^\*+|\*+$/g, "")
    .trim();
}

function headingKey(text: string): string {
  return text.toLowerCase().replace(/[^a-z\s]/g, " ").replace(/\s+/g, " ").trim();
}

function sentenceChunks(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((chunk) => chunk.trim())
    .filter(Boolean);
}

function pointsFromLines(lines: string[], maxPoints = 4): string[] {
  const bulletPoints = lines
    .filter((line) => /^[-*]\s+/.test(line) || /^\d+[.)]\s+/.test(line))
    .map((line) => normalizeBulletLine(line))
    .filter(Boolean);

  if (bulletPoints.length > 0) {
    return bulletPoints.slice(0, maxPoints);
  }

  const paragraphLines = lines
    .map((line) => line.replace(/^\*+|\*+$/g, "").trim())
    .filter(Boolean);

  const sentences = paragraphLines.flatMap((line) => sentenceChunks(line));
  return sentences.slice(0, maxPoints);
}

function findSectionLines(sections: Array<[string, string[]]>, preferredKeys: string[]): string[] {
  for (const preferred of preferredKeys) {
    const found = sections.find(([key]) => key.includes(preferred));
    if (found) return found[1];
  }
  return [];
}

function buildVerdictDigest(text: string): VerdictSection {
  if (!text.trim()) {
    return {
      decision: "Verdict pending",
      rationale: "Run judge after review to generate the final decision.",
      reasons: [],
      weaknesses: [],
      winner: "balanced",
      raw: "",
    };
  }

  const sectionMap = new Map<string, string[]>();
  sectionMap.set("overview", []);
  let currentKey = "overview";

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (!line || line === "---") continue;

    const headingMatch = line.match(/^#{1,6}\s*(.+)$/) || line.match(/^\*\*(.+?)\*\*$/);
    if (headingMatch) {
      currentKey = headingKey(headingMatch[1]);
      if (!sectionMap.has(currentKey)) {
        sectionMap.set(currentKey, []);
      }
      continue;
    }

    const target = sectionMap.get(currentKey) || [];
    target.push(line);
    sectionMap.set(currentKey, target);
  }

  const sectionEntries = Array.from(sectionMap.entries());
  const overviewLines = sectionMap.get("overview") || [];
  const proLines = findSectionLines(sectionEntries, ["strong points from pro", "pro", "in favor"]);
  const conLines = findSectionLines(sectionEntries, ["strong points from con", "con", "against"]);
  const weaknessLines = findSectionLines(sectionEntries, ["weaknesses on each side", "weaknesses", "weak points"]);
  const finalLines = findSectionLines(sectionEntries, ["final verdict", "verdict"]);
  const reasoningLines = findSectionLines(sectionEntries, ["reasoning", "rationale", "because"]);

  let decision = pointsFromLines(finalLines, 2)[0] || "Balanced evaluation";
  if (!decision || /^(final verdict|verdict)$/i.test(decision)) {
    const winnerMatch = text.match(/\b(pro|con)\s+(argument|side)\s+is\s+(currently\s+)?stronger\b/i);
    decision = winnerMatch
      ? `${winnerMatch[1].charAt(0).toUpperCase()}${winnerMatch[1].slice(1).toLowerCase()} side stronger`
      : "Balanced evaluation";
  }

  const rationaleCandidates = [...pointsFromLines(reasoningLines, 2), ...pointsFromLines(overviewLines, 2)];
  const rationale = rationaleCandidates[0] || "The judge provided an evidence-based comparison of both sides.";

  const winner: "pro" | "con" | "balanced" = /\bpro\b/i.test(decision)
    ? "pro"
    : /\bcon\b/i.test(decision)
      ? "con"
      : "balanced";

  let reasons = pointsFromLines(reasoningLines, 4);
  if (!reasons.length) {
    const winnerPoints = winner === "pro" ? pointsFromLines(proLines, 2) : pointsFromLines(conLines, 2);
    const otherPoints = winner === "pro" ? pointsFromLines(conLines, 1) : pointsFromLines(proLines, 1);
    reasons = [...winnerPoints, ...otherPoints];
  }

  const weaknesses = pointsFromLines(weaknessLines, 3);

  return {
    decision,
    rationale: compactText(rationale, 200),
    reasons,
    weaknesses,
    winner,
    raw: text,
  };
}

function App() {
  const [question, setQuestion] = useState("Should AI be used to replace traditional school exams?");
  const [session, setSession] = useState<SessionSummary | null>(null);
  const [sessions, setSessions] = useState<Array<SessionSummary["session"]>>([]);
  const [activeTab, setActiveTab] = useState<TabKey>("debate");
  const [tabData, setTabData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [reviewerOpinion, setReviewerOpinion] = useState("");

  const isTerminal =
    session?.session.status === "completed" ||
    session?.session.status === "failed" ||
    session?.session.status === "cancelled";

  const statusLabel = useMemo(() => {
    if (!session) return "idle";
    if (session.session.status === "awaiting_human_verdict") return "awaiting human verdict";
    return session.session.status.replace(/_/g, " ");
  }, [session]);

  const currentVerdictText = useMemo(
    () => (tabData?.verdict || session?.state.verdict || "").trim(),
    [tabData?.verdict, session?.state.verdict]
  );

  const verdictDigest = useMemo(() => buildVerdictDigest(currentVerdictText), [currentVerdictText]);

  const winnerChipText = useMemo(() => {
    if (verdictDigest.winner === "pro") return "Pro stronger";
    if (verdictDigest.winner === "con") return "Con stronger";
    return "Balanced";
  }, [verdictDigest.winner]);

  const verdictStageText = useMemo(() => {
    if (!session) return "";
    if (session.session.status === "awaiting_human_verdict") {
      return "Judge draft is ready. Approve, reject for regeneration, or provide your opinion to refine.";
    }
    if (session.session.status === "completed") {
      return "Final verdict has been approved and stored.";
    }
    return "Verdict not available yet. Run judge from the Debate tab after review.";
  }, [session]);

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const rows = await listSessions();
        setSessions(rows);
      } catch {
        // Keep UI usable even if history load fails.
      }
    };

    void loadSessions();
  }, []);

  useEffect(() => {
    if (!session?.session.session_id) return;

    const fetchTab = async () => {
      try {
        const data = await getTab(session.session.session_id, activeTab);
        setTabData(data);
      } catch {
        setTabData(null);
      }
    };

    void fetchTab();
  }, [activeTab, session?.session.session_id]);

  useEffect(() => {
    if (!session || isTerminal) return;

    const id = window.setInterval(async () => {
      try {
        const next = await getSession(session.session.session_id);
        setSession(next);
      } catch {
        // Ignore transient polling errors.
      }
    }, 2000);

    return () => window.clearInterval(id);
  }, [session, isTerminal]);

  const refreshSessions = async () => {
    const rows = await listSessions();
    setSessions(rows);
  };

  const handleStart = async () => {
    setError(null);
    setLoading(true);
    setEditMode(false);
    try {
      const created = await createSession(question);
      setSession(created);

      const reviewed = await runToReview(created.session.session_id);
      setSession(reviewed);
      setReviewerOpinion("");

      // Auto-continue to judge so users get a verdict without an extra manual step.
      const judged = await runJudge(created.session.session_id);
      setSession(judged);
      setActiveTab("verdict");

      await refreshSessions();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to start debate pipeline.");
    } finally {
      setLoading(false);
    }
  };

  const handleRunJudge = async () => {
    if (!session) return;

    setActionLoading(true);
    setError(null);
    try {
      const judged = await runJudge(session.session.session_id);
      setSession(judged);
      setReviewerOpinion("");
      setActiveTab("verdict");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Judge run failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectBeforeJudge = async () => {
    setActionLoading(true);
    setError(null);
    try {
      const created = await createSession(question);
      const reviewed = await runToReview(created.session.session_id);
      setSession(reviewed);
      setReviewerOpinion("");
      setActiveTab("debate");
      await refreshSessions();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not rerun review stage.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    setError(null);
    setLoading(true);
    setEditMode(false);
    try {
      const data = await getSession(sessionId);
      setSession(data);
      setReviewerOpinion("");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not load session.");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!session) return;
    setActionLoading(true);
    setError(null);
    try {
      await decide(session.session.session_id, "approve");
      const refreshed = await getSession(session.session.session_id);
      setSession(refreshed);
      setEditMode(false);
      await refreshSessions();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Approve action failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!session) return;
    setActionLoading(true);
    setError(null);
    try {
      await decide(session.session.session_id, "reject");
      const refreshed = await getSession(session.session.session_id);
      setSession(refreshed);
      setReviewerOpinion("");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Regenerate action failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!session) return;
    setActionLoading(true);
    setError(null);
    try {
      await decide(session.session.session_id, "edit", reviewerOpinion, "Verdict refined from human opinion");
      const refreshed = await getSession(session.session.session_id);
      setSession(refreshed);
      setEditMode(false);
      setReviewerOpinion("");
      await refreshSessions();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Edit action failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const selectedSessionId = session?.session.session_id;

  return (
    <div className="app-shell">
      <div className="backdrop back-a" aria-hidden="true" />
      <div className="backdrop back-b" aria-hidden="true" />
      <div className="layout-grid">
        <aside className="sidebar">
          <div className="brand-block">
            <span className="brand-mark">V</span>
            <div>
              <h1>Verdara</h1>
              <p>Human-supervised debate workflow</p>
            </div>
          </div>

          <section className="panel history-panel reveal delay-1">
            <div className="panel-head">
              <h2>Past Sessions</h2>
              <span>{sessions.length}</span>
            </div>
            <ul className="history-list">
              {sessions.map((row, idx) => (
                <li key={row.session_id} style={{ ["--item-index" as any]: idx }}>
                  <button
                    className={row.session_id === selectedSessionId ? "session-item active" : "session-item"}
                    onClick={() => handleSelectSession(row.session_id)}
                  >
                    <strong>{row.question}</strong>
                    <div>
                      <span>{row.session_id}</span>
                      <em>{row.status.replace(/_/g, " ")}</em>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </aside>

        <main className="main-pane">
          <section className="panel composer-panel reveal delay-1">
            <p className="label">New Session</p>
            <div className="composer-row">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={3}
                placeholder="Type your debate question to start a new pipeline"
              />
              <button className="primary" disabled={loading || !question.trim()} onClick={handleStart}>
                {loading ? "Running..." : "Start Pipeline"}
              </button>
            </div>
          </section>

          {error && <div className="error-banner">{error}</div>}

          {!session && (
            <section className="panel empty-panel reveal delay-2">
              <h2>No Active Session</h2>
              <p>Start a new debate above, or choose a past session from the sidebar history.</p>
            </section>
          )}

          {session && (
            <>
              <section className="panel session-overview reveal delay-2">
                <div>
                  <p className="label">Current Question</p>
                  <h2>{session.state.question || session.session.question}</h2>
                </div>
                <div className="overview-chips">
                  <span>{session.metrics.sources} sources</span>
                  <span>{session.metrics.arguments_points} points</span>
                  <span>{statusLabel}</span>
                </div>
              </section>

              <section className="panel pipeline-panel reveal delay-3">
                {pipelineOrder.map((key) => {
                  const state = session.stage_status[key];
                  const done = state === "completed";
                  const paused = state === "paused";
                  return (
                    <div className="pipeline-node" key={key}>
                      <div className={`node-indicator ${done ? "done" : ""} ${paused ? "paused" : ""}`}>
                        {done ? "✓" : paused ? "!" : "•"}
                      </div>
                      <p>{key.replace(/_/g, "/")}</p>
                    </div>
                  );
                })}
              </section>

              <section className="panel tabs-panel reveal delay-4">
                <nav className="tab-nav">
                  {tabs.map((tab) => (
                    <button
                      key={tab}
                      className={activeTab === tab ? "active" : ""}
                      onClick={() => setActiveTab(tab)}
                    >
                      {tab}
                    </button>
                  ))}
                </nav>

                <div key={activeTab} className="tab-content tab-transition">
                  {activeTab === "agents" && (
                    <ul className="list-grid">
                      {(tabData?.agents ?? []).map((agent: any) => (
                        <li key={agent.id}>
                          <strong>{agent.name}</strong>
                          <span>{agent.status}</span>
                        </li>
                      ))}
                    </ul>
                  )}

                  {activeTab === "research" && (
                    <ul className="research-list">
                      {(tabData?.sources ?? []).map((src: any) => (
                        <li key={src.rank}>
                          <h4>
                            {src.rank}. {src.title}
                          </h4>
                          <p>{src.snippet}</p>
                          <a href={src.url} target="_blank" rel="noreferrer">
                            {src.url}
                          </a>
                        </li>
                      ))}
                    </ul>
                  )}

                  {activeTab === "debate" && (
                    <div className="debate-grid">
                      <article className="argument-card pro">
                        <div className="debate-head">
                          <h4>Pro arguments</h4>
                          <span>{tabData?.pro?.points ?? 0} points</span>
                        </div>
                        <p className="mini-label">Main claim</p>
                        <p className="main-claim">{extractMainClaim(tabData?.pro?.text || "")}</p>
                        <p className="mini-label">Key points</p>
                        <ul className="key-points">
                          {extractKeyPoints(tabData?.pro?.text || "").map((point, idx) => (
                            <li key={`pro-point-${idx}`}>{point}</li>
                          ))}
                        </ul>
                      </article>

                      <article className="argument-card con">
                        <div className="debate-head">
                          <h4>Con arguments</h4>
                          <span>{tabData?.con?.points ?? 0} points</span>
                        </div>
                        <p className="mini-label">Main claim</p>
                        <p className="main-claim">{extractMainClaim(tabData?.con?.text || "")}</p>
                        <p className="mini-label">Key points</p>
                        <ul className="key-points">
                          {extractKeyPoints(tabData?.con?.text || "").map((point, idx) => (
                            <li key={`con-point-${idx}`}>{point}</li>
                          ))}
                        </ul>
                      </article>

                      {session.session.status === "awaiting_review" && (
                        <article className="review-card">
                          <h4>Human review required</h4>
                          <p>
                            This state exists because the graph has a human-in-the-loop pause before judge.
                            Use approve to continue or reject to rerun review.
                          </p>
                          <div className="actions-row">
                            <button onClick={handleRunJudge} disabled={actionLoading}>
                              Approve and run judge
                            </button>
                            <button onClick={handleRejectBeforeJudge} disabled={actionLoading}>
                              Reject and rerun review
                            </button>
                          </div>
                        </article>
                      )}
                    </div>
                  )}

                  {activeTab === "verdict" && (
                    <div className="verdict-panel">
                      <p className="workflow-note">{verdictStageText}</p>

                      {session.session.status !== "awaiting_human_verdict" && !isTerminal && (
                        <p className="hint-text">
                          Judge has not been run yet. Go to Debate tab and approve to run judge.
                        </p>
                      )}

                      {!editMode ? (
                        <div className="verdict-layout">
                          <section className="verdict-hero">
                            <p className="mini-label">
                              {session.session.status === "awaiting_human_verdict"
                                ? "Draft verdict"
                                : "Final verdict"}
                            </p>
                            <div className="verdict-title-row">
                              <h3>{verdictDigest.decision}</h3>
                              <span className={`winner-chip ${verdictDigest.winner}`}>{winnerChipText}</span>
                            </div>
                            <p>{verdictDigest.rationale}</p>
                          </section>

                          <section className="verdict-summary-grid">
                            <article className="verdict-summary-card">
                              <h4>Supporting reasons</h4>
                              {verdictDigest.reasons.length > 0 ? (
                                <ul>
                                  {verdictDigest.reasons.slice(0, 3).map((reason, idx) => (
                                    <li key={`reason-${idx}`}>{compactText(reason, 170)}</li>
                                  ))}
                                </ul>
                              ) : (
                                <p>No reasons were extracted yet.</p>
                              )}
                            </article>

                            <article className="verdict-summary-card">
                              <h4>Weaknesses and trade-offs</h4>
                              {verdictDigest.weaknesses.length > 0 ? (
                                <ul>
                                  {verdictDigest.weaknesses.slice(0, 3).map((risk, idx) => (
                                    <li key={`risk-${idx}`}>{compactText(risk, 170)}</li>
                                  ))}
                                </ul>
                              ) : (
                                <p>No notable weaknesses were extracted.</p>
                              )}
                            </article>
                          </section>

                          {currentVerdictText && (
                            <details className="raw-verdict">
                              <summary>View full judge text</summary>
                              <pre>{verdictDigest.raw}</pre>
                            </details>
                          )}
                        </div>
                      ) : (
                        <div className="edit-opinion-panel">
                          <p className="mini-label">Current judge draft</p>
                          <pre className="readonly-draft">
                            {currentVerdictText || "No draft verdict available."}
                          </pre>
                          <p className="mini-label">Your opinion / instruction for final verdict</p>
                          <textarea
                            value={reviewerOpinion}
                            onChange={(e) => setReviewerOpinion(e.target.value)}
                            rows={8}
                            placeholder="Example: Keep Con stronger, but make the final verdict shorter and more direct."
                          />
                        </div>
                      )}

                      <div className="actions-row">
                        <button
                          onClick={handleApprove}
                          disabled={actionLoading || isTerminal || session.session.status !== "awaiting_human_verdict"}
                        >
                          Approve as final
                        </button>
                        <button
                          onClick={handleRegenerate}
                          disabled={actionLoading || isTerminal || session.session.status !== "awaiting_human_verdict"}
                        >
                          Reject and regenerate
                        </button>
                        {!editMode ? (
                          <button
                            onClick={() => setEditMode(true)}
                            disabled={
                              actionLoading || isTerminal || session.session.status !== "awaiting_human_verdict"
                            }
                          >
                            Give opinion for final verdict
                          </button>
                        ) : (
                          <button onClick={handleSaveEdit} disabled={actionLoading || !reviewerOpinion.trim()}>
                            Generate final verdict
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {activeTab === "audit" && (
                    <ul className="audit-list">
                      {(tabData?.entries ?? []).map((entry: any, idx: number) => (
                        <li key={`${entry.timestamp}-${idx}`}>
                          <p>{entry.action}</p>
                          <small>{entry.timestamp}</small>
                          {entry.edit_summary && <span>{entry.edit_summary}</span>}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
