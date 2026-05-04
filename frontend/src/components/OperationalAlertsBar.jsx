import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { connectOpsWebSocket, fetchOpsState } from '../services/api';

function loadDismissedBulletins() {
  try {
    const raw = window.sessionStorage?.getItem('airhelp_ops_dismissed_bulletins');
    if (!raw) return new Set();
    const arr = JSON.parse(raw);
    return new Set(Array.isArray(arr) ? arr : []);
  } catch {
    return new Set();
  }
}

function saveDismissedBulletins(set) {
  try {
    window.sessionStorage?.setItem('airhelp_ops_dismissed_bulletins', JSON.stringify([...set]));
  } catch {
    /* ignore */
  }
}

function loadDismissedNoticeVersion() {
  try {
    const v = window.sessionStorage?.getItem('airhelp_ops_dismissed_notice_version');
    return v ? parseInt(v, 10) : 0;
  } catch {
    return 0;
  }
}

function saveDismissedNoticeVersion(version) {
  try {
    window.sessionStorage?.setItem('airhelp_ops_dismissed_notice_version', String(version));
  } catch {
    /* ignore */
  }
}

/**
 * Live strip for operator bulletins, global notice, and flight overrides (read-only for passengers).
 */
export default function OperationalAlertsBar() {
  const [state, setState] = useState(null);
  const [dismissedBulletins, setDismissedBulletins] = useState(loadDismissedBulletins);
  const [dismissedNoticeVersion, setDismissedNoticeVersion] = useState(loadDismissedNoticeVersion);

  useEffect(() => {
    let ws;
    let poll;
    const apply = (s) => setState(s);
    const token = (() => {
      try {
        return window.localStorage?.getItem('airhelp_operator_token') || '';
      } catch {
        return '';
      }
    })();

    fetchOpsState().then(apply).catch(() => {});

    try {
      ws = connectOpsWebSocket(apply, token.trim());
    } catch {
      /* ignore */
    }

    poll = window.setInterval(() => {
      fetchOpsState().then(apply).catch(() => {});
    }, 30000);

    return () => {
      if (ws && ws.readyState <= 1) ws.close();
      window.clearInterval(poll);
    };
  }, []);

  const dismissBulletin = useCallback((id) => {
    setDismissedBulletins((prev) => {
      const next = new Set(prev);
      next.add(id);
      saveDismissedBulletins(next);
      return next;
    });
  }, []);

  const dismissNotice = useCallback(() => {
    const v = state?.version ?? 0;
    setDismissedNoticeVersion(v);
    saveDismissedNoticeVersion(v);
  }, [state?.version]);

  const visibleBulletins = useMemo(() => {
    const list = state?.bulletins;
    if (!Array.isArray(list)) return [];
    return list.filter((b) => b && typeof b.id === 'string' && !dismissedBulletins.has(b.id));
  }, [state?.bulletins, dismissedBulletins]);

  const notice = state?.global_notice;
  const showNotice =
    notice &&
    typeof notice === 'object' &&
    (String(notice.title || '').trim() || String(notice.body || '').trim()) &&
    (state?.version ?? 0) > dismissedNoticeVersion;

  const flightOverrides = state?.flight_overrides;
  const flightKeys = useMemo(() => {
    if (!flightOverrides || typeof flightOverrides !== 'object') return [];
    return Object.keys(flightOverrides).slice(0, 6);
  }, [flightOverrides]);

  if (!state) return null;

  const severityClass =
    visibleBulletins.some((b) => b.severity === 'critical') || showNotice
      ? 'operational-alerts-bar--emphasis'
      : '';

  if (!showNotice && visibleBulletins.length === 0 && flightKeys.length === 0) return null;

  return (
    <div className={`operational-alerts-bar ${severityClass}`} role="region" aria-label="Airport live updates">
      {showNotice ? (
        <div className="operational-alerts-bar__row operational-alerts-bar__notice">
          <span className="operational-alerts-bar__badge">Notice</span>
          <div className="operational-alerts-bar__text">
            {notice.title ? <strong>{notice.title}</strong> : null}
            {notice.title && notice.body ? <span className="operational-alerts-bar__sep"> — </span> : null}
            {notice.body ? <span>{notice.body}</span> : null}
          </div>
          <button type="button" className="operational-alerts-bar__dismiss" onClick={dismissNotice} aria-label="Dismiss notice">
            ×
          </button>
        </div>
      ) : null}

      {visibleBulletins.slice(-4).map((b) => (
        <div
          key={b.id}
          className={`operational-alerts-bar__row operational-alerts-bar__bulletin operational-alerts-bar--sev-${b.severity || 'info'}`}
        >
          <span className="operational-alerts-bar__badge">{b.severity || 'info'}</span>
          <div className="operational-alerts-bar__text">
            <strong>{b.title}</strong>
            {b.body ? <span>: {b.body}</span> : null}
          </div>
          <button
            type="button"
            className="operational-alerts-bar__dismiss"
            onClick={() => dismissBulletin(b.id)}
            aria-label={`Dismiss ${b.title}`}
          >
            ×
          </button>
        </div>
      ))}

      {flightKeys.length > 0 ? (
        <div className="operational-alerts-bar__row operational-alerts-bar__flights">
          <span className="operational-alerts-bar__badge">Flights</span>
          <div className="operational-alerts-bar__flight-chips">
            {flightKeys.map((fn) => {
              const ov = flightOverrides[fn] || {};
              const bits = [];
              if (ov.gate) bits.push(`Gate ${ov.gate}`);
              if (ov.delay_minutes != null) bits.push(`+${ov.delay_minutes}m`);
              if (ov.status) bits.push(ov.status);
              return (
                <span key={fn} className="operational-alerts-bar__chip" title={ov.note || ''}>
                  <strong>{fn}</strong>
                  {bits.length ? ` · ${bits.join(' · ')}` : ''}
                </span>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
