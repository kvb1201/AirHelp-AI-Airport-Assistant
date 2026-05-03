import React from 'react';

const NAV_ITEMS = [
  { label: 'Home',       icon: 'home',            view: 'home' },
  { label: 'Routes',     icon: 'directions_walk', view: 'nav' },
  { label: 'Facilities', icon: 'apartment',       view: 'facilities' },
  { label: 'Map',        icon: 'map',             view: 'map' },
  { label: 'Profile',    icon: 'account_circle',  view: 'profile' },
];

/**
 * Mobile-only bottom navigation bar.
 */
export default function BottomNav({ activeView, onViewChange }) {
  return (
    <nav className="bottom-nav" aria-label="Mobile navigation">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.label}
          className={`bottom-nav-item ${activeView === item.view ? 'active' : ''}`}
          onClick={() => onViewChange(item.view)}
          aria-label={item.label}
          aria-current={activeView === item.view ? 'page' : undefined}
        >
          <span className="ms">{item.icon}</span>
          <span className="nav-label">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
