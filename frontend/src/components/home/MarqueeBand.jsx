import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '../../lib/gsapSetup';

export default function MarqueeBand({ items = ['ASK', 'NAVIGATE', 'FLY', 'RELAX', 'DISCOVER'] }) {
  const trackRef = useRef(null);
  const wrapRef = useRef(null);
  const sequence = [...items, ...items, ...items];

  useGSAP(
    () => {
      const track = trackRef.current;
      if (!track) return;

      const half = track.scrollWidth / 3;

      gsap.to(track, {
        x: -half,
        duration: 28,
        ease: 'none',
        repeat: -1,
      });
    },
    { scope: wrapRef },
  );

  return (
    <div ref={wrapRef} className="hx-marquee" aria-hidden="true">
      <div ref={trackRef} className="hx-marquee-track hx-marquee-track--gsap">
        {sequence.map((item, i) => (
          <span key={`${item}-${i}`} className="hx-marquee-item">
            {item}
            <span className="hx-marquee-dot">·</span>
          </span>
        ))}
      </div>
    </div>
  );
}
