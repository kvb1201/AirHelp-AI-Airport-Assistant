## Offline Flight Storage System 📱

### How It Works

```
USER SUBMITS FLIGHT DETAILS
    ↓
API Endpoint: POST /chat
    {
      "user_id": "user_john",
      "message": "I have flight AI 143 boarding at 10:35",
      "flight_number": "AI 143",
      "boarding_time": "10:35",
      "departure_time": "11:20"
    }
    ↓
chat.py → Passes to orchestrator
    ↓
orchestrator.py → Detects "time_check" intent
    ↓
flight_storage_service.py → store_flight_details()
    ↓
StateManager.merge() → Writes to users.json
    ↓
💾 Data persisted on disk
```

### File Structure

```
backend/app/data/users.json
├── user_john
│   ├── user_id: "user_john"
│   ├── flight_number: "AI 143"
│   ├── boarding_time: "10:35"
│   ├── departure_time: "11:20"
│   ├── terminal: "T2"
│   ├── gate: "B12"
│   ├── location: "entrance"
│   ├── created_at: "2026-05-04T04:00:00+05:30"
│   └── updated_at: "2026-05-04T04:30:00+05:30"
├── user_priya
│   ├── flight_number: "BA 286"
│   ├── boarding_time: "15:20"
│   └── ...
└── user_raj
    ├── flight_number: "SQ 406"
    └── ...
```

### API Examples

#### 1. Store Flight Details
```bash
POST /chat
Content-Type: application/json

{
  "user_id": "user_john",
  "message": "My flight AI 143 boards at 10:35",
  "flight_number": "AI 143",
  "boarding_time": "10:35",
  "departure_time": "11:20"
}

Response:
{
  "type": "flight",
  "intent": "time_check",
  "message": "AI 143 · T2\n- 09:20: Head to security\n- 10:35: Go to gate\n- 11:10: Final call\n\nNext: Head to security at 09:20.",
  "data": {
    "flight": {...},
    "nudges": [...]
  },
  "context": {
    "user_id": "user_john",
    "flight_number": "AI 143",
    "boarding_time": "10:35",
    "departure_time": "11:20",
    ...
  }
}
```

#### 2. Query Stored Flight (on next visit)
```bash
POST /chat
{
  "user_id": "user_john",
  "message": "When should I head to security?"
}

Response:
- Returns stored flight details from users.json
- Generates fresh time nudges
- Data persists across sessions ✅
```

### Key Components

| File | Purpose |
|------|---------|
| `backend/app/core/context/state_manager.py` | **File I/O handler** - Reads/writes `users.json` |
| `backend/app/services/flight_storage_service.py` | **API layer** - High-level functions to store/retrieve flights |
| `backend/app/data/users.json` | **Persistent storage** - JSON file with all user data |
| `backend/manage_users.py` | **Utility script** - View all stored users |
| `backend/test_json_storage.py` | **Test suite** - Verify storage persistence |

### Advantages ✅

- ✅ **Completely offline** - No database required
- ✅ **Server restart safe** - Data survives crashes
- ✅ **Human-readable** - Easy to inspect and edit users.json
- ✅ **Multi-user** - Each user gets their own entry
- ✅ **Timestamped** - Know when user created/updated
- ✅ **Expandable** - Add more fields without migration

### Features Enabled

1. **User Context Persistence**
   - Flight details saved automatically
   - Location context remembered
   - No need to re-enter info

2. **Background Alerts Ready**
   - `get_all_active_flights()` fetches all flights
   - Can iterate and check time-based conditions
   - Ready for scheduler integration

3. **Multi-Session Support**
   - User returns tomorrow
   - System retrieves their stored flight
   - Generates fresh nudges based on current time

### Next Steps (Optional)

1. **Add Background Scheduler**
   - Use APScheduler to run every minute
   - Check `get_all_active_flights()`
   - Trigger WebSocket alerts

2. **Add WebSocket Support**
   - Push notifications to client
   - Send alert when it's time for each nudge

3. **Export/Backup**
   - `users.json` is already portable
   - Copy file for backup/migration

### Testing

```bash
# Test storage persistence
python backend/test_json_storage.py

# View all users
python backend/manage_users.py

# Manual test via API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "flight_number": "AI 143",
    "message": "What time?"
  }'
```
