import React, { useCallback, useEffect, useMemo, useState } from 'react';
import GuidedStepMap, { normalizeGuidedPath } from './GuidedStepMap';
import TtsMiniBar from './TtsMiniBar';
import { fetchGuidedCheckpoints, fetchGuidedRelocalize, fetchMapData, fetchNavigation } from '../services/api';
import { formatRouteTimeCompact, formatRouteTimeLine } from '../utils/routeEstimate';
import { buildGuidedCheckpointSpeech, buildRouteSpeechText } from '../utils/routeSpeech';

const BUSY_TERMINAL_STORAGE_KEY = 'airhelp_busy_terminal';

function routesFromPayload(nav) {
  if (!nav?.ok) return [];
  if (Array.isArray(nav.routes) && nav.routes.length > 0) return nav.routes;
  return [nav];
}

function routeCardHint(routes, idx) {
  const base = routes[0]?.total_time_minutes ?? 0;
  const t = routes[idx]?.total_time_minutes ?? 0;
  const delta = t - base;
  if (idx === 0) return 'Shortest time';
  if (delta === 0) return 'Same time, different path';
  if (delta > 0) return `About +${delta} min`;
  return 'Different path';
}

function RouteDetailBody({ route }) {
  if (!route) return null;
  const routeSpeech = buildRouteSpeechText(route);
  return (
    <>
      {Array.isArray(route.shops_along_route?.tips) && route.shops_along_route.tips.length > 0 ? (
        <section className="nav-flow-callout" aria-label="Food and shopping near your walk">
          <div className="nav-flow-callout-kicker">While you walk</div>
          <ul className="nav-flow-tips">
            {route.shops_along_route.tips.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {route.simple_journey?.subtitle ? (
        <p className="nav-flow-subtitle">{route.simple_journey.subtitle}</p>
      ) : null}

      {Array.isArray(route.simple_journey?.bullets) && route.simple_journey.bullets.length > 0 ? (
        <>
          <div className="nav-flow-section-title nav-flow-section-title--row">
            <span>Your route</span>
            {routeSpeech ? (
              <TtsMiniBar
                sessionId="nav-route-detail"
                text={routeSpeech}
                buttonClass="nav-flow-tts-inline"
                wrapClass="nav-flow-tts-wrap"
              />
            ) : null}
          </div>
          <ul className="nav-flow-bullets">
            {route.simple_journey.bullets.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </>
      ) : routeSpeech ? (
        <div className="nav-flow-read-row">
          <TtsMiniBar
            sessionId="nav-route-detail"
            text={routeSpeech}
            buttonClass="nav-flow-tts-inline"
            wrapClass="nav-flow-tts-wrap"
          />
        </div>
      ) : null}

      {Array.isArray(route.shops_along_route?.picks) && route.shops_along_route.picks.length > 0 ? (
        <details className="nav-flow-details">
          <summary>Shop stops on this path ({route.shops_along_route.count_on_path || 0})</summary>
          <ul className="nav-flow-picks">
            {route.shops_along_route.picks.map((p) => (
              <li key={p.shop_id}>
                <span className="nav-flow-pick-name">{p.name_display}</span>
                <span className="nav-flow-pick-meta">
                  {p.bucket_label}
                  {p.floor_display || p.floor ? ` · ${p.floor_display || p.floor}` : ''}
                </span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}

      <details className="nav-flow-details">
        <summary>Step-by-step (each segment)</summary>
        <ol className="nav-flow-steps">
          {(route.steps || []).map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ol>
      </details>
    </>
  );
}

/**
 * Step-by-step walking navigation without the floor map until the user asks for it.
 */
export default function NavigationFlowView({ location, onLocationChange, onOpenFloorMap }) {
  const [meta, setMeta] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [loadErr, setLoadErr] = useState(null);

  const [step, setStep] = useState('pick');
  const [from, setFrom] = useState(location || 't2_entrance');
  const [to, setTo] = useState('t2_ne_sp_14');
  const [loading, setLoading] = useState(false);
  const [routeErr, setRouteErr] = useState(null);
  const [navPayload, setNavPayload] = useState(null);
  const [pickedIdx, setPickedIdx] = useState(0);
  const [busyTerminal, setBusyTerminal] = useState(() => {
    try {
      return typeof window !== 'undefined' && window.localStorage?.getItem(BUSY_TERMINAL_STORAGE_KEY) === '1';
    } catch {
      return false;
    }
  });

  const [guidedPayload, setGuidedPayload] = useState(null);
  const [guidedStepIndex, setGuidedStepIndex] = useState(0);
  const [lastConfirmedPathIndex, setLastConfirmedPathIndex] = useState(0);
  const [guidedPhase, setGuidedPhase] = useState('question');
  const [lostObservation, setLostObservation] = useState('');
  const [guidedErr, setGuidedErr] = useState(null);
  const [notYetHint, setNotYetHint] = useState('');
  const [relocalizeCandidates, setRelocalizeCandidates] = useState([]);
  const [guidedLoading, setGuidedLoading] = useState(false);

  useEffect(() => {
    if (location) setFrom(location);
  }, [location]);

  useEffect(() => {
    setNotYetHint('');
  }, [guidedStepIndex, guidedPhase, step]);

  useEffect(() => {
    try {
      window.localStorage?.setItem(BUSY_TERMINAL_STORAGE_KEY, busyTerminal ? '1' : '0');
    } catch {
      /* ignore */
    }
  }, [busyTerminal]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchMapData();
        if (cancelled) return;
        setMeta(data.meta || {});
        setNodes(data.nodes || []);
      } catch (e) {
        if (!cancelled) setLoadErr(e.message || 'Could not load places');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const sortedNodes = useMemo(
    () =>
      [...nodes].sort((a, b) =>
        (a.passenger_name || a.name || '').localeCompare(b.passenger_name || b.name || '', undefined, {
          sensitivity: 'base',
        }),
      ),
    [nodes],
  );

  const routeList = useMemo(() => routesFromPayload(navPayload), [navPayload]);
  const selectedRoute = routeList[pickedIdx] ?? null;

  const findRoutes = useCallback(async () => {
    setLoading(true);
    setRouteErr(null);
    setNavPayload(null);
    try {
      const data = await fetchNavigation(from, to, {
        localHour: new Date().getHours(),
        busyTerminal,
      });
      const nav = data?.data?.navigation;
      if (!nav?.ok) {
        setRouteErr(nav?.hint || nav?.error || 'No route found');
        setStep('pick');
        return;
      }
      setNavPayload(nav);
      setPickedIdx(0);
      setStep('routes');
      if (onLocationChange) onLocationChange(from);
    } catch (e) {
      setRouteErr(e.message || 'Could not reach navigation service');
      setStep('pick');
    } finally {
      setLoading(false);
    }
  }, [from, to, onLocationChange, busyTerminal]);

  const resetFlow = () => {
    setStep('pick');
    setNavPayload(null);
    setRouteErr(null);
    setPickedIdx(0);
    setGuidedPayload(null);
    setGuidedStepIndex(0);
    setLastConfirmedPathIndex(0);
    setGuidedPhase('question');
    setLostObservation('');
    setRelocalizeCandidates([]);
    setGuidedErr(null);
    setNotYetHint('');
  };

  const openMapForSelection = () => {
    onOpenFloorMap?.({ fromId: from, toId: to, routeIndex: pickedIdx });
  };

  const exitGuidedNav = () => {
    setStep('detail');
    setGuidedPayload(null);
    setGuidedStepIndex(0);
    setLastConfirmedPathIndex(0);
    setGuidedPhase('question');
    setLostObservation('');
    setRelocalizeCandidates([]);
    setGuidedErr(null);
    setNotYetHint('');
  };

  const startGuidedNav = useCallback(async () => {
    if (!selectedRoute?.path?.length) return;
    setGuidedLoading(true);
    setGuidedErr(null);
    try {
      const path = selectedRoute.path.map((p) => p.id);
      const edges = selectedRoute.edges || [];
      const cp = await fetchGuidedCheckpoints({ path, edges });
      if (!cp?.ok) {
        setGuidedErr(cp?.hint || cp?.error || 'Could not build guidance');
        return;
      }
      if (!cp.steps?.length) {
        setGuidedErr('Route is too short for live steps.');
        return;
      }
      setGuidedPayload(cp);
      setGuidedStepIndex(0);
      setLastConfirmedPathIndex(0);
      setGuidedPhase('question');
      setLostObservation('');
      setRelocalizeCandidates([]);
      setStep('guided');
    } catch (e) {
      setGuidedErr(e.message || 'Guidance request failed');
    } finally {
      setGuidedLoading(false);
    }
  }, [selectedRoute]);

  const confirmGuidedYes = () => {
    const steps = guidedPayload?.steps || [];
    const cur = steps[guidedStepIndex];
    if (!cur) return;
    setLastConfirmedPathIndex(cur.to_path_index);
    if (guidedStepIndex >= steps.length - 1) {
      setGuidedStepIndex(steps.length);
      return;
    }
    setGuidedStepIndex((x) => x + 1);
  };

  const submitLostObservation = async () => {
    const steps = guidedPayload?.steps || [];
    const cur = steps[guidedStepIndex];
    if (!cur || !lostObservation.trim()) return;
    setGuidedLoading(true);
    setGuidedErr(null);
    try {
      const res = await fetchGuidedRelocalize({
        path: normalizeGuidedPath(guidedPayload.path, guidedPayload.steps || []),
        last_confirmed_path_index: lastConfirmedPathIndex,
        next_waypoint_path_index: cur.to_path_index,
        observation: lostObservation.trim(),
        localHour: new Date().getHours(),
        busyTerminal,
      });
      if (!res?.ok) {
        setGuidedErr(res?.hint || res?.error || 'Relocalize failed');
        return;
      }
      setRelocalizeCandidates(res.candidates || []);
      setGuidedPhase('candidates');
    } catch (e) {
      setGuidedErr(e.message || 'Relocalize request failed');
    } finally {
      setGuidedLoading(false);
    }
  };

  const applyRelocalizeNode = async (graphNodeId) => {
    setGuidedLoading(true);
    setGuidedErr(null);
    try {
      setFrom(graphNodeId);
      if (onLocationChange) onLocationChange(graphNodeId);
      const data = await fetchNavigation(graphNodeId, to, {
        localHour: new Date().getHours(),
        busyTerminal,
      });
      const nav = data?.data?.navigation;
      if (!nav?.ok) {
        setGuidedErr(nav?.hint || nav?.error || 'No route from that spot');
        return;
      }
      setNavPayload(nav);
      setPickedIdx(0);
      const route0 = routesFromPayload(nav)[0];
      const path = route0.path.map((p) => p.id);
      const cp = await fetchGuidedCheckpoints({ path, edges: route0.edges || [] });
      if (!cp?.ok || !cp.steps?.length) {
        setGuidedErr(cp?.hint || 'Could not rebuild guidance from here');
        setGuidedPayload(null);
        setStep('detail');
        return;
      }
      setGuidedPayload(cp);
      setGuidedStepIndex(0);
      setLastConfirmedPathIndex(0);
      setGuidedPhase('question');
      setLostObservation('');
      setRelocalizeCandidates([]);
      setStep('guided');
    } catch (e) {
      setGuidedErr(e.message || 'Failed to replan');
    } finally {
      setGuidedLoading(false);
    }
  };

  const guidedSteps = guidedPayload?.steps || [];
  const guidedDone = Boolean(guidedPayload && guidedStepIndex >= guidedSteps.length);
  const guidedCur = guidedSteps[guidedStepIndex];

  return (
    <div
      className={`nav-flow nav-flow--full-bleed${
        step === 'detail' || step === 'guided' ? ' nav-flow--step-detail' : ''
      }`}
    >
      <header className="nav-flow-header">
        <div>
          <h1 className="nav-flow-title">Walking directions</h1>
          <p className="nav-flow-meta">
            {meta?.airport_name || 'BOM'} · {meta?.terminal || 'T2'} · {meta?.floor || 'L02'}
          </p>
          <p className="nav-flow-lead">
            Choose start and end, compare up to three walking paths, then open the floor map only when you need it.
          </p>
        </div>
      </header>

      {loadErr && (
        <p className="nav-flow-banner-error" role="alert">
          {loadErr}
        </p>
      )}

      <div className="nav-flow-body">
        {step === 'pick' && (
          <section className="nav-flow-panel" aria-labelledby="nav-flow-pick-title">
            <h2 id="nav-flow-pick-title" className="nav-flow-panel-title">
              Where are you going?
            </h2>
            <p className="nav-flow-panel-hint">Pick two places in the terminal. We will list every walking option we have.</p>

            <label className="nav-flow-field">
              From
              <select
                className="nav-flow-select"
                value={from}
                onChange={(e) => {
                  setFrom(e.target.value);
                  if (onLocationChange) onLocationChange(e.target.value);
                }}
              >
                {sortedNodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.passenger_name || n.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="nav-flow-field">
              To
              <select className="nav-flow-select" value={to} onChange={(e) => setTo(e.target.value)}>
                {sortedNodes.map((n) => (
                  <option key={`t-${n.id}`} value={n.id}>
                    {n.passenger_name || n.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="nav-flow-field nav-flow-field--checkbox">
              <input
                type="checkbox"
                checked={busyTerminal}
                onChange={(e) => setBusyTerminal(e.target.checked)}
              />
              <span>Busy terminal (heavier security wait estimate — not live crowd counts)</span>
            </label>

            {routeErr ? (
              <p className="nav-flow-error" role="alert">
                {routeErr}
              </p>
            ) : null}

            <div className="nav-flow-actions">
              <button type="button" className="nav-flow-btn nav-flow-btn--primary" disabled={loading} onClick={findRoutes}>
                {loading ? 'Finding routes…' : 'Find routes'}
              </button>
              <button type="button" className="nav-flow-btn nav-flow-btn--ghost" onClick={() => onOpenFloorMap?.({ fromId: from, toId: to, routeIndex: 0 })}>
                Use floor map instead
              </button>
            </div>
            <p className="nav-flow-footnote">
              Map mode is for tapping <strong>From</strong> and <strong>To</strong> on the plan, seeing shops, and facilities on the drawing.
            </p>
          </section>
        )}

        {step === 'routes' && navPayload?.ok && (
          <section className="nav-flow-panel" aria-labelledby="nav-flow-routes-title">
            <h2 id="nav-flow-routes-title" className="nav-flow-panel-title">
              Pick one route
            </h2>
            <p className="nav-flow-panel-hint">
              {routeList.length} option{routeList.length === 1 ? '' : 's'} between your two places. Tap a card to see steps — the others hide until you go back.
            </p>

            <div className="nav-flow-cards" role="list">
              {routeList.map((opt, idx) => (
                <button
                  key={`${opt.option_index ?? idx}-${opt.total_time_minutes}`}
                  type="button"
                  className="nav-flow-card"
                  role="listitem"
                  onClick={() => {
                    setPickedIdx(idx);
                    setStep('detail');
                  }}
                >
                  <span className="nav-flow-card-label">{opt.option_label || `Route ${idx + 1}`}</span>
                  <span className="nav-flow-card-time">{formatRouteTimeCompact(opt)}</span>
                  <span className="nav-flow-card-hint">{routeCardHint(routeList, idx)}</span>
                  {opt.simple_journey?.subtitle ? (
                    <span className="nav-flow-card-preview">{opt.simple_journey.subtitle}</span>
                  ) : null}
                </button>
              ))}
            </div>

            <div className="nav-flow-actions nav-flow-actions--spread">
              <button type="button" className="nav-flow-btn nav-flow-btn--ghost" onClick={resetFlow}>
                Change places
              </button>
              <button type="button" className="nav-flow-btn nav-flow-btn--ghost" onClick={() => onOpenFloorMap?.({ fromId: from, toId: to, routeIndex: 0 })}>
                Open floor map
              </button>
            </div>
          </section>
        )}

        {step === 'detail' && selectedRoute && (
          <section className="nav-flow-panel nav-flow-panel--detail" aria-labelledby="nav-flow-detail-title">
            <div className="nav-flow-detail-head">
              <div>
                <h2 id="nav-flow-detail-title" className="nav-flow-panel-title">
                  {selectedRoute.option_label || 'Your route'}
                </h2>
                <p className="nav-flow-detail-meta">{formatRouteTimeLine(selectedRoute, navPayload)}</p>
                {(selectedRoute.congestion?.disclaimer || navPayload?.congestion?.disclaimer) && (
                  <p className="nav-flow-footnote" role="note">
                    {selectedRoute.congestion?.disclaimer || navPayload?.congestion?.disclaimer}
                  </p>
                )}
              </div>
            </div>

            <RouteDetailBody route={selectedRoute} />

            <div className="nav-flow-actions nav-flow-actions--stack">
              <button
                type="button"
                className="nav-flow-btn nav-flow-btn--secondary"
                disabled={guidedLoading}
                onClick={() => startGuidedNav()}
              >
                {guidedLoading ? 'Preparing…' : 'Start step-by-step guidance'}
              </button>
            </div>
            {guidedErr && step === 'detail' ? (
              <p className="nav-flow-error" role="alert">
                {guidedErr}
              </p>
            ) : null}

            <div className="nav-flow-actions nav-flow-actions--spread">
              <button type="button" className="nav-flow-btn nav-flow-btn--ghost" onClick={() => setStep('routes')}>
                Choose a different route
              </button>
              <button type="button" className="nav-flow-btn nav-flow-btn--primary" onClick={openMapForSelection}>
                View on floor map
              </button>
            </div>
            <button type="button" className="nav-flow-linkish" onClick={resetFlow}>
              Start over with new places
            </button>
          </section>
        )}

        {step === 'guided' && guidedPayload && (
          <section className="nav-flow-panel nav-flow-panel--guided" aria-labelledby="nav-flow-guided-title">
            <div className="nav-flow-guided-layout">
              <div className="nav-flow-guided-main">
            <h2 id="nav-flow-guided-title" className="nav-flow-panel-title">
              Live guidance
            </h2>
            {guidedDone ? (
              <>
                <p className="nav-flow-panel-hint">
                  You confirmed the last checkpoint for <strong>{to}</strong>. Open the map if you want the full path
                  drawing, or exit when you are at your gate or desk.
                </p>
                <div className="nav-flow-actions nav-flow-actions--spread">
                  <button type="button" className="nav-flow-btn nav-flow-btn--ghost" onClick={exitGuidedNav}>
                    Back to route summary
                  </button>
                  <button type="button" className="nav-flow-btn nav-flow-btn--primary" onClick={openMapForSelection}>
                    View on floor map
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="nav-flow-guided-progress">
                  Step {guidedStepIndex + 1} of {guidedSteps.length}
                  {guidedCur?.to_place_label ? (
                    <span className="nav-flow-guided-target"> · Toward {guidedCur.to_place_label}</span>
                  ) : null}
                </p>

                {guidedPhase === 'question' && guidedCur ? (
                  <div className="nav-flow-guided-question" role="status">
                    <p>{guidedCur.question}</p>
                    {Array.isArray(guidedCur.look_for) && guidedCur.look_for.length > 0 ? (
                      <ul className="nav-flow-guided-lookfor">
                        {guidedCur.look_for.map((x) => (
                          <li key={x}>{x}</li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ) : null}

                {guidedPhase === 'lost_observation' ? (
                  <div className="nav-flow-guided-lost">
                    <label className="nav-flow-field" htmlFor="nav-flow-lost-obs">
                      What do you see right next to you?
                    </label>
                    <input
                      id="nav-flow-lost-obs"
                      className="nav-flow-input"
                      type="text"
                      placeholder="e.g. washroom, Starbucks, baggage belt…"
                      value={lostObservation}
                      onChange={(e) => setLostObservation(e.target.value)}
                      autoComplete="off"
                    />
                    <p className="nav-flow-footnote">
                      We match your text to shops and facilities on the graph, then rank likely spots near where you
                      were on the planned route.
                    </p>
                  </div>
                ) : null}

                {guidedPhase === 'candidates' ? (
                  <div className="nav-flow-guided-candidates">
                    {relocalizeCandidates.length === 0 ? (
                      <p className="nav-flow-panel-hint">
                        No strong match — try another word (restroom, duty-free, information, belt number…).
                      </p>
                    ) : (
                      <ul className="nav-flow-candidate-list">
                        {relocalizeCandidates.map((c) => (
                          <li key={c.graph_node_id}>
                            <button
                              type="button"
                              className="nav-flow-candidate-btn"
                              disabled={guidedLoading}
                              onClick={() => applyRelocalizeNode(c.graph_node_id)}
                            >
                              <span className="nav-flow-candidate-label">{c.label}</span>
                              <span className="nav-flow-candidate-meta">
                                ~{c.walking_minutes_from_last_anchor} min from last confirmed spot · score {c.match_score}
                              </span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                    <button
                      type="button"
                      className="nav-flow-linkish"
                      onClick={() => {
                        setGuidedPhase('question');
                        setRelocalizeCandidates([]);
                      }}
                    >
                      Back to checkpoint question
                    </button>
                  </div>
                ) : null}

                {guidedErr ? (
                  <p className="nav-flow-error" role="alert">
                    {guidedErr}
                  </p>
                ) : null}

                {guidedPhase === 'question' && guidedCur ? (
                  <div className="nav-flow-actions nav-flow-actions--guided">
                    {notYetHint ? (
                      <p className="nav-flow-footnote" role="status">
                        {notYetHint}
                      </p>
                    ) : null}
                    <TtsMiniBar
                      sessionId="nav-guided"
                      text={buildGuidedCheckpointSpeech(guidedCur)}
                      buttonClass="nav-flow-btn nav-flow-btn--ghost"
                      wrapClass="nav-flow-tts-guided-wrap"
                      disabled={guidedLoading}
                    />
                    <button
                      type="button"
                      className="nav-flow-btn nav-flow-btn--primary"
                      disabled={guidedLoading}
                      onClick={confirmGuidedYes}
                    >
                      Yes — I see that
                    </button>
                    <button
                      type="button"
                      className="nav-flow-btn nav-flow-btn--ghost"
                      disabled={guidedLoading}
                      onClick={() =>
                        setNotYetHint(
                          'No problem — keep following the path. Press Yes when you recognise the cues for this step.',
                        )
                      }
                    >
                      Not yet — still walking
                    </button>
                    <button
                      type="button"
                      className="nav-flow-btn nav-flow-btn--ghost"
                      disabled={guidedLoading}
                      onClick={() => {
                        setGuidedPhase('lost_observation');
                        setLostObservation('');
                      }}
                    >
                      No — I am somewhere else
                    </button>
                  </div>
                ) : null}

                {guidedPhase === 'lost_observation' ? (
                  <div className="nav-flow-actions nav-flow-actions--spread">
                    <button
                      type="button"
                      className="nav-flow-btn nav-flow-btn--ghost"
                      disabled={guidedLoading}
                      onClick={() => {
                        setGuidedPhase('question');
                        setLostObservation('');
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="nav-flow-btn nav-flow-btn--primary"
                      disabled={guidedLoading || !lostObservation.trim()}
                      onClick={() => submitLostObservation()}
                    >
                      {guidedLoading ? 'Searching…' : 'Find where I might be'}
                    </button>
                  </div>
                ) : null}

                <div className="nav-flow-actions nav-flow-actions--spread">
                  <button type="button" className="nav-flow-btn nav-flow-btn--ghost" onClick={exitGuidedNav}>
                    Exit live guidance
                  </button>
                  <button type="button" className="nav-flow-btn nav-flow-btn--ghost" onClick={openMapForSelection}>
                    Floor map
                  </button>
                </div>
              </>
            )}
              </div>
              <GuidedStepMap
                path={guidedPayload.path}
                steps={guidedSteps}
                stepIndex={guidedStepIndex}
                guidedDone={guidedDone}
                nextLookFor={guidedDone ? [] : guidedCur?.look_for}
              />
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
