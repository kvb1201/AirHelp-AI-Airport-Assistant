import React, { useEffect, useMemo, useState } from 'react';
import { fetchMapData } from '../services/api';
import { buildTerminalPlanProjection, PLAN_H, PLAN_W } from '../utils/terminalPlanGeometry';

/** Full route node ids; tolerate API omitting `path` if `steps` has from/to. */
export function normalizeGuidedPath(path, steps) {
  if (Array.isArray(path) && path.length >= 2) {
    const ids = path.map((x) => (typeof x === 'string' ? x : x?.id)).filter(Boolean);
    if (ids.length >= 2) return ids;
  }
  if (!Array.isArray(steps) || steps.length === 0) return [];
  const ids = [];
  const first = steps[0];
  if (first?.from_node_id) ids.push(first.from_node_id);
  for (const st of steps) {
    if (st?.to_node_id && ids[ids.length - 1] !== st.to_node_id) ids.push(st.to_node_id);
  }
  return ids.length >= 2 ? ids : [];
}

function tripleFromStep(path, steps, stepIndex, guidedDone) {
  if (!Array.isArray(path) || path.length < 2 || !Array.isArray(steps) || steps.length === 0) {
    return null;
  }
  if (guidedDone) {
    const last = steps[steps.length - 1];
    const prevId = steps.length >= 2 ? steps[steps.length - 2].to_node_id : last.from_node_id;
    return {
      prevId,
      thisId: last.to_node_id,
      nextId: null,
    };
  }
  const cur = steps[stepIndex];
  if (!cur) return null;
  const prevId = stepIndex > 0 ? steps[stepIndex - 1].to_node_id : null;
  return {
    prevId,
    thisId: cur.from_node_id,
    nextId: cur.to_node_id,
  };
}

function slicePathBetween(pathArr, fromId, toId) {
  const i0 = pathArr.indexOf(fromId);
  const i1 = pathArr.indexOf(toId);
  if (i0 < 0 || i1 < 0) return [];
  const lo = Math.min(i0, i1);
  const hi = Math.max(i0, i1);
  return pathArr.slice(lo, hi + 1);
}

function polylinePts(ids, byId, mx, my) {
  return ids
    .map((id) => byId[id])
    .filter((n) => n && n.x != null && n.y != null)
    .map((n) => `${mx(n.x)},${my(n.y)}`)
    .join(' ');
}

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

/**
 * Floor plan + walking route for live guidance (read-only). Highlights current leg on the full path.
 */
export default function GuidedStepMap({ path, steps, stepIndex, guidedDone, nextLookFor }) {
  const [meta, setMeta] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [loadErr, setLoadErr] = useState(null);

  const pathIds = useMemo(() => normalizeGuidedPath(path, steps), [path, steps]);
  const byId = useMemo(() => {
    const m = {};
    (nodes || []).forEach((n) => {
      m[n.id] = n;
    });
    return m;
  }, [nodes]);

  const { mx, my, nxs, planCalib } = useMemo(() => buildTerminalPlanProjection(meta), [meta]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const mapData = await fetchMapData();
        if (cancelled) return;
        setMeta(mapData.meta || {});
        setNodes(mapData.nodes || []);
      } catch (e) {
        if (!cancelled) setLoadErr(e.message || 'Could not load map');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const triple = useMemo(
    () => tripleFromStep(pathIds, steps, stepIndex, guidedDone),
    [pathIds, steps, stepIndex, guidedDone],
  );

  const pathSet = useMemo(() => new Set(pathIds), [pathIds]);

  const fullLine = useMemo(() => polylinePts(pathIds, byId, mx, my), [pathIds, byId, mx, my]);

  const legIds = useMemo(() => {
    if (!triple || guidedDone) return [];
    if (!triple.nextId) return [];
    return slicePathBetween(pathIds, triple.thisId, triple.nextId);
  }, [triple, pathIds, guidedDone]);

  const legLine = useMemo(() => (legIds.length >= 2 ? polylinePts(legIds, byId, mx, my) : ''), [legIds, byId, mx, my]);

  const pathNodesRender = useMemo(() => {
    return pathIds.map((id) => byId[id]).filter(Boolean);
  }, [pathIds, byId]);

  const hintsForNext = Array.isArray(nextLookFor) ? nextLookFor.filter(Boolean).slice(0, 6) : [];

  if (loadErr) {
    return (
      <div className="guided-floor-map guided-floor-map--error" role="note">
        {loadErr}
      </div>
    );
  }

  if (!triple) {
    if (Array.isArray(steps) && steps.length > 0) {
      return (
        <div className="guided-floor-map guided-floor-map--error" role="status">
          Could not draw the map for this route. Go back and start guidance again.
        </div>
      );
    }
    return null;
  }

  if (pathIds.length < 2) {
    return (
      <div className="guided-floor-map guided-floor-map--error" role="status">
        Route is too short to show on the map.
      </div>
    );
  }

  return (
    <div className="guided-floor-map" aria-label="Floor plan and your walking route">
      <div className="guided-floor-map-inner">
        <svg
          className="guided-floor-map-svg"
          viewBox={`0 0 ${PLAN_W} ${PLAN_H}`}
          preserveAspectRatio="xMidYMid meet"
          overflow="visible"
        >
          <defs>
            <filter id="guidedMapNodeGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2.2" result="b" />
              <feMerge>
                <feMergeNode in="b" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <g
            className="guided-floor-map-calib"
            transform={`translate(${planCalib.tx}, ${planCalib.ty}) translate(${PLAN_W / 2}, ${PLAN_H / 2}) scale(${planCalib.kx}, ${planCalib.ky}) translate(${-PLAN_W / 2}, ${-PLAN_H / 2})`}
          >
            <image
              href="/mumbai-t2-l2-plan.jpg"
              width={PLAN_W}
              height={PLAN_H}
              x={0}
              y={0}
              preserveAspectRatio="none"
            />
          </g>

          {fullLine && !guidedDone ? (
            <polyline
              className="guided-floor-map-route guided-floor-map-route--full"
              points={fullLine}
              fill="none"
              stroke="#735c00"
              strokeWidth={5.5}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={0.38}
              style={{ pointerEvents: 'none' }}
            />
          ) : null}

          {legLine && !guidedDone ? (
            <polyline
              className="guided-floor-map-route guided-floor-map-route--leg"
              points={legLine}
              fill="none"
              stroke="#ffb300"
              strokeWidth={8.5}
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ pointerEvents: 'none' }}
            />
          ) : null}

          {guidedDone && fullLine ? (
            <polyline
              className="guided-floor-map-route guided-floor-map-route--done"
              points={fullLine}
              fill="none"
              stroke="#2e7d32"
              strokeWidth={7.25}
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ pointerEvents: 'none' }}
            />
          ) : null}

          <g style={{ pointerEvents: 'none' }}>
            {pathNodesRender.map((n) => {
              if (n.x == null || n.y == null) return null;
              const onLeg = legIds.length >= 2 && legIds.includes(n.id);
              const isPrev = triple.prevId && n.id === triple.prevId;
              const isThis = n.id === triple.thisId;
              const isNext = triple.nextId && n.id === triple.nextId;
              const emphasis = isPrev || isThis || isNext;
              let r = emphasis ? 2.35 : pathSet.has(n.id) ? 1.55 : 0.9;
              if (guidedDone && n.id === triple.thisId) r = 2.85;
              const cx = mx(n.x);
              const cy = my(n.y);
              const pr = nxs(r);
              let fill = nodeColor(n.kind);
              let stroke = 'rgba(255,255,255,0.92)';
              let sw = 0.22;
              if (isThis) {
                fill = guidedDone ? '#43a047' : '#ffb300';
                stroke = guidedDone ? '#1b5e20' : '#5d4037';
                sw = 0.42;
              } else if (isNext) {
                fill = '#29b6f6';
                stroke = '#0d47a1';
                sw = 0.38;
              } else if (isPrev) {
                fill = '#90a4ae';
                stroke = '#37474f';
                sw = 0.32;
              }
              return (
                <g key={n.id}>
                  {emphasis ? (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={nxs(r + 0.55)}
                      fill="none"
                      stroke={isThis ? (guidedDone ? '#a5d6a7' : '#ffe082') : isNext ? '#81d4fa' : '#cfd8dc'}
                      strokeWidth={Math.max(1.1, nxs(0.36))}
                      opacity={0.95}
                    />
                  ) : null}
                  <circle
                    cx={cx}
                    cy={cy}
                    r={pr}
                    fill={fill}
                    stroke={stroke}
                    strokeWidth={Math.max(0.85, nxs(sw))}
                    filter={onLeg && !emphasis ? 'url(#guidedMapNodeGlow)' : undefined}
                  />
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {!guidedDone && hintsForNext.length > 0 ? (
        <p className="guided-floor-map-hints">
          <span className="guided-floor-map-hints-label">Look for</span> {hintsForNext.join(' · ')}
        </p>
      ) : guidedDone ? (
        <p className="guided-floor-map-hints guided-floor-map-hints--done">Green highlight: you reached this guided destination.</p>
      ) : null}
    </div>
  );
}
