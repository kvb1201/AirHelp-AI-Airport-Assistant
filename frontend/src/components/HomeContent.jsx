import React, { useState, useEffect, useRef, useCallback } from 'react';
import BoardingPassUpload from './BoardingPassUpload';

const QUICK_CHIPS = [
  { label: 'Flight status',   icon: 'flight_takeoff', message: 'What is the status of my flight?', location: null },
  { label: 'Walking routes', icon: 'directions_walk', action: 'navigation' },
  { label: 'Floor map',      icon: 'map',             action: 'floor_map' },
  { label: 'Find lounge',    icon: 'weekend',         message: 'Where is the nearest lounge?',      location: null },
  { label: 'Report an issue', icon: 'report_problem', action: 'report_issue' },
];

const SERVICES = [
  { name: 'Flight Status', sub: 'Real-time updates', icon: 'flight', iconColor: 'pink', message: 'Show me flight status updates.', location: null },
  { name: 'Flight Queries', sub: 'Save or scan boarding pass', icon: 'event', iconColor: 'gold', action: 'flight_queries' },
  { name: 'Walking Routes', sub: 'Compare paths A→B', icon: 'directions_walk', iconColor: 'gold', action: 'navigation' },
  { name: 'Floor Map', sub: 'Tap the terminal plan', icon: 'location_on', iconColor: 'gold', action: 'floor_map' },
  { name: 'Lounges', sub: 'Relax & unwind', icon: 'weekend', iconColor: 'pink', message: 'Where are the airport lounges?', location: null },
  { name: 'Wi-Fi Access', sub: 'Stay connected', icon: 'wifi', iconColor: 'gold', message: 'How do I connect to airport Wi-Fi?', location: null },
];

const DEPARTURE_FEED = [
  { flight: 'AI-202',  dest: 'Delhi',     gate: 'B14', time: '16:45', status: 'ON TIME' },
  { flight: '6E-851',  dest: 'Bangalore', gate: 'C7',  time: '17:10', status: 'BOARDING' },
  { flight: 'UK-972',  dest: 'London',    gate: 'D3',  time: '17:30', status: 'ON TIME' },
  { flight: 'EK-503',  dest: 'Dubai',     gate: 'E11', time: '18:00', status: 'DELAYED' },
  { flight: 'SG-181',  dest: 'Hyderabad', gate: 'B9',  time: '18:20', status: 'ON TIME' },
];

const STATS = [
  { value: '120+', label: 'Daily Flights' },
  { value: '47',   label: 'AI Map Nodes' },
  { value: '3',    label: 'Route Options' },
  { value: '24/7', label: 'AI Support' },
];

const TIPS = [
  { icon: 'schedule', title: 'Arrive early', body: 'Allow 2–3 hours for international flights. Security and immigration can be busy during peak hours.' },
  { icon: 'luggage', title: 'Baggage limits', body: 'Check-in baggage is typically 15–23 kg. Keep liquids under 100ml in a clear bag for carry-on.' },
  { icon: 'currency_rupee', title: 'Currency exchange', body: 'Exchange counters are available before and after immigration on Level 2.' },
  { icon: 'wifi', title: 'Free Wi-Fi', body: 'Connect to "CSMIA_Free_WiFi" and verify with your phone number for 45 minutes of complimentary access.' },
];

function statusClass(status) {
  if (status === 'BOARDING') return 'fids-board__status--boarding';
  if (status === 'DELAYED') return 'fids-board__status--delay';
  return 'fids-board__status--ok';
}

function useScrollReveal() {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); } }),
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );
    const items = el.querySelectorAll('.reveal');
    items.forEach((item) => observer.observe(item));
    return () => items.forEach((item) => observer.unobserve(item));
  }, []);
  return ref;
}

export default function HomeContent({ onSend, onOpenNavigation, onOpenFloorMap, onOpenReportIssue, onOpenFlightQueries }) {
  const [time, setTime] = useState(new Date());
  useEffect(() => { const id = setInterval(() => setTime(new Date()), 60000); return () => clearInterval(id); }, []);
  const scrollRef = useScrollReveal();

  const greeting = time.getHours() < 12 ? 'Good morning' : time.getHours() < 17 ? 'Good afternoon' : 'Good evening';

  const handleChip = (chip) => {
    if (chip.action === 'navigation' && onOpenNavigation) { onOpenNavigation(); return; }
    if (chip.action === 'floor_map' && onOpenFloorMap) { onOpenFloorMap(null); return; }
    if (chip.action === 'flight_queries' && onOpenFlightQueries) { onOpenFlightQueries(); return; }
    if (chip.action === 'report_issue') {
      if (onOpenReportIssue) onOpenReportIssue();
      else if (onSend) onSend('I need to report an issue.', chip.location ?? null);
      return;
    }
    if (onSend) onSend(chip.message, chip.location);
  };

  const handleService = (svc) => {
    if (svc.action === 'navigation' && onOpenNavigation) onOpenNavigation();
    else if (svc.action === 'floor_map' && onOpenFloorMap) onOpenFloorMap(null);
    else if (svc.action === 'flight_queries' && typeof onOpenFlightQueries === 'function') onOpenFlightQueries();
    else if (onSend) onSend(svc.message, svc.location);
  };

  return (
    <div ref={scrollRef}>
      {/* ── Hero ── */}
      <div className="home-hero">
        <div className="hero-text">
          <div className="hero-kicker">CSMIA · Terminal 2 · Mumbai</div>
          <h1 className="hero-greeting">{greeting}</h1>
          <p className="hero-subtitle">
            Your AI airport companion — flights, walking routes, facilities, and live support at your fingertips.
          </p>

          <div className="hero-search">
            <span className="ms">search</span>
            <input
              className="hero-search-input"
              type="text"
              placeholder="Ask anything — flights, gates, lounges..."
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
                if (input.value.trim()) { onSend(input.value.trim(), null); input.value = ''; }
              }}
            >
              <span className="ms">arrow_forward</span>
            </button>
          </div>

          <div className="quick-chips" role="toolbar" aria-label="Quick actions">
            {QUICK_CHIPS.map((chip) => (
              <button type="button" key={chip.label} className="quick-chip" onClick={() => handleChip(chip)} aria-label={chip.label}>
                <span className="ms">{chip.icon}</span>
                {chip.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Stats Row ── */}
      <div className="stats-row">
        {STATS.map((s, i) => (
          <div key={s.label} className={`stat-card reveal reveal-delay-${i + 1}`}>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Services ── */}
      <section className="section reveal" aria-label="Popular services">
        <div className="section-header">
          <h2 className="section-title">Services</h2>
        </div>
        <div className="services-grid">
          {SERVICES.map((svc, i) => (
            <button type="button" key={svc.name} className={`service-card reveal reveal-delay-${i + 1}`} onClick={() => handleService(svc)} aria-label={svc.name}>
              <div className={`service-icon ${svc.iconColor}`}>
                <span className="ms">{svc.icon}</span>
              </div>
              <div className="service-name">{svc.name}</div>
              <div className="service-sub">{svc.sub}</div>
            </button>
          ))}
        </div>
      </section>

      {/* ── Travel Tips ── */}
      <section className="section reveal" aria-label="Travel tips">
        <div className="section-header">
          <h2 className="section-title">Travel Tips</h2>
        </div>
        <div className="tips-grid">
          {TIPS.map((tip, i) => (
            <div key={tip.title} className={`tip-card reveal reveal-delay-${i + 1}`}>
              <div className="tip-icon">
                <span className="ms">{tip.icon}</span>
              </div>
              <div className="tip-content">
                <div className="tip-title">{tip.title}</div>
                <div className="tip-body">{tip.body}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Departures Board ── */}
      <section className="section reveal" aria-label="Departures">
        <div className="section-header">
          <h2 className="section-title">Upcoming Departures</h2>
          <button type="button" className="section-link" onClick={() => onSend && onSend('Show all departures', null)}>View all</button>
        </div>

        <div className="fids-board">
          <div className="fids-board__header">
            <span>Flight</span>
            <span>Destination</span>
            <span>Gate</span>
            <span>Time</span>
            <span>Status</span>
          </div>
          {DEPARTURE_FEED.map((dep, i) => (
            <div key={dep.flight} className={`fids-board__row reveal reveal-delay-${i + 1}`}>
              <span className="fids-board__flight">{dep.flight}</span>
              <span className="fids-board__dest">{dep.dest}</span>
              <span className="fids-board__gate">{dep.gate}</span>
              <span className="fids-board__time">{dep.time}</span>
              <span className={`fids-board__status ${statusClass(dep.status)}`}>{dep.status}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Mobile Quick Actions ── */}
      <div className="mobile-quick-list" role="list" aria-label="Quick navigation">
        {[
          { label: 'Flight status',    sub: 'Check real-time flight information', icon: 'flight_takeoff', message: 'What is the flight status?',    location: null },
          { label: 'Airport facilities', sub: 'Find lounges, restaurants, services', icon: 'apartment',  message: 'Show me airport facilities.',    location: null },
          { label: 'Report an issue',  sub: 'Describe the problem and get a ticket number',    icon: 'report_problem', action: 'report_issue' },
          { label: 'Walking directions', sub: 'From / to, then pick one of three routes', icon: 'directions_walk', action: 'navigation' },
        ].map((item) => (
          <button
            type="button"
            key={item.label}
            className="mobile-quick-item"
            role="listitem"
            onClick={() => {
              if (item.action === 'navigation' && onOpenNavigation) onOpenNavigation();
              else if (item.action === 'report_issue') {
                if (onOpenReportIssue) onOpenReportIssue();
                else if (onSend) onSend('I need to report an issue.', item.location ?? null);
              } else if (onSend) onSend(item.message, item.location);
            }}
          >
            <div className="mqi-icon">
              <span className="ms">{item.icon}</span>
            </div>
            <div className="mqi-text">
              <h4>{item.label}</h4>
              <p>{item.sub}</p>
            </div>
            <span className="ms" style={{ color: 'var(--text-muted)', marginLeft: 'auto' }}>chevron_right</span>
          </button>
        ))}
      </div>

      {/* ── Assistance Banner ── */}
      <div className="assistance-banner reveal" role="complementary" aria-label="Assistance">
        <div className="assistance-info">
          <div className="assistance-icon" aria-hidden="true">
            <span className="ms">help</span>
          </div>
          <div className="assistance-text">
            <h4>Need help?</h4>
            <p>Report an issue or request live assistance from airport staff.</p>
          </div>
        </div>
        <button
          type="button"
          className="assistance-btn"
          onClick={() => {
            if (onOpenReportIssue) onOpenReportIssue();
            else if (onSend) onSend('I need assistance from the support team.', null);
          }}
        >
          <span className="ms">support_agent</span>
          Get Support
        </button>
      </div>

      {/* ── Boarding Pass ── */}
      <BoardingPassUpload onBoardingPassProcessed={(data) => {
        if (onSend) {
          onSend(`I've uploaded my boarding pass. Flight: ${data.flight_number}, Gate: ${data.gate}, Seat: ${data.seat}. Can you help me navigate?`, null);
        }
      }} />
    </div>
  );
}
