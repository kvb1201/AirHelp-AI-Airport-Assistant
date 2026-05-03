import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchMapData, fetchNavigation } from '../services/api';

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
          <div className="nav-flow-section-title">Your route</div>
          <ul className="nav-flow-bullets">
            {route.simple_journey.bullets.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </>
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

  useEffect(() => {
    if (location) setFrom(location);
  }, [location]);

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
      const data = await fetchNavigation(from, to);
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
  }, [from, to, onLocationChange]);

  const resetFlow = () => {
    setStep('pick');
    setNavPayload(null);
    setRouteErr(null);
    setPickedIdx(0);
  };

  const openMapForSelection = () => {
    onOpenFloorMap?.({ fromId: from, toId: to, routeIndex: pickedIdx });
  };

  return (
    <div className={`nav-flow nav-flow--full-bleed${step === 'detail' ? ' nav-flow--step-detail' : ''}`}>
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
                  <span className="nav-flow-card-time">{opt.total_time_minutes} min</span>
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
                <p className="nav-flow-detail-meta">
                  About <strong>{selectedRoute.total_time_minutes}</strong> minutes walking
                </p>
              </div>
            </div>

            <RouteDetailBody route={selectedRoute} />

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
      </div>
    </div>
  );
}
