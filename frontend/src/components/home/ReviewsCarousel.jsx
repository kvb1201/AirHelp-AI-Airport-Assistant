import React, { useState, useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap, scrollReveal } from '../../lib/gsapSetup';
import HomeSection from './HomeSection';

export default function ReviewsCarousel({ reviews }) {
  const [index, setIndex] = useState(0);
  const slideRef = useRef(null);
  const current = reviews[index];

  const next = () => setIndex((i) => (i + 1) % reviews.length);
  const prev = () => setIndex((i) => (i - 1 + reviews.length) % reviews.length);

  const rootRef = useRef(null);

  useGSAP(
    () => {
      const root = rootRef.current;
      if (!root) return;
      scrollReveal(
        root.querySelector('.hx-review-stage'),
        { opacity: 0, y: 36 },
        { duration: 0.8, ease: 'power3.out' },
        { trigger: root, start: 'top 85%' },
      );
    },
    { scope: rootRef },
  );

  useGSAP(
    () => {
      const el = slideRef.current;
      if (!el) return;
      gsap.fromTo(
        el,
        { opacity: 0, x: 48 },
        { opacity: 1, x: 0, duration: 0.45, ease: 'power3.out' },
      );
    },
    { dependencies: [index] },
  );

  return (
    <div ref={rootRef}>
    <HomeSection
      id="reviews-carousel-title"
      tag="Voices"
      title="What passengers say"
      lead="Real experiences from Terminal 2 travellers."
      className="hx-reviews-carousel"
    >
      <div className="hx-review-stage">
        <button type="button" className="hx-review-nav hx-review-nav--prev" onClick={prev} aria-label="Previous review">
          <span className="ms" aria-hidden="true">chevron_left</span>
        </button>

        <div className="hx-review-slide-wrap">
          <blockquote ref={slideRef} className="hx-review-slide hx-surface">
            <span className="hx-review-quote-icon ms" aria-hidden="true">format_quote</span>
            <p className="hx-review-quote">&ldquo;{current.quote}&rdquo;</p>
            <footer>
              <cite className="hx-review-author">— {current.author}</cite>
              <span className="hx-review-context">{current.context}</span>
            </footer>
          </blockquote>
        </div>

        <button type="button" className="hx-review-nav hx-review-nav--next" onClick={next} aria-label="Next review">
          <span className="ms" aria-hidden="true">chevron_right</span>
        </button>
      </div>

      <div className="hx-review-dots" role="tablist" aria-label="Review pagination">
        {reviews.map((r, i) => (
          <button
            key={r.author}
            type="button"
            role="tab"
            aria-selected={index === i}
            className={`hx-review-dot${index === i ? ' hx-review-dot--active' : ''}`}
            onClick={() => setIndex(i)}
          />
        ))}
      </div>
    </HomeSection>
    </div>
  );
}
