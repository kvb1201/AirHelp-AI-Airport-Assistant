// Replace localhost with local IP for mobile testing (e.g. http://192.168.x.x:8000/api)
const BASE_URL = 'http://localhost:8000/api';

/**
 * Graph route for map / sidebar (GET /navigate).
 * @param {string} start - e.g. entrance, security, gate_a1
 * @param {string} end   - e.g. gate_b12, food_court
 */
export async function fetchNavigation(start, end) {
  const q = new URLSearchParams({ start, end });
  const response = await fetch(`${BASE_URL}/navigate?${q}`);
  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }
  return response.json();
}

/** Nodes (x,y) + edges for Terminal 2 Level 2 map */
export async function fetchMapData() {
  const response = await fetch(`${BASE_URL}/map`);
  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }
  return response.json();
}

/** Mock flights, shops, services, offers */
export async function fetchCatalog() {
  const response = await fetch(`${BASE_URL}/catalog`);
  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }
  return response.json();
}

/**
 * Send a chat message to the backend.
 * @param {string} message  - The user's message text
 * @param {string} [location] - Semantic zone (omit to keep server-side last location)
 * @returns {Promise<object>} - { type, intent, message, data, context }
 */
export async function sendChatMessage(message, location) {
  const body = {
    user_id: 'user_123',
    message,
    language: 'en',
  };
  if (location != null && location !== '') body.location = location;

  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  return response.json();
}
