import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchMapData, fetchNavigation } from '../services/api';

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
  const [to, setTo] = useState('t2_gate_ne');
  const [loading, setLoading] = useState(false);
  const [route, setRoute] = useState(null);
  const [routeErr, setRouteErr] = useState(null);

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

  const runRoute = useCallback(async () => {
    setLoading(true);
    setRoute(null);
    setRouteErr(null);
    try {
      const data = await fetchNavigation(from, to);
      const nav = data?.data?.navigation;
      if (!nav?.ok) {
        setRouteErr(nav?.hint || nav?.error || 'No route');
        return;
      }
      setRoute(nav);
      if (onLocationChange) onLocationChange(from);
    } catch (e) {
      setRouteErr(e.message || 'API error');
    } finally {
      setLoading(false);
    }
  }, [from, to, onLocationChange]);

  const pathIds = useMemo(() => new Set((route?.path || []).map((p) => p.id)), [route]);

  const polylinePts = useMemo(() => {
    if (!route?.path) return '';
    return route.path
      .filter((p) => p.x != null && p.y != null)
      .map((p) => `${p.x},${p.y}`)
      .join(' ');
  }, [route]);

  const onPickNode = (id) => {
    setTo(id);
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
        <div className="terminal-map-canvas-wrap">
          <svg
            className="terminal-map-svg"
            viewBox="0 0 100 100"
            preserveAspectRatio="xMidYMid meet"
            role="img"
            aria-label="Level 2 walking graph"
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

            <image
              href="/mumbai-t2-l2-plan.jpg"
              x="0"
              y="0"
              width="100"
              height="100"
              preserveAspectRatio="xMidYMid slice"
              opacity="0.28"
            />

            <g className="terminal-map-x-guide" opacity="0.45">
              <path
                d="M50 78 L50 48 M38 58 L50 48 L62 58 M38 38 L50 48 L62 38 M14 86 L38 58 L50 48 L62 58 L86 86 M14 12 L38 38 L50 48 L62 38 L86 12"
                fill="none"
                stroke="var(--primary)"
                strokeWidth="0.35"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>

            <g className="terminal-map-edges" opacity="0.2">
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
                className="terminal-map-route-line"
                points={polylinePts}
                fill="none"
                stroke="var(--secondary)"
                strokeWidth="0.55"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {sortedNodes.map((n) => {
              if (n.x == null || n.y == null) return null;
              const sel = pathIds.has(n.id);
              const isFrom = n.id === from;
              const isTo = n.id === to;
              const r = sel ? 1.35 : isFrom || isTo ? 1.15 : 0.85;
              return (
                <g key={n.id} className="terminal-map-node" style={{ cursor: 'pointer' }}>
                  <circle
                    cx={n.x}
                    cy={n.y}
                    r={r}
                    fill={nodeColor(n.kind)}
                    stroke={isTo ? '#fff' : isFrom ? 'var(--secondary-fixed)' : 'rgba(255,255,255,0.85)'}
                    strokeWidth={isFrom || isTo ? 0.35 : 0.2}
                    filter={sel ? 'url(#node-glow)' : undefined}
                    onClick={() => onPickNode(n.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(ev) => {
                      if (ev.key === 'Enter' || ev.key === ' ') {
                        ev.preventDefault();
                        onPickNode(n.id);
                      }
                    }}
                    aria-label={`${n.name}, set as destination`}
                  />
                  {(isFrom || isTo || sel) && (
                    <text
                      x={n.x}
                      y={n.y - r - 0.8}
                      textAnchor="middle"
                      className="terminal-map-node-label"
                      fill="var(--on-surface)"
                      fontSize="2.2px"
                    >
                      {(isFrom && 'Start') || (isTo && 'To') || ''}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          <div className="terminal-map-legend">
            {Object.entries(KIND_COLORS).map(([kind, color]) => (
              <span key={kind} className="terminal-map-legend-item">
                <i style={{ background: color }} aria-hidden />
                {kind}
              </span>
            ))}
          </div>
        </div>

        <aside className="terminal-map-side">
          <h2 className="terminal-map-side-title">Route</h2>
          <p className="terminal-map-side-hint">
            Tap a dot to set <strong>destination</strong>. Use lists for start/end, then{' '}
            <strong>Compute route</strong>.
          </p>

          <label className="terminal-map-field">
            From
            <select
              className="terminal-map-select"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
            >
              {sortedNodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.name}
                </option>
              ))}
            </select>
          </label>
          <label className="terminal-map-field">
            To
            <select
              className="terminal-map-select"
              value={to}
              onChange={(e) => setTo(e.target.value)}
            >
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
