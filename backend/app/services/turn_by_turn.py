"""
Generate detailed turn-by-turn walking directions with distances and landmarks.
"""

from __future__ import annotations

from typing import Any

from app.core.graph.airport_data import NODES
from app.services.distance_calculator import (
    bearing_to_simple_direction,
    calculate_bearing,
    calculate_turn_angle,
    estimate_walking_time,
    format_distance,
    get_node_coordinates,
    normalized_to_meters,
)
from app.services.facilities_loader import load_facilities_bom
from app.services.route_narrative import passenger_place_name
from app.services.shops_loader import load_shops_t2_l02


def find_nearby_landmarks(
    x: float,
    y: float,
    floor: str,
    *,
    max_distance: float = 50.0,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """
    Find nearby shops and facilities to use as landmarks.
    
    Args:
        x, y: Normalized coordinates
        floor: Floor level (e.g., "L02", "L03")
        max_distance: Maximum distance in meters to consider
        limit: Maximum number of landmarks to return
    
    Returns:
        List of landmark dictionaries with name and distance
    """
    landmarks: list[tuple[float, dict[str, Any]]] = []
    
    # Check facilities
    facilities = load_facilities_bom()
    for facility in facilities:
        if facility.get("floor") != floor:
            continue
        
        fx = facility.get("x_norm")
        fy = facility.get("y_norm")
        
        if fx is None or fy is None:
            continue
        
        distance = normalized_to_meters(x, y, float(fx), float(fy))
        
        if distance <= max_distance:
            landmarks.append((
                distance,
                {
                    "type": "facility",
                    "name": facility.get("name_display", ""),
                    "category": facility.get("category", ""),
                    "distance_meters": distance,
                }
            ))
    
    # Check shops
    shops = load_shops_t2_l02()
    for shop in shops:
        if shop.get("floor") != floor:
            continue
        
        sx = shop.get("x_norm")
        sy = shop.get("y_norm")
        
        if sx is None or sy is None:
            continue
        
        distance = normalized_to_meters(x, y, float(sx), float(sy))
        
        if distance <= max_distance:
            landmarks.append((
                distance,
                {
                    "type": "shop",
                    "name": shop.get("name_display", ""),
                    "category": shop.get("category", ""),
                    "distance_meters": distance,
                }
            ))
    
    # Sort by distance and return top results
    landmarks.sort(key=lambda item: item[0])
    return [landmark for _, landmark in landmarks[:limit]]


def generate_turn_by_turn_directions(
    path_nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Generate detailed turn-by-turn directions with distances and bearings.
    
    Args:
        path_nodes: List of node dictionaries with coordinates
        edges: List of edge dictionaries
    
    Returns:
        List of turn-by-turn instruction dictionaries
    """
    if len(path_nodes) < 2:
        return []
    
    instructions: list[dict[str, Any]] = []
    cumulative_distance = 0.0
    cumulative_time = 0
    
    # Starting instruction
    start_node = path_nodes[0]
    start_coords = get_node_coordinates(start_node)
    
    if start_coords:
        start_landmarks = find_nearby_landmarks(
            start_coords[0],
            start_coords[1],
            start_node.get("floor", "L02"),
        )
        
        instructions.append({
            "step": 0,
            "type": "start",
            "instruction": f"Start at {passenger_place_name(start_node)}",
            "location": passenger_place_name(start_node),
            "node_id": start_node.get("id"),
            "floor": start_node.get("floor"),
            "coordinates": {"x": start_coords[0], "y": start_coords[1]},
            "nearby_landmarks": start_landmarks,
            "cumulative_distance_meters": 0,
            "cumulative_time_minutes": 0,
        })
    
    # Process each segment
    prev_bearing = None
    
    for i in range(len(path_nodes) - 1):
        current_node = path_nodes[i]
        next_node = path_nodes[i + 1]
        
        current_coords = get_node_coordinates(current_node)
        next_coords = get_node_coordinates(next_node)
        
        if not current_coords or not next_coords:
            continue
        
        # Calculate segment details
        distance = normalized_to_meters(
            current_coords[0], current_coords[1],
            next_coords[0], next_coords[1]
        )
        bearing = calculate_bearing(
            current_coords[0], current_coords[1],
            next_coords[0], next_coords[1]
        )
        time_minutes = estimate_walking_time(distance)
        
        cumulative_distance += distance
        cumulative_time += time_minutes
        
        # Determine turn instruction
        if prev_bearing is not None:
            turn_angle, turn_description = calculate_turn_angle(prev_bearing, bearing)
        else:
            turn_angle = 0
            turn_description = "proceed"
        
        # Get direction description
        direction = bearing_to_simple_direction(bearing)
        
        # Find landmarks near the destination
        landmarks = find_nearby_landmarks(
            next_coords[0],
            next_coords[1],
            next_node.get("floor", "L02"),
        )
        
        # Build instruction text
        location_name = passenger_place_name(next_node)
        
        if turn_description == "continue straight":
            instruction_text = f"Continue straight for {format_distance(distance)} to {location_name}"
        else:
            instruction_text = f"{turn_description.capitalize()}, then walk {format_distance(distance)} {direction} to {location_name}"
        
        # Add landmark context if available
        if landmarks:
            landmark_names = [lm["name"] for lm in landmarks[:2]]
            if len(landmark_names) == 1:
                instruction_text += f" (near {landmark_names[0]})"
            elif len(landmark_names) == 2:
                instruction_text += f" (near {landmark_names[0]} and {landmark_names[1]})"
        
        instructions.append({
            "step": i + 1,
            "type": "navigate",
            "instruction": instruction_text,
            "turn_description": turn_description,
            "turn_angle_degrees": turn_angle if prev_bearing is not None else None,
            "bearing_degrees": bearing,
            "direction": direction,
            "distance_meters": distance,
            "distance_formatted": format_distance(distance),
            "time_minutes": time_minutes,
            "from_location": passenger_place_name(current_node),
            "to_location": location_name,
            "from_node_id": current_node.get("id"),
            "to_node_id": next_node.get("id"),
            "floor": next_node.get("floor"),
            "coordinates": {"x": next_coords[0], "y": next_coords[1]},
            "nearby_landmarks": landmarks,
            "cumulative_distance_meters": round(cumulative_distance, 1),
            "cumulative_time_minutes": cumulative_time,
        })
        
        prev_bearing = bearing
    
    # Final arrival instruction
    final_node = path_nodes[-1]
    final_coords = get_node_coordinates(final_node)
    
    if final_coords:
        final_landmarks = find_nearby_landmarks(
            final_coords[0],
            final_coords[1],
            final_node.get("floor", "L02"),
        )
        
        instructions.append({
            "step": len(path_nodes),
            "type": "arrive",
            "instruction": f"You have arrived at {passenger_place_name(final_node)}",
            "location": passenger_place_name(final_node),
            "node_id": final_node.get("id"),
            "floor": final_node.get("floor"),
            "coordinates": {"x": final_coords[0], "y": final_coords[1]},
            "nearby_landmarks": final_landmarks,
            "cumulative_distance_meters": round(cumulative_distance, 1),
            "cumulative_time_minutes": cumulative_time,
        })
    
    return instructions


def generate_summary_stats(instructions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Generate summary statistics for the route.
    
    Args:
        instructions: List of turn-by-turn instructions
    
    Returns:
        Dictionary with summary statistics
    """
    if not instructions:
        return {
            "total_distance_meters": 0,
            "total_distance_formatted": "0m",
            "total_time_minutes": 0,
            "number_of_turns": 0,
            "number_of_steps": 0,
            "floors_traversed": [],
        }
    
    # Get final cumulative values
    final_instruction = instructions[-1]
    total_distance = final_instruction.get("cumulative_distance_meters", 0)
    total_time = final_instruction.get("cumulative_time_minutes", 0)
    
    # Count turns (excluding straight segments)
    turns = [
        inst for inst in instructions
        if inst.get("type") == "navigate" and inst.get("turn_description") != "continue straight"
    ]
    
    # Get unique floors
    floors = list(set(
        inst.get("floor")
        for inst in instructions
        if inst.get("floor")
    ))
    
    return {
        "total_distance_meters": total_distance,
        "total_distance_formatted": format_distance(total_distance),
        "total_time_minutes": total_time,
        "number_of_turns": len(turns),
        "number_of_steps": len([inst for inst in instructions if inst.get("type") == "navigate"]),
        "floors_traversed": sorted(floors),
    }
