"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, CheckCircle2, Clock, Loader2,
  AlertCircle, Sparkles, RefreshCw, ExternalLink,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface PipelineStage {
  id: string;
  label: string;
}

interface StatusData {
  stage: string;
  message: string;
  progress: number;
  updated_at?: number;
  error?: string;
  stages?: PipelineStage[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STAGE_ORDER = ["extracting", "prompts", "combining", "done"];

const STAGE_LABELS: Record<string, string> = {
  upload:     "Video uploaded",
  extracting: "Extracting viral clips",
  prompts:    "Generating AI prompts",
  combining:  "Combining clips",
  done:       "Pipeline complete",
};

// ── Main Component ────────────────────────────────────────────────────────────

export default function StatusPage() {
  const params = useParams();
  const game = params.game as string;

  const [status, setStatus] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState(Date.now());

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/process/status/${game}`, { headers: { "ngrok-skip-browser-warning": "1" } });
      if (res.status === 404) {
        setStatus({ stage: "idle", message: "No pipeline started yet. Upload a video first.", progress: 0 });
        setError(null);
        setLoading(false);
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: StatusData = await res.json();
      setStatus(data);
      setError(null);
    } catch (e) {
      setError("Could not reach the backend. Make sure it's running.");
    } finally {
      setLoading(false);
    }
  }, [game]);

  // Auto-poll every 3 s while not done/error
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      if (status?.stage !== "done" && status?.stage !== "error") {
        fetchStatus();
        setLastRefresh(Date.now());
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [fetchStatus, status?.stage]);

  const isDone  = status?.stage === "done";
  const isError = status?.stage === "error";
  const isActive = !isDone && !isError && status?.stage !== "idle";

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen pt-8 px-6 sm:px-12 pb-24 flex flex-col items-center">
      <div className="w-full max-w-2xl mb-8 flex items-center justify-between">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Dashboard
        </Link>
        <button
          onClick={() => { fetchStatus(); setLastRefresh(Date.now()); }}
          className="inline-flex items-center gap-2 text-xs text-zinc-600 hover:text-white transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 glow-badge px-3.5 py-1.5 rounded-full text-xs font-medium mb-4">
            <Sparkles className="w-3 h-3" />
            Project Status
          </div>
          <h1 className="text-3xl font-bold text-white">
            Processing <span className="gradient-text-primary">{game}</span>
          </h1>
          <p className="text-zinc-500 mt-1">
            {isActive ? "Pipeline is running — updates every 3 seconds." : isDone ? "Your shorts are ready!" : "Waiting for pipeline to start."}
          </p>
        </div>

        {loading && (
          <div className="glass rounded-2xl p-10 flex items-center justify-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
            <span className="text-zinc-400 text-sm">Loading status…</span>
          </div>
        )}

        {!loading && error && (
          <div className="glass rounded-2xl p-8 border border-red-500/20 text-center">
            <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
            <p className="text-white font-medium mb-1">Connection error</p>
            <p className="text-sm text-zinc-500">{error}</p>
            <button
              onClick={fetchStatus}
              className="mt-4 btn-secondary px-5 py-2.5 rounded-xl text-sm inline-flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" /> Retry
            </button>
          </div>
        )}

        {!loading && status && !error && (
          <AnimatePresence mode="wait">
            <motion.div
              key={status.stage}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* Overall progress card */}
              <div className="glass rounded-2xl p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-1">Current stage</p>
                    <p className="text-lg font-semibold text-white">
                      {STAGE_LABELS[status.stage] ?? status.stage}
                    </p>
                    <p className="text-sm text-zinc-400 mt-1">{status.message}</p>
                  </div>
                  <StatusBadge stage={status.stage} />
                </div>

                {/* Progress bar */}
                <div className="mt-5">
                  <div className="flex justify-between text-xs text-zinc-500 mb-2">
                    <span>Progress</span>
                    <span className="tabular-nums font-medium text-white">{status.progress}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
                    <motion.div
                      className={`h-full rounded-full ${isError ? "bg-red-500" : isDone ? "bg-green-500" : "bg-gradient-to-r from-purple-500 to-pink-500"}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${status.progress}%` }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                    />
                  </div>
                </div>

                {/* GPT-4o slow warning */}
                {status.stage === "extracting" && status.progress < 45 && (
                  <div className="mt-4 p-3 rounded-xl bg-amber-500/8 border border-amber-500/20 flex items-start gap-2.5">
                    <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin mt-0.5 shrink-0" />
                    <p className="text-xs text-amber-400/80 leading-relaxed">
                      GPT-4o Vision is analyzing your gameplay frames. This typically takes <strong className="text-amber-400">3-8 minutes</strong> — the page auto-updates every 3 seconds.
                    </p>
                  </div>
                )}

                {status.error && (
                  <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                    <p className="text-xs text-red-400 font-mono">{status.error}</p>
                  </div>
                )}

                {status.updated_at && (
                  <p className="text-xs text-zinc-700 mt-4">
                    Last updated: {new Date(status.updated_at * 1000).toLocaleTimeString()}
                  </p>
                )}
              </div>

              {/* Pipeline stages timeline */}
              <div className="glass rounded-2xl p-6">
                <p className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-5">Pipeline stages</p>
                <div className="space-y-0">
                  {STAGE_ORDER.map((stageId, i) => {
                    const currentIdx = STAGE_ORDER.indexOf(status.stage);
                    const stageIdx   = i;
                    const isDoneStage    = isDone || stageIdx < currentIdx;
                    const isCurrentStage = stageId === status.stage && !isDone;
                    const isPendingStage = stageIdx > currentIdx && !isDone;

                    return (
                      <div key={stageId} className="flex gap-4">
                        {/* Timeline dot + line */}
                        <div className="flex flex-col items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-all
                            ${isDoneStage ? "bg-green-500/20 border border-green-500/40" :
                              isCurrentStage ? "bg-purple-500/20 border border-purple-500/60" :
                                "bg-zinc-800/60 border border-zinc-700/40"}`}
                          >
                            {isDoneStage ? (
                              <CheckCircle2 className="w-4 h-4 text-green-400" />
                            ) : isCurrentStage ? (
                              <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                            ) : (
                              <Clock className="w-4 h-4 text-zinc-600" />
                            )}
                          </div>
                          {i < STAGE_ORDER.length - 1 && (
                            <div className={`w-px flex-1 my-1 ${isDoneStage ? "bg-green-500/30" : "bg-zinc-800"}`} style={{ minHeight: 24 }} />
                          )}
                        </div>

                        {/* Label */}
                        <div className={`pb-6 pt-1 ${i === STAGE_ORDER.length - 1 ? "pb-0" : ""}`}>
                          <p className={`text-sm font-medium leading-none mb-1
                            ${isDoneStage ? "text-green-400" : isCurrentStage ? "text-white" : "text-zinc-600"}`}
                          >
                            {STAGE_LABELS[stageId]}
                          </p>
                          {isCurrentStage && (
                            <p className="text-xs text-zinc-500">{status.message}</p>
                          )}
                          {isDoneStage && stageId !== "done" && (
                            <p className="text-xs text-zinc-600">Completed</p>
                          )}
                          {isPendingStage && (
                            <p className="text-xs text-zinc-700">Pending</p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Done CTA */}
              {isDone && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="glass rounded-2xl p-6 border border-green-500/20 text-center"
                >
                  <div className="w-14 h-14 rounded-2xl bg-green-500/15 flex items-center justify-center mx-auto mb-4">
                    <CheckCircle2 className="w-7 h-7 text-green-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1">Shorts ready!</h3>
                  <p className="text-sm text-zinc-500 mb-5">
                    Your clips are in <code className="text-green-400 bg-green-500/10 px-1.5 py-0.5 rounded text-xs">games/{game}/clips/</code>
                  </p>
                  <div className="flex justify-center gap-3">
                    <Link href="/" className="btn-secondary px-5 py-2.5 rounded-xl text-sm flex items-center gap-2">
                      <ArrowLeft className="w-4 h-4" /> Dashboard
                    </Link>
                    <Link href="/upload" className="btn-premium px-5 py-2.5 rounded-xl text-sm flex items-center gap-2">
                      <Sparkles className="w-4 h-4" /> New Project
                    </Link>
                  </div>
                </motion.div>
              )}

              {/* Error CTA */}
              {isError && (
                <div className="glass rounded-2xl p-6 border border-red-500/20 text-center">
                  <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold text-white mb-1">Pipeline failed</h3>
                  <p className="text-sm text-zinc-500 mb-5">{status.error ?? "An unexpected error occurred."}</p>
                  <Link href="/upload" className="btn-premium px-6 py-3 rounded-xl text-sm inline-flex items-center gap-2">
                    <ExternalLink className="w-4 h-4" /> Try again
                  </Link>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatusBadge({ stage }: { stage: string }) {
  if (stage === "done") return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full bg-green-500/15 border border-green-500/30 text-green-400">
      <CheckCircle2 className="w-3.5 h-3.5" /> Done
    </span>
  );
  if (stage === "error") return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full bg-red-500/15 border border-red-500/30 text-red-400">
      <AlertCircle className="w-3.5 h-3.5" /> Error
    </span>
  );
  if (stage === "idle") return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700 text-zinc-500">
      <Clock className="w-3.5 h-3.5" /> Idle
    </span>
  );
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full bg-purple-500/15 border border-purple-500/30 text-purple-400">
      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Running
    </span>
  );
}
