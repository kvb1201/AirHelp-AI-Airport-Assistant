# Distance Calibration Notes

## Terminal 2 Actual Specifications

### Official Dimensions
- **Total area:** ~450,000 m² (4.8 million sq ft)
- **Layout:** X-shaped (cross-shaped) with central headhouse + 3 piers
- **Floors:** 4 stories (~45m height)
- **Roof area:** 70,000 m²
- **Column spacing:** 64m (North-South) × 34m (East-West)
- **Capacity:** 40 million passengers annually

### Level 2 (Departures) Estimated Footprint
- **Per-floor area:** ~112,500 m² (450,000 ÷ 4)
- **Layout:** Central headhouse + NW, NE, SW, SE piers

## Current Coordinate System

### Normalized Coordinates (0-100 scale)
The graph uses a normalized 0-100 coordinate system where:
- **x-axis:** 0 (West) to 100 (East)
- **y-axis:** 0 (North) to 100 (South)
- **Origin:** Top-left corner

### Distance Conversion (Updated)

**Current settings:**
```python
TERMINAL_WIDTH_METERS = 900.0   # East-West span
TERMINAL_HEIGHT_METERS = 900.0  # North-South span
```

**Rationale:**
- X-shaped layout with 3 piers extending from central headhouse
- Central headhouse: ~300m × 300m (estimated)
- Each pier: ~300m extension
- Total span (pier tip to pier tip): ~900m

**Formula:**
```
distance_meters = √[(Δx/100 × 900)² + (Δy/100 × 900)²]
```

## Calibration Status

### ⚠️ Needs Verification

The current dimensions (900m × 900m) are **estimates** based on:
1. Total area of 450,000 m²
2. X-shaped layout geometry
3. Typical airport terminal pier lengths

### Recommended Calibration Steps

1. **Obtain Official Floor Plans**
   - Request CAD drawings from CSMIA
   - Verify actual pier lengths
   - Measure central headhouse dimensions

2. **Ground Truth Measurements**
   - Walk known routes with GPS tracker
   - Time walks between known points
   - Compare with calculated distances

3. **Reference Points**
   - Entrance to Security: Measure actual distance
   - Central hub to pier tips: Verify lengths
   - Cross-terminal distances: Validate

4. **Adjust Scaling Factors**
   - Update `TERMINAL_WIDTH_METERS`
   - Update `TERMINAL_HEIGHT_METERS`
   - May need separate scaling for X vs Y axis

## Known Reference Distances

### To Be Measured
- [ ] Main entrance to international security
- [ ] Main entrance to domestic security
- [ ] Security to central hub
- [ ] Central hub to NE pier gate area
- [ ] Central hub to NW pier gate area
- [ ] Central hub to SW pier gate area
- [ ] Central hub to SE pier gate area
- [ ] Pier length (hub to furthest gate)

### Column Spacing Reference
- **N-S spacing:** 64m (verified from specs)
- **E-W spacing:** 34m (verified from specs)

These can be used to calibrate the coordinate system by:
1. Identifying column positions in the graph
2. Measuring normalized coordinate distances
3. Comparing with actual 64m/34m spacing

## Impact on Navigation

### Current Accuracy
- **Distance estimates:** ±20-30% (needs calibration)
- **Relative distances:** Accurate (graph topology is correct)
- **Turn directions:** Accurate (bearings are relative)
- **Time estimates:** May be off by ±2-5 minutes

### After Calibration
- **Distance estimates:** ±5-10m (expected)
- **Time estimates:** ±1-2 minutes (expected)

## Calibration Priority

### High Priority
1. **Pier lengths** - Most critical for long-distance routes
2. **Central hub dimensions** - Affects most routes
3. **Entrance to security** - Common starting point

### Medium Priority
4. **Pier-to-pier distances** - For cross-terminal routes
5. **Service area locations** - For landmark accuracy

### Low Priority
6. **Fine-grained corridor segments** - Relative distances work

## Temporary Workaround

Until calibration is complete:

1. **Use time estimates** as primary metric (more reliable)
2. **Show distance ranges** instead of exact values
3. **Add disclaimer** about distance accuracy
4. **Focus on turn-by-turn** (directions are accurate)

## Example Calibration Process

### Step 1: Identify Known Distance
```
Entrance (t2_entrance) to Security (t2_security_intl)
Coordinates: (50.0, 86.0) → (46.0, 68.0)
```

### Step 2: Calculate Current Distance
```python
dx = (46.0 - 50.0) / 100.0 * 900.0 = -36m
dy = (68.0 - 86.0) / 100.0 * 900.0 = -162m
distance = √(36² + 162²) = 166m
```

### Step 3: Measure Actual Distance
```
Walk the route with GPS/measuring wheel
Actual distance: [TO BE MEASURED]
```

### Step 4: Calculate Scaling Factor
```python
scaling_factor = actual_distance / calculated_distance
# Apply to TERMINAL_WIDTH_METERS and TERMINAL_HEIGHT_METERS
```

## Alternative Approach: Zone-Based Scaling

Given the X-shaped layout, different zones may need different scaling:

```python
# Zone-specific scaling
CENTRAL_HUB_SCALE = 300.0  # Central headhouse
PIER_LENGTH_SCALE = 300.0  # Each pier extension
PIER_WIDTH_SCALE = 100.0   # Pier width

# Apply based on node zone
if node.zone == "central_mall":
    scale = CENTRAL_HUB_SCALE
elif node.zone.startswith("pier_"):
    scale = PIER_LENGTH_SCALE
```

## Action Items

- [ ] Request official floor plans from CSMIA
- [ ] Conduct ground truth measurements
- [ ] Identify column positions in graph
- [ ] Calculate scaling factors
- [ ] Update distance_calculator.py
- [ ] Re-run test suite
- [ ] Validate with real user walks

## Notes

The current system provides **directionally correct** navigation with **approximate distances**. The turn-by-turn directions, bearings, and relative positioning are accurate. Only the absolute distance values need calibration.

**Priority:** Calibrate before production deployment, but system is usable for testing and development with current estimates.
