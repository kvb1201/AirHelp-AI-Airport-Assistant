import React, { useState } from 'react';

/**
 * Fixed input bar at the bottom of the screen.
 * @param {function} onSend    - Called with the trimmed message string
 * @param {boolean}  isLoading - Disables input while awaiting API response
 */
export default function InputBox({ onSend, isLoading }) {
  const [value, setValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      <input
        id="chat-input"
        className="chat-input"
        type="text"
        placeholder="Ask about gates, food, services…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={isLoading}
        autoComplete="off"
        aria-label="Chat message input"
      />
      <button
        className="send-btn"
        type="submit"
        disabled={!value.trim() || isLoading}
        aria-label="Send message"
      >
        {/* Send arrow SVG icon */}
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </form>
  );
}
