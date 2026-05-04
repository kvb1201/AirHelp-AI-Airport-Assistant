/** Same pixel size as `public/mumbai-t2-l2-plan.jpg` — graph 0–100 maps linearly onto this rectangle. */
export const PLAN_W = 1609;
export const PLAN_H = 2033;

export function nx(x) {
  return (Number(x) / 100) * PLAN_W;
}
export function ny(y) {
  return (Number(y) / 100) * PLAN_H;
}

const NODE_VIS_SCALE = 0.56;
export function ns(u) {
  return (Number(u) / 100) * ((PLAN_W + PLAN_H) / 2);
}
export function nxs(u) {
  return ns(u) * NODE_VIS_SCALE;
}

export const FALLBACK_PLAN_IMAGE_CALIB = { tx: -122, ty: 18, kx: 1.018, ky: 0.998 };

export function planCalibFromMeta(m) {
  const t = m?.plan_image_transform;
  if (!t || typeof t !== 'object') return null;
  const tx = Number(t.tx_px);
  const ty = Number(t.ty_px);
  const kx = Number(t.scale_x);
  const ky = Number(t.scale_y);
  if (!Number.isFinite(tx) || !Number.isFinite(ty)) return null;
  return {
    tx,
    ty,
    kx: Number.isFinite(kx) && kx > 0.5 && kx < 2 ? kx : 1,
    ky: Number.isFinite(ky) && ky > 0.5 && ky < 2 ? ky : 1,
  };
}

/** `?mapCalib=tx,ty` | `tx,ty,k` (uniform scale) | `tx,ty,kx,ky` — overrides graph meta. */
export function readPlanCalibFromUrl() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.location.search || window.location.hash.replace(/^#/, '');
    const qs = new URLSearchParams(raw.includes('?') ? raw.split('?')[1] || '' : raw);
    const s = qs.get('mapCalib');
    if (!s) return null;
    const parts = s.split(',').map((x) => Number(String(x).trim()));
    if (parts.length < 2 || !parts.slice(0, 2).every(Number.isFinite)) return null;
    const [tx, ty] = parts;
    if (parts.length >= 4 && [parts[2], parts[3]].every(Number.isFinite)) {
      const kx = parts[2] > 0.5 && parts[2] < 2 ? parts[2] : 1;
      const ky = parts[3] > 0.5 && parts[3] < 2 ? parts[3] : 1;
      return { tx, ty, kx, ky };
    }
    if (parts.length >= 3 && Number.isFinite(parts[2])) {
      const k = parts[2] > 0.5 && parts[2] < 2 ? parts[2] : 1;
      return { tx, ty, kx: k, ky: k };
    }
    return { tx, ty, kx: 1, ky: 1 };
  } catch {
    /* ignore */
  }
  return null;
}

/**
 * Raster calibration + graph→image flip (must match `TerminalMapView`).
 * @param {Record<string, unknown> | null} meta from `/map`
 */
export function buildTerminalPlanProjection(meta) {
  const url = readPlanCalibFromUrl();
  const planCalib = url || planCalibFromMeta(meta) || { ...FALLBACK_PLAN_IMAGE_CALIB };
  const v = meta?.plan_graph_to_image?.flip_180;
  const graphFlip180 = v === true || v === 'true' || v === 1;
  const mx = (x) => nx(graphFlip180 ? 100 - Number(x) : Number(x));
  const my = (y) => ny(graphFlip180 ? 100 - Number(y) : Number(y));
  return { mx, my, ns, nxs, planCalib, graphFlip180, PLAN_W, PLAN_H };
}
