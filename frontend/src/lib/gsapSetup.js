import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export function homeScroller() {
  return (
    document.querySelector('.view-stage-inner') ||
    document.querySelector('.main-content--home') ||
    document.querySelector('.main-content') ||
    undefined
  );
}

export function homeScrollTrigger(config = {}) {
  const scroller = homeScroller();
  return scroller ? { scroller, ...config } : config;
}

/**
 * Scroll reveal — never call gsap.set(opacity:0) up front.
 * immediateRender:false keeps content visible until the trigger fires.
 */
export function scrollReveal(targets, fromVars, toVars = {}, triggerConfig = {}) {
  if (!targets || (targets.length !== undefined && !targets.length)) return;

  if (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  ) {
    return;
  }

  gsap.fromTo(
    targets,
    fromVars,
    {
      opacity: 1,
      y: 0,
      x: 0,
      scale: 1,
      ...toVars,
      immediateRender: false,
      scrollTrigger: homeScrollTrigger({
        once: true,
        ...triggerConfig,
      }),
    },
  );
}

/** After layout / fonts / images — refresh triggers and unstick anything left hidden */
export function refreshHomeScroll() {
  const scroller = homeScroller();
  if (!scroller) return;

  ScrollTrigger.defaults({ scroller });
  ScrollTrigger.refresh();

  const stuck = scroller.querySelectorAll('.home-experience [data-gsap-hidden]');
  stuck.forEach((el) => {
    gsap.set(el, { clearProps: 'opacity,transform,visibility,clipPath' });
    el.removeAttribute('data-gsap-hidden');
  });
}

export { gsap, ScrollTrigger };
