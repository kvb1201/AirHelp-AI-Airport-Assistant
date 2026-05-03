# Quick Start Guide - Turn-by-Turn Navigation

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend
```bash
cd backend
python run.py
```

The server will start at `http://localhost:8000`

### Step 2: Test the System
```bash
# In a new terminal
cd backend
python test_turn_by_turn.py
```

You should see:
```
✓ PASS: Basic Navigation
✓ PASS: Location Search
✓ PASS: Location Context
✓ PASS: Contextual Navigation

🎉 All tests passed!
```

### Step 3: Try the API
```bash
# Get navigation from entrance to gate
curl "http://localhost:8000/api/navigation/navigate?start=entrance&end=gate_ne"
```

## 📋 Common Use Cases

### Use Case 1: Basic Navigation
**Goal:** Get from entrance to a gate

```bash
curl "http://localhost:8000/api/navigation/navigate?start=entrance&end=gate_ne"
```

**Response includes:**
- Total distance in meters
- Total time in minutes
- Turn-by-turn directions
- Nearby landmarks

### Use Case 2: Find a Shop
**Goal:** Search for Starbucks

```bash
curl "http://localhost:8000/api/navigation/search?q=starbucks"
```

**Response includes:**
- Shop name and location
- Floor level
- Graph node ID (for navigation)

### Use Case 3: Navigate to Shop
**Goal:** Get directions to Starbucks from entrance

```bash
# First, search for Starbucks
curl "http://localhost:8000/api/navigation/search?q=starbucks"

# Use the graph_node_id from response
curl "http://localhost:8000/api/navigation/navigate?start=entrance&end=t2_l03_postsec"
```

### Use Case 4: What's Near Me?
**Goal:** See what's around a location

```bash
curl "http://localhost:8000/api/navigation/location/t2_hub_02_02"
```

**Response includes:**
- Nearby facilities (within 100m)
- Nearby shops (within 100m)
- Exact distances in meters

### Use Case 5: Contextual Navigation
**Goal:** Get directions with context about restrooms

```bash
curl "http://localhost:8000/api/navigation/contextual?start=t2_entrance&end=t2_security_intl&query=restroom"
```

**Response includes:**
- Full route with turn-by-turn
- Start location context
- Destination context
- Relevant knowledge base info

## 🎯 Key Endpoints

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/api/navigation/navigate` | Basic A-to-B navigation | `?start=entrance&end=gate_ne` |
| `/api/navigation/search` | Search locations | `?q=coffee` |
| `/api/navigation/location/{id}` | Location details | `/location/t2_hub_02_02` |
| `/api/navigation/contextual` | Navigation with context | `?start=...&end=...&query=...` |

## 📊 Understanding the Response

### Route Summary
```json
{
  "route_summary": {
    "total_distance_meters": 723,      // Total walking distance
    "total_distance_formatted": "723m", // Human-readable
    "total_time_minutes": 27,          // Estimated walking time
    "number_of_turns": 6,              // How many turns
    "number_of_steps": 27,             // Total navigation steps
    "floors_traversed": ["L02"]        // Which floors
  }
}
```

### Turn-by-Turn Direction
```json
{
  "step": 1,
  "instruction": "Turn right, then walk 45m to Security",
  "distance_meters": 45.2,           // Exact distance
  "distance_formatted": "45m",       // Human-readable
  "bearing_degrees": 92.3,           // Compass direction
  "turn_angle_degrees": 87.5,        // How much to turn
  "time_minutes": 1,                 // Time for this step
  "nearby_landmarks": [              // What's nearby
    {"name": "Info desk", "distance_meters": 12.5}
  ],
  "cumulative_distance_meters": 45.2, // Total so far
  "cumulative_time_minutes": 1        // Time so far
}
```

## 🔍 Common Node IDs

### Entry Points
- `t2_entrance` - Main entrance
- `t2_baggage_claim` - Baggage area

### Security
- `t2_security_intl` - International security
- `t2_security_dom` - Domestic security
- `t2_post_security` - After security

### Central Areas
- `t2_hub_02_02` - Central concourse
- `t2_vertical_core` - Lifts/escalators

### Gates
- `t2_nw_sp_14` - Northwest pier gates (65-72)
- `t2_ne_sp_14` - Northeast pier gates (73-78)
- `t2_sw_sp_14` - Southwest pier gates (79-84)
- `t2_se_sp_14` - Southeast pier gates (85-90)

### Services
- `t2_information` - Information desk
- `t2_medical` - Medical station
- `t2_wc_central` - Central restrooms
- `t2_forex` - Currency exchange

## 🛠️ Troubleshooting

### Problem: "Unknown node" error
**Solution:** Use the search endpoint to find valid node IDs
```bash
curl "http://localhost:8000/api/navigation/search?q=security"
```

### Problem: "No path exists"
**Solution:** Check if nodes are on the same floor or connected
```bash
# Get location details
curl "http://localhost:8000/api/navigation/location/t2_entrance"
```

### Problem: Backend won't start
**Solution:** Check Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Problem: Tests fail
**Solution:** Ensure data files exist
```bash
ls backend/app/data/
# Should see: mumbai_t2_level02_graph.json, facilities_bom.csv, shops_t2_l02.csv
```

## 📚 Learn More

- **Full Documentation:** `docs/turn_by_turn_navigation.md`
- **API Examples:** `docs/api_examples.md`
- **System Architecture:** `docs/system_architecture.md`
- **Implementation Summary:** `NAVIGATION_V2_SUMMARY.md`

## 💡 Tips

1. **Use semantic names:** `entrance`, `security`, `gate_ne` work better than node IDs
2. **Search first:** Use `/search` to find exact locations
3. **Check context:** Use `/location/{id}` to see what's nearby
4. **Add queries:** Use `query` parameter for contextual results

## 🎉 You're Ready!

The turn-by-turn navigation system is now running. Try these examples:

```bash
# Example 1: Entrance to gate
curl "http://localhost:8000/api/navigation/navigate?start=entrance&end=gate_ne"

# Example 2: Find coffee
curl "http://localhost:8000/api/navigation/search?q=coffee"

# Example 3: What's at central hub?
curl "http://localhost:8000/api/navigation/location/t2_hub_02_02"

# Example 4: Navigate with context
curl "http://localhost:8000/api/navigation/contextual?start=entrance&end=security&query=restroom"
```

## 🚀 Next Steps

1. Integrate with your frontend
2. Add user location tracking
3. Customize walking speed
4. Add accessibility preferences
5. Implement voice navigation

---

**Need help?** Check the documentation in the `docs/` folder or run the test suite to verify everything works.
