import React from 'react';
import GsapReveal from './GsapReveal';

export default function HomeSection({
  id,
  tag,
  title,
  lead,
  children,
  className = '',
}) {
  return (
    <section className={`hx-block ${className}`.trim()} aria-labelledby={id}>
      <div className="hx-contained">
        {(tag || title || lead) && (
          <GsapReveal variant="fadeUp">
            <header className="hx-block-head">
              {tag ? <span className="hx-block-tag">{tag}</span> : null}
              <div className="hx-block-head-text">
                {title ? (
                  <h2 id={id} className="hx-block-title">
                    {title}
                  </h2>
                ) : null}
                {lead ? <p className="hx-block-lead">{lead}</p> : null}
              </div>
            </header>
          </GsapReveal>
        )}
        {children}
      </div>
    </section>
  );
}
