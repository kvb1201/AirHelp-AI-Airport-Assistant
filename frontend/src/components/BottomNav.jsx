import React from 'react';

const NAV_ITEMS = [
  { label: 'Home', icon: 'home', view: 'home' },
  { label: 'Ask', icon: 'chat', view: 'chat', chatClass: true },
  { label: 'Map', icon: 'map', view: 'map' },
  { label: 'Go', icon: 'directions_walk', view: 'nav' },
  { label: 'More', icon: 'more_horiz', view: 'more' },
];

/**
 * Mobile bottom navigation — floating lotus glass dock (5 primary actions).
 */
export default function BottomNav({ activeView, onViewChange, onMoreOpen }) {
  return (
    <nav className="bottom-nav" aria-label="Mobile navigation">
      {NAV_ITEMS.map((item) => {
        const isMore = item.view === 'more';
        const isActive = isMore
          ? ['facilities', 'lostfound', 'profile', 'operator'].includes(activeView)
          : activeView === item.view;

        return (
          <button
            type="button"
            key={item.label}
            className={`bottom-nav-item${item.chatClass ? ' bottom-nav-item--chat' : ''}${isActive ? ' active' : ''}`}
            onClick={() => (isMore ? onMoreOpen() : onViewChange(item.view))}
            aria-label={item.label}
            aria-current={isActive ? 'page' : undefined}
            aria-haspopup={isMore ? 'menu' : undefined}
          >
            <span className="ms">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
