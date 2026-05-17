import React, { useState, useEffect, useRef } from 'react';
import { gsap } from '../../lib/gsapSetup';

const SLIDES = [
  { gradient: 'linear-gradient(135deg, #f8e1e7 0%, #fff 50%, #fed65b33 100%)', icon: 'flight_takeoff', label: 'Live flights' },
  { gradient: 'linear-gradient(135deg, #e8f4f8 0%, #fff 60%, #f8e1e7 100%)', icon: 'route', label: 'Indoor routes' },
  { gradient: 'linear-gradient(145deg, #fdfbfb 0%, #f4dde3 100%)', icon: 'forum', label: 'Ask anything' },
  { gradient: 'linear-gradient(135deg, #fff9eb 0%, #f8e1e7 100%)', icon: 'qr_code_scanner', label: 'Scan & go' },
];

export default function PillarShowcase({ pillars, hideHeader = false }) {
  const [activeSlide, setActiveSlide] = useState(0);
  const [activePillar, setActivePillar] = useState(0);
  const slideRef = useRef(null);
  const autoRef = useRef(null);

  const pillar = pillars[activePillar] || pillars[0];
  const slide = SLIDES[activeSlide % SLIDES.length];

  useEffect(() => {
    autoRef.current = setInterval(() => {
      setActiveSlide((s) => (s + 1) % SLIDES.length);
    }, 4500);
    return () => clearInterval(autoRef.current);
  }, []);

  useEffect(() => {
    const el = slideRef.current;
    if (!el) return;
    gsap.fromTo(
      el,
      { opacity: 0.6, scale: 0.98 },
      { opacity: 1, scale: 1, duration: 0.35, ease: 'power2.out' },
    );
  }, [activeSlide]);

  const grid = (
    <div className="hx-pillar-showcase-grid">
      <div className="hx-pillar-visual">
        <div className="hx-pillar-carousel">
          <div
            ref={slideRef}
            className="hx-pillar-slide"
            style={{ background: slide.gradient }}
          >
            <span className="ms hx-pillar-slide-icon" aria-hidden="true">{slide.icon}</span>
            <span className="hx-pillar-slide-label">{slide.label}</span>
          </div>
          <div className="hx-pillar-dots" role="tablist" aria-label="Feature slides">
            {SLIDES.map((_, i) => (
              <button
                key={i}
                type="button"
                role="tab"
                aria-selected={activeSlide === i}
                className={`hx-pillar-dot${activeSlide === i ? ' hx-pillar-dot--active' : ''}`}
                onClick={() => setActiveSlide(i)}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="hx-pillar-list" role="list">
        {pillars.map((p, i) => (
          <button
            key={p.title}
            type="button"
            role="listitem"
            className={`hx-pillar-row${activePillar === i ? ' hx-pillar-row--active' : ''}`}
            onClick={() => {
              setActivePillar(i);
              setActiveSlide(i % SLIDES.length);
            }}
          >
            <span className="hx-pillar-row-icon" aria-hidden="true">
              <span className="ms">{p.icon}</span>
            </span>
            <span className="hx-pillar-row-text">
              <span className="hx-pillar-row-title">{p.title}</span>
            </span>
            <span className="hx-pillar-row-chevron ms" aria-hidden="true">chevron_right</span>
          </button>
        ))}
      </div>

      <p className="hx-pillar-active-desc">{pillar?.body}</p>
    </div>
  );

  if (hideHeader) {
    return <div className="hx-pillar-showcase hx-pillar-showcase--embedded">{grid}</div>;
  }

  return (
    <section className="hx-pillar-showcase" aria-labelledby="pillars-showcase-title">
      <div className="hx-contained">
        <h2 id="pillars-showcase-title" className="hx-band-title">
          Everything you need.
        </h2>
        {grid}
      </div>
    </section>
  );
}
