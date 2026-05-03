import React from 'react';
import { useTtsPlayback } from '../context/TtsPlaybackContext';

/**
 * Read-aloud control: English Piper, chunked playback, pause / resume / stop.
 */
export default function TtsMiniBar({ sessionId, text, buttonClass, wrapClass, disabled = false }) {
  const sid = String(sessionId);
  const { play, stop, pause, resume, activeSessionId, phase, lineProgress } = useTtsPlayback();
  const t = (text || '').trim();
  if (!t) return null;

  const active = activeSessionId === sid && phase !== 'idle';
  const paused = phase === 'paused';
  const bc = buttonClass || 'msg-tts-btn';
  const wc = wrapClass || 'msg-tts-controls';
  const dis = Boolean(disabled);

  return (
    <div className={wc}>
      {!active ? (
        <button
          type="button"
          className={bc}
          disabled={dis}
          onClick={() => void play(sid, t)}
          aria-label="Read aloud"
          title="Read aloud (English)"
        >
          <span className="ms">volume_up</span>
        </button>
      ) : (
        <>
          {paused ? (
            <button type="button" className={bc} disabled={dis} onClick={() => resume()} aria-label="Resume" title="Resume">
              <span className="ms">play_arrow</span>
            </button>
          ) : (
            <button type="button" className={bc} disabled={dis} onClick={() => pause()} aria-label="Pause" title="Pause">
              <span className="ms">pause</span>
            </button>
          )}
          <button type="button" className={bc} disabled={dis} onClick={() => stop()} aria-label="Stop" title="Stop">
            <span className="ms">stop</span>
          </button>
          {lineProgress.total > 0 ? (
            <span className="msg-tts-progress" aria-live="polite">
              {lineProgress.cur}/{lineProgress.total}
            </span>
          ) : null}
        </>
      )}
    </div>
  );
}
