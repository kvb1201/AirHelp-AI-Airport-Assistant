import React from 'react';

const NAV_ITEMS = [
  { label: 'Home', icon: 'home' },
  { label: 'Facilities', icon: 'apartment' },
  { label: 'Lost & Found', icon: 'luggage' },
  { label: 'Navigation', icon: 'directions_walk' },
  { label: 'Map', icon: 'map' },
  { label: 'Operator', icon: 'admin_panel_settings' },
];

export default function Sidebar({ activeNav, onNavChange, onNewChat, onAsk }) {
  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="sidebar-header">
        <div className="brand">
          <div className="brand-logo" aria-hidden="true">
            <span className="ms filled">spa</span>
          </div>
          <span className="brand-name">AirHelp</span>
        </div>

        <button type="button" className="sidebar-ask-btn" onClick={() => onAsk?.()}>
          <span className="ms" aria-hidden="true">forum</span>
          Ask AirHelp
        </button>

        <button type="button" className="new-chat-btn" aria-label="Start a new chat" onClick={() => onNewChat?.()}>
          <span className="ms" aria-hidden="true">add</span>
          New chat
        </button>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.label}
            type="button"
            className={`nav-item ${activeNav === item.label ? 'active' : ''}`}
            onClick={() => onNavChange(item.label)}
            aria-current={activeNav === item.label ? 'page' : undefined}
          >
            <span className="ms" aria-hidden="true">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile" role="button" tabIndex={0} aria-label="User profile">
          <div className="user-avatar" aria-hidden="true">G</div>
          <div>
            <div className="user-name">Guest</div>
            <div className="user-email">Passenger</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
