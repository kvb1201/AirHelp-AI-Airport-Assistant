import React from 'react';

const SWATCHES = [
  { name: 'Gold', var: '--lotus-gold' },
  { name: 'Petal', var: '--lotus-petal' },
  { name: 'Mauve', var: '--lotus-mauve' },
  { name: 'Canvas', var: '--lotus-background' },
  { name: 'Success', var: '--lotus-success' },
  { name: 'Error', var: '--lotus-error' },
];

export default function DesignSystemShowcase({ onBack }) {
  return (
    <div className="design-system-page">
      <button type="button" className="lotus-btn lotus-btn--ghost" onClick={onBack}>
        ← Back to AirHelp
      </button>

      <header style={{ marginTop: 24, marginBottom: 32 }}>
        <p className="hero-kicker">Lotus Travel Experience</p>
        <h1 className="text-headline-lg" style={{ marginTop: 8 }}>
          Design system
        </h1>
        <p className="text-body-md" style={{ marginTop: 12, color: 'var(--lotus-on-surface-variant)' }}>
          Tokens, components, and motion primitives for AirHelp · CSMIA T2.
        </p>
      </header>

      <section className="design-system-section">
        <h2 className="section-title">Color</h2>
        <div className="design-system-grid">
          {SWATCHES.map((s) => (
            <div key={s.name} style={{ textAlign: 'center' }}>
              <div className="design-system-swatch" style={{ background: `var(${s.var})` }} />
              <p className="text-label-sm" style={{ marginTop: 8 }}>{s.name}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="design-system-section">
        <h2 className="section-title">Buttons</h2>
        <div className="design-system-grid">
          <button type="button" className="lotus-btn lotus-btn--primary">Primary</button>
          <button type="button" className="lotus-btn lotus-btn--secondary">Secondary</button>
          <button type="button" className="lotus-btn lotus-btn--ghost">Ghost</button>
          <button type="button" className="lotus-btn lotus-btn--danger">Danger</button>
        </div>
      </section>

      <section className="design-system-section">
        <h2 className="section-title">Glass & cards</h2>
        <div className="lotus-glass" style={{ padding: 20, marginBottom: 12 }}>
          <p className="text-body-md">Glass panel — frosted lotus dock style.</p>
        </div>
        <div className="lotus-petal-card" style={{ padding: 20 }}>
          <p className="text-body-md">Petal card — water shimmer gradient.</p>
        </div>
      </section>

      <section className="design-system-section">
        <h2 className="section-title">Flight status</h2>
        <div className="fids-board" style={{ maxWidth: 480 }}>
          <div className="fids-board__row">
            <span className="fids-board__flight">AI-202</span>
            <span className="fids-board__dest">Delhi</span>
            <span className="fids-board__gate">B14</span>
            <span className="fids-board__time">16:45</span>
            <span className="fids-board__status fids-board__status--ok">ON TIME</span>
          </div>
          <div className="fids-board__row">
            <span className="fids-board__flight">6E-851</span>
            <span className="fids-board__dest">Bangalore</span>
            <span className="fids-board__gate">C7</span>
            <span className="fids-board__time">17:10</span>
            <span className="fids-board__status fids-board__status--boarding">BOARDING</span>
          </div>
          <div className="fids-board__row">
            <span className="fids-board__flight">EK-503</span>
            <span className="fids-board__dest">Dubai</span>
            <span className="fids-board__gate">E11</span>
            <span className="fids-board__time">18:00</span>
            <span className="fids-board__status fids-board__status--delay">DELAYED</span>
          </div>
        </div>
      </section>

      <section className="design-system-section">
        <h2 className="section-title">Typography</h2>
        <p className="text-headline-lg" style={{ marginBottom: 8 }}>Noto Serif headline</p>
        <p className="text-body-lg" style={{ marginBottom: 8 }}>Plus Jakarta Sans body large</p>
        <p className="text-label-sm">LABEL · GATE · ETA</p>
      </section>
    </div>
  );
}
