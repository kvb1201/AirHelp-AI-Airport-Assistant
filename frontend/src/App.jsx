import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import QuickActions from './components/QuickActions';
import { sendChatMessage } from './services/api';
import './styles.css';

const WELCOME = {
  text: "Hi! I'm your AI Airport Companion. Ask me about gates, food, services, or let me know where you are.",
  role: 'bot',
  time: formatTime(),
};

/** Returns a short HH:MM timestamp string. */
function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function App() {
  const [messages, setMessages] = useState([WELCOME]);
  const [isLoading, setIsLoading] = useState(false);
  const [location, setLocation] = useState('entrance');

  /**
   * Core send function — adds user message, calls API, appends bot reply.
   * @param {string} text       - Message text
   * @param {string|null} loc   - Optional location override from quick actions
   */
  const handleSend = async (text, loc = null) => {
    // Resolve location: quick action may carry a location update
    const currentLocation = loc ?? location;
    if (loc) setLocation(loc);

    // Append user message immediately
    const userMsg = { text, role: 'user', time: formatTime() };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await sendChatMessage(text, currentLocation);
      console.log('API response:', data); // Log full response for debugging

      const botText = data.message || data.response || 'Got it!';
      setMessages((prev) => [...prev, { text: botText, role: 'bot', time: formatTime() }]);
    } catch (err) {
      console.error('API error:', err);
      setMessages((prev) => [
        ...prev,
        { text: 'Server not responding. Please try again.', role: 'error', time: formatTime() },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Called when a quick action button is clicked
  const handleQuickAction = ({ message, location: actionLocation }) => {
    handleSend(message, actionLocation);
  };

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-icon" aria-hidden="true">✈️</div>
        <div className="header-text">
          <h1>Airport Companion</h1>
          <p className="subtitle">AI-powered airport assistant</p>
        </div>
      </header>

      {/* ── Scrollable chat area ── */}
      <ChatWindow messages={messages} isLoading={isLoading} />

      {/* ── Quick action pills ── */}
      <QuickActions onAction={handleQuickAction} />

      {/* ── Fixed input bar ── */}
      <InputBox onSend={handleSend} isLoading={isLoading} />
    </div>
  );
}
