import React, { useState } from 'react';
import { useTtsPlayback } from '../context/TtsPlaybackContext';
<<<<<<< HEAD
import { translateText } from '../services/api';
=======
import MarkdownBody from './MarkdownBody';
>>>>>>> 957572d85f2bc9bc965df2f6aaad701e16c715ba

/**
 * Single chat bubble with timestamp, read-aloud, and translation.
 */
export default function MessageBubble({ text: initialText, role, time, utteranceId }) {
  const isBot = role === 'bot' || role === 'error';
  const sid = String(utteranceId);
  const { play, stop, pause, resume, activeSessionId, phase, lineProgress } = useTtsPlayback();
  const [hint, setHint] = useState('');
  const [translatedText, setTranslatedText] = useState(null);
  const [isTranslating, setIsTranslating] = useState(false);

  const isActive = activeSessionId === sid && phase !== 'idle';
  const isPaused = phase === 'paused';

  const onRead = (e) => {
    e.stopPropagation();
    setHint('');
    void play(sid, translatedText || initialText).then((r) => {
      if (!r.ok) setHint(r.error || 'Playback failed.');
    });
  };

  const handleTranslate = async (e) => {
    e.stopPropagation();
    if (translatedText) {
      setTranslatedText(null);
      return;
    }

    setIsTranslating(true);
    try {
      // Default to English -> Hindi for testing
      const data = await translateText(initialText, "eng_Latn", "hin_Deva");
      setTranslatedText(data.translation);
    } catch (err) {
      console.error("Translation failed:", err);
      setHint("Translation failed.");
    } finally {
      setIsTranslating(false);
    }
  };

  return (
    <div className={`msg-row ${role}`}>
      {isBot && (
        <div className="bot-avatar" aria-hidden="true">
          <span className="bot-avatar-initial">A</span>
        </div>
      )}

      <div className="bubble-wrap">
<<<<<<< HEAD
        <div className="bubble">{translatedText || initialText}</div>
=======
        <div className={`bubble${isBot ? ' bubble--md' : ''}`}>
          {isBot ? <MarkdownBody>{text}</MarkdownBody> : text}
        </div>
>>>>>>> 957572d85f2bc9bc965df2f6aaad701e16c715ba
        <div className="msg-meta-row">
          {time && <div className="msg-time">{time}</div>}
          {role === 'bot' && (
            <div className="msg-controls">
              <div className="msg-tts-controls">
                {!isActive ? (
                  <button
                    type="button"
                    className="msg-tts-btn"
                    onClick={onRead}
                    aria-label="Read reply aloud"
                    title="Read aloud"
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
                  </>
                )}
              </div>
              <button
                type="button"
                className={`msg-translate-btn ${isTranslating ? 'loading' : ''}`}
                onClick={handleTranslate}
                aria-label="Translate message"
                title={translatedText ? "Show original" : "Translate to Hindi"}
                disabled={isTranslating}
              >
                <span className="ms">{translatedText ? 'undo' : 'translate'}</span>
              </button>
            </div>
          )}
        </div>
        {hint ? <div className="msg-tts-hint" role="status">{hint}</div> : null}
      </div>
    </div>
  );
}
