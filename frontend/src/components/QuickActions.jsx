import React from 'react';

const ACTIONS = [
  { label: '📍 At Entrance',       message: 'I am at Entrance',    location: 'entrance' },
  { label: '🛡️ At Security',       message: 'I am at Security',    location: 'security' },
  { label: '✈️ Gate B12',           message: 'Take me to Gate B12', location: null },
  { label: '🍔 Nearby Food',        message: 'Show me nearby food options', location: null },
  { label: '🛍️ Duty Free',          message: 'Where is duty free?', location: null },
];

/**
 * Horizontal scrolling strip of quick-action pill buttons.
 * @param {function} onAction - Called with { message, location }
 */
export default function QuickActions({ onAction }) {
  return (
    <div className="quick-actions" role="toolbar" aria-label="Quick actions">
      {ACTIONS.map((action) => (
        <button
          key={action.label}
          className="quick-btn"
          onClick={() => onAction({ message: action.message, location: action.location })}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
