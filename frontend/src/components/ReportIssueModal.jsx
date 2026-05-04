import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createSupportTicket, fetchTicketCategories } from '../services/api';

/** Mirrors backend `ISSUE_CATEGORIES` if the category endpoint is unreachable. */
const FALLBACK_CATEGORIES = [
  { id: 'wrong_information', label: 'Wrong or outdated information' },
  { id: 'app_issue', label: 'Problem with AirHelp (this app)' },
  { id: 'directions_or_map', label: 'Directions or map did not match the terminal' },
  { id: 'accessibility', label: 'Accessibility or special assistance' },
  { id: 'safety_security', label: 'Safety or security' },
  { id: 'other', label: 'Something else' },
];

/**
 * Multi-step issue report: category → what happened → optional context → ticket id.
 */
export default function ReportIssueModal({ open, onClose, graphLocationId, onTicketCreated }) {
  const closeBtnRef = useRef(null);
  const [step, setStep] = useState(1);
  const [categories, setCategories] = useState([]);
  const [catLoading, setCatLoading] = useState(false);
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [whereHint, setWhereHint] = useState('');
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState('');
  const [result, setResult] = useState(null);

  const reset = useCallback(() => {
    setStep(1);
    setCategory('');
    setDescription('');
    setWhereHint('');
    setEmail('');
    setErr('');
    setResult(null);
    setSubmitting(false);
  }, []);

  useEffect(() => {
    if (!open) return;
    reset();
    setCatLoading(true);
    fetchTicketCategories()
      .then((data) => {
        const list = Array.isArray(data.categories) ? data.categories : [];
        setCategories(list.length ? list : FALLBACK_CATEGORIES);
      })
      .catch(() => {
        setCategories(FALLBACK_CATEGORIES);
      })
      .finally(() => setCatLoading(false));
  }, [open, reset]);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeBtnRef.current?.focus();
    const onKey = (e) => {
      if (e.key === 'Escape' && !submitting) onClose?.();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
    };
  }, [open, onClose, submitting]);

  const handleSubmit = async () => {
    setErr('');
    setSubmitting(true);
    try {
      const ticket = await createSupportTicket({
        category,
        description: description.trim(),
        where_hint: whereHint.trim() || undefined,
        email: email.trim() || undefined,
        location_graph_id: graphLocationId || undefined,
      });
      setResult(ticket);
      onTicketCreated?.(ticket);
      setStep(4);
    } catch (e) {
      setErr(e.message || 'Could not create ticket. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const copyId = () => {
    if (!result?.ticket_id) return;
    navigator.clipboard?.writeText(result.ticket_id).catch(() => {});
  };

  if (!open) return null;

  const descOk = description.trim().length >= 10;
  const canNext1 = Boolean(category);
  const canSubmit = descOk && !submitting;

  return (
    <div
      className="report-issue-root"
      role="dialog"
      aria-modal="true"
      aria-labelledby="report-issue-title"
    >
      <div className="report-issue-scrim" onClick={() => !submitting && onClose?.()} aria-hidden="true" />
      <div className="report-issue-card">
        <div className="report-issue-head">
          <div>
            <h2 id="report-issue-title" className="report-issue-title">
              Report an issue
            </h2>
            <p className="report-issue-sub">
              {step < 4
                ? 'A few short questions, then we generate a ticket you can save or share.'
                : 'Your ticket is saved.'}
            </p>
          </div>
          <button
            ref={closeBtnRef}
            type="button"
            className="report-issue-close"
            aria-label="Close"
            disabled={submitting}
            onClick={() => onClose?.()}
          >
            <span className="ms">close</span>
          </button>
        </div>

        {err ? (
          <p className="report-issue-banner" role="alert">
            {err}
          </p>
        ) : null}

        {step === 1 && (
          <div className="report-issue-body">
            <p className="report-issue-q">What best describes your issue?</p>
            {catLoading ? (
              <p className="report-issue-muted">Loading…</p>
            ) : (
              <div className="report-issue-chips" role="list">
                {categories.map((c) => (
                  <button
                    type="button"
                    key={c.id}
                    role="listitem"
                    className={`report-issue-chip${category === c.id ? ' report-issue-chip--on' : ''}`}
                    onClick={() => setCategory(c.id)}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
            )}
            <div className="report-issue-actions">
              <button type="button" className="report-issue-btn report-issue-btn--ghost" onClick={onClose}>
                Cancel
              </button>
              <button
                type="button"
                className="report-issue-btn report-issue-btn--primary"
                disabled={!canNext1 || catLoading}
                onClick={() => setStep(2)}
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="report-issue-body">
            <label htmlFor="report-issue-desc" className="report-issue-q">
              What happened?
            </label>
            <textarea
              id="report-issue-desc"
              className="report-issue-textarea"
              rows={5}
              placeholder="Describe the problem in your own words (at least a sentence)."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={4000}
            />
            <p className="report-issue-hint">{description.trim().length}/4000 — minimum 10 characters.</p>
            <div className="report-issue-actions">
              <button type="button" className="report-issue-btn report-issue-btn--ghost" onClick={() => setStep(1)}>
                Back
              </button>
              <button
                type="button"
                className="report-issue-btn report-issue-btn--primary"
                disabled={!descOk}
                onClick={() => setStep(3)}
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="report-issue-body">
            <p className="report-issue-q">Anything else we should know? (optional)</p>
            <label className="report-issue-label" htmlFor="report-issue-where">
              Where were you?
            </label>
            <input
              id="report-issue-where"
              className="report-issue-input"
              type="text"
              placeholder="e.g. Near departure security, Gate 47"
              value={whereHint}
              onChange={(e) => setWhereHint(e.target.value)}
              maxLength={500}
            />
            <label className="report-issue-label" htmlFor="report-issue-email">
              Email (optional — if you want a follow-up)
            </label>
            <input
              id="report-issue-email"
              className="report-issue-input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              maxLength={320}
            />
            {graphLocationId ? (
              <p className="report-issue-muted">
                We will attach your last known map location (<code>{graphLocationId}</code>) to the ticket.
              </p>
            ) : null}
            <div className="report-issue-actions">
              <button type="button" className="report-issue-btn report-issue-btn--ghost" onClick={() => setStep(2)}>
                Back
              </button>
              <button
                type="button"
                className="report-issue-btn report-issue-btn--primary"
                disabled={!canSubmit}
                onClick={handleSubmit}
              >
                {submitting ? 'Creating ticket…' : 'Create ticket'}
              </button>
            </div>
          </div>
        )}

        {step === 4 && result && (
          <div className="report-issue-body report-issue-done">
            <div className="report-issue-ticket-box" aria-live="polite">
              <span className="report-issue-ticket-label">Ticket reference</span>
              <span className="report-issue-ticket-id">{result.ticket_id}</span>
            </div>
            <p className="report-issue-summary">
              <strong>{result.category_label}</strong>
              <br />
              {result.summary}
            </p>
            <div className="report-issue-actions report-issue-actions--stack">
              <button type="button" className="report-issue-btn report-issue-btn--secondary" onClick={copyId}>
                <span className="ms">content_copy</span>
                Copy ticket number
              </button>
              <button type="button" className="report-issue-btn report-issue-btn--primary" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
