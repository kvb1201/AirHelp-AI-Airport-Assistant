import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { scrollReveal } from '../../lib/gsapSetup';
import GsapReveal from './GsapReveal';

export default function StoryAnimated({ onOpenChat }) {
  const ref = useRef(null);

  useGSAP(
    () => {
      const section = ref.current;
      if (!section) return;

      scrollReveal(
        section.querySelectorAll('.hx-story-copy > p'),
        { opacity: 0, y: 24 },
        { duration: 0.7, stagger: 0.12, ease: 'power3.out' },
        { trigger: section.querySelector('.hx-story-copy'), start: 'top 85%' },
      );

      scrollReveal(
        section.querySelector('.hx-story-card'),
        { opacity: 0, x: 48, scale: 0.96 },
        { duration: 1, ease: 'power3.out' },
        { trigger: section.querySelector('.hx-story-visual'), start: 'top 80%' },
      );
    },
    { scope: ref },
  );

  return (
    <section ref={ref} className="hx-block hx-story" aria-labelledby="story-title">
      <div className="hx-contained">
        <header className="hx-block-head">
          <span className="hx-block-tag">About</span>
          <h2 id="story-title" className="hx-block-title">
            What is AirHelp
          </h2>
        </header>

        <div className="hx-story-grid">
          <div className="hx-story-copy">
            <p className="hx-story-lead">
              AirHelp is your intelligent companion inside CSMIA Terminal 2. Unlike static signage,
              it understands where you are and guides you in plain language.
            </p>
            <p className="hx-story-body">
              Ask about gates, lounges, or facilities. Upload a boarding pass and we read your flight,
              gate, and seat — every answer is grounded in the real T2 floor plan.
            </p>
            <GsapReveal>
              <button type="button" className="hx-cta-outline" onClick={() => onOpenChat?.()}>
                Start a conversation
                <span className="ms" aria-hidden="true">arrow_forward</span>
              </button>
            </GsapReveal>
          </div>
          <GsapReveal className="hx-story-visual" variant="slideLeft">
            <div className="hx-story-card hx-surface">
              <span className="hx-story-card-tag">Terminal 2</span>
              <p className="hx-story-card-stat">
                <strong>1</strong>
                <span>companion for every gate, lounge, and walkway</span>
              </p>
              <ul className="hx-story-card-list">
                <li><span className="ms" aria-hidden="true">forum</span> Chat & voice</li>
                <li><span className="ms" aria-hidden="true">route</span> Indoor routes</li>
                <li><span className="ms" aria-hidden="true">flight</span> Live FIDS</li>
              </ul>
            </div>
          </GsapReveal>
        </div>
      </div>
    </section>
  );
}
