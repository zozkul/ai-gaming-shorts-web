"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  UploadCloud, FileVideo, Loader2, CheckCircle2, Sparkles,
  ArrowLeft, ArrowRight, Monitor, Mic, ChevronRight,
  Youtube, Instagram, Music2, Tv2, X, Settings2, MessageSquare,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

const PLATFORMS = [
  { id: "tiktok", label: "TikTok", icon: <Music2 className="w-4 h-4" /> },
  { id: "youtube", label: "YouTube Shorts", icon: <Youtube className="w-4 h-4" /> },
  { id: "instagram_reels", label: "Instagram Reels", icon: <Instagram className="w-4 h-4" /> },
  { id: "instagram_story", label: "Instagram Story", icon: <Tv2 className="w-4 h-4" /> },
];

const VOICES = [
  { id: "y8mBjGEqtMV3PO41kDm0", label: "Custom Voice", desc: "Your own trained voice" },
  { id: "pNInz4obpvDQR2KxHPt2", label: "Adam", desc: "Deep, powerful male" },
  { id: "21m00Tcm4TlvDq8ikWAM", label: "Rachel", desc: "Friendly female" },
  { id: "AZnzlk1XvdvUeBnXmlld", label: "Domi", desc: "Energetic female" },
  { id: "ErXwobaYiN019PkySvjV", label: "Antoni", desc: "Smooth male" },
];

const GAME_NAME = "default";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STEPS = ["Upload", "Clips & Platforms", "Presenter", "Voice", "Review"];

// ── Main Component ────────────────────────────────────────────────────────────

export default function UploadPage() {
  const router = useRouter();

  // Wizard state
  const [step, setStep] = useState(0);

  // Step 0 – Upload
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadDone, setUploadDone] = useState(false);

  // Step 1 – Clips & Platforms
  const [maxClips, setMaxClips] = useState(5);
  const [platforms, setPlatforms] = useState<string[]>(["tiktok"]);

  // Step 2 – Presenter Mode
  const [presenterMode, setPresenterMode] = useState<"ai_presenter" | "voiceover">("ai_presenter");

  // Step 3 – Voice (only if voiceover)
  const [commentaryMode, setCommentaryMode] = useState<"auto" | "manual">("auto");
  const [commentaryText, setCommentaryText] = useState("");
  const [voiceId, setVoiceId] = useState(VOICES[0].id);
  const [useDefaultSettings, setUseDefaultSettings] = useState(true);
  const [stability, setStability] = useState(0.5);
  const [similarity, setSimilarity] = useState(0.5);
  const [style, setStyle] = useState(0.5);
  const [speed, setSpeed] = useState(1.1);
  const [speakerBoost, setSpeakerBoost] = useState(true);

  // Step 4 – Processing
  const [isProcessing, setIsProcessing] = useState(false);
  const [processDone, setProcessDone] = useState(false);

  // ── Helpers ────────────────────────────────────────────────────────────────

  const visibleSteps = presenterMode === "voiceover" ? STEPS : STEPS.filter((s) => s !== "Voice");

  const togglePlatform = (id: string) => {
    setPlatforms((prev) =>
      prev.includes(id) ? (prev.length > 1 ? prev.filter((p) => p !== id) : prev) : [...prev, id]
    );
  };

  // ── Upload logic ───────────────────────────────────────────────────────────

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setUploadProgress(0);

    const CHUNK_SIZE = 4 * 1024 * 1024; // 4MB per chunk
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

    try {
      for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE;
        const blob = file.slice(start, start + CHUNK_SIZE);

        const formData = new FormData();
        formData.append("file", blob, file.name);
        formData.append("chunk_index", String(i));
        formData.append("total_chunks", String(totalChunks));
        formData.append("filename", file.name);

        const res = await fetch(
          `${API_BASE}/api/upload-chunk/${GAME_NAME}?chunk_index=${i}&total_chunks=${totalChunks}&filename=${encodeURIComponent(file.name)}`,
          { method: "POST", body: formData }
        );

        if (!res.ok) {
          alert("Upload failed at chunk " + i);
          setIsUploading(false);
          return;
        }

        setUploadProgress(Math.round(((i + 1) / totalChunks) * 100));
      }

      setTimeout(() => {
        setUploadDone(true);
        setIsUploading(false);
      }, 400);
    } catch {
      alert("Error connecting to backend API.");
      setIsUploading(false);
    }
  };

  // ── Start processing ────────────────────────────────────────────────────────

  const handleStartProcessing = async () => {
    if (!file) return;
    setIsProcessing(true);

    const config = {
      video_filename: file.name,
      max_clips: maxClips,
      platforms,
      presenter_mode: presenterMode,
      commentary_mode: commentaryMode,
      commentary_text: commentaryMode === "manual" ? commentaryText : null,
      voice_id: presenterMode === "voiceover" ? voiceId : null,
      voice_settings: presenterMode === "voiceover"
        ? useDefaultSettings
          ? null
          : { stability, similarity_boost: similarity, style, speed, use_speaker_boost: speakerBoost }
        : null,
    };

    try {
      const res = await fetch(`${API_BASE}/api/process/start/${GAME_NAME}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (res.ok) {
        setProcessDone(true);
        router.push(`/status/${GAME_NAME}`);
      } else {
        const data = await res.json();
        alert("Error: " + data.detail);
      }
    } catch {
      alert("Failed to start processing.");
    } finally {
      setIsProcessing(false);
    }
  };

  // ── Next / Back ────────────────────────────────────────────────────────────

  const nextStep = () => {
    if (presenterMode === "ai_presenter" && step === 2) {
      setStep(4); // skip voice step
    } else {
      setStep((s) => Math.min(s + 1, 4));
    }
  };

  const prevStep = () => {
    if (presenterMode === "ai_presenter" && step === 4) {
      setStep(2); // skip voice step going back
    } else {
      setStep((s) => Math.max(s - 1, 0));
    }
  };

  // ── Progress indicator ────────────────────────────────────────────────────

  const getStepIndex = () => {
    if (presenterMode === "ai_presenter") {
      // steps: 0,1,2,4 → map to indices 0,1,2,3
      const map: Record<number, number> = { 0: 0, 1: 1, 2: 2, 4: 3 };
      return map[step] ?? step;
    }
    return step;
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen pt-8 px-6 sm:px-12 pb-24 flex flex-col items-center">
      {/* Back */}
      <div className="w-full max-w-2xl mb-8">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>

      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 glow-badge px-3.5 py-1.5 rounded-full text-xs font-medium mb-4">
            <Sparkles className="w-3 h-3" />
            New Project
          </div>
          <h1 className="text-3xl font-bold text-white">Create Shorts</h1>
          <p className="text-zinc-500 mt-1">Upload gameplay and configure how your shorts will be generated.</p>
        </div>

        {/* Step progress bar */}
        <StepBar steps={visibleSteps} currentIndex={getStepIndex()} />

        {/* Step content */}
        <div className="mt-8">
          <AnimatePresence mode="wait">
            {step === 0 && (
              <StepPanel key="upload">
                <StepTitle icon={<UploadCloud className="w-5 h-5 text-purple-400" />} title="Upload Gameplay Video" />

                <div
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  className={`glass rounded-2xl border-2 border-dashed p-10 flex flex-col items-center text-center relative overflow-hidden transition-all
                    ${isDragging ? "border-purple-500/60 bg-purple-500/5" : "border-white/8 hover:border-white/15"}
                    ${uploadDone ? "border-green-500/40 bg-green-500/5" : ""}`}
                >
                  {isUploading && (
                    <div
                      className="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  )}

                  <input
                    type="file"
                    accept="video/*"
                    className="absolute inset-0 opacity-0 cursor-pointer"
                    onChange={handleFileChange}
                    disabled={isUploading || uploadDone}
                  />

                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-5 transition-all
                    ${uploadDone ? "bg-green-500/15" : file ? "bg-purple-500/15" : "bg-white/5"}`}
                  >
                    {uploadDone ? <CheckCircle2 className="w-7 h-7 text-green-400" /> :
                      file ? <FileVideo className="w-7 h-7 text-purple-400" /> :
                        <UploadCloud className="w-7 h-7 text-zinc-500" />}
                  </div>

                  {uploadDone ? (
                    <>
                      <p className="text-base font-semibold text-green-400 mb-1">Upload Complete!</p>
                      <p className="text-sm text-zinc-500">{file?.name}</p>
                    </>
                  ) : file ? (
                    <>
                      <p className="text-base font-semibold text-white mb-1 max-w-xs truncate">{file.name}</p>
                      <p className="text-sm text-zinc-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                    </>
                  ) : (
                    <>
                      <p className="text-base font-semibold text-white mb-1">
                        {isDragging ? "Drop it here!" : "Drag & drop or click to browse"}
                      </p>
                      <p className="text-sm text-zinc-600">MP4, MOV — up to 10 GB</p>
                    </>
                  )}
                </div>

                <div className="flex justify-between items-center mt-6">
                  {file && !uploadDone && (
                    <button
                      className="flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors"
                      onClick={() => setFile(null)}
                    >
                      <X className="w-4 h-4" /> Clear
                    </button>
                  )}
                  <div className="ml-auto flex gap-3">
                    {!uploadDone ? (
                      <button
                        className="btn-premium px-8 py-3 rounded-xl text-sm flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
                        onClick={handleUpload}
                        disabled={!file || isUploading}
                      >
                        {isUploading
                          ? <><Loader2 className="w-4 h-4 animate-spin" /> Uploading {uploadProgress}%</>
                          : <><UploadCloud className="w-4 h-4" /> Upload</>}
                      </button>
                    ) : (
                      <button
                        className="btn-premium px-8 py-3 rounded-xl text-sm flex items-center gap-2"
                        onClick={nextStep}
                      >
                        Configure <ArrowRight className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </StepPanel>
            )}

            {step === 1 && (
              <StepPanel key="clips">
                <StepTitle icon={<Settings2 className="w-5 h-5 text-purple-400" />} title="Clips & Platforms" />

                {/* Clip count */}
                <div className="mb-8">
                  <label className="block text-sm font-medium text-zinc-300 mb-1">
                    Number of clips
                    <span className="ml-2 text-purple-400 font-bold">{maxClips}</span>
                  </label>
                  <p className="text-xs text-zinc-600 mb-4">How many viral moments to extract from your footage</p>
                  <input
                    type="range" min={1} max={10} value={maxClips}
                    onChange={(e) => setMaxClips(Number(e.target.value))}
                    className="w-full accent-purple-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-zinc-600 mt-1">
                    <span>1 clip</span><span>10 clips</span>
                  </div>
                </div>

                {/* Platform selection */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1">Target platforms</label>
                  <p className="text-xs text-zinc-600 mb-4">Videos will be formatted for each selected platform</p>
                  <div className="grid grid-cols-2 gap-3">
                    {PLATFORMS.map((p) => {
                      const active = platforms.includes(p.id);
                      return (
                        <button
                          key={p.id}
                          onClick={() => togglePlatform(p.id)}
                          className={`flex items-center gap-3 p-4 rounded-2xl border text-sm font-medium transition-all text-left
                            ${active
                              ? "bg-purple-500/15 border-purple-500/50 text-white"
                              : "glass border-white/5 text-zinc-500 hover:text-white hover:border-white/10"}`}
                        >
                          <span className={active ? "text-purple-400" : ""}>{p.icon}</span>
                          {p.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <NavButtons onBack={prevStep} onNext={nextStep} />
              </StepPanel>
            )}

            {step === 2 && (
              <StepPanel key="presenter">
                <StepTitle icon={<Monitor className="w-5 h-5 text-purple-400" />} title="Presenter Mode" />
                <p className="text-sm text-zinc-500 mb-6">Choose how your clips will be presented to viewers</p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <ModeCard
                    selected={presenterMode === "ai_presenter"}
                    onClick={() => setPresenterMode("ai_presenter")}
                    icon={<Monitor className="w-6 h-6 text-purple-400" />}
                    title="AI Presenter"
                    desc="Generate a realistic AI influencer video using Veo3. The presenter reacts to your gameplay."
                    tag="Veo3"
                    tagColor="text-purple-400 bg-purple-500/10 border-purple-500/20"
                  />
                  <ModeCard
                    selected={presenterMode === "voiceover"}
                    onClick={() => setPresenterMode("voiceover")}
                    icon={<Mic className="w-6 h-6 text-pink-400" />}
                    title="Voiceover"
                    desc="Add AI-generated commentary with ElevenLabs TTS voices and auto subtitles."
                    tag="ElevenLabs"
                    tagColor="text-pink-400 bg-pink-500/10 border-pink-500/20"
                  />
                </div>

                <NavButtons onBack={prevStep} onNext={nextStep} nextLabel={presenterMode === "ai_presenter" ? "Skip to Review" : "Configure Voice"} />
              </StepPanel>
            )}

            {step === 3 && presenterMode === "voiceover" && (
              <StepPanel key="voice">
                <StepTitle icon={<Mic className="w-5 h-5 text-pink-400" />} title="Voice Configuration" />

                {/* Commentary mode */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-zinc-300 mb-3">Commentary text</label>
                  <div className="flex gap-3 mb-4">
                    {[
                      { id: "auto", label: "Auto (GPT-4o)", icon: <Sparkles className="w-4 h-4" /> },
                      { id: "manual", label: "Write my own", icon: <MessageSquare className="w-4 h-4" /> },
                    ].map((m) => (
                      <button
                        key={m.id}
                        onClick={() => setCommentaryMode(m.id as "auto" | "manual")}
                        className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border text-sm font-medium transition-all
                          ${commentaryMode === m.id
                            ? "bg-pink-500/15 border-pink-500/50 text-white"
                            : "glass border-white/5 text-zinc-500 hover:text-white"}`}
                      >
                        {m.icon} {m.label}
                      </button>
                    ))}
                  </div>
                  {commentaryMode === "manual" && (
                    <textarea
                      value={commentaryText}
                      onChange={(e) => setCommentaryText(e.target.value)}
                      placeholder="Write your commentary here…"
                      rows={3}
                      className="w-full glass rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-600 resize-none focus:outline-none focus:border-pink-500/40 border border-white/5 transition-colors"
                    />
                  )}
                </div>

                {/* Voice selection */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-zinc-300 mb-3">Voice</label>
                  <div className="grid grid-cols-1 gap-2">
                    {VOICES.map((v) => (
                      <button
                        key={v.id}
                        onClick={() => setVoiceId(v.id)}
                        className={`flex items-center justify-between px-4 py-3 rounded-xl border text-sm transition-all
                          ${voiceId === v.id
                            ? "bg-pink-500/15 border-pink-500/50 text-white"
                            : "glass border-white/5 text-zinc-400 hover:text-white"}`}
                      >
                        <span className="font-medium">{v.label}</span>
                        <span className={`text-xs ${voiceId === v.id ? "text-zinc-400" : "text-zinc-600"}`}>{v.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Voice settings */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-zinc-300 mb-3">Voice settings</label>
                  <div className="flex gap-3 mb-4">
                    {[
                      { id: true, label: "Default" },
                      { id: false, label: "Custom" },
                    ].map((o) => (
                      <button
                        key={String(o.id)}
                        onClick={() => setUseDefaultSettings(o.id)}
                        className={`flex-1 py-2.5 rounded-xl border text-sm font-medium transition-all
                          ${useDefaultSettings === o.id
                            ? "bg-pink-500/15 border-pink-500/50 text-white"
                            : "glass border-white/5 text-zinc-500 hover:text-white"}`}
                      >
                        {o.label}
                      </button>
                    ))}
                  </div>

                  {!useDefaultSettings && (
                    <div className="glass rounded-2xl p-5 space-y-4">
                      <SliderField label="Stability" value={stability} onChange={setStability} min={0} max={1} step={0.05} />
                      <SliderField label="Similarity" value={similarity} onChange={setSimilarity} min={0} max={1} step={0.05} />
                      <SliderField label="Style" value={style} onChange={setStyle} min={0} max={1} step={0.05} />
                      <SliderField label="Speed" value={speed} onChange={setSpeed} min={0.7} max={1.2} step={0.05} />
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-zinc-300">Speaker Boost</span>
                        <button
                          onClick={() => setSpeakerBoost((b) => !b)}
                          className={`w-11 h-6 rounded-full transition-colors relative ${speakerBoost ? "bg-pink-500" : "bg-zinc-700"}`}
                        >
                          <span className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${speakerBoost ? "left-6" : "left-1"}`} />
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                <NavButtons onBack={prevStep} onNext={nextStep} nextLabel="Review" />
              </StepPanel>
            )}

            {step === 4 && (
              <StepPanel key="review">
                <StepTitle icon={<CheckCircle2 className="w-5 h-5 text-green-400" />} title="Review & Start" />

                {processDone ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 rounded-2xl bg-green-500/15 flex items-center justify-center mx-auto mb-4">
                      <CheckCircle2 className="w-8 h-8 text-green-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">Pipeline Started!</h3>
                    <p className="text-sm text-zinc-500">Processing is running in the background. Check the backend console for progress.</p>
                    <Link href="/" className="inline-flex items-center gap-2 mt-6 btn-premium px-6 py-3 rounded-xl text-sm">
                      Back to Dashboard
                    </Link>
                  </div>
                ) : (
                  <>
                    <div className="glass rounded-2xl p-5 space-y-3 mb-8">
                      <ReviewRow label="Video" value={file?.name ?? "—"} />
                      <ReviewRow label="Clips" value={`${maxClips} clips`} />
                      <ReviewRow label="Platforms" value={platforms.map((id) => PLATFORMS.find((p) => p.id === id)?.label).join(", ")} />
                      <ReviewRow label="Mode" value={presenterMode === "ai_presenter" ? "AI Presenter (Veo3)" : "Voiceover (ElevenLabs)"} />
                      {presenterMode === "voiceover" && (
                        <>
                          <ReviewRow label="Commentary" value={commentaryMode === "auto" ? "Auto (GPT-4o)" : "Manual"} />
                          <ReviewRow label="Voice" value={VOICES.find((v) => v.id === voiceId)?.label ?? voiceId} />
                          <ReviewRow label="Settings" value={useDefaultSettings ? "Default" : "Custom"} />
                        </>
                      )}
                    </div>

                    <div className="flex justify-between">
                      <button onClick={prevStep} className="btn-secondary px-6 py-3 rounded-xl text-sm flex items-center gap-2">
                        <ArrowLeft className="w-4 h-4" /> Back
                      </button>
                      <button
                        onClick={handleStartProcessing}
                        disabled={isProcessing}
                        className="btn-premium px-8 py-3 rounded-xl text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                      >
                        {isProcessing
                          ? <><Loader2 className="w-4 h-4 animate-spin" /> Starting…</>
                          : <><Sparkles className="w-4 h-4" /> Start AI Processing</>}
                      </button>
                    </div>
                  </>
                )}
              </StepPanel>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StepPanel({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -12 }}
      transition={{ duration: 0.25 }}
    >
      {children}
    </motion.div>
  );
}

function StepTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-3 mb-6">
      <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center">{icon}</div>
      <h2 className="text-xl font-semibold text-white">{title}</h2>
    </div>
  );
}

function StepBar({ steps, currentIndex }: { steps: string[]; currentIndex: number }) {
  return (
    <div className="flex items-center gap-0">
      {steps.map((label, i) => (
        <div key={label} className="flex items-center flex-1 last:flex-none">
          <div className="flex flex-col items-center">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all
              ${i < currentIndex ? "bg-purple-600 text-white" :
                i === currentIndex ? "bg-white text-black" :
                  "bg-zinc-800 text-zinc-500"}`}
            >
              {i < currentIndex ? <CheckCircle2 className="w-4 h-4" /> : i + 1}
            </div>
            <span className={`mt-1.5 text-[10px] font-medium whitespace-nowrap ${i === currentIndex ? "text-white" : "text-zinc-600"}`}>
              {label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className={`flex-1 h-px mx-2 mb-4 transition-colors ${i < currentIndex ? "bg-purple-600" : "bg-zinc-800"}`} />
          )}
        </div>
      ))}
    </div>
  );
}

function NavButtons({ onBack, onNext, nextLabel = "Next" }: { onBack: () => void; onNext: () => void; nextLabel?: string }) {
  return (
    <div className="flex justify-between mt-8">
      <button onClick={onBack} className="btn-secondary px-6 py-3 rounded-xl text-sm flex items-center gap-2">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>
      <button onClick={onNext} className="btn-premium px-6 py-3 rounded-xl text-sm flex items-center gap-2">
        {nextLabel} <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

function ModeCard({ selected, onClick, icon, title, desc, tag, tagColor }: {
  selected: boolean; onClick: () => void; icon: React.ReactNode;
  title: string; desc: string; tag: string; tagColor: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`text-left p-5 rounded-2xl border transition-all flex flex-col gap-4 h-full
        ${selected ? "bg-purple-500/10 border-purple-500/40" : "glass border-white/5 hover:border-white/10"}`}
    >
      <div className="flex items-start justify-between">
        <div className="w-11 h-11 rounded-xl bg-white/5 flex items-center justify-center">{icon}</div>
        <span className={`text-[10px] font-semibold px-2 py-1 rounded-lg border ${tagColor}`}>{tag}</span>
      </div>
      <div>
        <p className="font-semibold text-white mb-1.5">{title}</p>
        <p className="text-xs text-zinc-500 leading-relaxed">{desc}</p>
      </div>
      {selected && (
        <div className="flex items-center gap-1.5 text-xs text-purple-400 font-medium mt-auto">
          <CheckCircle2 className="w-3.5 h-3.5" /> Selected
        </div>
      )}
    </button>
  );
}

function SliderField({ label, value, onChange, min, max, step }: {
  label: string; value: number; onChange: (v: number) => void; min: number; max: number; step: number;
}) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5">
        <span className="text-zinc-300">{label}</span>
        <span className="text-pink-400 font-medium tabular-nums">{value.toFixed(2)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-pink-500 cursor-pointer"
      />
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1 border-b border-white/5 last:border-0">
      <span className="text-sm text-zinc-500 shrink-0">{label}</span>
      <span className="text-sm text-white text-right truncate max-w-[260px]">{value}</span>
    </div>
  );
}
