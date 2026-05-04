import React, { useEffect, useRef } from 'react';

/**
 * Full-screen overlay when the backend returns ``crisis_contact`` (medical / lost / disoriented).
 * Helpline + 112 + official site are shown large with a pulse so they are hard to miss.
 */
export default function CrisisContactOverlay({ data, onDismiss }) {
  const closeRef = useRef(null);

  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();
    const onKey = (e) => {
      if (e.key === 'Escape') onDismiss?.();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
    };
  }, [onDismiss]);

  if (!data) return null;

  const { headline, helpline, helpline_label, emergency_dial, emergency_label, website_url, website_label } =
    data;

  return (
    <div
      className="crisis-overlay-root"
      role="dialog"
      aria-modal="true"
      aria-labelledby="crisis-overlay-title"
      aria-describedby="crisis-overlay-desc"
    >
      <div className="crisis-overlay-scrim" onClick={onDismiss} aria-hidden="true" />
      <div className="crisis-overlay-card">
        <div className="crisis-overlay-badge" aria-hidden="true">
          <span className="ms crisis-overlay-icon">health_and_safety</span>
        </div>
        <h1 id="crisis-overlay-title" className="crisis-overlay-title">
          {headline || 'Airport help'}
        </h1>
        <p id="crisis-overlay-desc" className="crisis-overlay-lede">
          Call or open the official page first — walking directions are in the chat below.
        </p>

        <div className="crisis-flash-stack" aria-live="assertive">
          {emergency_dial ? (
            <a className="crisis-flash-block crisis-flash-block--112" href={`tel:${String(emergency_dial).replace(/\D/g, '')}`}>
              <span className="crisis-flash-label">{emergency_label || 'Emergency'}</span>
              <span className="crisis-flash-value crisis-flash-pulse">{emergency_dial}</span>
              <span className="crisis-flash-hint">Tap to dial</span>
            </a>
          ) : null}

          {helpline ? (
            <a className="crisis-flash-block crisis-flash-block--helpline" href={`tel:${String(helpline).replace(/\D/g, '')}`}>
              <span className="crisis-flash-label">{helpline_label || 'Airport helpline'}</span>
              <span className="crisis-flash-value crisis-flash-pulse">{helpline}</span>
              <span className="crisis-flash-hint">Tap to dial</span>
            </a>
          ) : null}

          {website_url ? (
            <a
              className="crisis-flash-block crisis-flash-block--web"
              href={website_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <span className="crisis-flash-label">{website_label || 'Official website'}</span>
              <span className="crisis-flash-value crisis-flash-web crisis-flash-pulse-soft">{website_url}</span>
              <span className="crisis-flash-hint">Opens in a new tab</span>
            </a>
          ) : null}
        </div>

        <div className="crisis-overlay-actions">
          <button type="button" ref={closeRef} className="crisis-overlay-dismiss" onClick={onDismiss}>
            Continue to chat & map
          </button>
        </div>
      </div>
    </div>
  );
}
