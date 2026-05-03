import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

/**
 * Scrollable message list with auto-scroll and typing indicator.
 * @param {Array}   messages  - Array of { text, role, time? }
 * @param {boolean} isLoading - Show animated typing indicator when true
 */
export default function ChatWindow({ messages, isLoading }) {
  const bottomRef = useRef(null);

  // Auto-scroll to bottom whenever messages change or loading toggles
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-window" role="log" aria-live="polite" aria-label="Chat history">
      {messages.map((msg, i) => (
        <MessageBubble key={i} text={msg.text} role={msg.role} time={msg.time} />
      ))}

      {/* Animated typing indicator */}
      {isLoading && (
        <div className="typing-row">
          <div className="bot-avatar" aria-hidden="true">✈️</div>
          <div className="typing-bubble">
            <span /><span /><span />
          </div>
        </div>
      )}

      {/* Invisible scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
}
