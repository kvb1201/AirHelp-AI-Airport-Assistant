import React, { useState } from 'react';
import { useTtsPlayback } from '../context/TtsPlaybackContext';

/**
 * Single chat bubble with timestamp and read-aloud (English Piper, line-by-line with pause/resume).
 */
export default function MessageBubble({ text, role, time, utteranceId }) {
  const isBot = role === 'bot' || role === 'error';
  const sid = String(utteranceId);
  const { play, stop, pause, resume, activeSessionId, phase, lineProgress } = useTtsPlayback();
  const [hint, setHint] = useState('');

  const isActive = activeSessionId === sid && phase !== 'idle';
  const isPaused = phase === 'paused';

  const onRead = (e) => {
    e.stopPropagation();
    setHint('');
    void play(sid, text).then((r) => {
      if (!r.ok) setHint(r.error || 'Playback failed.');
    });
  };

  return (
    <div className={`msg-row ${role}`}>
      {isBot && (
        <div className="bot-avatar" aria-hidden="true">
          <span className="bot-avatar-initial">A</span>
        </div>
      )}

      <div className="bubble-wrap">
        <div className="bubble">{text}</div>
        <div className="msg-meta-row">
          {time && <div className="msg-time">{time}</div>}
          {role === 'bot' && (
            <div className="msg-tts-controls">
              {!isActive ? (
                <button
                  type="button"
                  className="msg-tts-btn"
                  onClick={onRead}
                  aria-label="Read reply aloud"
                  title="Read aloud (English, line by line)"
                >
                  <span className="ms">volume_up</span>
                </button>
              ) : (
                <>
                  {isPaused ? (
                    <button
                      type="button"
                      className="msg-tts-btn"
                      onClick={() => resume()}
                      aria-label="Resume reading"
                      title="Resume"
                    >
                      <span className="ms">play_arrow</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="msg-tts-btn"
                      onClick={() => pause()}
                      aria-label="Pause reading"
                      title="Pause"
                    >
                      <span className="ms">pause</span>
                    </button>
                  )}
                  <button
                    type="button"
                    className="msg-tts-btn"
                    onClick={() => stop()}
                    aria-label="Stop reading"
                    title="Stop"
                  >
                    <span className="ms">stop</span>
                  </button>
                  {lineProgress.total > 0 ? (
                    <span className="msg-tts-progress" aria-live="polite">
                      Line {lineProgress.cur}/{lineProgress.total}
                    </span>
                  ) : null}
                </>
              )}
            </div>
          )}
        </div>
        {hint ? <div className="msg-tts-hint" role="status">{hint}</div> : null}
      </div>
    </div>
  );
}
