import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap, homeScrollTrigger } from '../../lib/gsapSetup';

const PRESETS = {
  fadeUp: { opacity: 0, y: 40 },
  fadeIn: { opacity: 0 },
  scaleIn: { opacity: 0, scale: 0.94 },
  slideLeft: { opacity: 0, x: 32 },
  slideRight: { opacity: 0, x: -32 },
};

const RESET = {
  opacity: 1,
  y: 0,
  x: 0,
  scale: 1,
};

export default function GsapReveal({
  children,
  className = '',
  variant = 'fadeUp',
  delay = 0,
  duration = 0.75,
  scrub = false,
  start = 'top 90%',
}) {
  const ref = useRef(null);

  useGSAP(
    () => {
      const el = ref.current;
      if (!el) return;

      if (
        typeof window !== 'undefined' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches
      ) {
        return;
      }

      const from = PRESETS[variant] || PRESETS.fadeUp;

      gsap.fromTo(
        el,
        from,
        {
          ...RESET,
          duration: scrub ? 1 : duration,
          delay,
          ease: scrub ? 'none' : 'power3.out',
          immediateRender: false,
          scrollTrigger: homeScrollTrigger({
            trigger: el,
            start,
            end: scrub ? 'bottom 40%' : undefined,
            scrub: scrub || false,
            once: !scrub,
          }),
        },
      );
    },
    { scope: ref, dependencies: [variant, delay, duration, scrub, start] },
  );

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
