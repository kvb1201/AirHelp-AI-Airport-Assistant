import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { fetchFacilities, fetchMapData, fetchNavigation, fetchShops } from '../services/api';
import TtsMiniBar from './TtsMiniBar';
import { formatRouteTimeCompact, formatRouteTimeLine } from '../utils/routeEstimate';
import { buildRouteSpeechText } from '../utils/routeSpeech';
import { buildTerminalPlanProjection, PLAN_H, PLAN_W } from '../utils/terminalPlanGeometry';

const BUSY_TERMINAL_STORAGE_KEY = 'airhelp_busy_terminal';

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

export default function TerminalMapView({ location, onLocationChange, launchRoute, onLaunchRouteConsumed }) {
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
  /** Skip one debounced `fetchRoute(from,to)` after map “pick From” so we don’t route with stale To before the second tap. */
  const skipDebouncedRouteFetchOnce = useRef(false);
  const prevLocationRef = useRef(undefined);
  const [loading, setLoading] = useState(false);
  /** Full navigation API payload (may include `routes` array for alternatives). */
  const [navPayload, setNavPayload] = useState(null);
  const [activeRouteIdx, setActiveRouteIdx] = useState(0);
  const [routeErr, setRouteErr] = useState(null);
  const [busyTerminal, setBusyTerminal] = useState(() => {
    try {
      return typeof window !== 'undefined' && window.localStorage?.getItem(BUSY_TERMINAL_STORAGE_KEY) === '1';
    } catch {
      return false;
    }
  });

  const mapStackRef = useRef(null);
  const mapPanInnerRef = useRef(null);
  const mapPanRef = useRef({ x: 0, y: 0 });
  const mapPanDragRef = useRef({
    active: false,
    pointerId: null,
    startX: 0,
    startY: 0,
    originX: 0,
    originY: 0,
    maxX: 1,
    maxY: 1,
  });
  const [mapPan, setMapPan] = useState({ x: 0, y: 0 });
  const [mapIsPanning, setMapIsPanning] = useState(false);

  useEffect(() => {
    mapPanRef.current = mapPan;
  }, [mapPan]);

  const onMapPanPointerDown = useCallback((e) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    if (e.target.closest?.('.terminal-map-node')) return;
    const stack = mapStackRef.current;
    if (!stack) return;
    const rect = stack.getBoundingClientRect();
    const w = Math.max(1, rect.width);
    const h = Math.max(1, rect.height);
    const d = mapPanDragRef.current;
    d.active = true;
    d.pointerId = e.pointerId;
    d.startX = e.clientX;
    d.startY = e.clientY;
    d.originX = mapPanRef.current.x;
    d.originY = mapPanRef.current.y;
    d.maxX = w * 0.48;
    d.maxY = h * 0.48;
    setMapIsPanning(true);
    try {
      mapPanInnerRef.current?.setPointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
  }, []);

  const onMapPanPointerMove = useCallback((e) => {
    const d = mapPanDragRef.current;
    if (!d.active || e.pointerId !== d.pointerId) return;
    const nx = Math.max(-d.maxX, Math.min(d.maxX, d.originX + (e.clientX - d.startX)));
    const ny = Math.max(-d.maxY, Math.min(d.maxY, d.originY + (e.clientY - d.startY)));
    setMapPan({ x: nx, y: ny });
  }, []);

  const endMapPan = useCallback((e) => {
    const d = mapPanDragRef.current;
    if (!d.active) return;
    if (e?.pointerId != null && e.pointerId !== d.pointerId) return;
    const pid = d.pointerId;
    d.active = false;
    d.pointerId = null;
    setMapIsPanning(false);
    try {
      if (pid != null && mapPanInnerRef.current?.releasePointerCapture) {
        mapPanInnerRef.current.releasePointerCapture(pid);
      }
    } catch {
      /* ignore */
    }
  }, []);

  const onMapPanLostCapture = useCallback(() => {
    const d = mapPanDragRef.current;
    d.active = false;
    d.pointerId = null;
    setMapIsPanning(false);
  }, []);

  useEffect(() => {
    const onBlur = () => {
      endMapPan(undefined);
    };
    window.addEventListener('blur', onBlur);
    return () => window.removeEventListener('blur', onBlur);
  }, [endMapPan]);

  const onMapPanDoubleClick = useCallback((e) => {
    if (e.target.closest?.('.terminal-map-node')) return;
    setMapPan({ x: 0, y: 0 });
  }, []);

  const route = useMemo(() => {
    if (!navPayload?.ok) return null;
    const list = navPayload.routes;
    if (Array.isArray(list) && list.length > 0) {
      return list[activeRouteIdx] ?? list[0];
    }
    return navPayload;
  }, [navPayload, activeRouteIdx]);
  const [shops, setShops] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [facilitiesByNode, setFacilitiesByNode] = useState([]);

  const { mx, my, ns, nxs, planCalib, graphFlip180 } = useMemo(() => buildTerminalPlanProjection(meta), [meta]);

  useEffect(() => {
    try {
      window.localStorage?.setItem(BUSY_TERMINAL_STORAGE_KEY, busyTerminal ? '1' : '0');
    } catch {
      /* ignore */
    }
  }, [busyTerminal]);

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
    () =>
      [...nodes].sort((a, b) =>
        (a.passenger_name || a.name || '').localeCompare(b.passenger_name || b.name || '', undefined, {
          sensitivity: 'base',
        }),
      ),
    [nodes],
  );

  const pathIds = useMemo(() => new Set((route?.path || []).map((p) => p.id)), [route]);

  /**
   * When a route is loaded, show only that walk on the map.
   * IMPORTANT: `ok` lives on `navPayload`, not on each `route` option — do not use `route.ok` here.
   */
  const routeFocusMode = Boolean(
    navPayload?.ok && route && Array.isArray(route.path) && route.path.length > 0,
  );

  const nodesPool = useMemo(() => {
    if (!routeFocusMode) return sortedNodes;
    const keep = new Set(pathIds);
    keep.add(from);
    keep.add(to);
    return sortedNodes.filter((n) => keep.has(n.id));
  }, [sortedNodes, routeFocusMode, pathIds, from, to]);

  /** Draw From/To on top of other nodes so rings and labels stay readable. */
  const nodesRenderOrder = useMemo(() => {
    const rest = nodesPool.filter((n) => n.id !== from && n.id !== to);
    const ends = nodesPool.filter((n) => n.id === from || n.id === to);
    return [...rest, ...ends];
  }, [nodesPool, from, to]);

  const fetchRoute = useCallback(
    async (startId, endId, opts = {}) => {
      const prefer = typeof opts.preferRouteIdx === 'number' ? opts.preferRouteIdx : 0;
      setLoading(true);
      setNavPayload(null);
      setActiveRouteIdx(prefer);
      setRouteErr(null);
      try {
        const data = await fetchNavigation(startId, endId, {
          localHour: new Date().getHours(),
          busyTerminal,
          ...opts,
        });
        const nav = data?.data?.navigation;
        if (!nav?.ok) {
          setRouteErr(nav?.hint || nav?.error || 'No route');
          return;
        }
        setNavPayload(nav);
        const list = nav.routes;
        const maxIdx = Array.isArray(list) && list.length ? list.length - 1 : 0;
        setActiveRouteIdx(Math.min(Math.max(prefer, 0), maxIdx));
        if (onLocationChange) onLocationChange(startId);
      } catch (e) {
        setRouteErr(e.message || 'API error');
      } finally {
        setLoading(false);
      }
    },
    [onLocationChange, busyTerminal],
  );

  useEffect(() => {
    if (skipDebouncedRouteFetchOnce.current) {
      skipDebouncedRouteFetchOnce.current = false;
      return undefined;
    }
    if (!from || !to) return undefined;
    const tid = window.setTimeout(() => {
      void fetchRoute(from, to);
    }, 450);
    return () => window.clearTimeout(tid);
  }, [from, to, fetchRoute, busyTerminal]);

  useEffect(() => {
    if (!launchRoute?.fromId || !launchRoute?.toId) return;
    skipDebouncedRouteFetchOnce.current = true;
    const ri = typeof launchRoute.routeIndex === 'number' ? launchRoute.routeIndex : 0;
    prevLocationRef.current = launchRoute.fromId;
    setFrom(launchRoute.fromId);
    setTo(launchRoute.toId);
    fromRef.current = launchRoute.fromId;
    setTapPhase('from');
    tapPhaseRef.current = 'from';
    let cancelled = false;
    void (async () => {
      await fetchRoute(launchRoute.fromId, launchRoute.toId, { preferRouteIdx: ri });
      if (!cancelled) onLaunchRouteConsumed?.();
    })();
    return () => {
      cancelled = true;
    };
  }, [launchRoute, fetchRoute, onLaunchRouteConsumed]);

  const runRoute = useCallback(() => {
    fetchRoute(from, to);
  }, [from, to, fetchRoute]);

  const onPickNode = useCallback(
    (id) => {
      if (tapPhaseRef.current === 'from') {
        skipDebouncedRouteFetchOnce.current = true;
        fromRef.current = id;
        tapPhaseRef.current = 'to';
        setFrom(id);
        setTapPhase('to');
        setNavPayload(null);
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

  const routeOptions = navPayload?.routes;

  const polylinePts = useMemo(() => {
    if (!route?.path) return '';
    return route.path
      .filter((p) => p.x != null && p.y != null)
      .map((p) => `${mx(p.x)},${my(p.y)}`)
      .join(' ');
  }, [route, mx, my]);

  const onDropdownFrom = (e) => {
    const v = e.target.value;
    setFrom(v);
    fromRef.current = v;
    setTapPhase('from');
    setNavPayload(null);
    setRouteErr(null);
  };

  const onDropdownTo = (e) => {
    setTo(e.target.value);
    setTapPhase('from');
    setNavPayload(null);
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
        <div
          ref={mapStackRef}
          className={`terminal-map-stack${routeFocusMode ? ' terminal-map-stack--route-focus' : ''}${mapIsPanning ? ' terminal-map-stack--panning' : ''}`}
        >
          <div
            ref={mapPanInnerRef}
            className="terminal-map-pan-inner"
            style={{ transform: `translate3d(${mapPan.x}px, ${mapPan.y}px, 0)` }}
            onPointerDown={onMapPanPointerDown}
            onPointerMove={onMapPanPointerMove}
            onPointerUp={endMapPan}
            onPointerCancel={endMapPan}
            onLostPointerCapture={onMapPanLostCapture}
            onDoubleClick={onMapPanDoubleClick}
          >
          <svg
            className="terminal-map-svg-full"
            viewBox={`0 0 ${PLAN_W} ${PLAN_H}`}
            preserveAspectRatio="xMidYMid meet"
            overflow="visible"
            role="img"
            aria-label="Terminal floor plan with walking graph"
          >
            <defs>
              <filter id="terminalMapNodeGlow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="2.2" result="b" />
                <feMerge>
                  <feMergeNode in="b" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <g
              className="terminal-map-floor-calib"
              transform={`translate(${planCalib.tx}, ${planCalib.ty}) translate(${PLAN_W / 2}, ${PLAN_H / 2}) scale(${planCalib.kx}, ${planCalib.ky}) translate(${-PLAN_W / 2}, ${-PLAN_H / 2})`}
            >
              <image
                className="terminal-map-floor-image"
                href="/mumbai-t2-l2-plan.jpg"
                width={PLAN_W}
                height={PLAN_H}
                x={0}
                y={0}
                preserveAspectRatio="none"
              />
            </g>

            {!routeFocusMode ? (
              <g
                className="terminal-map-x-guide-wrap terminal-map-no-pointer"
                style={{ pointerEvents: 'none' }}
                transform={graphFlip180 ? `rotate(180 ${PLAN_W / 2} ${PLAN_H / 2})` : undefined}
              >
                <g
                  className="terminal-map-x-guide"
                  opacity={0.42}
                  transform={`scale(${PLAN_W / 100}, ${PLAN_H / 100})`}
                >
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
                    strokeWidth={2.5}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    vectorEffect="nonScalingStroke"
                  />
                </g>
              </g>
            ) : null}

            {!routeFocusMode ? (
              <g className="terminal-map-edges terminal-map-no-pointer" opacity={0.22} style={{ pointerEvents: 'none' }}>
                {edges.map((e) => {
                  const a = byId[e.from];
                  const b = byId[e.to];
                  if (!a || !b || a.x == null || b.x == null) return null;
                  return (
                    <line
                      key={`${e.from}-${e.to}`}
                      x1={mx(a.x)}
                      y1={my(a.y)}
                      x2={mx(b.x)}
                      y2={my(b.y)}
                      stroke="#4d4447"
                      strokeWidth={Math.max(1.5, ns(0.12))}
                    />
                  );
                })}
              </g>
            ) : null}

            {!routeFocusMode ? (
              <>
                <g className="terminal-map-facilities" style={{ pointerEvents: 'none' }} aria-hidden="false">
                  {facilities.map((f) => {
                    const x = Number(f.x_norm);
                    const y = Number(f.y_norm);
                    if (Number.isNaN(x) || Number.isNaN(y)) return null;
                    const h = ns(0.85);
                    const w = ns(0.55);
                    const pts = `0,-${h} ${w},${h * 0.55} -${w},${h * 0.55}`;
                    return (
                      <g key={f.facility_id} className="terminal-map-facility-marker" transform={`translate(${mx(x)},${my(y)})`}>
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
                          strokeWidth={Math.max(1, ns(0.1))}
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
                    const w = ns(1.15);
                    return (
                      <g key={s.shop_id} className="terminal-map-shop-marker" transform={`translate(${mx(x)},${my(y)}) rotate(45)`}>
                        <title>
                          {s.name_display}
                          {s.category ? ` · ${s.category}` : ''}
                          {s.listing_location ? ` · ${s.listing_location}` : ''}
                          {s.graph_node_id ? ` · Route: ${s.graph_node_id}` : ''}
                        </title>
                        <rect x={-w / 2} y={-w / 2} width={w} height={w} rx={ns(0.2)} fill="#9c27b0" fillOpacity={0.88} stroke="#fff" strokeWidth={Math.max(1, ns(0.12))} />
                      </g>
                    );
                  })}
                </g>
              </>
            ) : null}

            {nodesRenderOrder.map((n) => {
              if (n.x == null || n.y == null) return null;
              const onPath = pathIds.has(n.id);
              const isFrom = n.id === from;
              const isTo = n.id === to;
              const endpoint = isFrom || isTo;
              /** In route-focus mode, enlarge path dots and From/To so the chosen walk reads clearly. */
              let r;
              if (endpoint) {
                r = routeFocusMode ? 2.72 : 2.05;
              } else if (routeFocusMode && onPath) {
                r = 1.68;
              } else if (onPath) {
                r = 1.2;
              } else {
                r = 0.78;
              }
              const ringExtraOuter = routeFocusMode && endpoint ? 0.72 : 0.55;
              const ringExtraInner = routeFocusMode && endpoint ? 0.32 : 0.22;
              const phaseHint = tapPhase === 'from' ? 'Set as From' : 'Set as To and run route';
              const pathStepFill = routeFocusMode ? '#5c6b73' : nodeColor(n.kind);
              const fill = endpoint ? (isFrom ? '#ffc107' : '#29b6f6') : pathStepFill;
              const stroke = endpoint ? (isFrom ? '#5d4037' : '#0d47a1') : 'rgba(255,255,255,0.95)';
              const strokeW = endpoint ? 0.52 : routeFocusMode ? 0.28 : onPath ? 0.22 : 0.2;
              const cx = mx(n.x);
              const cy = my(n.y);
              const pr = nxs(r);
              return (
                <g key={n.id} className={`terminal-map-node${endpoint ? ' terminal-map-node--endpoint' : ''}`}>
                  {endpoint ? (
                    <>
                      <circle
                        cx={cx}
                        cy={cy}
                        r={nxs(r + ringExtraOuter)}
                        fill="none"
                        stroke={isFrom ? '#ff8f00' : '#81d4fa'}
                        strokeWidth={Math.max(1.25, nxs(routeFocusMode ? 0.44 : 0.38))}
                        opacity={0.95}
                        style={{ pointerEvents: 'none' }}
                        aria-hidden
                      />
                      <circle
                        cx={cx}
                        cy={cy}
                        r={nxs(r + ringExtraInner)}
                        fill="none"
                        stroke={isFrom ? '#fff8e1' : '#e1f5fe'}
                        strokeWidth={Math.max(1, nxs(routeFocusMode ? 0.24 : 0.2))}
                        style={{ pointerEvents: 'none' }}
                        aria-hidden
                      />
                    </>
                  ) : null}
                  <circle
                    cx={cx}
                    cy={cy}
                    r={pr}
                    fill={fill}
                    stroke={stroke}
                    strokeWidth={Math.max(0.85, nxs(strokeW))}
                    filter={onPath && !endpoint ? 'url(#terminalMapNodeGlow)' : undefined}
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
                    aria-label={`${n.passenger_name || n.name}. ${phaseHint}.`}
                  />
                  {endpoint ? (
                    <text
                      x={cx}
                      y={cy - pr - nxs(routeFocusMode ? 1.42 : 1.05)}
                      textAnchor="middle"
                      className="terminal-map-node-label terminal-map-node-label--endpoint"
                      fill={isFrom ? '#3e2723' : '#01579b'}
                      stroke="#ffffff"
                      strokeWidth={Math.max(1.1, nxs(routeFocusMode ? 0.38 : 0.34))}
                      paintOrder="stroke fill"
                      fontSize={nxs(routeFocusMode ? 3.15 : 2.85)}
                      fontWeight="800"
                      style={{ pointerEvents: 'none' }}
                    >
                      {isFrom ? 'FROM' : 'TO'}
                    </text>
                  ) : null}
                </g>
              );
            })}

            {polylinePts ? (
              <polyline
                className={`terminal-map-route-line terminal-map-no-pointer${routeFocusMode ? ' terminal-map-route-line--focus' : ''}`}
                style={{ pointerEvents: 'none' }}
                points={polylinePts}
                fill="none"
                stroke="#735c00"
                strokeWidth={routeFocusMode ? 7.25 : 4.75}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ) : null}
          </svg>

          <div className="terminal-map-tap-badge" aria-live="polite">
            {tapPhase === 'from' ? 'Tap map: pick From' : 'Tap map: pick To (route runs)'}
          </div>

          <div className="terminal-map-pan-hint" aria-hidden>
            Drag empty map area to move · double-click to reset
          </div>

          <div className={`terminal-map-legend${routeFocusMode ? ' terminal-map-legend--route-focus' : ''}`}>
            {routeFocusMode ? (
              <span className="terminal-map-legend-route-msg">
                Showing <strong>your chosen walk</strong> only — gold line is the path. Tap the orange/blue markers to
                change From or To. Press <strong>Show full map</strong> in the side panel to see every node again.
              </span>
            ) : (
              <>
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
              </>
            )}
          </div>
          </div>
        </div>

        <aside className="terminal-map-side">
          <h2 className="terminal-map-side-title">Route</h2>
          <p className="terminal-map-side-hint">
            <strong>Map:</strong> first tap sets <strong>From</strong>, second tap sets <strong>To</strong> and loads
            the path. Changing <strong>From</strong> or <strong>To</strong> in the dropdowns also recomputes the walk
            after a short delay (map stays full until a route succeeds). Teal triangles = airport facilities; purple
            diamonds = shops. Facilities below are grouped by walking-graph node (every facility appears under its node).
          </p>

          <details className="terminal-map-shops-panel">
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

          <details className="terminal-map-shops-panel">
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
                  {n.passenger_name || n.name}
                </option>
              ))}
            </select>
          </label>
          <label className="terminal-map-field">
            To
            <select className="terminal-map-select" value={to} onChange={onDropdownTo}>
              {sortedNodes.map((n) => (
                <option key={`t-${n.id}`} value={n.id}>
                  {n.passenger_name || n.name}
                </option>
              ))}
            </select>
          </label>

          <label className="terminal-map-field terminal-map-field--checkbox">
            <input
              type="checkbox"
              checked={busyTerminal}
              onChange={(e) => setBusyTerminal(e.target.checked)}
            />
            <span>Busy terminal (adds typical security-queue allowance — not live crowd data)</span>
          </label>

          <button
            type="button"
            className="terminal-map-btn"
            onClick={runRoute}
            disabled={loading || !sortedNodes.length}
          >
            {loading ? 'Computing…' : 'Compute route'}
          </button>

          {routeFocusMode ? (
            <button
              type="button"
              className="terminal-map-btn terminal-map-btn--secondary"
              onClick={() => {
                setNavPayload(null);
                setRouteErr(null);
              }}
            >
              Show full map
            </button>
          ) : null}

          {routeErr && (
            <p className="terminal-map-side-error" role="alert">
              {routeErr}
            </p>
          )}

          {navPayload?.ok && route && (
            <div className="terminal-map-result">
              {Array.isArray(routeOptions) && routeOptions.length > 1 ? (
                <div className="terminal-map-route-options" role="tablist" aria-label="Route choices">
                  <div className="terminal-map-route-options-title">Pick a way to walk</div>
                  <p className="terminal-map-route-options-hint">
                    We show up to three different walking paths. Fastest is first; others may add a few minutes but can
                    feel less crowded.
                  </p>
                  <div className="terminal-map-route-options-row">
                    {routeOptions.map((opt, idx) => {
                      const base = routeOptions[0]?.total_time_minutes ?? 0;
                      const delta = (opt.total_time_minutes ?? 0) - base;
                      const hint =
                        idx === 0
                          ? 'Shortest time'
                          : delta === 0
                            ? 'Same time, different path'
                            : `About +${delta} min`;
                      return (
                        <button
                          key={`${opt.option_index ?? idx}-${opt.total_time_minutes}`}
                          type="button"
                          className={`terminal-map-route-opt${idx === activeRouteIdx ? ' terminal-map-route-opt--active' : ''}`}
                          onClick={() => setActiveRouteIdx(idx)}
                          role="tab"
                          aria-selected={idx === activeRouteIdx}
                        >
                          <span className="terminal-map-route-opt-label">
                            {opt.option_label || `Route ${idx + 1}`}
                          </span>
                          <span className="terminal-map-route-opt-time">{formatRouteTimeCompact(opt)}</span>
                          <span className="terminal-map-route-opt-hint">{hint}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              <div className="terminal-map-result-meta">
                {Array.isArray(routeOptions) && routeOptions.length > 1 ? (
                  <>
                    Following <strong>{route.option_label || 'selected route'}</strong> — {formatRouteTimeLine(route, navPayload)}.
                  </>
                ) : (
                  <>{formatRouteTimeLine(route, navPayload)} — plain-language steps below (no staff gate codes).</>
                )}
              </div>
              {(route.congestion?.disclaimer || navPayload?.congestion?.disclaimer) && (
                <p className="terminal-map-side-hint terminal-map-congestion-note" role="note">
                  {route.congestion?.disclaimer || navPayload?.congestion?.disclaimer}
                </p>
              )}

              {Array.isArray(route.shops_along_route?.tips) && route.shops_along_route.tips.length > 0 ? (
                <section className="terminal-map-route-callout" aria-label="Food and shopping near your walk">
                  <div className="terminal-map-route-callout-kicker">While you walk</div>
                  <h3 className="terminal-map-route-callout-title">Places you could stop</h3>
                  <p className="terminal-map-route-callout-lead">
                    These sit on the same general path (same area as your route). You can skip them or dip in if you
                    have time.
                  </p>
                  <ul className="terminal-map-recommendations-tips">
                    {route.shops_along_route.tips.map((t, i) => (
                      <li key={i}>{t}</li>
                    ))}
                  </ul>
                </section>
              ) : null}

              {route.simple_journey?.subtitle ? (
                <p className="terminal-map-journey-line">{route.simple_journey.subtitle}</p>
              ) : null}

              {Array.isArray(route.simple_journey?.bullets) && route.simple_journey.bullets.length > 0 ? (
                <>
                  <div className="terminal-map-journey-heading terminal-map-journey-heading--row">
                    <span>Your route</span>
                    {buildRouteSpeechText(route) ? (
                      <TtsMiniBar
                        sessionId="map-route-side"
                        text={buildRouteSpeechText(route)}
                        buttonClass="terminal-map-tts-btn"
                        wrapClass="terminal-map-tts-wrap"
                      />
                    ) : null}
                  </div>
                  <ul className="terminal-map-journey-bullets">
                    {route.simple_journey.bullets.map((line, i) => (
                      <li key={i}>{line}</li>
                    ))}
                  </ul>
                </>
              ) : buildRouteSpeechText(route) ? (
                <div className="terminal-map-read-row">
                  <TtsMiniBar
                    sessionId="map-route-side"
                    text={buildRouteSpeechText(route)}
                    buttonClass="terminal-map-tts-btn"
                    wrapClass="terminal-map-tts-wrap"
                  />
                </div>
              ) : null}

              {Array.isArray(route.shops_along_route?.picks) && route.shops_along_route.picks.length > 0 ? (
                <details className="terminal-map-tech-details">
                  <summary>Shop stops on this path ({route.shops_along_route.count_on_path || 0})</summary>
                  <ul className="terminal-map-picks-list">
                    {route.shops_along_route.picks.map((p) => (
                      <li key={p.shop_id}>
                        <span className="terminal-map-pick-name">{p.name_display}</span>
                        <span className="terminal-map-pick-meta">
                          {p.bucket_label}
                          {p.floor_display || p.floor ? ` · ${p.floor_display || p.floor}` : ''}
                        </span>
                      </li>
                    ))}
                  </ul>
                </details>
              ) : null}

              <details className="terminal-map-tech-details">
                <summary>Technical step-by-step (every graph edge)</summary>
                <ol className="terminal-map-steps">
                  {(route.steps || []).map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ol>
              </details>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
