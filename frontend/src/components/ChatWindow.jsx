import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

/**
 * Scrollable message list with auto-scroll and typing indicator.
 */
export default function ChatWindow({ messages, isLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-window" role="log" aria-live="polite" aria-label="Chat history">
      {messages.map((msg, i) => (
        <MessageBubble
          key={`${msg.time}-${i}`}
          utteranceId={`msg-${i}-${msg.time}`}
          text={msg.text}
          role={msg.role}
          time={msg.time}
        />
      ))}

      {isLoading && (
        <div className="typing-row">
          <div className="bot-avatar" aria-hidden="true">
            <span className="ms">smart_toy</span>
          </div>
          <div className="typing-bubble" aria-label="Assistant is typing">
            <span /><span /><span />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
