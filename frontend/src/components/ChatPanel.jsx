import React from 'react';
import ChatWindow from './ChatWindow';
import InputBox from './InputBox';

const SUGGESTED = [
  'I need help with my baggage',
  'Where is the nearest lounge?',
  'My flight is delayed. What now?',
];

/**
 * Floating chat widget — desktop only (hidden on mobile via CSS).
 */
export default function ChatPanel({ messages, isLoading, onSend, isOpen, onToggle, onClose }) {
  const showSuggestions = messages.length <= 1;

  return (
    <div
      className={`chat-panel ${isOpen ? '' : 'minimized'}`}
      role="complementary"
      aria-label="AirHelp Assistant chat"
    >
      {/* ── Panel Header ── */}
      <div className="chat-panel-header" onClick={onToggle} aria-expanded={isOpen}>
        <div className="chat-panel-avatar" aria-hidden="true">
          <span className="ms">smart_toy</span>
        </div>
        <div className="chat-panel-info">
          <div className="chat-panel-name">AirHelp Assistant</div>
          <div className="chat-panel-status">
            <span className="status-dot" aria-hidden="true" />
            Online
          </div>
        </div>
        <div className="chat-panel-actions">
          <button
            className="chat-panel-btn"
            onClick={(e) => { e.stopPropagation(); onToggle(); }}
            aria-label={isOpen ? 'Minimize chat' : 'Expand chat'}
          >
            <span className="ms">{isOpen ? 'remove' : 'open_in_full'}</span>
          </button>
          <button
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
          {/* Suggested replies (only when chat is fresh) */}
          {showSuggestions && (
            <div className="suggested-replies" aria-label="Suggested questions">
              {SUGGESTED.map((s) => (
                <button
                  key={s}
                  className="suggested-reply"
                  onClick={() => onSend(s, null)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Message list */}
          <ChatWindow messages={messages} isLoading={isLoading} />

          {/* Input */}
          <InputBox onSend={onSend} isLoading={isLoading} />
        </div>
      )}
    </div>
  );
}
