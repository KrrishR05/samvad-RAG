/**
 * SAMVAD — useVoiceRecorder Hook
 *
 * Manages browser microphone capture lifecycle:
 *   idle → requesting → recording → stopped
 *
 * Returns the recorded audio as a Blob for submission to the API.
 * Does NOT perform any transcription — that is the backend's job.
 */

"use client";

import { useState, useRef, useCallback, useMemo } from "react";

export type RecorderState =
  | "idle"
  | "requesting"
  | "recording"
  | "stopped"
  | "error";

interface UseVoiceRecorderReturn {
  state: RecorderState;
  audioBlob: Blob | null;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  reset: () => void;
}

export function useVoiceRecorder(): UseVoiceRecorderReturn {
  const [state, setState] = useState<RecorderState>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    setError(null);
    setAudioBlob(null);
    setState("requesting");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        setState("stopped");

        // Release microphone
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.onerror = () => {
        setError("Recording failed.");
        setState("error");
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setState("recording");
    } catch (err) {
      const message =
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "Microphone access denied. Please allow microphone access."
          : "Unable to access microphone.";
      setError(message);
      setState("error");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "recording"
    ) {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const reset = useCallback(() => {
    setAudioBlob(null);
    setError(null);
    setState("idle");
  }, []);

  return useMemo(
    () => ({
      state,
      audioBlob,
      error,
      startRecording,
      stopRecording,
      reset,
    }),
    [state, audioBlob, error, startRecording, stopRecording, reset]
  );
}
