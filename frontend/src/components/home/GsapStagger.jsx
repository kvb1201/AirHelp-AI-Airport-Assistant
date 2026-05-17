import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap, homeScrollTrigger } from '../../lib/gsapSetup';

export default function GsapStagger({
  children,
  className = '',
  selector = '.gsap-stagger-item',
  stagger = 0.08,
  y = 32,
}) {
  const ref = useRef(null);

  useGSAP(
    () => {
      const root = ref.current;
      if (!root) return;

      const items = root.querySelectorAll(selector);
      if (!items.length) return;

      if (
        typeof window !== 'undefined' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches
      ) {
        return;
      }

      gsap.fromTo(
        items,
        { opacity: 0, y },
        {
          opacity: 1,
          y: 0,
          duration: 0.65,
          stagger,
          ease: 'power3.out',
          immediateRender: false,
          scrollTrigger: homeScrollTrigger({
            trigger: root,
            start: 'top 88%',
            once: true,
          }),
        },
      );
    },
    { scope: ref },
  );

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
