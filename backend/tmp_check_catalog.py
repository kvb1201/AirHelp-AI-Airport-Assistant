import json
from pathlib import Path

# Simple, dependency-free loader to check which flight catalog is used.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

paths = [
    PROJECT_ROOT / "data" / "airport" / "flights.json",
    PROJECT_ROOT / "backend" / "app" / "data" / "mumbai_t2_catalog.json",
]

chosen = None
payload = None
for p in paths:
    try:
        if p.exists():
            with p.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            chosen = p
            break
    except Exception as e:
        print("Failed to read", p, e)

if chosen is None:
    print("No catalog found at expected paths:")
    for p in paths:
        print(" -", p)
    raise SystemExit(1)

print("Using catalog:", chosen)

# Normalize minimal output depending on format
flights = []
if isinstance(payload, dict) and "flights" in payload:
    flights = payload.get("flights", [])
elif isinstance(payload, list):
    for item in payload:
        flight_id = item.get("flight_id") or item.get("flight_number")
        flight_number = None
        if flight_id:
            parts = str(flight_id).split("_")
            if len(parts) >= 2:
                flight_number = f"{parts[0]} {parts[1]}"
            else:
                flight_number = str(flight_id)

        timings = item.get("timings") or {}
        departure = timings.get("scheduled") or item.get("departure_time")
        boarding = timings.get("boarding") or item.get("boarding_time")

        flights.append({
            "flight_number": flight_number,
            "departure_time": departure,
            "boarding_time": boarding,
            "terminal": item.get("terminal"),
        })
else:
    print("Unrecognized catalog format in", chosen)

print("Loaded", len(flights), "flights (showing up to 5):")
for i, f in enumerate(flights[:5]):
    print(i + 1, f.get("flight_number"), f.get("departure_time"), f.get("boarding_time"), f.get("terminal"))

print("\nPaths checked:")
for p in paths:
    print(p.exists(), p)
