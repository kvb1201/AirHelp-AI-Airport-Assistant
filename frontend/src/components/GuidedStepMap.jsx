import React, { useEffect, useMemo, useState } from 'react';
import { fetchFacilities, fetchMapData, fetchShops } from '../services/api';

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
      labelPrev: 'Previous',
      labelThis: 'You arrived',
      labelNext: null,
    };
  }
  const cur = steps[stepIndex];
  if (!cur) return null;
  const prevId = stepIndex > 0 ? steps[stepIndex - 1].to_node_id : null;
  return {
    prevId,
    thisId: cur.from_node_id,
    nextId: cur.to_node_id,
    labelPrev: 'Previous',
    labelThis: 'This leg',
    labelNext: 'Next',
  };
}

function placeLabel(nodeId, byId) {
  const n = byId[nodeId];
  if (!n) return nodeId;
  return n.passenger_name || n.name || nodeId;
}

function featuresAroundNode(nodeId, facilities, shops, maxEach = 8) {
  const fid = String(nodeId || '').trim();
  const fac = (facilities || [])
    .filter((f) => String(f.graph_node_id || '').trim() === fid)
    .map((f) => ({
      key: `f-${f.facility_id}`,
      title: f.name_display || f.name_normalized,
      sub: f.category ? String(f.category).replace(/_/g, ' ') : '',
    }))
    .slice(0, maxEach);
  const sho = (shops || [])
    .filter((s) => String(s.graph_node_id || '').trim() === fid)
    .map((s) => ({
      key: `s-${s.shop_id}`,
      title: s.name_display || s.name_normalized,
      sub: s.category ? String(s.category).replace(/_/g, ' ') : '',
    }))
    .slice(0, maxEach);
  return { fac, sho };
}

/**
 * Three-node navigation strip (no floor image): previous · this leg · next, each with
 * shops and facilities tied to that walking-graph node. Updates when the parent advances steps.
 */
export default function GuidedStepMap({ path, steps, stepIndex, guidedDone, nextLookFor }) {
  const [byId, setById] = useState({});
  const [facilities, setFacilities] = useState([]);
  const [shops, setShops] = useState([]);
  const [loadErr, setLoadErr] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [mapData, facBundle, shopBundle] = await Promise.all([
          fetchMapData(),
          fetchFacilities().catch(() => ({ facilities: [] })),
          fetchShops().catch(() => ({ shops: [] })),
        ]);
        if (cancelled) return;
        const m = {};
        (mapData.nodes || []).forEach((n) => {
          m[n.id] = n;
        });
        setById(m);
        setFacilities(Array.isArray(facBundle.facilities) ? facBundle.facilities : []);
        setShops(Array.isArray(shopBundle.shops) ? shopBundle.shops : []);
      } catch (e) {
        if (!cancelled) setLoadErr(e.message || 'Could not load node directory');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const triple = useMemo(() => tripleFromStep(path, steps, stepIndex, guidedDone), [path, steps, stepIndex, guidedDone]);

  const cards = useMemo(() => {
    if (!triple) return [];
    const out = [];
    if (triple.prevId && triple.prevId !== triple.thisId) {
      out.push({
        key: 'prev',
        variant: 'prev',
        badge: triple.labelPrev,
        nodeId: triple.prevId,
      });
    }
    out.push({
      key: 'this',
      variant: 'this',
      badge: triple.labelThis,
      nodeId: triple.thisId,
    });
    if (triple.nextId) {
      out.push({
        key: 'next',
        variant: 'next',
        badge: triple.labelNext,
        nodeId: triple.nextId,
      });
    }
    return out;
  }, [triple]);

  if (loadErr) {
    return (
      <div className="guided-node-strip guided-node-strip--error" role="note">
        {loadErr}
      </div>
    );
  }

  if (!triple) return null;

  const hintsForNext = Array.isArray(nextLookFor) ? nextLookFor.filter(Boolean) : [];

  return (
    <div className="guided-node-strip" aria-label="Three-node navigation with nearby features">
      <div className="guided-node-strip-kicker">Where you are on the route</div>
      <p className="guided-node-strip-lead">
        {guidedDone
          ? 'Three stops on your last guided segment — what is around each walking-graph point (not a floor plan).'
          : 'Each card is one walking-graph node. Lists come from our facilities and shop anchors on that node. Tap Yes above when the next checkpoint matches what you see.'}
      </p>
      <div className={`guided-node-cards guided-node-cards--count-${cards.length}`}>
        {cards.map((c) => {
          const { fac, sho } = featuresAroundNode(c.nodeId, facilities, shops);
          const title = placeLabel(c.nodeId, byId);
          const meta = byId[c.nodeId];
          const metaLine = [meta?.kind, meta?.zone].filter(Boolean).join(' · ');
          const showHints = c.key === 'next' && hintsForNext.length > 0 && !guidedDone;

          return (
            <article key={c.key} className={`guided-node-card guided-node-card--${c.variant}`}>
              <header className="guided-node-card-head">
                <span className={`guided-node-badge guided-node-badge--${c.variant}`}>{c.badge}</span>
                <h3 className="guided-node-title">{title}</h3>
                {metaLine ? <p className="guided-node-meta">{metaLine}</p> : null}
                <p className="guided-node-id">
                  <code>{c.nodeId}</code>
                </p>
              </header>
              {showHints ? (
                <section className="guided-node-section" aria-label="Checkpoint hints">
                  <h4 className="guided-node-section-title">Checkpoint cues</h4>
                  <ul className="guided-node-list">
                    {hintsForNext.map((h) => (
                      <li key={h}>{h}</li>
                    ))}
                  </ul>
                </section>
              ) : null}
              <section className="guided-node-section" aria-label="Facilities">
                <h4 className="guided-node-section-title">Facilities nearby</h4>
                {fac.length === 0 ? (
                  <p className="guided-node-empty">None listed on this node in our data.</p>
                ) : (
                  <ul className="guided-node-list">
                    {fac.map((item) => (
                      <li key={item.key}>
                        <span className="guided-node-item-title">{item.title}</span>
                        {item.sub ? <span className="guided-node-item-sub">{item.sub}</span> : null}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <section className="guided-node-section" aria-label="Shops and dining">
                <h4 className="guided-node-section-title">Shops &amp; dining nearby</h4>
                {sho.length === 0 ? (
                  <p className="guided-node-empty">None listed on this node in our data.</p>
                ) : (
                  <ul className="guided-node-list">
                    {sho.map((item) => (
                      <li key={item.key}>
                        <span className="guided-node-item-title">{item.title}</span>
                        {item.sub ? <span className="guided-node-item-sub">{item.sub}</span> : null}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </article>
          );
        })}
      </div>
    </div>
  );
}
