import React, { useCallback, useEffect, useState } from 'react';
import {
  connectOpsWebSocket,
  deleteOpsBulletin,
  deleteOpsFlightOverride,
  fetchOpsState,
  postOpsBulletin,
  postOpsFlightOverride,
  postOpsGlobalNotice,
} from '../services/api';

const emptyForm = {
  noticeTitle: '',
  noticeBody: '',
  bulletinTitle: '',
  bulletinBody: '',
  bulletinSeverity: 'warning',
  flight: '',
  gate: '',
  delayMinutes: '',
  status: '',
  note: '',
};

/**
 * Airport operator console: edit live notices / delays / gates; persists on the laptop server.
 */
export default function OperatorConsoleView({ onBack }) {
  const [state, setState] = useState(null);
  const [error, setError] = useState('');
  const [ok, setOk] = useState('');
  const [tokenInput, setTokenInput] = useState(() => {
    try {
      return window.localStorage?.getItem('airhelp_operator_token') || '';
    } catch {
      return '';
    }
  });
  const [form, setForm] = useState(emptyForm);

  const refresh = useCallback(() => {
    fetchOpsState()
      .then(setState)
      .catch((e) => setError(String(e.message || e)));
  }, []);

  useEffect(() => {
    refresh();
    const tok = (() => {
      try {
        return window.localStorage?.getItem('airhelp_operator_token') || '';
      } catch {
        return '';
      }
    })();
    let ws;
    try {
      ws = connectOpsWebSocket(setState, tok.trim());
    } catch {
      /* ignore */
    }
    return () => {
      if (ws && ws.readyState <= 1) ws.close();
    };
  }, [refresh]);

  const saveToken = useCallback(() => {
    try {
      const t = tokenInput.trim();
      if (t) window.localStorage.setItem('airhelp_operator_token', t);
      else window.localStorage.removeItem('airhelp_operator_token');
      setOk('Token saved. Reconnect WebSocket by leaving this page or refresh.');
      setError('');
    } catch (e) {
      setError(String(e));
    }
  }, [tokenInput]);

  const flashOk = (msg) => {
    setOk(msg);
    setError('');
    window.setTimeout(() => setOk(''), 4000);
  };

  const handleGlobalNotice = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await postOpsGlobalNotice({
        title: form.noticeTitle.trim() || null,
        body: form.noticeBody.trim() || null,
      });
      flashOk('Global notice published.');
      setForm((f) => ({ ...f, noticeTitle: '', noticeBody: '' }));
      refresh();
    } catch (err) {
      setError(err?.message || String(err));
    }
  };

  const handleBulletin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await postOpsBulletin({
        title: form.bulletinTitle.trim(),
        body: form.bulletinBody.trim(),
        severity: form.bulletinSeverity,
      });
      flashOk('Bulletin added.');
      setForm((f) => ({ ...f, bulletinTitle: '', bulletinBody: '' }));
      refresh();
    } catch (err) {
      setError(err?.message || String(err));
    }
  };

  const handleFlight = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const dm = form.delayMinutes.trim();
      await postOpsFlightOverride({
        flight: form.flight.trim(),
        gate: form.gate.trim() || null,
        delay_minutes: dm === '' ? null : parseInt(dm, 10),
        status: form.status.trim() || null,
        note: form.note.trim() || null,
      });
      flashOk('Flight override saved.');
      setForm((f) => ({ ...f, flight: '', gate: '', delayMinutes: '', status: '', note: '' }));
      refresh();
    } catch (err) {
      setError(err?.message || String(err));
    }
  };

  const bulletins = Array.isArray(state?.bulletins) ? state.bulletins : [];
  const flights = state?.flight_overrides && typeof state.flight_overrides === 'object' ? state.flight_overrides : {};

  return (
    <div className="operator-console">
      <header className="operator-console__header">
        <button type="button" className="operator-console__back" onClick={onBack}>
          ← Back
        </button>
        <div>
          <h1 className="operator-console__title">Operator console</h1>
          <p className="operator-console__subtitle">
            Changes sync to every device on this server via WebSocket. Set{' '}
            <code>AIRHELP_OPERATOR_TOKEN</code> on the API to require the token below for edits.
          </p>
        </div>
      </header>

      {error ? <div className="operator-console__banner operator-console__banner--err">{error}</div> : null}
      {ok ? <div className="operator-console__banner operator-console__banner--ok">{ok}</div> : null}

      <section className="operator-console__card">
        <h2>Operator token (browser)</h2>
        <p className="operator-console__hint">Stored only in this browser as <code>airhelp_operator_token</code>.</p>
        <div className="operator-console__row">
          <input
            type="password"
            className="operator-console__input"
            placeholder="Paste token if server requires it"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            autoComplete="off"
          />
          <button type="button" className="operator-console__btn" onClick={saveToken}>
            Save token
          </button>
        </div>
      </section>

      <div className="operator-console__grid">
        <section className="operator-console__card">
          <h2>Global notice</h2>
          <form onSubmit={handleGlobalNotice} className="operator-console__form">
            <label>
              Title
              <input
                className="operator-console__input"
                value={form.noticeTitle}
                onChange={(e) => setForm((f) => ({ ...f, noticeTitle: e.target.value }))}
              />
            </label>
            <label>
              Body
              <textarea
                className="operator-console__textarea"
                rows={3}
                value={form.noticeBody}
                onChange={(e) => setForm((f) => ({ ...f, noticeBody: e.target.value }))}
              />
            </label>
            <div className="operator-console__actions">
              <button type="submit" className="operator-console__btn operator-console__btn--primary">
                Publish notice
              </button>
              <button
                type="button"
                className="operator-console__btn operator-console__btn--ghost"
                onClick={async () => {
                  setError('');
                  try {
                    await postOpsGlobalNotice({ title: null, body: null });
                    flashOk('Notice cleared.');
                    refresh();
                  } catch (err) {
                    setError(err?.message || String(err));
                  }
                }}
              >
                Clear notice
              </button>
            </div>
          </form>
        </section>

        <section className="operator-console__card">
          <h2>Bulletin</h2>
          <form onSubmit={handleBulletin} className="operator-console__form">
            <label>
              Title
              <input
                required
                className="operator-console__input"
                value={form.bulletinTitle}
                onChange={(e) => setForm((f) => ({ ...f, bulletinTitle: e.target.value }))}
              />
            </label>
            <label>
              Body
              <textarea
                required
                className="operator-console__textarea"
                rows={3}
                value={form.bulletinBody}
                onChange={(e) => setForm((f) => ({ ...f, bulletinBody: e.target.value }))}
              />
            </label>
            <label>
              Severity
              <select
                className="operator-console__input"
                value={form.bulletinSeverity}
                onChange={(e) => setForm((f) => ({ ...f, bulletinSeverity: e.target.value }))}
              >
                <option value="info">info</option>
                <option value="warning">warning</option>
                <option value="critical">critical</option>
              </select>
            </label>
            <button type="submit" className="operator-console__btn operator-console__btn--primary">
              Add bulletin
            </button>
          </form>
        </section>

        <section className="operator-console__card operator-console__card--wide">
          <h2>Flight override</h2>
          <form onSubmit={handleFlight} className="operator-console__form operator-console__form--inline">
            <label>
              Flight #
              <input
                required
                className="operator-console__input"
                placeholder="e.g. AI144"
                value={form.flight}
                onChange={(e) => setForm((f) => ({ ...f, flight: e.target.value }))}
              />
            </label>
            <label>
              Gate
              <input
                className="operator-console__input"
                placeholder="e.g. 72"
                value={form.gate}
                onChange={(e) => setForm((f) => ({ ...f, gate: e.target.value }))}
              />
            </label>
            <label>
              Delay (min)
              <input
                className="operator-console__input"
                type="number"
                min={0}
                placeholder="optional"
                value={form.delayMinutes}
                onChange={(e) => setForm((f) => ({ ...f, delayMinutes: e.target.value }))}
              />
            </label>
            <label>
              Status
              <input
                className="operator-console__input"
                placeholder="Boarding / Delayed"
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              />
            </label>
            <label className="operator-console__grow">
              Note
              <input
                className="operator-console__input"
                value={form.note}
                onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
              />
            </label>
            <button type="submit" className="operator-console__btn operator-console__btn--primary">
              Save override
            </button>
          </form>
        </section>
      </div>

      <section className="operator-console__card">
        <div className="operator-console__list-head">
          <h2>Active bulletins ({bulletins.length})</h2>
          <span className="operator-console__meta">version {state?.version ?? '—'}</span>
        </div>
        <ul className="operator-console__list">
          {[...bulletins].reverse().map((b) => (
            <li key={b.id}>
              <div>
                <strong>[{b.severity}]</strong> {b.title}
                <div className="operator-console__muted">{b.body}</div>
              </div>
              <button
                type="button"
                className="operator-console__btn operator-console__btn--ghost"
                onClick={async () => {
                  setError('');
                  try {
                    await deleteOpsBulletin(b.id);
                    flashOk('Removed.');
                    refresh();
                  } catch (err) {
                    setError(err?.message || String(err));
                  }
                }}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="operator-console__card">
        <h2>Flight overrides</h2>
        <ul className="operator-console__list">
          {Object.keys(flights).length === 0 ? <li className="operator-console__muted">None</li> : null}
          {Object.entries(flights).map(([fn, ov]) => (
            <li key={fn}>
              <div>
                <strong>{fn}</strong>
                <div className="operator-console__muted">
                  {[ov.gate && `Gate ${ov.gate}`, ov.delay_minutes != null && `+${ov.delay_minutes}m`, ov.status, ov.note]
                    .filter(Boolean)
                    .join(' · ')}
                </div>
              </div>
              <button
                type="button"
                className="operator-console__btn operator-console__btn--ghost"
                onClick={async () => {
                  setError('');
                  try {
                    await deleteOpsFlightOverride(fn);
                    flashOk('Removed.');
                    refresh();
                  } catch (err) {
                    setError(err?.message || String(err));
                  }
                }}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
