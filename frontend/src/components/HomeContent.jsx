import React from 'react';

const QUICK_CHIPS = [
  { label: 'Flight status',   icon: 'flight_takeoff', message: 'What is the status of my flight?', location: null },
  { label: 'Walking routes', icon: 'directions_walk', action: 'navigation' },
  { label: 'Floor map',      icon: 'map',             action: 'floor_map' },
  { label: 'Find lounge',    icon: 'weekend',         message: 'Where is the nearest lounge?',      location: null },
  { label: 'Report an issue', icon: 'report_problem', message: 'I need to report an issue.',        location: null },
];

const SERVICES = [
  { name: 'Flight Status', sub: 'Real-time updates', icon: 'flight',    iconColor: 'pink', message: 'Show me flight status updates.',    location: null },
  { name: 'Flight Queries', sub: 'Save or scan boarding pass', icon: 'event', iconColor: 'gold', action: 'flight_queries' },
  { name: 'Walking routes', sub: 'Compare paths A→B', icon: 'directions_walk', iconColor: 'gold', action: 'navigation' },
  { name: 'Floor map',   sub: 'Tap the terminal plan', icon: 'location_on', iconColor: 'gold', action: 'floor_map' },
  { name: 'Lounges',       sub: 'Relax & unwind',    icon: 'weekend',   iconColor: 'pink', message: 'Where are the airport lounges?',    location: null },
  { name: 'Wi-Fi Access',  sub: 'Stay connected',    icon: 'wifi',      iconColor: 'gold', message: 'How do I connect to airport Wi-Fi?', location: null },
];

export default function HomeContent({ onSend, onOpenNavigation, onOpenFloorMap, onOpenFlightQueries }) {
  const handleChip = (chip) => {
    if (chip.action === 'navigation' && onOpenNavigation) {
      onOpenNavigation();
      return;
    }
    if (chip.action === 'floor_map' && onOpenFloorMap) {
      onOpenFloorMap(null);
      return;
    }
    if (onSend) onSend(chip.message, chip.location);
  };

  return (
    <>
      {/* ── Hero ── */}
      <div className="home-hero">
        <div className="hero-text">
          <h1 className="hero-greeting">Hello! 👋</h1>
          <p className="hero-subtitle">Your smart travel companion at every step.</p>

          {/* Search bar */}
          <div className="hero-search">
            <span className="ms">search</span>
            <input
              className="hero-search-input"
              type="text"
              placeholder="What can I help you with?"
              aria-label="Search"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.target.value.trim()) {
                  onSend(e.target.value.trim(), null);
                  e.target.value = '';
                }
              }}
            />
            <button
              type="button"
              className="hero-search-btn"
              aria-label="Submit search"
              onClick={(e) => {
                const input = e.currentTarget.closest('.hero-search').querySelector('input');
                if (input.value.trim()) {
                  onSend(input.value.trim(), null);
                  input.value = '';
                }
              }}
            >
              <span className="ms">send</span>
            </button>
          </div>

          {/* Quick chips */}
          <div className="quick-chips" role="toolbar" aria-label="Quick actions">
            {QUICK_CHIPS.map((chip) => (
              <button
                type="button"
                key={chip.label}
                className="quick-chip"
                onClick={() => handleChip(chip)}
                aria-label={chip.label}
              >
                <span className="ms">{chip.icon}</span>
                {chip.label}
              </button>
            ))}
          </div>
        </div>

        {/* Bot illustration (desktop only) */}
        <div className="hero-illustration" aria-hidden="true">
          <div className="bot-orb">
            <span className="ms">smart_toy</span>
          </div>
        </div>
      </div>

      {/* ── Popular Services ── */}
      <section className="section" aria-label="Popular services">
        <div className="section-header">
          <h2 className="section-title">Popular Services</h2>
          <button
            type="button"
            className="section-link"
            aria-label="View all services"
            onClick={() => document.querySelector('.services-grid')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
          >
            View all
          </button>
        </div>

        <div className="services-grid">
          {SERVICES.map((svc) => (
            <button
              type="button"
              key={svc.name}
              className="service-card"
              onClick={() => {
                  if (svc.action === 'navigation' && onOpenNavigation) onOpenNavigation();
                  else if (svc.action === 'floor_map' && onOpenFloorMap) onOpenFloorMap(null);
                  else if (svc.action === 'flight_queries' && typeof onOpenFlightQueries === 'function') onOpenFlightQueries();
                  else if (onSend) onSend(svc.message, svc.location);
                }}
              aria-label={svc.name}
            >
              <div className={`service-icon ${svc.iconColor}`}>
                <span className="ms">{svc.icon}</span>
              </div>
              <div className="service-name">{svc.name}</div>
              <div className="service-sub">{svc.sub}</div>
            </button>
          ))}
        </div>
      </section>

      {/* ── Mobile Quick Actions ── */}
      <div className="mobile-quick-list" role="list" aria-label="Quick navigation">
        {[
          { label: 'Flight status',    sub: 'Check real-time flight information', icon: 'flight_takeoff', message: 'What is the flight status?',    location: null },
          { label: 'Airport facilities', sub: 'Find lounges, restaurants, services', icon: 'apartment',  message: 'Show me airport facilities.',    location: null },
          { label: 'Report an issue',  sub: 'Get help with any airport issue',    icon: 'report_problem', message: 'I need to report an issue.',    location: null },
          { label: 'Walking directions', sub: 'From / to, then pick one of three routes', icon: 'directions_walk', action: 'navigation' },
        ].map((item) => (
          <button
            type="button"
            key={item.label}
            className="mobile-quick-item"
            role="listitem"
            onClick={() => {
              if (item.action === 'navigation' && onOpenNavigation) onOpenNavigation();
              else if (onSend) onSend(item.message, item.location);
            }}
          >
            <div className="mqi-icon">
              <span className="ms">{item.icon}</span>
            </div>
            <div className="mqi-text">
              <h4>{item.label}</h4>
              <p>{item.sub}</p>
            </div>
            <span className="ms" style={{ color: 'var(--outline-variant)', marginLeft: 'auto' }}>
              chevron_right
            </span>
          </button>
        ))}
      </div>

      {/* ── Need Assistance Banner ── */}
      <div className="assistance-banner" role="complementary" aria-label="Assistance">
        <div className="assistance-info">
          <div className="assistance-icon">
            <span className="ms">smart_toy</span>
          </div>
          <div className="assistance-text">
            <h4>Need assistance?</h4>
            <p>Report an issue or request help from our support team.</p>
          </div>
        </div>
        <button
          type="button"
          className="assistance-btn"
          onClick={() => onSend && onSend('I need assistance from the support team.', null)}
        >
          <span className="ms">support_agent</span>
          Report an Issue
        </button>
      </div>
    </>
  );
}
