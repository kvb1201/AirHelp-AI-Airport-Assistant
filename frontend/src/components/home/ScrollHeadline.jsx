import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap, homeScrollTrigger } from '../../lib/gsapSetup';

export default function ScrollHeadline() {
  const ref = useRef(null);

  useGSAP(
    () => {
      const track = ref.current?.querySelector('.hx-scroll-headline-track');
      if (!track) return;

      gsap.to(track, {
        xPercent: -15,
        ease: 'none',
        scrollTrigger: homeScrollTrigger({
          trigger: ref.current,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 1,
        }),
      });
    },
    { scope: ref },
  );

  return (
    <section ref={ref} className="hx-scroll-headline" aria-hidden="true">
      <div className="hx-scroll-headline-track">
        <span>EXPERIENCE THE TERMINAL</span>
        <span>·</span>
        <span>EXPERIENCE THE TERMINAL</span>
        <span>·</span>
        <span>EXPERIENCE THE TERMINAL</span>
      </div>
    </section>
  );
}
