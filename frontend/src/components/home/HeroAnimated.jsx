import React from 'react';

export default function HeroAnimated({
  greeting,
  locationLabel,
  askValue,
  onAskChange,
  onAskSubmit,
  askRef,
  prompts,
  onPrompt,
}) {
  return (
    <section
      className="hx-zone hx-zone--hero hx-hero hx-hero--cinematic"
      aria-labelledby="home-title"
    >
      <div className="hx-hero-bg" aria-hidden="true" />
      <div className="hx-contained hx-hero-inner">
        <p className="hx-hero-pre">{greeting} · CSMIA Mumbai</p>
        <p className="hx-hero-eyebrow">Your Terminal 2 companion</p>

        <h1 id="home-title" className="hx-hero-stack">
          <span className="hx-hero-line hx-hero-line--1">Welcome to</span>
          <span className="hx-hero-line hx-hero-line--2">Terminal 2</span>
          <span className="hx-hero-line hx-hero-line--accent">with AirHelp</span>
        </h1>

        <p className="hx-hero-sub">
          Flights, walking routes, lounges, and facilities — one calm conversation from curb to gate.
        </p>

        <div className="hx-hero-meta">
          <span className="hx-location">
            <span className="ms" aria-hidden="true">my_location</span>
            {locationLabel}
          </span>
          <span className="hx-status-pill">
            <span className="hx-status-dot" aria-hidden="true" />
            Assistant online
          </span>
        </div>

        <div className="hx-ask-bar hx-ask-bar--hero">
          <span className="ms" aria-hidden="true">chat</span>
          <input
            ref={askRef}
            className="hx-ask-input"
            type="text"
            value={askValue}
            onChange={(e) => onAskChange(e.target.value)}
            placeholder="Where is my gate? Find food near me…"
            aria-label="Ask AirHelp"
            onKeyDown={(e) => {
              if (e.key === 'Enter') onAskSubmit();
            }}
          />
          <button type="button" className="hx-ask-submit" aria-label="Send" onClick={onAskSubmit}>
            <span className="ms" aria-hidden="true">arrow_forward</span>
          </button>
        </div>

        <div className="hx-prompts" role="toolbar" aria-label="Suggested questions">
          {prompts.map((p) => (
            <button key={p.label} type="button" className="hx-prompt" onClick={() => onPrompt(p)}>
              <span className="ms" aria-hidden="true">{p.icon}</span>
              {p.label}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
