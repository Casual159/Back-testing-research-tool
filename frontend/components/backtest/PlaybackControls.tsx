"use client";

import { Play, Pause, Square, SkipBack } from "lucide-react";
import type { PlaybackSpeed, PlaybackState } from "@/hooks/usePlaybackEngine";

const SPEEDS: PlaybackSpeed[] = [1, 2, 5, 10, 50];

interface PlaybackControlsProps {
  state: PlaybackState;
  onPlay: () => void;
  onPause: () => void;
  onStop: () => void;
  onSeek: (index: number) => void;
  onSetSpeed: (speed: PlaybackSpeed) => void;
  /** Candle timestamps for display */
  candleTimes?: number[];
}

export default function PlaybackControls({
  state,
  onPlay,
  onPause,
  onStop,
  onSeek,
  onSetSpeed,
  candleTimes,
}: PlaybackControlsProps) {
  const { status, speed, currentIndex, totalCandles } = state;
  const isPlaying = status === "playing";
  const isStopped = status === "stopped";

  // Current time display
  const currentTimeStr = candleTimes && candleTimes[currentIndex]
    ? new Date(candleTimes[currentIndex] * 1000).toLocaleDateString()
    : "";

  const progress = totalCandles > 1
    ? ((isStopped ? totalCandles - 1 : currentIndex) / (totalCandles - 1)) * 100
    : 0;

  return (
    <div className="flex flex-col gap-2">
      {/* Timeline scrubber */}
      <div className="relative">
        <input
          type="range"
          min={0}
          max={totalCandles - 1}
          value={isStopped ? totalCandles - 1 : currentIndex}
          onChange={(e) => onSeek(Number(e.target.value))}
          className="w-full h-1.5 appearance-none cursor-pointer rounded-full bg-neutral-700
            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500
            [&::-webkit-slider-thumb]:hover:bg-blue-400 [&::-webkit-slider-thumb]:transition-colors"
          style={{
            background: `linear-gradient(to right, #3b82f6 ${progress}%, #404040 ${progress}%)`,
          }}
        />
      </div>

      {/* Controls row */}
      <div className="flex items-center gap-3 text-xs">
        {/* Transport buttons */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => onSeek(0)}
            className="rounded p-1 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-700 transition-colors"
            title="Go to start"
          >
            <SkipBack className="h-3.5 w-3.5" />
          </button>

          {isPlaying ? (
            <button
              onClick={onPause}
              className="rounded p-1 text-neutral-200 bg-neutral-700 hover:bg-neutral-600 transition-colors"
              title="Pause"
            >
              <Pause className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={onPlay}
              className="rounded p-1 text-neutral-200 bg-blue-600 hover:bg-blue-500 transition-colors"
              title="Play"
            >
              <Play className="h-4 w-4" />
            </button>
          )}

          <button
            onClick={onStop}
            className="rounded p-1 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-700 transition-colors"
            title="Stop (show all)"
          >
            <Square className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Speed buttons */}
        <div className="flex items-center gap-0.5 border-l border-neutral-700 pl-3">
          {SPEEDS.map((s) => (
            <button
              key={s}
              onClick={() => onSetSpeed(s)}
              className={`rounded px-1.5 py-0.5 font-mono transition-colors ${
                speed === s
                  ? "bg-neutral-700 text-neutral-200"
                  : "text-neutral-500 hover:text-neutral-300"
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Time / progress info */}
        <div className="ml-auto flex items-center gap-3 text-neutral-500">
          {currentTimeStr && (
            <span className="font-mono">{currentTimeStr}</span>
          )}
          <span className="font-mono">
            {(isStopped ? totalCandles : currentIndex + 1).toLocaleString()} / {totalCandles.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}
