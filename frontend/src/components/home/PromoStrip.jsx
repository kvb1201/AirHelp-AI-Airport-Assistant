import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap, homeScrollTrigger } from '../../lib/gsapSetup';

export default function PromoStrip() {
  const ref = useRef(null);

  useGSAP(
    () => {
      const section = ref.current;
      if (!section) return;

      if (
        typeof window !== 'undefined' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches
      ) {
        return;
      }

      const reveal = section.querySelector('.hx-promo-reveal');
      if (!reveal) return;

      gsap.fromTo(
        reveal,
        { clipPath: 'polygon(0 0, 100% 0, 100% 0, 0 0)' },
        {
          clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)',
          duration: 1,
          ease: 'power2.inOut',
          immediateRender: false,
          scrollTrigger: homeScrollTrigger({
            trigger: section,
            start: 'top 88%',
            once: true,
          }),
        },
      );

      const tl = gsap.timeline({
        scrollTrigger: homeScrollTrigger({
          trigger: section,
          start: 'top 80%',
          once: true,
        }),
        delay: 0.2,
      });

      tl.from('.hx-promo-top, .hx-promo-bottom', {
        opacity: 0,
        y: 16,
        duration: 0.7,
        stagger: 0.12,
        ease: 'power2.out',
      }).from(
        '.hx-promo-center',
        { opacity: 0, scale: 0.96, duration: 0.5, ease: 'back.out(1.4)' },
        '-=0.35',
      );
    },
    { scope: ref },
  );

  return (
    <section ref={ref} className="hx-promo" aria-label="AirHelp experience">
      <div className="hx-promo-inner">
        <h2 className="hx-promo-top">
          EXPERIENCE MUMBAI&apos;S FIRST AI TERMINAL COMPANION
        </h2>
        <div className="hx-promo-reveal">
          <div className="hx-promo-reveal-inner">
            <p className="hx-promo-center">Calm · Clear · Always on</p>
          </div>
        </div>
        <h2 className="hx-promo-bottom">
          GUIDANCE FROM CURB TO GATE — IN ONE CONVERSATION
        </h2>
      </div>
    </section>
  );
}
