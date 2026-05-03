import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import HomeContent from './components/HomeContent';
import RightPanel from './components/RightPanel';
import ChatPanel from './components/ChatPanel';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import QuickActions from './components/QuickActions';
import BottomNav from './components/BottomNav';
import { sendChatMessage } from './services/api';
import './styles.css';

function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const WELCOME = {
  text: "Hi Priya! I'm here to help you with airport facilities, flights, or any issues. How can I assist you?",
  role: 'bot',
  time: formatTime(),
};

export default function App() {
  const [messages, setMessages] = useState([WELCOME]);
  const [isLoading, setIsLoading] = useState(false);
  const [location, setLocation] = useState('entrance');
  const [chatOpen, setChatOpen] = useState(true);       // desktop chat panel open/minimized
  const [mobileView, setMobileView] = useState('home'); // 'home' | 'chat' | 'trips' | 'map' | 'profile'

  const handleSend = async (text, loc = null) => {
    const currentLocation = loc ?? location;
    if (loc) setLocation(loc);

    const userMsg = { text, role: 'user', time: formatTime() };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Switch mobile to chat view when user sends a message
    setMobileView('chat');
    // Ensure desktop panel is open
    setChatOpen(true);

    try {
      const data = await sendChatMessage(text, currentLocation);
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
      {/* ── Left Sidebar (Desktop) ── */}
      <Sidebar />

      {/* ── Main Body ── */}
      <div className="app-body">

        {/* Desktop Header */}
        <header className="desktop-header" role="banner">
          <button className="header-lang-btn" aria-label="Change language">
            <span className="ms" style={{ fontSize: 16 }}>language</span>
            EN
          </button>
          <div className="header-avatar" role="button" tabIndex={0} aria-label="User account">
            P
          </div>
        </header>

        {/* Mobile Header */}
        <header className="mobile-header" role="banner">
          <button className="mobile-header-menu" aria-label="Open menu">
            <span className="ms">menu</span>
          </button>
          <div className="mobile-header-title">
            <h1>AirHelp</h1>
            <p>Smart help for your journey</p>
          </div>
          <button className="mobile-header-bell" aria-label="Notifications">
            <span className="ms">notifications</span>
          </button>
        </header>

        {/* Content area */}
        <div className="content-area">
          <main className="main-content">
            {/* Home screen — always visible on desktop; on mobile only when mobileView is 'home' */}
            <div style={mobileView !== 'home' ? { display: 'none' } : undefined} className="home-view-mobile">
              <HomeContent onSend={handleSend} />
            </div>

            {/* Mobile chat history — shown when user has been chatting */}
            {mobileView === 'chat' && (
              <div className="mobile-chat-history">
                <div style={{ paddingTop: 16 }}>
                  <ChatWindow messages={messages} isLoading={isLoading} />
                </div>
              </div>
            )}
          </main>

          {/* Right Panel (desktop) */}
          <RightPanel />
        </div>

        {/* ── Mobile Bottom Area (fixed) ── */}
        <div className="mobile-bottom">
          {mobileView === 'home' && (
            <QuickActions onAction={handleQuickAction} />
          )}
          <InputBox
            onSend={handleSend}
            isLoading={isLoading}
            placeholder="Ask me anything…"
          />
          <BottomNav activeView={mobileView} onViewChange={setMobileView} />
        </div>
      </div>

      {/* ── Floating Chat Panel (Desktop only) ── */}
      <ChatPanel
        messages={messages}
        isLoading={isLoading}
        onSend={handleSend}
        isOpen={chatOpen}
        onToggle={() => setChatOpen((prev) => !prev)}
        onClose={() => setChatOpen(false)}
      />
    </div>
  );
}
