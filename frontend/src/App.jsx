import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import QuickActions from './components/QuickActions';
import { sendChatMessage } from './services/api';
import './styles.css';

const WELCOME = {
  text: "Hello, Priya! 👋 I'm your AirHelp Assistant. Ask me about your flights, facilities, or let me know how I can help.",
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
   */
  const handleSend = async (text, loc = null) => {
    const currentLocation = loc ?? location;
    if (loc) setLocation(loc);

    const userMsg = { text, role: 'user', time: formatTime() };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await sendChatMessage(text, currentLocation);
      console.log('API response:', data);

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

  const handleQuickAction = ({ message, location: actionLocation }) => {
    handleSend(message, actionLocation);
  };

  return (
    <div className="app-container">
      {/* ── Left Navigation Sidebar ── */}
      <Sidebar />

      {/* ── Main Chat Area ── */}
      <main className="chat-main">
        {/* Mobile Header (Hidden on Desktop) */}
        <header className="chat-header-mobile">
          <h1>AirHelp</h1>
          <div className="brand-logo" style={{width: 32, height: 32, fontSize: 16}}>✈️</div>
        </header>

        {/* Scrollable Message List */}
        <ChatWindow messages={messages} isLoading={isLoading} />

        {/* Input Area anchored to the bottom center */}
        <div className="input-area-wrapper">
          <QuickActions onAction={handleQuickAction} />
          <InputBox onSend={handleSend} isLoading={isLoading} />
        </div>
      </main>
    </div>
  );
}
