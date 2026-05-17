import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap, scrollReveal, homeScrollTrigger } from '../../lib/gsapSetup';

const STATS = [
  { value: 120, suffix: '+', title: 'Facilities mapped', description: 'Food, lounges, shops, and services indexed across Terminal 2.' },
  { value: 48, suffix: '', title: 'Gates covered', description: 'Walking routes from entrance to gate — step by step.' },
  { value: 24, suffix: '/7', title: 'Assistant online', description: 'Ask about flights, directions, or issues whenever you need clarity.' },
];

export default function StatsBand() {
  const ref = useRef(null);

  useGSAP(
    () => {
      const root = ref.current;
      if (!root) return;

      root.querySelectorAll('.hx-stat-value-num').forEach((el) => {
        const target = Number(el.dataset.value) || 0;
        const obj = { val: 0 };
        gsap.to(obj, {
          val: target,
          duration: 2,
          ease: 'power2.out',
          scrollTrigger: homeScrollTrigger({
            trigger: el,
            start: 'top 88%',
            once: true,
          }),
          onUpdate: () => {
            el.textContent = Math.floor(obj.val).toLocaleString('en-US');
          },
        });
      });

      scrollReveal(
        root.querySelectorAll('.hx-stat'),
        { opacity: 0, y: 40 },
        { duration: 0.75, stagger: 0.12, ease: 'power3.out' },
        { trigger: root, start: 'top 85%' },
      );
    },
    { scope: ref },
  );

  return (
    <section ref={ref} className="hx-stats" aria-label="Terminal coverage">
      <div className="hx-contained">
        <div className="hx-stats-grid">
          {STATS.map((stat) => (
            <article key={stat.title} className="hx-stat">
              <div className="hx-stat-value">
                <span className="hx-stat-value-num" data-value={stat.value}>
                  0
                </span>
                {stat.suffix ? <span className="hx-stat-suffix">{stat.suffix}</span> : null}
              </div>
              <h3 className="hx-stat-title">{stat.title}</h3>
              <p className="hx-stat-desc">{stat.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
