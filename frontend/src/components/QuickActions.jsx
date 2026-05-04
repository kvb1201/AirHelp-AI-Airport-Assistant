import React from 'react';

const ACTIONS = [
  { label: 'At entrance', message: 'I am at Entrance', location: 'entrance' },
  { label: 'At security', message: 'I am at Security', location: 'security' },
  { label: 'Gate B12', message: 'Take me to Gate B12', location: null },
  { label: 'Food nearby', message: 'Show me nearby food options', location: null },
  { label: 'Duty free', message: 'Where is duty free?', location: null },
];

/**
 * Horizontal scroll strip of quick-action pills — shown in mobile bottom area.
 */
export default function QuickActions({ onAction }) {
  return (
    <div className="mobile-quick-actions" role="toolbar" aria-label="Quick actions">
      {ACTIONS.map((action) => (
        <button
          type="button"
          key={action.label}
          className="mobile-qa-btn"
          onClick={() => onAction({ message: action.message, location: action.location })}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
