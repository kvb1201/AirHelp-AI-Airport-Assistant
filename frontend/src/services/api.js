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