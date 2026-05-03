import React from 'react';

const NAV_ITEMS = [
  { label: 'Home', icon: 'home', active: true },
  { label: 'Flights', icon: 'flight_takeoff', active: false },
  { label: 'Facilities', icon: 'apartment', active: false },
  { label: 'Navigation', icon: 'directions_walk', active: false },
  { label: 'Map', icon: 'map', active: false },
  { label: 'My Trips', icon: 'work', active: false },
  { label: 'Help & Support', icon: 'help', active: false },
  { label: 'Settings', icon: 'settings', active: false },
];

export default function Sidebar({ activeNav, onNavChange }) {
  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="sidebar-header">
        <div className="brand">
          <div className="brand-logo" aria-hidden="true">
            <span className="ms">flight</span>
          </div>
          <span className="brand-name">AirHelp</span>
        </div>

        <button className="new-chat-btn" aria-label="Start a new chat">
          <span className="ms">add</span>
          New Chat
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
            <span className="ms">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile" role="button" tabIndex={0} aria-label="User profile">
          <div className="user-avatar" aria-hidden="true">G</div>
          <div>
            <div className="user-name">Guest</div>
            <div className="user-email">guest@example.com</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
