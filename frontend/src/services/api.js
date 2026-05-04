// frontend/src/services/api.js

function getBaseUrl() {
  const hostname = window.location.hostname;

  // Case 1: Running on laptop (localhost)
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "http://localhost:8000/api";
  }

  // Case 2: Accessed from mobile via LAN
  return `http://${hostname}:8000/api`;
}

const BASE_URL = getBaseUrl();

export async function fetchMapData() {
  const response = await fetch(`${BASE_URL}/map`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

/**
 * Build guided checkpoint questions along a chosen route (`path` + `edges` from /navigate).
 * @param {{ path: string[], edges: { from: string, to: string, minutes: number }[] }} body
 */
export async function fetchGuidedCheckpoints(body) {
  const response = await fetch(`${BASE_URL}/guided-nav/checkpoints`, {
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
  const response = await fetch(`${BASE_URL}/guided-nav/relocalize`, {
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
  const response = await fetch(`${BASE_URL}/navigate?${q}`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

export async function fetchFacilities(params = {}) {
  const q = new URLSearchParams();
  if (params.category) q.set('category', params.category);
  const suffix = q.toString() ? `?${q}` : '';
  const response = await fetch(`${BASE_URL}/facilities${suffix}`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

export async function fetchShops(params = {}) {
  const q = new URLSearchParams();
  if (params.zone) q.set('zone', params.zone);
  if (params.category) q.set('category', params.category);
  const suffix = q.toString() ? `?${q}` : '';
  const response = await fetch(`${BASE_URL}/shops${suffix}`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

export async function fetchCatalog() {
  const response = await fetch(`${BASE_URL}/catalog`);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

/**
 * Send a chat message to the backend.
 */
export async function sendChatMessage(message, location = "entrance") {
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
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

/**
 * Send flight details (stores on backend and returns nudges/response).
 */
export async function sendFlightDetails({ userId = 'user_123', flightNumber, boardingTime, departureTime, location = 'entrance' }) {
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        message: `Store flight ${flightNumber}`,
        flight_number: flightNumber,
        boarding_time: boardingTime,
        departure_time: departureTime,
        location,
        language: 'en',
      }),
    });

    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    return await response.json();
  } catch (err) {
    console.error('API error:', err);
    return {
      type: 'error',
      intent: 'error',
      message: 'Server not reachable. Check connection.',
      data: {},
      context: {},
    };
  }
}
