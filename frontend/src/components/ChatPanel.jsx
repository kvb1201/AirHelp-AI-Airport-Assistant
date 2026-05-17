import React, { useMemo } from 'react';
import ChatWindow from './ChatWindow';
import InputBox from './InputBox';
import MarkdownBody from './MarkdownBody';
import TtsMiniBar from './TtsMiniBar';

const SUGGESTED = [
  'I need help with my baggage',
  'Where is the nearest lounge?',
  'My flight is delayed. What now?',
];

/**
 * Floating chat widget — desktop only (hidden on mobile via CSS).
 */
export default function ChatPanel({ messages, isLoading, onSend, isOpen, onToggle, onClose, mapMode, drawerMode }) {
  const showSuggestions = !mapMode && messages.length <= 1;

  const mapLastExchange = useMemo(() => {
    let lastUser = null;
    let lastAssistant = null;
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (!lastAssistant && (m.role === 'bot' || m.role === 'error')) lastAssistant = m;
      if (!lastUser && m.role === 'user') lastUser = m;
      if (lastUser && lastAssistant) break;
    }
    return { lastUser, lastAssistant };
  }, [messages]);

  return (
    <div
      className={`chat-panel ${isOpen ? '' : 'minimized'}${mapMode ? ' chat-panel--map' : ''}${drawerMode ? ' chat-panel--drawer' : ''}`}
      role="complementary"
      aria-label="Assistant chat"
    >
      {/* ── Panel Header ── */}
      <div
        className="chat-panel-header"
        onClick={drawerMode ? undefined : onToggle}
        aria-expanded={isOpen}
      >
        <div className="chat-panel-avatar" aria-hidden="true">
          <span className="chat-panel-avatar-initial">AH</span>
        </div>
        <div className="chat-panel-info">
          <div className="chat-panel-name">Assistant</div>
          <div className="chat-panel-status">
            <span className="status-dot" aria-hidden="true" />
            Online
          </div>
        </div>
        <div className="chat-panel-actions">
          {!drawerMode ? (
            <button
              type="button"
              className="chat-panel-btn"
              onClick={(e) => { e.stopPropagation(); onToggle(); }}
              aria-label={isOpen ? 'Minimize chat' : 'Expand chat'}
            >
              <span className="ms">{isOpen ? 'remove' : 'open_in_full'}</span>
            </button>
          ) : null}
          <button
            type="button"
            className="chat-panel-btn"
            onClick={(e) => { e.stopPropagation(); onClose(); }}
            aria-label="Close chat"
          >
            <span className="ms">close</span>
          </button>
        </div>
      </div>

      {/* ── Panel Body ── */}
      {isOpen && (
        <div className="chat-panel-body">
          {mapMode ? (
            <>
              <p className="chat-panel-map-hint">
                Quick questions while you use the map — your walking route stays in the panel on the right.
              </p>
              {(mapLastExchange.lastUser || mapLastExchange.lastAssistant || isLoading) && (
                <div className="chat-panel-map-exchange" aria-label="Latest reply">
                  {mapLastExchange.lastUser ? (
                    <div className="chat-panel-map-line chat-panel-map-line--user">
                      <span className="chat-panel-map-kicker">You</span>
                      <span className="chat-panel-map-text">{mapLastExchange.lastUser.text}</span>
                    </div>
                  ) : null}
                  {isLoading ? (
                    <div className="chat-panel-map-line chat-panel-map-line--bot">
                      <span className="chat-panel-map-kicker">AirHelp</span>
                      <span className="chat-panel-map-text chat-panel-map-typing">Loading…</span>
                    </div>
                  ) : mapLastExchange.lastAssistant ? (
                    <div className="chat-panel-map-line chat-panel-map-line--bot">
                      <span className="chat-panel-map-kicker">AirHelp</span>
                      <div className="chat-panel-map-line-body">
                        <MarkdownBody className="chat-panel-map-text">
                          {mapLastExchange.lastAssistant.text}
                        </MarkdownBody>
                        {mapLastExchange.lastAssistant.role === 'bot' && (
                          <TtsMiniBar
                            sessionId="chat-map-preview"
                            text={mapLastExchange.lastAssistant.text}
                            buttonClass="chat-panel-map-tts"
                            wrapClass="chat-panel-map-tts-wrap"
                          />
                        )}
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
              <InputBox onSend={onSend} isLoading={isLoading} />
            </>
          ) : (
            <>
              {showSuggestions && (
                <div className="suggested-replies" aria-label="Suggested questions">
                  {SUGGESTED.map((s) => (
                    <button
                      type="button"
                      key={s}
                      className="suggested-reply"
                      onClick={() => onSend(s, null)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
              <ChatWindow messages={messages} isLoading={isLoading} />
              <InputBox onSend={onSend} isLoading={isLoading} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
