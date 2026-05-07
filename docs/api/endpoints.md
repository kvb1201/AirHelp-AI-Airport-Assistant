# API Endpoints

## Base URL

```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

## Authentication

Currently, the API uses simple user_id-based authentication. In production, implement JWT or OAuth2.

```http
Authorization: Bearer <token>
```

## Endpoints Overview

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/chat` | POST | Conversational queries | No |
| `/navigate` | GET | Route calculation | No |
| `/guided-nav/checkpoints` | POST | Guided navigation | No |
| `/guided-nav/relocalize` | POST | Relocalization | No |
| `/map` | GET | Airport map data | No |
| `/facilities` | GET | Facility listings | No |
| `/shops` | GET | Shop listings | No |
| `/catalog` | GET | Complete catalog | No |
| `/transcribe` | POST | Speech-to-text | No |
| `/translate` | POST | Text translation | No |
| `/tts` | POST | Text-to-speech | No |
| `/tts/status` | GET | TTS service status | No |
| `/lost-found/lost` | POST | Report lost item | No |
| `/lost-found/found` | POST | Report found item | No |
| `/lost-found/matches/{id}` | GET | Get matches | No |
| `/lost-found/confirm` | POST | Confirm match | No |
| `/support/tickets` | POST | Create support ticket | No |
| `/support/ticket-categories` | GET | Get ticket categories | No |
| `/travel-documents/upload` | POST | Upload travel document | No |
| `/travel-documents/{user_id}` | GET | Get user documents | No |
| `/ops/state` | GET | Operational state | No |
| `/ops/ws` | WebSocket | Real-time updates | No |
| `/ops/global-notice` | POST | Set global notice | Yes (Operator) |
| `/ops/bulletin` | POST | Create bulletin | Yes (Operator) |
| `/ops/bulletin/{id}` | DELETE | Delete bulletin | Yes (Operator) |
| `/ops/flight-override` | POST | Override flight info | Yes (Operator) |
| `/ops/flight-override/{flight}` | DELETE | Remove override | Yes (Operator) |

---

## Chat API

### POST `/chat`

Process conversational queries and return context-aware responses.

**Request**:
```json
{
  "user_id": "user_123",
  "message": "Where can I find food near gate B12?",
  "location": "terminal_2_entrance",
  "language": "en",
  "input_mode": "text",
  "whisper_lang": null,
  "flight_number": "AI123",
  "boarding_time": "2026-05-07T14:30:00",
  "departure_time": "2026-05-07T15:00:00"
}
```

**Response**:
```json
{
  "type": "recommendations",
  "intent": "discovery",
  "message": "I found 5 food options near Gate B12. Here are my top recommendations:\n\n1. **Starbucks** - International coffee chain\n   - Location: Terminal 2, Level 2, Zone B\n   - Distance: 50m from Gate B12\n   - Quick service, perfect for a pre-flight coffee\n\n2. **McDonald's** - Fast food restaurant\n   - Location: Terminal 2, Level 2, Zone B\n   - Distance: 80m from Gate B12\n   - Quick meals, family-friendly\n\n3. **Subway** - Sandwich shop\n   - Location: Terminal 2, Level 2, Zone B\n   - Distance: 100m from Gate B12\n   - Healthy options, customizable",
  "data": {
    "recommendations": [
      {
        "name": "Starbucks",
        "category": "food",
        "subcategory": "cafe",
        "location": "Terminal 2, Level 2, Zone B",
        "distance": 50,
        "rating": 4.5,
        "price_range": "mid",
        "description": "International coffee chain offering hot and cold beverages"
      }
    ],
    "navigation": null
  },
  "context": {
    "user_id": "user_123",
    "last_intent": "discovery",
    "last_query": "Where can I find food near gate B12?",
    "current_location": "terminal_2_entrance",
    "flight_info": {
      "flight_number": "AI123",
      "boarding_time": "2026-05-07T14:30:00",
      "departure_time": "2026-05-07T15:00:00"
    }
  }
}
```

**Error Response**:
```json
{
  "type": "error",
  "intent": "error",
  "message": "I encountered an issue processing your request. Please try again.",
  "data": {},
  "context": {}
}
```

---

## Navigation API

### GET `/navigate`

Calculate route between two locations.

**Request**:
```http
GET /navigate?start=terminal_2_entrance&end=gate_b12&local_hour=14&busy_terminal=true
```

**Query Parameters**:
- `start` (required): Starting location ID
- `end` (required): Destination location ID
- `local_hour` (optional): Current hour (0-23) for congestion calculation
- `busy_terminal` (optional): Boolean flag for busy periods

**Response**:
```json
{
  "start": "terminal_2_entrance",
  "end": "gate_b12",
  "path": [
    "terminal_2_entrance",
    "security_checkpoint_t2",
    "corridor_b",
    "gate_b12"
  ],
  "edges": [
    {
      "from": "terminal_2_entrance",
      "to": "security_checkpoint_t2",
      "minutes": 3.5,
      "distance": 150
    },
    {
      "from": "security_checkpoint_t2",
      "to": "corridor_b",
      "minutes": 2.0,
      "distance": 80
    },
    {
      "from": "corridor_b",
      "to": "gate_b12",
      "minutes": 2.5,
      "distance": 100
    }
  ],
  "total_minutes": 8.0,
  "total_distance": 330,
  "instructions": [
    "Head straight from the entrance towards security",
    "Pass through security checkpoint",
    "Turn right into Corridor B",
    "Gate B12 will be on your left"
  ]
}
```

---

## Guided Navigation API

### POST `/guided-nav/checkpoints`

Generate guided checkpoints for a route.

**Request**:
```json
{
  "path": ["terminal_2_entrance", "security_checkpoint_t2", "corridor_b", "gate_b12"],
  "edges": [
    {"from": "terminal_2_entrance", "to": "security_checkpoint_t2", "minutes": 3.5},
    {"from": "security_checkpoint_t2", "to": "corridor_b", "minutes": 2.0},
    {"from": "corridor_b", "to": "gate_b12", "minutes": 2.5}
  ]
}
```

**Response**:
```json
{
  "checkpoints": [
    {
      "path_index": 0,
      "node_id": "terminal_2_entrance",
      "question": "Do you see the security checkpoint ahead?",
      "expected_cues": ["security gates", "x-ray machines", "queue lines"],
      "next_instruction": "Head towards the security checkpoint"
    },
    {
      "path_index": 1,
      "node_id": "security_checkpoint_t2",
      "question": "Have you passed through security?",
      "expected_cues": ["duty-free shops", "corridor signs", "gate numbers"],
      "next_instruction": "Turn right into Corridor B"
    }
  ]
}
```

### POST `/guided-nav/relocalize`

Relocalize user when lost.

**Request**:
```json
{
  "path": ["terminal_2_entrance", "security_checkpoint_t2", "corridor_b", "gate_b12"],
  "last_confirmed_path_index": 1,
  "next_waypoint_path_index": 2,
  "observation": "I see a Starbucks and a washroom",
  "local_hour": 14,
  "busy_terminal": true
}
```

**Response**:
```json
{
  "likely_location": "corridor_b_starbucks",
  "confidence": 0.85,
  "new_route": {
    "path": ["corridor_b_starbucks", "corridor_b", "gate_b12"],
    "instructions": ["Continue straight", "Gate B12 is 100m ahead on your left"]
  },
  "message": "Based on your description, you're near the Starbucks in Corridor B. Continue straight and Gate B12 will be on your left."
}
```

---

## Voice API

### POST `/transcribe`

Transcribe audio to text using Whisper.

**Request**:
```http
POST /transcribe
Content-Type: multipart/form-data

file: <audio_file>
language: en (optional)
```

**Response**:
```json
{
  "transcript": "Where is gate B12?",
  "detected_language": "en",
  "language_probability": 0.98
}
```

### POST `/translate`

Translate text between languages.

**Request**:
```json
{
  "text": "Where is gate B12?",
  "src_lang": "eng_Latn",
  "tgt_lang": "hin_Deva"
}
```

**Response**:
```json
{
  "translated_text": "गेट B12 कहाँ है?",
  "src_lang": "eng_Latn",
  "tgt_lang": "hin_Deva"
}
```

### POST `/tts`

Convert text to speech.

**Request**:
```json
{
  "text": "Gate B12 is on your left",
  "language": "en"
}
```

**Response**:
```
Content-Type: audio/wav
<audio_data>
```

### GET `/tts/status`

Check TTS service status.

**Response**:
```json
{
  "status": "active",
  "piper_found": true,
  "voices_configured": ["en"],
  "ready": true,
  "offline_mode": true
}
```

---

## Lost & Found API

### POST `/lost-found/lost`

Report a lost item.

**Request**:
```json
{
  "user_id": "user_123",
  "item_type": "luggage",
  "description": "Black suitcase with red ribbon",
  "last_seen_location": "security_checkpoint_t2",
  "last_seen_time": "2026-05-07T10:30:00",
  "contact_email": "user@example.com",
  "contact_phone": "+91-9876543210",
  "shared_secret": "my_secret_code"
}
```

**Response**:
```json
{
  "report_id": "LOST-20260507-001",
  "status": "registered",
  "message": "Your lost item report has been registered. We'll notify you if a match is found.",
  "meet_point": "information_desk_t2"
}
```

### POST `/lost-found/found`

Report a found item.

**Request**:
```json
{
  "user_id": "user_123",
  "item_type": "luggage",
  "description": "Black suitcase with red ribbon",
  "found_location": "gate_b12",
  "found_time": "2026-05-07T11:00:00",
  "contact_email": "finder@example.com"
}
```

**Response**:
```json
{
  "report_id": "FOUND-20260507-001",
  "status": "registered",
  "potential_matches": 1,
  "message": "Thank you for reporting the found item. We found 1 potential match."
}
```

### GET `/lost-found/matches/{report_id}`

Get potential matches for a report.

**Response**:
```json
{
  "report_id": "LOST-20260507-001",
  "matches": [
    {
      "match_id": "FOUND-20260507-001",
      "similarity_score": 0.95,
      "item_type": "luggage",
      "description": "Black suitcase with red ribbon",
      "found_location": "gate_b12",
      "found_time": "2026-05-07T11:00:00"
    }
  ]
}
```

### POST `/lost-found/confirm`

Confirm a match.

**Request**:
```json
{
  "lost_report_id": "LOST-20260507-001",
  "found_report_id": "FOUND-20260507-001",
  "shared_secret": "my_secret_code"
}
```

**Response**:
```json
{
  "status": "confirmed",
  "meet_point": "information_desk_t2",
  "message": "Match confirmed! Please proceed to the Information Desk at Terminal 2 to collect your item."
}
```

---

## Support API

### GET `/support/ticket-categories`

Get available ticket categories.

**Response**:
```json
{
  "categories": [
    {"id": "facility_issue", "label": "Facility Issue"},
    {"id": "cleanliness", "label": "Cleanliness"},
    {"id": "staff_behavior", "label": "Staff Behavior"},
    {"id": "accessibility", "label": "Accessibility"},
    {"id": "other", "label": "Other"}
  ]
}
```

### POST `/support/tickets`

Create a support ticket.

**Request**:
```json
{
  "category": "facility_issue",
  "description": "Broken escalator near Gate B12",
  "where_hint": "Terminal 2, Level 2, near Gate B12",
  "email": "user@example.com",
  "location_graph_id": "corridor_b"
}
```

**Response**:
```json
{
  "ticket_id": "TICKET-20260507-001",
  "status": "submitted",
  "message": "Your support ticket has been submitted. We'll address this issue shortly.",
  "estimated_response_time": "30 minutes"
}
```

---

## Operational State API

### GET `/ops/state`

Get current operational state (bulletins, delays, notices).

**Response**:
```json
{
  "global_notice": {
    "title": "Welcome to Mumbai Airport",
    "body": "Please arrive 2 hours before domestic flights."
  },
  "bulletins": [
    {
      "id": "BULL-001",
      "title": "Gate Change",
      "body": "Flight AI123 moved from Gate B12 to Gate B15",
      "severity": "warning",
      "created_at": "2026-05-07T10:00:00"
    }
  ],
  "flight_overrides": {
    "AI123": {
      "gate": "B15",
      "delay_minutes": 30,
      "status": "delayed",
      "note": "Weather delay"
    }
  }
}
```

### WebSocket `/ops/ws`

Real-time operational updates.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ops/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Message Format**:
```json
{
  "type": "ops_updated",
  "state": {
    "global_notice": {...},
    "bulletins": [...],
    "flight_overrides": {...}
  }
}
```

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Request validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

**Error Response Format**:
```json
{
  "detail": "Error message",
  "error_code": "INVALID_LOCATION",
  "timestamp": "2026-05-07T12:00:00Z"
}
```

---

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Burst**: 200 requests per minute
- **WebSocket**: 1 connection per user

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1683456000
```

---

## Pagination

For list endpoints, use pagination parameters:

```http
GET /facilities?page=1&page_size=20
```

**Response**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

## CORS

CORS is enabled for all origins in development. In production, configure allowed origins:

```python
allow_origins=["https://your-domain.com"]
```

---

**Related Documentation**:
- [Request/Response Schema](request-response-schema.md)
- [WebSocket Events](websocket-events.md)
- [Error Handling](error-handling.md)
