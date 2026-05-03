// Replace localhost with local IP for mobile testing (e.g. http://192.168.x.x:8000/api)
const BASE_URL = 'http://localhost:8000/api';

/**
 * Send a chat message to the backend.
 * @param {string} message  - The user's message text
 * @param {string} location - Current location in the airport (default: "entrance")
 * @returns {Promise<object>} - { type, intent, message, data, context }
 */
export async function sendChatMessage(message, location = 'entrance') {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: 'user_123',
      message,
      location,
      language: 'en',
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  return response.json();
}
