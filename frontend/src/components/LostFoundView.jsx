import React, { useEffect, useMemo, useState } from 'react';
import {
  fetchLostFoundMatches,
  fetchLostFoundMeetDefaults,
  fetchMapData,
  postLostFoundConfirm,
  postLostFoundFound,
  postLostFoundLost,
} from '../services/api';

const TABS = [
  { id: 'lost', label: 'Report lost' },
  { id: 'found', label: 'Report found' },
  { id: 'matches', label: 'Matches' },
  { id: 'confirm', label: 'Confirm' },
];

function emptyForm() {
  return {
    flight: '',
    travel_date: '',
    bag_color: '',
    unique_detail: '',
    pir_reference: '',
    last_seen_node_id: '',
    lost_report_id: '',
    claim_code: '',
  };
}

/**
 * Safer lost/found flow: structured intake, similarity-ranked suggestions,
 * confirm with claim code or matching PIR, then route to baggage meet node.
 */
export default function LostFoundView({ location, onOpenFloorMap }) {
  const [tab, setTab] = useState('lost');
  const [nodes, setNodes] = useState([]);
  const [meetDefaults, setMeetDefaults] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [lastLost, setLastLost] = useState(null);
  const [lastFound, setLastFound] = useState(null);
  const [matchReportId, setMatchReportId] = useState('');
  const [matchData, setMatchData] = useState(null);
  const [confirmState, setConfirmState] = useState({
    lost_report_id: '',
    found_report_id: '',
    shared_secret: '',
  });
  const [confirmResult, setConfirmResult] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [map, meet] = await Promise.all([fetchMapData(), fetchLostFoundMeetDefaults()]);
        if (cancelled) return;
        setNodes(Array.isArray(map.nodes) ? map.nodes : []);
        setMeetDefaults(meet);
      } catch {
        if (!cancelled) setNodes([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const nodeOptions = useMemo(() => {
    return [...nodes].sort((a, b) =>
      String(a.passenger_name || a.name || a.id || '').localeCompare(
        String(b.passenger_name || b.name || b.id || ''),
        undefined,
        { sensitivity: 'base' },
      ),
    );
  }, [nodes]);

  const setField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const parseApiErr = async (e) => {
    if (e instanceof Error) return e.message;
    return String(e);
  };

  const submitLost = async (e) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const body = {
        flight: form.flight.trim() || null,
        travel_date: form.travel_date.trim() || null,
        bag_color: form.bag_color.trim() || null,
        unique_detail: form.unique_detail.trim(),
        pir_reference: form.pir_reference.trim() || null,
        last_seen_node_id: form.last_seen_node_id.trim() || null,
      };
      const data = await postLostFoundLost(body);
      setLastLost(data);
      setLastFound(null);
      setForm(emptyForm());
    } catch (ex) {
      setErr(await parseApiErr(ex));
    } finally {
      setBusy(false);
    }
  };

  const submitFound = async (e) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const body = {
        flight: form.flight.trim() || null,
        travel_date: form.travel_date.trim() || null,
        bag_color: form.bag_color.trim() || null,
        unique_detail: form.unique_detail.trim(),
        pir_reference: form.pir_reference.trim() || null,
        last_seen_node_id: form.last_seen_node_id.trim() || null,
        lost_report_id: form.lost_report_id.trim() || null,
        claim_code: form.claim_code.trim() || null,
      };
      const data = await postLostFoundFound(body);
      setLastFound(data);
      if (data.status === 'matched' && data.meet_graph_node_id) {
        setLastLost(null);
      }
      setForm(emptyForm());
    } catch (ex) {
      setErr(await parseApiErr(ex));
    } finally {
      setBusy(false);
    }
  };

  const loadMatches = async (e) => {
    e?.preventDefault();
    setErr(null);
    setMatchData(null);
    const id = matchReportId.trim();
    if (!id) {
      setErr('Enter a report ID from a lost or found submission.');
      return;
    }
    setBusy(true);
    try {
      const data = await fetchLostFoundMatches(id);
      setMatchData(data);
    } catch (ex) {
      setErr(ex.message || 'Could not load matches');
    } finally {
      setBusy(false);
    }
  };

  const submitConfirm = async (e) => {
    e.preventDefault();
    setErr(null);
    setConfirmResult(null);
    setBusy(true);
    try {
      const data = await postLostFoundConfirm({
        lost_report_id: confirmState.lost_report_id.trim(),
        found_report_id: confirmState.found_report_id.trim(),
        shared_secret: confirmState.shared_secret.trim(),
      });
      setConfirmResult(data);
    } catch (ex) {
      setErr(await parseApiErr(ex));
    } finally {
      setBusy(false);
    }
  };

  const openRouteToMeet = (nodeId) => {
    const to = nodeId || meetDefaults?.meet_graph_node_id || 't2_baggage_claim';
    onOpenFloorMap?.({ fromId: location, toId: to, routeIndex: 0 });
  };

  return (
    <div className="lf-view fac-dir">
      <header className="fac-dir-header">
        <h1 className="fac-dir-title">Lost &amp; Found</h1>
        <p className="fac-dir-lead">
          Demo assist only: file details stay on this device/server for matching. Always involve airline baggage staff and
          your PIR. We never share phone numbers; confirm a match only with the traveller&apos;s claim code or identical
          PIR text.
        </p>
        <div className="lf-tabs" role="tablist" aria-label="Lost and found sections">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              className={`lf-tab ${tab === t.id ? 'active' : ''}`}
              onClick={() => {
                setTab(t.id);
                setErr(null);
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>

      <div className="fac-dir-body">
        {err && <div className="lf-err">{err}</div>}

        {tab === 'lost' && (
          <section className="fac-dir-section">
            <h2 className="fac-dir-section-title">Lost bag</h2>
            <p className="lf-muted">
              Describe one distinctive detail only you would recognize. You will get a claim code to share with the finder
              or staff after you verify them in person.
            </p>
            <form className="lf-card" onSubmit={submitLost}>
              <div className="lf-field">
                <label htmlFor="lf-l-flight">Flight (optional)</label>
                <input id="lf-l-flight" value={form.flight} onChange={(ev) => setField('flight', ev.target.value)} />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-l-date">Travel date (optional)</label>
                <input
                  id="lf-l-date"
                  type="text"
                  placeholder="e.g. 2026-05-03"
                  value={form.travel_date}
                  onChange={(ev) => setField('travel_date', ev.target.value)}
                />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-l-color">Bag colour / type</label>
                <input id="lf-l-color" value={form.bag_color} onChange={(ev) => setField('bag_color', ev.target.value)} />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-l-detail">Unique detail (required)</label>
                <textarea
                  id="lf-l-detail"
                  required
                  minLength={3}
                  value={form.unique_detail}
                  onChange={(ev) => setField('unique_detail', ev.target.value)}
                />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-l-pir">PIR / file reference (optional)</label>
                <input id="lf-l-pir" value={form.pir_reference} onChange={(ev) => setField('pir_reference', ev.target.value)} />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-l-node">Last seen area (graph node)</label>
                <select
                  id="lf-l-node"
                  value={form.last_seen_node_id}
                  onChange={(ev) => setField('last_seen_node_id', ev.target.value)}
                >
                  <option value="">— Unsure / skip —</option>
                  {nodeOptions.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.passenger_name || n.name || n.id}
                    </option>
                  ))}
                </select>
              </div>
              <button type="submit" className="fac-dir-btn" disabled={busy}>
                {busy ? 'Saving…' : 'Submit lost report'}
              </button>
            </form>
            {lastLost && (
              <div className="lf-claim-box">
                <div>Saved. Your report ID (keep for your records):</div>
                <div className="lf-claim-code" style={{ letterSpacing: '0.04em' }}>
                  {lastLost.id}
                </div>
                <div style={{ marginTop: 10 }}>Claim code (share carefully):</div>
                <div className="lf-claim-code">{lastLost.claim_code}</div>
                <p className="lf-muted" style={{ marginTop: 12 }}>
                  {lastLost.message}
                </p>
                <div className="lf-actions">
                  <button type="button" className="fac-dir-btn" onClick={() => setTab('matches')}>
                    Find possible matches
                  </button>
                  <button type="button" className="fac-dir-btn" onClick={() => setMatchReportId(lastLost.id)}>
                    Load my matches
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {tab === 'found' && (
          <section className="fac-dir-section">
            <h2 className="fac-dir-section-title">Found bag</h2>
            <p className="lf-muted">
              If the owner gave you their report ID and claim code, enter them below for an instant supervised handover
              path. Otherwise submit details and use the Matches tab.
            </p>
            <form className="lf-card" onSubmit={submitFound}>
              <div className="lf-field">
                <label htmlFor="lf-f-lostid">Lost report ID (optional, with claim code)</label>
                <input
                  id="lf-f-lostid"
                  placeholder="UUID from owner"
                  value={form.lost_report_id}
                  onChange={(ev) => setField('lost_report_id', ev.target.value)}
                />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-f-claim">Claim code from owner (optional)</label>
                <input
                  id="lf-f-claim"
                  autoComplete="off"
                  value={form.claim_code}
                  onChange={(ev) => setField('claim_code', ev.target.value)}
                />
              </div>
              <hr style={{ border: 0, borderTop: '1px solid var(--outline-variant)', margin: '8px 0 14px' }} />
              <div className="lf-field">
                <label htmlFor="lf-f-flight">Flight (optional)</label>
                <input id="lf-f-flight" value={form.flight} onChange={(ev) => setField('flight', ev.target.value)} />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-f-date">Travel date (optional)</label>
                <input id="lf-f-date" value={form.travel_date} onChange={(ev) => setField('travel_date', ev.target.value)} />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-f-color">Bag colour / type</label>
                <input id="lf-f-color" value={form.bag_color} onChange={(ev) => setField('bag_color', ev.target.value)} />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-f-detail">What you observed (required)</label>
                <textarea
                  id="lf-f-detail"
                  required
                  minLength={3}
                  value={form.unique_detail}
                  onChange={(ev) => setField('unique_detail', ev.target.value)}
                />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-f-pir">PIR on tag (optional)</label>
                <input id="lf-f-pir" value={form.pir_reference} onChange={(ev) => setField('pir_reference', ev.target.value)} />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-f-node">Where you found / left it</label>
                <select
                  id="lf-f-node"
                  value={form.last_seen_node_id}
                  onChange={(ev) => setField('last_seen_node_id', ev.target.value)}
                >
                  <option value="">— Unsure / skip —</option>
                  {nodeOptions.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.passenger_name || n.name || n.id}
                    </option>
                  ))}
                </select>
              </div>
              <button type="submit" className="fac-dir-btn" disabled={busy}>
                {busy ? 'Saving…' : 'Submit found report'}
              </button>
            </form>
            {lastFound && (
              <div className="lf-claim-box">
                <div>Report ID: {lastFound.id}</div>
                <p className="lf-muted">{lastFound.message}</p>
                {lastFound.status === 'matched' && (
                  <div className="lf-actions">
                    <button type="button" className="fac-dir-btn" onClick={() => openRouteToMeet(lastFound.meet_graph_node_id)}>
                      Open map to meet point
                    </button>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {tab === 'matches' && (
          <section className="fac-dir-section">
            <h2 className="fac-dir-section-title">Possible matches</h2>
            <p className="lf-muted">{matchData?.disclaimer}</p>
            <form className="lf-card" onSubmit={loadMatches}>
              <div className="lf-field">
                <label htmlFor="lf-m-id">Your report ID</label>
                <input
                  id="lf-m-id"
                  value={matchReportId}
                  onChange={(ev) => setMatchReportId(ev.target.value)}
                  placeholder="Paste lost or found report UUID"
                />
              </div>
              <button type="submit" className="fac-dir-btn" disabled={busy}>
                {busy ? 'Loading…' : 'Load ranked matches'}
              </button>
            </form>
            {matchData?.matches?.length > 0 && (
              <div style={{ marginTop: 14 }}>
                <h3 className="fac-dir-section-title">Results</h3>
                {matchData.matches.map((m) => (
                  <div key={m.id} className="lf-match-row">
                    <div className="lf-match-score">Similarity {(m.similarity * 100).toFixed(1)}%</div>
                    <div className="fac-dir-name">Report {m.id}</div>
                    <div className="fac-dir-meta">
                      {[m.flight, m.travel_date, m.bag_color].filter(Boolean).join(' · ')}
                    </div>
                    <div className="fac-dir-meta">{m.unique_detail}</div>
                    {m.last_seen_node_id && (
                      <div className="fac-dir-node">Node: {m.last_seen_node_id}</div>
                    )}
                    <div className="fac-dir-meta">PIR on file: {m.has_pir ? 'yes (hidden)' : 'not provided'}</div>
                  </div>
                ))}
              </div>
            )}
            {matchData && (!matchData.matches || matchData.matches.length === 0) && (
              <p className="lf-muted">No open counterpart reports above the similarity threshold.</p>
            )}
          </section>
        )}

        {tab === 'confirm' && (
          <section className="fac-dir-section">
            <h2 className="fac-dir-section-title">Confirm match</h2>
            <p className="lf-muted">
              Enter the lost report ID, your found report ID, and either the lost traveller&apos;s claim code or a PIR
              string that matches exactly on both reports (both sides must have entered the same PIR text).
            </p>
            <form className="lf-card" onSubmit={submitConfirm}>
              <div className="lf-field">
                <label htmlFor="lf-c-lost">Lost report ID</label>
                <input
                  id="lf-c-lost"
                  value={confirmState.lost_report_id}
                  onChange={(ev) => setConfirmState((s) => ({ ...s, lost_report_id: ev.target.value }))}
                />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-c-found">Found report ID</label>
                <input
                  id="lf-c-found"
                  value={confirmState.found_report_id}
                  onChange={(ev) => setConfirmState((s) => ({ ...s, found_report_id: ev.target.value }))}
                />
              </div>
              <div className="lf-field">
                <label htmlFor="lf-c-secret">Claim code or shared PIR text</label>
                <input
                  id="lf-c-secret"
                  autoComplete="off"
                  value={confirmState.shared_secret}
                  onChange={(ev) => setConfirmState((s) => ({ ...s, shared_secret: ev.target.value }))}
                />
              </div>
              <button type="submit" className="fac-dir-btn" disabled={busy}>
                {busy ? 'Confirming…' : 'Confirm'}
              </button>
            </form>
            {confirmResult && (
              <div className="lf-claim-box">
                <p className="lf-muted">{confirmResult.message}</p>
                <div className="lf-actions">
                  <button
                    type="button"
                    className="fac-dir-btn"
                    onClick={() => openRouteToMeet(confirmResult.meet_graph_node_id)}
                  >
                    Open map to meet point
                  </button>
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
