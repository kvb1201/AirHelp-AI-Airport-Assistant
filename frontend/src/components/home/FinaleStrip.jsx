import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap, scrollReveal } from '../../lib/gsapSetup';

export default function FinaleStrip({ onOpenChat }) {
  const ref = useRef(null);

  useGSAP(
    () => {
      const el = ref.current;
      if (!el) return;

      scrollReveal(
        el.querySelectorAll('.hx-finale-inner > *'),
        { opacity: 0, y: 32 },
        { duration: 0.8, stagger: 0.12, ease: 'power3.out' },
        { trigger: el, start: 'top 85%' },
      );
    },
    { scope: ref },
  );

  return (
    <section ref={ref} className="hx-zone hx-zone--finale hx-finale" aria-label="Get started">
      <div className="hx-finale-inner">
        <h2 className="hx-finale-title">Ready when you are.</h2>
        <p className="hx-finale-sub">One tap. One question. Your terminal, understood.</p>
        <button type="button" className="hx-finale-cta" onClick={() => onOpenChat?.()}>
          <span className="ms" aria-hidden="true">forum</span>
          Ask AirHelp now
        </button>
      </div>
    </section>
  );
}
