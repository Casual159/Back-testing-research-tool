"use client";

import { useReducer, useEffect, useRef, useCallback } from "react";

// ── Types ──────────────────────────────────────────────────────────────

export type PlaybackSpeed = 1 | 2 | 5 | 10 | 50;
export type PlaybackStatus = "stopped" | "playing" | "paused";

export interface PlaybackState {
  status: PlaybackStatus;
  speed: PlaybackSpeed;
  currentIndex: number;
  totalCandles: number;
}

type PlaybackAction =
  | { type: "PLAY" }
  | { type: "PAUSE" }
  | { type: "STOP" }
  | { type: "SET_SPEED"; speed: PlaybackSpeed }
  | { type: "SEEK"; index: number }
  | { type: "TICK" }
  | { type: "INIT"; totalCandles: number };

// ── Reducer ────────────────────────────────────────────────────────────

function playbackReducer(state: PlaybackState, action: PlaybackAction): PlaybackState {
  switch (action.type) {
    case "INIT":
      return {
        status: "stopped",
        speed: state.speed,
        currentIndex: action.totalCandles - 1,
        totalCandles: action.totalCandles,
      };
    case "PLAY":
      if (state.currentIndex >= state.totalCandles - 1) {
        // At end - restart from beginning
        return { ...state, status: "playing", currentIndex: 0 };
      }
      return { ...state, status: "playing" };
    case "PAUSE":
      return { ...state, status: "paused" };
    case "STOP":
      return { ...state, status: "stopped", currentIndex: state.totalCandles - 1 };
    case "SET_SPEED":
      return { ...state, speed: action.speed };
    case "SEEK":
      return {
        ...state,
        currentIndex: Math.max(0, Math.min(action.index, state.totalCandles - 1)),
      };
    case "TICK": {
      const next = state.currentIndex + 1;
      if (next >= state.totalCandles) {
        return { ...state, status: "paused", currentIndex: state.totalCandles - 1 };
      }
      return { ...state, currentIndex: next };
    }
    default:
      return state;
  }
}

// ── Hook ───────────────────────────────────────────────────────────────

const BASE_INTERVAL_MS = 200;

export function usePlaybackEngine(totalCandles: number) {
  const [state, dispatch] = useReducer(playbackReducer, {
    status: "stopped",
    speed: 1 as PlaybackSpeed,
    currentIndex: Math.max(totalCandles - 1, 0),
    totalCandles,
  });

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Init when totalCandles changes
  useEffect(() => {
    if (totalCandles > 0) {
      dispatch({ type: "INIT", totalCandles });
    }
  }, [totalCandles]);

  // Tick loop
  useEffect(() => {
    if (state.status === "playing") {
      const interval = BASE_INTERVAL_MS / state.speed;
      intervalRef.current = setInterval(() => {
        dispatch({ type: "TICK" });
      }, interval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [state.status, state.speed]);

  const play = useCallback(() => dispatch({ type: "PLAY" }), []);
  const pause = useCallback(() => dispatch({ type: "PAUSE" }), []);
  const stop = useCallback(() => dispatch({ type: "STOP" }), []);
  const seek = useCallback((index: number) => dispatch({ type: "SEEK", index }), []);
  const setSpeed = useCallback((speed: PlaybackSpeed) => dispatch({ type: "SET_SPEED", speed }), []);

  // Derive whether we're in "show all" mode (stopped = show everything)
  const playbackIndex = state.status === "stopped" ? null : state.currentIndex;

  return {
    state,
    playbackIndex,
    play,
    pause,
    stop,
    seek,
    setSpeed,
  };
}
