import React from 'react';

const MENU_ITEMS = [
  { label: 'Home', icon: '🏠' },
  { label: 'Flights', icon: '✈️' },
  { label: 'Facilities', icon: '🏢' },
  { label: 'Map', icon: '🗺️' },
  { label: 'My Trips', icon: '🎒' },
  { label: 'Help & Support', icon: '❓' },
  { label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand">
          <div className="brand-logo">✈️</div>
          <h2>AirHelp</h2>
        </div>
        <button className="new-chat-btn">
          <span>+</span> New Chat
        </button>
      </div>

      <nav className="sidebar-nav">
        {MENU_ITEMS.map((item) => (
          <button key={item.label} className="nav-btn">
            <span className="nav-icon" aria-hidden="true">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="avatar">P</div>
          <span className="username">Priya</span>
        </div>
      </div>
    </aside>
  );
}
