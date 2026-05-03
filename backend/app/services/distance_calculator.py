"""
Calculate real-world distances and bearings for turn-by-turn navigation.
Converts normalized coordinates (0-100) to approximate meters for Mumbai T2.
"""

from __future__ import annotations

import math
from typing import Any


# Mumbai T2 Terminal 2 actual dimensions
# Terminal 2: ~450,000 m² total, X-shaped layout, 4 stories
# Level 2 (departures): ~112,500 m² footprint
# Based on X-shaped layout with central headhouse + 3 piers
# Column spacing: 64m (N-S) × 34m (E-W)
# Estimated envelope for normalized coordinate mapping:
TERMINAL_WIDTH_METERS = 900.0   # East-West span (pier tip to pier tip)
TERMINAL_HEIGHT_METERS = 900.0  # North-South span (pier tip to pier tip)

# Note: These dimensions represent the maximum extent of the X-shaped layout
# including all three piers. The actual walkable distance varies by path.
# Central headhouse is approximately 300m × 300m, with piers extending ~300m each.


def normalized_to_meters(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Convert normalized coordinates (0-100) to approximate walking distance in meters.
    
    Args:
        x1, y1: Start point in normalized coordinates
        x2, y2: End point in normalized coordinates
    
    Returns:
        Distance in meters
    """
    # Calculate normalized distance
    dx = (x2 - x1) / 100.0  # Fraction of terminal width
    dy = (y2 - y1) / 100.0  # Fraction of terminal height
    
    # Convert to meters
    dx_meters = dx * TERMINAL_WIDTH_METERS
    dy_meters = dy * TERMINAL_HEIGHT_METERS
    
    # Euclidean distance
    distance = math.sqrt(dx_meters**2 + dy_meters**2)
    return round(distance, 1)


def calculate_bearing(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate compass bearing from point 1 to point 2.
    
    Args:
        x1, y1: Start point in normalized coordinates
        x2, y2: End point in normalized coordinates
    
    Returns:
        Bearing in degrees (0-360), where 0=North, 90=East, 180=South, 270=West
    """
    dx = x2 - x1
    dy = y1 - y2  # Inverted because y increases downward in the coordinate system
    
    # Calculate angle in radians
    angle_rad = math.atan2(dx, dy)
    
    # Convert to degrees (0-360)
    bearing = (math.degrees(angle_rad) + 360) % 360
    return round(bearing, 1)


def bearing_to_direction(bearing: float) -> str:
    """
    Convert bearing to cardinal/intercardinal direction.
    
    Args:
        bearing: Bearing in degrees (0-360)
    
    Returns:
        Direction string (e.g., "North", "Northeast", "East")
    """
    directions = [
        "North", "North-Northeast", "Northeast", "East-Northeast",
        "East", "East-Southeast", "Southeast", "South-Southeast",
        "South", "South-Southwest", "Southwest", "West-Southwest",
        "West", "West-Northwest", "Northwest", "North-Northwest"
    ]
    
    # Divide 360 degrees into 16 sectors (22.5 degrees each)
    index = int((bearing + 11.25) / 22.5) % 16
    return directions[index]


def bearing_to_simple_direction(bearing: float) -> str:
    """
    Convert bearing to simple 4-direction (N/S/E/W) or 8-direction.
    
    Args:
        bearing: Bearing in degrees (0-360)
    
    Returns:
        Simple direction string
    """
    if bearing < 22.5 or bearing >= 337.5:
        return "straight ahead (north)"
    elif bearing < 67.5:
        return "ahead and to your right (northeast)"
    elif bearing < 112.5:
        return "to your right (east)"
    elif bearing < 157.5:
        return "behind and to your right (southeast)"
    elif bearing < 202.5:
        return "behind you (south)"
    elif bearing < 247.5:
        return "behind and to your left (southwest)"
    elif bearing < 292.5:
        return "to your left (west)"
    else:
        return "ahead and to your left (northwest)"


def calculate_turn_angle(bearing1: float, bearing2: float) -> tuple[float, str]:
    """
    Calculate the turn angle between two bearings.
    
    Args:
        bearing1: Initial bearing (where you're coming from)
        bearing2: New bearing (where you're going)
    
    Returns:
        Tuple of (turn_angle, turn_description)
        turn_angle: Degrees to turn (-180 to 180, negative=left, positive=right)
        turn_description: Human-readable turn instruction
    """
    # Calculate the difference
    diff = (bearing2 - bearing1 + 360) % 360
    
    # Normalize to -180 to 180
    if diff > 180:
        diff -= 360
    
    turn_angle = round(diff, 1)
    
    # Generate description
    abs_angle = abs(turn_angle)
    
    if abs_angle < 15:
        description = "continue straight"
    elif abs_angle < 45:
        direction = "slight right" if turn_angle > 0 else "slight left"
        description = f"bear {direction}"
    elif abs_angle < 135:
        direction = "right" if turn_angle > 0 else "left"
        description = f"turn {direction}"
    else:
        direction = "right" if turn_angle > 0 else "left"
        description = f"sharp turn {direction}"
    
    return turn_angle, description


def estimate_walking_time(distance_meters: float, speed_mps: float = 1.2) -> int:
    """
    Estimate walking time based on distance.
    
    Args:
        distance_meters: Distance in meters
        speed_mps: Walking speed in meters per second (default 1.2 m/s = ~4.3 km/h)
    
    Returns:
        Time in minutes (rounded up)
    """
    time_seconds = distance_meters / speed_mps
    time_minutes = math.ceil(time_seconds / 60)
    return max(1, time_minutes)  # Minimum 1 minute


def get_node_coordinates(node_data: dict[str, Any]) -> tuple[float, float] | None:
    """
    Extract x, y coordinates from node data.
    
    Args:
        node_data: Node dictionary with 'x' and 'y' keys
    
    Returns:
        Tuple of (x, y) or None if coordinates not available
    """
    x = node_data.get("x")
    y = node_data.get("y")
    
    if x is not None and y is not None:
        return float(x), float(y)
    
    return None


def format_distance(meters: float) -> str:
    """
    Format distance for human readability.
    
    Args:
        meters: Distance in meters
    
    Returns:
        Formatted string (e.g., "50m", "1.2km")
    """
    if meters < 1000:
        return f"{int(meters)}m"
    else:
        km = meters / 1000
        return f"{km:.1f}km"
