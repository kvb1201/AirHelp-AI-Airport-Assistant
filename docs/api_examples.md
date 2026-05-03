# Navigation API Examples

## Example 1: Basic Navigation Request

### Request
```http
GET /api/navigation/navigate?start=entrance&end=gate_ne
```

### Response (Abbreviated)
```json
{
  "type": "navigation",
  "intent": "navigation",
  "message": "Main entrance → Gate lounge — NE pier (mock 73–78) — 723m, about 27 min walk",
  "data": {
    "navigation": {
      "ok": true,
      "start_id": "t2_entrance",
      "goal_id": "t2_ne_sp_14",
      "route_count": 3,
      "total_time_minutes": 27,
      "node_count": 28,
      
      "route_summary": {
        "total_distance_meters": 723.0,
        "total_distance_formatted": "723m",
        "total_time_minutes": 27,
        "number_of_turns": 6,
        "number_of_steps": 27,
        "floors_traversed": ["L02"]
      },
      
      "turn_by_turn_directions": [
        {
          "step": 0,
          "type": "start",
          "instruction": "Start at Main entrance",
          "location": "Main entrance",
          "node_id": "t2_entrance",
          "floor": "L02",
          "coordinates": {"x": 50.0, "y": 86.0},
          "nearby_landmarks": [
            {
              "type": "facility",
              "name": "Information desk — T2 arrival plaza",
              "category": "information_desk_t2",
              "distance_meters": 0.8
            }
          ],
          "cumulative_distance_meters": 0,
          "cumulative_time_minutes": 0
        },
        {
          "step": 1,
          "type": "navigate",
          "instruction": "Proceed, then walk 32m straight ahead (north) to Walkway near the entrance",
          "turn_description": "proceed",
          "turn_angle_degrees": null,
          "bearing_degrees": 0.0,
          "direction": "straight ahead (north)",
          "distance_meters": 32.0,
          "distance_formatted": "32m",
          "time_minutes": 1,
          "from_location": "Main entrance",
          "to_location": "Walkway near the entrance",
          "from_node_id": "t2_entrance",
          "to_node_id": "t2_circ_south_1",
          "floor": "L02",
          "coordinates": {"x": 50.0, "y": 82.0},
          "nearby_landmarks": [
            {
              "type": "facility",
              "name": "Information desk — T2 check-in Gate 5 (Island H)",
              "category": "information_desk_t2",
              "distance_meters": 9.6
            },
            {
              "type": "facility",
              "name": "Self-Baggage Drop",
              "category": "main_facilities",
              "distance_meters": 10.8
            }
          ],
          "cumulative_distance_meters": 32.0,
          "cumulative_time_minutes": 1
        },
        {
          "step": 4,
          "type": "navigate",
          "instruction": "Turn left, then walk 40m ahead and to your left (northwest) to Security",
          "turn_description": "turn left",
          "turn_angle_degrees": -63.4,
          "bearing_degrees": 296.6,
          "direction": "ahead and to your left (northwest)",
          "distance_meters": 40.0,
          "distance_formatted": "40m",
          "time_minutes": 1,
          "from_location": "Walkway near the entrance",
          "to_location": "Security",
          "from_node_id": "t2_circ_south_2",
          "to_node_id": "t2_security_intl",
          "floor": "L02",
          "coordinates": {"x": 46.0, "y": 68.0},
          "nearby_landmarks": [
            {
              "type": "facility",
              "name": "Digi Yatra",
              "category": "main_facilities",
              "distance_meters": 35.2
            }
          ],
          "cumulative_distance_meters": 152.0,
          "cumulative_time_minutes": 4
        }
      ],
      
      "simple_journey": {
        "title": "About 27 min",
        "subtitle": "Main entrance → Gate lounge — NE pier (mock 73–78)",
        "bullets": [
          "Start at Main entrance. The whole walk is about 27 minutes.",
          "Continue toward Security — about 4 minutes on this part.",
          "Continue toward After security (airside) — about 3 minutes on this part.",
          "Then move further through the main hall (toward the piers / gates side) — about 1 more minutes.",
          "Continue toward North-East walkway — start of the boarding walk — about 2 minutes on this part.",
          "Then head to Gate lounge — NE pier (mock 73–78) — about 14 more minutes."
        ],
        "milestone_count": 6
      },
      
      "shops_along_route": {
        "count_on_path": 15,
        "picks": [
          {
            "shop_id": "csmia_e8ab0d3424e72c",
            "name_display": "Costa Coffee",
            "category": "coffee_shop",
            "experience_bucket": "coffee_snack",
            "bucket_label": "Coffee & snacks",
            "graph_node_id": "t2_baggage_claim",
            "floor": "L02",
            "floor_display": "Level 2"
          }
        ],
        "tips": [
          "If you want coffee, tea, or a quick bite, look for Costa Coffee, Cafe 2.0, Cafeccino.",
          "If you'd like a proper meal or a bar, there's Budweiser Bar."
        ]
      }
    }
  }
}
```

## Example 2: Location Search

### Request
```http
GET /api/navigation/search?q=starbucks
```

### Response
```json
{
  "type": "location_search",
  "query": "starbucks",
  "results": [
    {
      "type": "shop",
      "id": "csmia_abc123",
      "name": "Starbucks",
      "category": "coffee_shop",
      "floor": "L03",
      "graph_node_id": "t2_l03_postsec"
    },
    {
      "type": "shop",
      "id": "csmia_def456",
      "name": "Starbucks",
      "category": "coffee_shop",
      "floor": "L04",
      "graph_node_id": "t2_l04_postsec"
    }
  ],
  "count": 2
}
```

## Example 3: Location Context

### Request
```http
GET /api/navigation/location/t2_hub_02_02
```

### Response
```json
{
  "type": "location_context",
  "data": {
    "node": {
      "name": "Central concourse grid (2,2)",
      "kind": "corridor",
      "zone": "central_mall",
      "terminal": "T2",
      "floor": "L02",
      "x": 50.0,
      "y": 50.0,
      "id": "t2_hub_02_02"
    },
    "coordinates": {
      "x": 50.0,
      "y": 50.0
    },
    "nearby_facilities": [
      {
        "name": "Charging Stations",
        "category": "other_facilities_pranaam",
        "distance_meters": 11.2,
        "distance_formatted": "11m",
        "graph_node_id": "t2_hub_02_02"
      },
      {
        "name": "Wi-Fi",
        "category": "main_facilities",
        "distance_meters": 12.5,
        "distance_formatted": "13m",
        "graph_node_id": "t2_hub_02_02"
      },
      {
        "name": "ATMs",
        "category": "other_facilities_pranaam",
        "distance_meters": 29.3,
        "distance_formatted": "29m",
        "graph_node_id": "t2_forex"
      }
    ],
    "nearby_shops": [
      {
        "name": "MANIS CAFE",
        "category": "qsr",
        "distance_meters": 61.2,
        "distance_formatted": "61m",
        "graph_node_id": "t2_post_security"
      },
      {
        "name": "Forest Essential",
        "category": "health_and_beauty",
        "distance_meters": 62.4,
        "distance_formatted": "62m",
        "graph_node_id": "t2_post_security"
      }
    ]
  }
}
```

## Example 4: Contextual Navigation

### Request
```http
GET /api/navigation/contextual?start=t2_entrance&end=t2_security_intl&query=restroom
```

### Response
```json
{
  "type": "contextual_navigation",
  "intent": "navigation",
  "data": {
    "ok": true,
    "start_id": "t2_entrance",
    "goal_id": "t2_security_intl",
    
    "start_context": {
      "node": {
        "name": "Level 2 — Main public entry (south)",
        "kind": "entrance",
        "floor": "L02",
        "id": "t2_entrance"
      },
      "coordinates": {"x": 50.0, "y": 86.0},
      "nearby_facilities": [
        {
          "name": "Information desk — T2 arrival plaza",
          "category": "information_desk_t2",
          "distance_meters": 0.8,
          "distance_formatted": "1m"
        },
        {
          "name": "Transportation",
          "category": "main_facilities",
          "distance_meters": 3.2,
          "distance_formatted": "3m"
        }
      ],
      "nearby_shops": []
    },
    
    "goal_context": {
      "node": {
        "name": "Security — International departures",
        "kind": "security",
        "floor": "L02",
        "id": "t2_security_intl"
      },
      "coordinates": {"x": 46.0, "y": 68.0},
      "nearby_facilities": [
        {
          "name": "Digi Yatra",
          "category": "main_facilities",
          "distance_meters": 35.2,
          "distance_formatted": "35m"
        },
        {
          "name": "Information desk — T2 arrival domestic",
          "category": "information_desk_t2",
          "distance_meters": 42.1,
          "distance_formatted": "42m"
        }
      ],
      "nearby_shops": []
    },
    
    "knowledge_base_context": [],
    
    "turn_by_turn_directions": [
      {
        "step": 0,
        "type": "start",
        "instruction": "Start at Main entrance",
        "cumulative_distance_meters": 0,
        "cumulative_time_minutes": 0
      },
      {
        "step": 1,
        "type": "navigate",
        "instruction": "Proceed, then walk 32m straight ahead (north) to Walkway near the entrance",
        "distance_meters": 32.0,
        "distance_formatted": "32m",
        "time_minutes": 1,
        "cumulative_distance_meters": 32.0,
        "cumulative_time_minutes": 1
      },
      {
        "step": 5,
        "type": "arrive",
        "instruction": "You have arrived at Security — International departures",
        "cumulative_distance_meters": 152.0,
        "cumulative_time_minutes": 4
      }
    ],
    
    "route_summary": {
      "total_distance_meters": 152.0,
      "total_distance_formatted": "152m",
      "total_time_minutes": 4,
      "number_of_turns": 1,
      "number_of_steps": 4,
      "floors_traversed": ["L02"]
    }
  }
}
```

## Key Response Fields

### Turn-by-Turn Direction Object
- **step**: Step number (0-indexed)
- **type**: "start", "navigate", or "arrive"
- **instruction**: Human-readable direction
- **turn_description**: "turn left", "turn right", "continue straight", etc.
- **turn_angle_degrees**: Angle to turn (-180 to 180, negative=left)
- **bearing_degrees**: Compass bearing (0-360, 0=North)
- **direction**: Simple direction description
- **distance_meters**: Segment distance in meters
- **distance_formatted**: Human-readable distance ("45m", "1.2km")
- **time_minutes**: Estimated walking time for segment
- **nearby_landmarks**: Array of nearby shops/facilities
- **cumulative_distance_meters**: Total distance so far
- **cumulative_time_minutes**: Total time so far

### Route Summary Object
- **total_distance_meters**: Total route distance
- **total_distance_formatted**: Human-readable total distance
- **total_time_minutes**: Total estimated walking time
- **number_of_turns**: Count of turns (excluding straight segments)
- **number_of_steps**: Total navigation steps
- **floors_traversed**: Array of floor levels on route

### Landmark Object
- **type**: "facility" or "shop"
- **name**: Display name
- **category**: Category/type
- **distance_meters**: Distance from reference point

## Usage Patterns

### Pattern 1: Simple A-to-B Navigation
```javascript
// Get route from entrance to gate
const response = await fetch('/api/navigation/navigate?start=entrance&end=gate_ne');
const data = await response.json();

// Display summary
console.log(data.message); // "Main entrance → Gate lounge — 723m, about 27 min"

// Show turn-by-turn
data.data.navigation.turn_by_turn_directions.forEach(step => {
  console.log(`${step.step}. ${step.instruction}`);
});
```

### Pattern 2: Search Then Navigate
```javascript
// 1. Search for coffee
const searchResponse = await fetch('/api/navigation/search?q=coffee');
const searchData = await searchResponse.json();

// 2. Pick a result
const starbucks = searchData.results[0];
const targetNode = starbucks.graph_node_id;

// 3. Navigate to it
const navResponse = await fetch(
  `/api/navigation/navigate?start=entrance&end=${targetNode}`
);
```

### Pattern 3: Contextual Navigation with Query
```javascript
// Get navigation with context about restrooms
const response = await fetch(
  '/api/navigation/contextual?start=t2_entrance&end=t2_security_intl&query=restroom'
);
const data = await response.json();

// Show nearby facilities at destination
data.data.goal_context.nearby_facilities.forEach(facility => {
  console.log(`${facility.name} - ${facility.distance_formatted} away`);
});
```

### Pattern 4: Location Details
```javascript
// Get details about current location
const response = await fetch('/api/navigation/location/t2_hub_02_02');
const data = await response.json();

// Show what's nearby
console.log('Nearby facilities:');
data.data.nearby_facilities.forEach(f => {
  console.log(`  ${f.name} (${f.distance_formatted})`);
});

console.log('Nearby shops:');
data.data.nearby_shops.forEach(s => {
  console.log(`  ${s.name} (${s.distance_formatted})`);
});
```
