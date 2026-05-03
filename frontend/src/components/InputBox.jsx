import React, { useState } from 'react';

/**
 * Chat input bar — used in ChatPanel (desktop) and mobile bottom area.
 */
export default function InputBox({ onSend, isLoading, placeholder = 'Type your message…' }) {
  const [value, setValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <form className="input-bar" onSubmit={handleSubmit} aria-label="Send a message">
      <input
        className="chat-input"
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={isLoading}
        autoComplete="off"
        aria-label="Chat message"
      />
      <button
        className="send-btn"
        type="submit"
        disabled={!value.trim() || isLoading}
        aria-label="Send message"
      >
        <span className="ms">send</span>
      </button>
    </form>
  );
}
