"use client";

import { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import VoiceButton from "@/components/voice/VoiceButton";
import TextQueryInput from "@/components/ui/TextQueryInput";
import PipelineVisualizer from "@/components/pipeline/PipelineVisualizer";
import AnswerPanel from "@/components/answer/AnswerPanel";
import { useVoiceRecorder } from "@/hooks/use-voice-recorder";
import { submitTextQuery, submitVoiceQuery } from "@/lib/api/client";
import { PIPELINE_STAGES } from "@/types/pipeline";
import type { QueryResponse } from "@/types/api";
import type { PipelineStageInfo } from "@/types/pipeline";

export default function HomePage() {
  const recorder = useVoiceRecorder();
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [stages, setStages] = useState<PipelineStageInfo[]>(
    PIPELINE_STAGES.map((s) => ({ ...s }))
  );

  const resetStages = () => {
    setStages(PIPELINE_STAGES.map((s) => ({ ...s, status: "pending" })));
  };

  const handleTextQuery = async (query: string) => {
    setIsLoading(true);
    setResponse(null);
    resetStages();
    try {
      const result = await submitTextQuery({ query });
      setResponse(result);
    } catch (err) {
      setResponse({
        request_id: "error",
        status: "error",
        sources: [],
        message:
          err instanceof Error
            ? err.message
            : "Failed to connect to the backend.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const { state: recorderState, audioBlob, reset: resetRecorder } = recorder;

  // Submit voice recording automatically when audioBlob is ready and state is stopped
  useEffect(() => {
    if (recorderState === "stopped" && audioBlob) {
      const submitVoice = async () => {
        setIsLoading(true);
        setResponse(null);
        resetStages();
        try {
          const result = await submitVoiceQuery(audioBlob);
          setResponse(result);
        } catch (err) {
          setResponse({
            request_id: "error",
            status: "error",
            sources: [],
            message:
              err instanceof Error
                ? err.message
                : "Failed to connect to the backend.",
          });
        } finally {
          setIsLoading(false);
          resetRecorder();
        }
      };
      submitVoice();
    }
  }, [recorderState, audioBlob, resetRecorder]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
          {/* Main column */}
          <div className="space-y-8">
            {/* Hero */}
            <section className="text-center py-12 animate-fade-in">
              <h1 className="text-3xl font-bold tracking-tight text-text-primary mb-2">
                SAMVAD
              </h1>
              <p className="text-sm text-text-muted tracking-wide">
                Speak. Retrieve. Ground.
              </p>
            </section>

            {/* Voice button */}
            <section className="flex justify-center">
              <VoiceButton
                state={recorder.state}
                onStart={recorder.startRecording}
                onStop={recorder.stopRecording}
              />
            </section>

            {/* Error from recorder */}
            {recorder.error && (
              <div className="rounded-lg border border-error/20 bg-error/5 px-4 py-3 text-xs text-error text-center animate-fade-in">
                {recorder.error}
              </div>
            )}

            {/* Or text input */}
            <section className="max-w-2xl mx-auto w-full">
              <TextQueryInput
                onSubmit={handleTextQuery}
                isLoading={isLoading}
              />
            </section>

            {/* Answer */}
            <section className="max-w-2xl mx-auto w-full">
              <AnswerPanel response={response} isLoading={isLoading} />
            </section>
          </div>

          {/* Sidebar — Pipeline */}
          <aside className="hidden lg:block">
            <div className="sticky top-24">
              <PipelineVisualizer stages={stages} />
            </div>
          </aside>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border-subtle py-4 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span className="text-[10px] font-mono text-text-muted">
            SAMVAD v0.1.0 — Foundation
          </span>
          <span className="text-[10px] font-mono text-text-muted">
            Hacker House Goa 2026
          </span>
        </div>
      </footer>
    </div>
  );
}
