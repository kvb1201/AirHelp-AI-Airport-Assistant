import React, { useEffect, useMemo, useState } from 'react';
import { fetchFacilities } from '../services/api';

function categoryLabel(cat) {
  if (!cat) return 'Other';
  return String(cat).replace(/_/g, ' ');
}

/**
 * Browse airport facilities and open a walking route on the floor map to the linked graph node.
 */
export default function FacilitiesDirectoryView({ location, onGoToFacility }) {
  const [facilities, setFacilities] = useState([]);
  const [loadErr, setLoadErr] = useState(null);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchFacilities();
        if (cancelled) return;
        setFacilities(Array.isArray(data.facilities) ? data.facilities : []);
      } catch (e) {
        if (!cancelled) setLoadErr(e.message || 'Could not load facilities');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    const list = [...facilities].sort((a, b) =>
      String(a.name_display || '').localeCompare(String(b.name_display || ''), undefined, { sensitivity: 'base' }),
    );
    if (!q) return list;
    return list.filter((f) => {
      const hay = [
        f.name_display,
        f.category,
        f.listing_location,
        f.graph_node_id,
        f.terminal,
        f.traffic_type,
        f.landmark,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return hay.includes(q);
    });
  }, [facilities, filter]);

  const byCategory = useMemo(() => {
    const m = new Map();
    for (const f of filtered) {
      const key = f.category || '_other';
      if (!m.has(key)) m.set(key, []);
      m.get(key).push(f);
    }
    return Array.from(m.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [filtered]);

  return (
    <div className="fac-dir">
      <header className="fac-dir-header">
        <h1 className="fac-dir-title">Facilities</h1>
        <p className="fac-dir-lead">
          Pick a service to plot a walk on the floor map. We route from your saved location (
          <code className="fac-dir-code">{location || 't2_entrance'}</code>) to the facility&apos;s graph node (e.g.
          Lost and Found → <code className="fac-dir-code">t2_lost_found</code>).
        </p>
        <label className="fac-dir-search">
          <span className="fac-dir-search-icon ms" aria-hidden>
            search
          </span>
          <input
            type="search"
            className="fac-dir-search-input"
            placeholder="Filter by name, category, or node…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            aria-label="Filter facilities"
          />
        </label>
      </header>

      {loadErr && (
        <p className="fac-dir-error" role="alert">
          {loadErr}
        </p>
      )}

      <div className="fac-dir-body">
        {byCategory.map(([cat, rows]) => (
          <section key={cat} className="fac-dir-section" aria-labelledby={`fac-dir-cat-${cat}`}>
            <h2 id={`fac-dir-cat-${cat}`} className="fac-dir-section-title">
              {categoryLabel(cat)}
            </h2>
            <ul className="fac-dir-list">
              {rows.map((f) => {
                const gid = f.graph_node_id ? String(f.graph_node_id).trim() : '';
                const routable = Boolean(gid);
                return (
                  <li key={f.facility_id} className="fac-dir-row">
                    <div className="fac-dir-row-main">
                      <span className="fac-dir-name">{f.name_display}</span>
                      {f.listing_location || f.landmark ? (
                        <span
                          className="fac-dir-meta"
                          title={[f.listing_location, f.landmark && f.landmark !== f.listing_location ? `Landmark: ${f.landmark}` : '']
                            .filter(Boolean)
                            .join(' · ')}
                        >
                          {[f.terminal, f.traffic_type, f.listing_location].filter(Boolean).join(' · ')}
                          {f.landmark && !String(f.listing_location || '').includes(f.landmark) ? ` · ${f.landmark}` : ''}
                        </span>
                      ) : null}
                      {gid ? (
                        <span className="fac-dir-node" title="Walking graph node used for routing">
                          Route: {gid}
                        </span>
                      ) : (
                        <span className="fac-dir-node fac-dir-node--muted">No walking route linked</span>
                      )}
                    </div>
                    <div className="fac-dir-row-actions">
                      {f.page_url ? (
                        <a className="fac-dir-link" href={f.page_url} target="_blank" rel="noreferrer">
                          CSMIA page
                        </a>
                      ) : null}
                      <button
                        type="button"
                        className="fac-dir-btn"
                        disabled={!routable}
                        title={
                          routable
                            ? 'Show path on floor map'
                            : 'This listing has no graph node yet — use the map to pick a destination manually.'
                        }
                        onClick={() => {
                          if (!routable || !onGoToFacility) return;
                          onGoToFacility({ graphNodeId: gid });
                        }}
                      >
                        Show route on map
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
