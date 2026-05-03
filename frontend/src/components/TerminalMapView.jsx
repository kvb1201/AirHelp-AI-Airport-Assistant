import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { fetchFacilities, fetchMapData, fetchNavigation, fetchShops } from '../services/api';

const KIND_COLORS = {
  entrance: '#735c00',
  security: '#ba1a1a',
  corridor: '#6b5a5f',
  gate: '#1b5e20',
  food: '#6a1b9a',
  shopping: '#c2185b',
  restroom: '#0277bd',
  service: '#455a64',
  vertical: '#37474f',
  junction: '#78909c',
  baggage: '#5d4037',
  shop: '#9c27b0',
  facility: '#00897b',
};

function nodeColor(kind) {
  return KIND_COLORS[kind] || '#6b5a5f';
}

export default function TerminalMapView({ location, onLocationChange }) {
  const [meta, setMeta] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [byId, setById] = useState({});
  const [loadErr, setLoadErr] = useState(null);

  const [from, setFrom] = useState('t2_entrance');
  const [to, setTo] = useState('t2_ne_sp_14');
  /** Map taps: first pick = From, second = To (then repeats). */
  const [tapPhase, setTapPhase] = useState('from');
  const tapPhaseRef = useRef('from');
  const fromRef = useRef(from);
  const prevLocationRef = useRef(undefined);
  const [loading, setLoading] = useState(false);
  const [route, setRoute] = useState(null);
  const [routeErr, setRouteErr] = useState(null);
  const [shops, setShops] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [facilitiesByNode, setFacilitiesByNode] = useState([]);

  useEffect(() => {
    fromRef.current = from;
  }, [from]);

  useEffect(() => {
    tapPhaseRef.current = tapPhase;
  }, [tapPhase]);

  /**
   * When parent `location` changes (chat / home), adopt it as From and reset tap sequence.
   * Map From-taps must NOT call onLocationChange — that would fire this effect and cancel To-pick.
   */
  useEffect(() => {
    if (!location) return;
    if (prevLocationRef.current === location) return;
    prevLocationRef.current = location;
    setFrom(location);
    fromRef.current = location;
    setTapPhase('from');
    tapPhaseRef.current = 'from';
  }, [location]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchMapData();
        if (cancelled) return;
        setMeta(data.meta || {});
        const list = data.nodes || [];
        setNodes(list);
        setEdges(data.edges || []);
        const m = {};
        list.forEach((n) => {
          m[n.id] = n;
        });
        setById(m);
      } catch (e) {
        if (!cancelled) setLoadErr(e.message || 'Could not load map');
        return;
      }
      try {
        const shopBundle = await fetchShops();
        if (cancelled) return;
        setShops(shopBundle.shops || []);
      } catch {
        if (!cancelled) setShops([]);
      }
      try {
        const facBundle = await fetchFacilities();
        if (cancelled) return;
        setFacilities(facBundle.facilities || []);
        setFacilitiesByNode(facBundle.facilities_by_node || []);
      } catch {
        if (!cancelled) {
          setFacilities([]);
          setFacilitiesByNode([]);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const sortedNodes = useMemo(
    () => [...nodes].sort((a, b) => (a.name || '').localeCompare(b.name || '')),
    [nodes],
  );

  const fetchRoute = useCallback(
    async (startId, endId) => {
      setLoading(true);
      setRoute(null);
      setRouteErr(null);
      try {
        const data = await fetchNavigation(startId, endId);
        const nav = data?.data?.navigation;
        if (!nav?.ok) {
          setRouteErr(nav?.hint || nav?.error || 'No route');
          return;
        }
        setRoute(nav);
        if (onLocationChange) onLocationChange(startId);
      } catch (e) {
        setRouteErr(e.message || 'API error');
      } finally {
        setLoading(false);
      }
    },
    [onLocationChange],
  );

  const runRoute = useCallback(() => {
    fetchRoute(from, to);
  }, [from, to, fetchRoute]);

  const onPickNode = useCallback(
    (id) => {
      if (tapPhaseRef.current === 'from') {
        fromRef.current = id;
        tapPhaseRef.current = 'to';
        setFrom(id);
        setTapPhase('to');
        setRoute(null);
        setRouteErr(null);
        return;
      }
      tapPhaseRef.current = 'from';
      setTapPhase('from');
      setTo(id);
      void fetchRoute(fromRef.current, id);
    },
    [fetchRoute],
  );

  const pathIds = useMemo(() => new Set((route?.path || []).map((p) => p.id)), [route]);

  const polylinePts = useMemo(() => {
    if (!route?.path) return '';
    return route.path
      .filter((p) => p.x != null && p.y != null)
      .map((p) => `${p.x},${p.y}`)
      .join(' ');
  }, [route]);

  const onDropdownFrom = (e) => {
    const v = e.target.value;
    setFrom(v);
    fromRef.current = v;
    setTapPhase('from');
    setRoute(null);
    setRouteErr(null);
  };

  const onDropdownTo = (e) => {
    setTo(e.target.value);
    setTapPhase('from');
    setRoute(null);
    setRouteErr(null);
  };

  return (
    <div className="terminal-map">
      <header className="terminal-map-header">
        <div>
          <h1 className="terminal-map-title">{meta?.title || 'Terminal map'}</h1>
          <p className="terminal-map-meta">
            {meta?.airport_name || 'BOM'} · {meta?.terminal || 'T2'} · {meta?.floor || 'L02'}
          </p>
          {meta?.disclaimer && (
            <p className="terminal-map-disclaimer">{meta.disclaimer}</p>
          )}
        </div>
      </header>

      {loadErr && (
        <p className="terminal-map-banner-error" role="alert">
          {loadErr}
        </p>
      )}

      <div className="terminal-map-body">
        <div className="terminal-map-stack">
          <img
            className="terminal-map-bg"
            src="/mumbai-t2-l2-plan.jpg"
            alt=""
            draggable={false}
          />
          <svg
            className="terminal-map-svg-overlay"
            viewBox="0 0 100 100"
            preserveAspectRatio="xMidYMid meet"
            role="presentation"
          >
            <defs>
              <filter id="node-glow" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="0.6" result="b" />
                <feMerge>
                  <feMergeNode in="b" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <g className="terminal-map-x-guide terminal-map-no-pointer" opacity="0.42" style={{ pointerEvents: 'none' }}>
              <path
                d="
                  M 10 10 L 42 40 L 50 48 L 58 40 L 90 10
                  M 10 90 L 42 56 L 50 48 L 58 56 L 90 90
                  M 42 40 L 42 56
                  M 58 40 L 58 56
                  M 50 86 L 50 72 L 50 68
                  M 46 68 L 54 68
                  M 50 64 L 50 58 L 48 53
                "
                fill="none"
                stroke="#6b5a5f"
                strokeWidth="0.32"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>

            <g className="terminal-map-edges terminal-map-no-pointer" opacity="0.22" style={{ pointerEvents: 'none' }}>
              {edges.map((e) => {
                const a = byId[e.from];
                const b = byId[e.to];
                if (!a || !b || a.x == null || b.x == null) return null;
                return (
                  <line
                    key={`${e.from}-${e.to}`}
                    x1={a.x}
                    y1={a.y}
                    x2={b.x}
                    y2={b.y}
                    stroke="#4d4447"
                    strokeWidth="0.12"
                  />
                );
              })}
            </g>

            {polylinePts && (
              <polyline
                className="terminal-map-route-line terminal-map-no-pointer"
                style={{ pointerEvents: 'none' }}
                points={polylinePts}
                fill="none"
                stroke="#735c00"
                strokeWidth="0.55"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            <g className="terminal-map-facilities" style={{ pointerEvents: 'none' }} aria-hidden="false">
              {facilities.map((f) => {
                const x = Number(f.x_norm);
                const y = Number(f.y_norm);
                if (Number.isNaN(x) || Number.isNaN(y)) return null;
                const h = 0.85;
                const w = 0.55;
                const pts = `0,-${h} ${w},${h * 0.55} -${w},${h * 0.55}`;
                return (
                  <g key={f.facility_id} className="terminal-map-facility-marker" transform={`translate(${x},${y})`}>
                    <title>
                      {f.name_display}
                      {f.category ? ` · ${f.category}` : ''}
                      {f.listing_location ? ` · ${f.listing_location}` : ''}
                      {f.graph_node_id ? ` · Route: ${f.graph_node_id}` : ''}
                    </title>
                    <polygon
                      points={pts}
                      fill="#00897b"
                      fillOpacity={0.9}
                      stroke="#fff"
                      strokeWidth={0.1}
                    />
                  </g>
                );
              })}
            </g>

            <g className="terminal-map-shops" style={{ pointerEvents: 'none' }} aria-hidden="false">
              {shops.map((s) => {
                const x = Number(s.x_norm);
                const y = Number(s.y_norm);
                if (Number.isNaN(x) || Number.isNaN(y)) return null;
                const w = 1.15;
                return (
                  <g key={s.shop_id} className="terminal-map-shop-marker" transform={`translate(${x},${y}) rotate(45)`}>
                    <title>
                      {s.name_display}
                      {s.category ? ` · ${s.category}` : ''}
                      {s.listing_location ? ` · ${s.listing_location}` : ''}
                      {s.graph_node_id ? ` · Route: ${s.graph_node_id}` : ''}
                    </title>
                    <rect x={-w / 2} y={-w / 2} width={w} height={w} rx={0.2} fill="#9c27b0" fillOpacity={0.88} stroke="#fff" strokeWidth={0.12} />
                  </g>
                );
              })}
            </g>

            {sortedNodes.map((n) => {
              if (n.x == null || n.y == null) return null;
              const onPath = pathIds.has(n.id);
              const isFrom = n.id === from;
              const isTo = n.id === to;
              const r = onPath ? 1.35 : isFrom || isTo ? 1.2 : 0.85;
              const phaseHint = tapPhase === 'from' ? 'Set as From' : 'Set as To and run route';
              return (
                <g key={n.id} className="terminal-map-node">
                  <circle
                    cx={n.x}
                    cy={n.y}
                    r={r}
                    fill={nodeColor(n.kind)}
                    stroke={isTo ? '#ffffff' : isFrom ? '#fed65b' : 'rgba(255,255,255,0.9)'}
                    strokeWidth={isFrom || isTo ? 0.45 : 0.2}
                    filter={onPath ? 'url(#node-glow)' : undefined}
                    style={{ cursor: 'pointer' }}
                    onClick={() => onPickNode(n.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(ev) => {
                      if (ev.key === 'Enter' || ev.key === ' ') {
                        ev.preventDefault();
                        onPickNode(n.id);
                      }
                    }}
                    aria-label={`${n.name}. ${phaseHint}.`}
                  />
                  {(isFrom || isTo) && (
                    <text
                      x={n.x}
                      y={n.y - r - 0.85}
                      textAnchor="middle"
                      className="terminal-map-node-label"
                      fill="#1b1c1c"
                      fontSize="2.1px"
                      fontWeight="600"
                    >
                      {isFrom ? 'From' : 'To'}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          <div className="terminal-map-tap-badge" aria-live="polite">
            {tapPhase === 'from' ? 'Tap map: pick From' : 'Tap map: pick To (route runs)'}
          </div>

          <div className="terminal-map-legend">
            {Object.entries(KIND_COLORS).map(([kind, color]) => (
              <span key={kind} className="terminal-map-legend-item">
                <i style={{ background: color }} aria-hidden />
                {kind}
              </span>
            ))}
            <span className="terminal-map-legend-item">
              <i className="terminal-map-legend-facility-icon" aria-hidden />
              facility (map)
            </span>
          </div>
        </div>

        <aside className="terminal-map-side">
          <h2 className="terminal-map-side-title">Route</h2>
          <p className="terminal-map-side-hint">
            <strong>Map:</strong> first tap sets <strong>From</strong>, second tap sets <strong>To</strong> and
            loads the path. Dropdowns reset the tap sequence to From.             Teal triangles = airport facilities;
            purple diamonds = shops. Facilities below are grouped by walking-graph node (every facility appears under its node).
          </p>

          <details className="terminal-map-shops-panel" open>
            <summary className="terminal-map-shops-summary">
              Facilities by graph node ({facilities.length} at {facilitiesByNode.length} nodes)
            </summary>
            <div className="terminal-map-facilities-by-node">
              {facilitiesByNode.map(({ graph_node_id: nodeId, node_name: nodeName, facilities: atNode }) => (
                <details key={nodeId} className="terminal-map-node-facility-block">
                  <summary className="terminal-map-node-facility-summary">
                    <span className="terminal-map-node-facility-title">{nodeName}</span>
                    <span className="terminal-map-node-facility-meta">
                      {nodeId !== '_unassigned' ? `${nodeId} · ` : ''}
                      {atNode.length}
                    </span>
                  </summary>
                  <ul className="terminal-map-shops-list terminal-map-facilities-nested-list">
                    {atNode.map((f) => (
                      <li
                        key={f.facility_id}
                        title={[f.listing_location, f.graph_node_id].filter(Boolean).join(' · ')}
                      >
                        <span className="terminal-map-shop-name">{f.name_display}</span>
                        <span className="terminal-map-shop-cat">
                          {f.category?.replace(/_/g, ' ')}
                        </span>
                        {f.page_url ? (
                          <a
                            className="terminal-map-facility-link"
                            href={f.page_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                          >
                            CSMIA page
                          </a>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </details>
              ))}
            </div>
          </details>

          <details className="terminal-map-shops-panel" open>
            <summary className="terminal-map-shops-summary">
              Shops on map ({shops.length})
            </summary>
            <ul className="terminal-map-shops-list">
              {shops.map((s) => (
                <li
                  key={s.shop_id}
                  title={[s.listing_location, s.graph_node_id].filter(Boolean).join(' · ')}
                >
                  <span className="terminal-map-shop-name">{s.name_display}</span>
                  <span className="terminal-map-shop-cat">{s.category}</span>
                  {s.graph_node_id ? (
                    <span className="terminal-map-shop-node">{s.graph_node_id}</span>
                  ) : null}
                </li>
              ))}
            </ul>
          </details>

          <label className="terminal-map-field">
            From
            <select className="terminal-map-select" value={from} onChange={onDropdownFrom}>
              {sortedNodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.name}
                </option>
              ))}
            </select>
          </label>
          <label className="terminal-map-field">
            To
            <select className="terminal-map-select" value={to} onChange={onDropdownTo}>
              {sortedNodes.map((n) => (
                <option key={`t-${n.id}`} value={n.id}>
                  {n.name}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            className="terminal-map-btn"
            onClick={runRoute}
            disabled={loading || !sortedNodes.length}
          >
            {loading ? 'Computing…' : 'Compute route'}
          </button>

          {routeErr && (
            <p className="terminal-map-side-error" role="alert">
              {routeErr}
            </p>
          )}

          {route?.ok && (
            <div className="terminal-map-result">
              <div className="terminal-map-result-meta">
                <strong>{route.total_time_minutes}</strong> min · {route.path?.length} nodes
              </div>
              <ol className="terminal-map-steps">
                {(route.steps || []).map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
