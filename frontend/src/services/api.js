// frontend/src/services/api.js

/**
 * API base including `/api` suffix.
 * Priority: localStorage `airhelp_api_base` → Vite `VITE_API_BASE_URL` → same host as the page on LAN → localhost.
 * Use localStorage / env when the UI runs on another laptop but data lives on the storage laptop (host:8000).
 */
function getBaseUrl() {
  try {
    const ls = window.localStorage?.getItem("airhelp_api_base");
    if (ls && String(ls).trim()) {
      const u = String(ls).trim().replace(/\/+$/, "");
      return u.endsWith("/api") ? u : `${u}/api`;
    }
  } catch {
    /* ignore */
  }

  const envBase = import.meta.env?.VITE_API_BASE_URL;
  if (envBase && String(envBase).trim()) {
    const u = String(envBase).trim().replace(/\/+$/, "");
    return u.endsWith("/api") ? u : `${u}/api`;
  }

  const hostname = window.location.hostname;

  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "http://localhost:8000/api";
  }

  return `http://${hostname}:8000/api`;
}

function apiBase() {
  return getBaseUrl();
}

export async function fetchMapData() {
  const response = await fetch(`${apiBase()}/map`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

/**
 * Build guided checkpoint questions along a chosen route (`path` + `edges` from /navigate).
 * @param {{ path: string[], edges: { from: string, to: string, minutes: number }[] }} body
 */
export async function fetchGuidedCheckpoints(body) {
  const response = await fetch(`${apiBase()}/guided-nav/checkpoints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

/**
 * Relocalize when the user does not see the expected cues; pass what they see (e.g. washroom).
 * @param {{ path: string[], last_confirmed_path_index: number, next_waypoint_path_index: number, observation: string, localHour?: number, busyTerminal?: boolean }} body
 */
export async function fetchGuidedRelocalize(body) {
  const payload = {
    path: body.path,
    last_confirmed_path_index: body.last_confirmed_path_index,
    next_waypoint_path_index: body.next_waypoint_path_index,
    observation: body.observation,
  };
  if (typeof body.localHour === 'number' && body.localHour >= 0 && body.localHour <= 23) {
    payload.local_hour = Math.floor(body.localHour);
  }
  if (body.busyTerminal) payload.busy_terminal = true;
  const response = await fetch(`${apiBase()}/guided-nav/relocalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

/**
 * @param {string} start
 * @param {string} end
 * @param {{ localHour?: number, busyTerminal?: boolean }} [opts]
 */
export async function fetchNavigation(start, end, opts = {}) {
  const q = new URLSearchParams({ start, end });
  if (typeof opts.localHour === 'number' && opts.localHour >= 0 && opts.localHour <= 23) {
    q.set('local_hour', String(Math.floor(opts.localHour)));
  }
  if (opts.busyTerminal) {
    q.set('busy_terminal', 'true');
  }
  const response = await fetch(`${apiBase()}/navigate?${q}`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

export async function fetchFacilities(params = {}) {
  const q = new URLSearchParams();
  if (params.category) q.set('category', params.category);
  const suffix = q.toString() ? `?${q}` : '';
  const response = await fetch(`${apiBase()}/facilities${suffix}`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

export async function fetchShops(params = {}) {
  const q = new URLSearchParams();
  if (params.zone) q.set('zone', params.zone);
  if (params.category) q.set('category', params.category);
  const suffix = q.toString() ? `?${q}` : '';
  const response = await fetch(`${apiBase()}/shops${suffix}`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

export async function fetchCatalog() {
  const response = await fetch(`${apiBase()}/catalog`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

/** Lost / found baggage: default meet point on the graph. */
export async function fetchLostFoundMeetDefaults() {
  const response = await fetch(`${apiBase()}/lost-found/meet-defaults`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

async function readLostFoundError(response) {
  try {
    const j = await response.json();
    if (j && typeof j.detail === 'string') return j.detail;
    if (j && j.detail != null) return JSON.stringify(j.detail);
  } catch {
    /* ignore */
  }
  return `HTTP ${response.status}`;
}

/** @param {Record<string, unknown>} body */
export async function postLostFoundLost(body) {
  const response = await fetch(`${apiBase()}/lost-found/lost`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await readLostFoundError(response));
  return response.json();
}

/** @param {Record<string, unknown>} body */
export async function postLostFoundFound(body) {
  const response = await fetch(`${apiBase()}/lost-found/found`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await readLostFoundError(response));
  return response.json();
}

export async function fetchLostFoundMatches(reportId) {
  const response = await fetch(`${apiBase()}/lost-found/matches/${encodeURIComponent(reportId)}`);
  if (!response.ok) throw new Error(await readLostFoundError(response));
  return response.json();
}

/** @param {{ lost_report_id: string, found_report_id: string, shared_secret: string }} body */
export async function postLostFoundConfirm(body) {
  const response = await fetch(`${apiBase()}/lost-found/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await readLostFoundError(response));
  return response.json();
}

/**
 * Piper TTS status (English only): piper_found, voices_configured { en }, ready.
 */
export async function fetchTtsStatus() {
  const response = await fetch(`${apiBase()}/tts/status`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

/**
 * Offline TTS (WAV) from laptop Piper — English only.
 */
export async function fetchTtsAudio(text, language = "en") {
  const response = await fetch(`${apiBase()}/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language: "en" }),
  });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const j = await response.json();
      if (j.detail != null) {
        detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
      }
    } catch {
      /* ignore */
    }
    const err = new Error(detail);
    err.status = response.status;
    throw err;
  }
  return response.blob();
}

/**
 * Send a chat message to the backend (English assistant).
 * @param {string} message
 * @param {string} [location]
 */
export async function sendChatMessage(message, location = "entrance") {
  try {
    const response = await fetch(`${apiBase()}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "user_123",
        message,
        location,
        language: "en",
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    return await response.json();
  } catch (err) {
    console.error("API error:", err);
    return {
      type: "error",
      intent: "error",
      message: "Server not reachable. Check connection.",
      data: {},
      context: {},
    };
  }
}
