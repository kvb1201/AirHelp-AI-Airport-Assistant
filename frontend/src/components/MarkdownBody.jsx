import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/** Renders assistant Markdown (GFM) for chat bubbles and map preview lines. */
export default function MarkdownBody({ children, className = '' }) {
  const c = typeof children === 'string' ? children : '';
  return (
    <div className={`bubble-md-root ${className}`.trim()}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{c}</ReactMarkdown>
    </div>
  );
}
