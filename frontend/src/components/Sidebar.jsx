import React, { useState } from 'react';

const NAV_ITEMS = [
  { label: 'Home',         icon: 'home',          active: true },
  { label: 'Flights',      icon: 'flight_takeoff', active: false },
  { label: 'Facilities',   icon: 'apartment',      active: false },
  { label: 'Map',          icon: 'map',            active: false },
  { label: 'My Trips',     icon: 'work',           active: false },
  { label: 'Help & Support', icon: 'help',         active: false },
  { label: 'Settings',     icon: 'settings',       active: false },
];

export default function Sidebar() {
  const [activeItem, setActiveItem] = useState('Home');

  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      {/* Brand */}
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

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.label}
            className={`nav-item ${activeItem === item.label ? 'active' : ''}`}
            onClick={() => setActiveItem(item.label)}
            aria-current={activeItem === item.label ? 'page' : undefined}
          >
            <span className="ms">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* User Profile */}
      <div className="sidebar-footer">
        <div className="user-profile" role="button" tabIndex={0} aria-label="User profile">
          <div className="user-avatar" aria-hidden="true">P</div>
          <div>
            <div className="user-name">Priya</div>
            <div className="user-email">priya@airhelp.in</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
