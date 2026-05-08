import React, { useState, useEffect } from 'react';

export default function RightPanel() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
  const [hourMin, ampm] = timeStr.split(' ');
  const dateStr = time.toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' });

  return (
    <aside className="right-panel" aria-label="Info panel">

      <div className="widget time-widget" aria-label="Local time">
        <div className="widget-label">Local Time</div>
        <div className="time-display">
          {hourMin}
          <span className="time-ampm">{ampm}</span>
        </div>
        <div className="time-date">{dateStr}</div>
      </div>

      <div className="widget" aria-label="Current weather">
        <div className="widget-label">Weather · Mumbai</div>
        <div className="weather-row">
          <div className="weather-icon">
            <span className="ms filled">wb_sunny</span>
          </div>
          <div>
            <div className="weather-temp">32°C</div>
            <div className="weather-desc">Haze</div>
          </div>
        </div>
      </div>

      <div className="widget" aria-label="Terminal info">
        <div className="widget-label">Terminal</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, lineHeight: 1.5, color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Airport</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>BOM / CSMIA</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Terminal</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>T2 International</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Floor</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>L2 Departures</span>
          </div>
        </div>
      </div>

    </aside>
  );
}
