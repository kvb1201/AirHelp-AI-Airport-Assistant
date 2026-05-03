import React from 'react';

/**
 * Simple placeholder when a nav item is not fully implemented (desktop sidebar stubs, mobile profile).
 */
export default function PlaceholderView({ title, onBack, backLabel = 'Back to Home', children }) {
  return (
    <div className="placeholder-view" role="region" aria-label={title}>
      <h2 className="placeholder-view-title">{title}</h2>
      {children ? <div className="placeholder-view-body">{children}</div> : null}
      <button type="button" className="nav-flow-btn nav-flow-btn--primary" onClick={onBack}>
        {backLabel}
      </button>
    </div>
  );
}
