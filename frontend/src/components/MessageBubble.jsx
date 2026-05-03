import React from 'react';

/**
 * Single chat bubble with timestamp.
 */
export default function MessageBubble({ text, role, time }) {
  const isBot = role === 'bot' || role === 'error';

  return (
    <div className={`msg-row ${role}`}>
      {isBot && (
        <div className="bot-avatar" aria-hidden="true">
          <span className="ms">smart_toy</span>
        </div>
      )}

      <div className="bubble-wrap">
        <div className="bubble">{text}</div>
        {time && <div className="msg-time">{time}</div>}
      </div>
    </div>
  );
}
