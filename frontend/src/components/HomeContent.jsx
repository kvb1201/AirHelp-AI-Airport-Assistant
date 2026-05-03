import React from 'react';

const QUICK_CHIPS = [
  { label: 'Flight status',  icon: 'flight_takeoff', message: 'What is the status of my flight?', location: null },
  { label: 'Terminal map',   icon: 'map',            message: 'Show me the terminal map.',         location: null },
  { label: 'Find lounge',    icon: 'weekend',        message: 'Where is the nearest lounge?',      location: null },
  { label: 'Report an issue',icon: 'report_problem', message: 'I need to report an issue.',        location: null },
];

const SERVICES = [
  { name: 'Flight Status', sub: 'Real-time updates', icon: 'flight',    iconColor: 'pink', message: 'Show me flight status updates.',    location: null },
  { name: 'Airport Map',   sub: 'Navigate easily',   icon: 'location_on', iconColor: 'gold', message: 'Show me the airport map.',        location: null },
  { name: 'Lounges',       sub: 'Relax & unwind',    icon: 'weekend',   iconColor: 'pink', message: 'Where are the airport lounges?',    location: null },
  { name: 'Wi-Fi Access',  sub: 'Stay connected',    icon: 'wifi',      iconColor: 'gold', message: 'How do I connect to airport Wi-Fi?', location: null },
];

export default function HomeContent({ onSend }) {
  const handleChip = (chip) => {
    if (onSend) onSend(chip.message, chip.location);
  };

  return (
    <>
      {/* ── Hero ── */}
      <div className="home-hero">
        <div className="hero-text">
          <h1 className="hero-greeting">Hello, Priya! 👋</h1>
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
          <button className="section-link" aria-label="View all services">View all</button>
        </div>

        <div className="services-grid">
          {SERVICES.map((svc) => (
            <button
              key={svc.name}
              className="service-card"
              onClick={() => onSend && onSend(svc.message, svc.location)}
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
          { label: 'Navigation',       sub: 'Find your way in the airport',       icon: 'map',           message: 'Help me navigate the airport.',  location: 'entrance' },
        ].map((item) => (
          <button
            key={item.label}
            className="mobile-quick-item"
            role="listitem"
            onClick={() => onSend && onSend(item.message, item.location)}
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
