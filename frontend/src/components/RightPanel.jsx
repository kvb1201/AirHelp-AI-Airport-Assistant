import React, { useState, useEffect } from 'react';

export default function RightPanel() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
  const [hourMin, ampm] = timeStr.split(' ');
  const dateStr = time.toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' });

  return (
    <aside className="right-panel" aria-label="Flight and weather info">

      {/* ── Weather Widget ── */}
      <div className="widget" aria-label="Current weather at DEL">
        <div className="widget-label">Current at DEL</div>
        <div className="weather-row">
          <div className="weather-icon">
            <span className="ms">wb_cloudy</span>
          </div>
          <div>
            <div className="weather-temp">32°C</div>
            <div className="weather-desc">Haze</div>
          </div>
        </div>
      </div>

      {/* ── Time Widget ── */}
      <div className="widget time-widget" aria-label="Local time">
        <div className="widget-label">Local Time</div>
        <div className="time-display">
          {hourMin}
          <span className="time-ampm">{ampm}</span>
        </div>
        <div className="time-date">{dateStr}</div>
      </div>

      {/* ── My Trip Widget ── */}
      <div className="widget trip-widget" aria-label="My trip details">
        <div className="trip-header">
          <span className="widget-label">My Trip</span>
          <span className="trip-status">On Time</span>
        </div>

        <div className="trip-flight-number">AI 143</div>

        <div className="trip-route">
          <div className="trip-airport">
            <div className="trip-code">DEL</div>
            <div className="trip-city">Delhi</div>
          </div>
          <div className="trip-arrow">
            <span className="ms">arrow_forward</span>
          </div>
          <div className="trip-airport" style={{ textAlign: 'right' }}>
            <div className="trip-code">BOM</div>
            <div className="trip-city">Mumbai</div>
          </div>
        </div>

        <div className="trip-details">
          <div className="trip-detail-item">
            <div className="trip-detail-label">Terminal</div>
            <div className="trip-detail-value">Terminal 3</div>
          </div>
          <div className="trip-detail-item">
            <div className="trip-detail-label">Gate</div>
            <div className="trip-detail-value">Gate 24</div>
          </div>
          <div className="trip-detail-item">
            <div className="trip-detail-label">Boarding</div>
            <div className="trip-detail-value">11:20 AM</div>
          </div>
        </div>
      </div>

    </aside>
  );
}
