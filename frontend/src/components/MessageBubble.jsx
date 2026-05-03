import React from 'react';

/**
 * A single chat bubble with optional timestamp.
 * @param {string} text              - Message text
 * @param {'user'|'bot'|'error'} role - Who sent it
 * @param {string} [time]            - Optional display timestamp
 */
export default function MessageBubble({ text, role, time }) {
  return (
    <div className={`msg-row ${role}`}>
      {/* Bot avatar — only shown for bot/error messages */}
      {(role === 'bot' || role === 'error') && (
        <div className="bot-avatar" aria-hidden="true">✈️</div>
      )}

      <div>
        <div className="bubble">{text}</div>
        {time && <div className="msg-time">{time}</div>}
      </div>
    </div>
  );
}
