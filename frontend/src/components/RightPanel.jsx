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
    <aside className="right-panel" aria-label="Weather and local time">

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

    </aside>
  );
}
