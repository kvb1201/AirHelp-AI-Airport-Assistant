"""
Integrate navigation graph with knowledge base for contextual wayfinding.
Enriches routes with facility and shop information for better user guidance.
"""

from __future__ import annotations

from typing import Any

from app.core.graph.airport_data import NODES
from app.core.graph.node_mapper import resolve_to_graph_node_id
from app.core.knowledge_base.repository import KnowledgeBaseRepository
from app.services.distance_calculator import (
    format_distance,
    get_node_coordinates,
    normalized_to_meters,
)
from app.services.facilities_loader import load_facilities_bom
from app.services.shops_loader import load_shops_t2_l02


class NavigationKnowledgeIntegrator:
    """Combines graph navigation with knowledge base for enriched wayfinding."""
    
    def __init__(self):
        self.kb_repo = KnowledgeBaseRepository()
        self._facilities_cache: list[dict[str, Any]] | None = None
        self._shops_cache: list[dict[str, Any]] | None = None
    
    def get_facilities(self) -> list[dict[str, Any]]:
        """Get cached facilities data."""
        if self._facilities_cache is None:
            self._facilities_cache = load_facilities_bom()
        return self._facilities_cache
    
    def get_shops(self) -> list[dict[str, Any]]:
        """Get cached shops data."""
        if self._shops_cache is None:
            self._shops_cache = load_shops_t2_l02()
        return self._shops_cache
    
    def find_nearest_facility(
        self,
        x: float,
        y: float,
        floor: str,
        category: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Find the nearest facility to given coordinates.
        
        Args:
            x, y: Normalized coordinates
            floor: Floor level
            category: Optional category filter
        
        Returns:
            Facility dictionary with distance, or None
        """
        facilities = self.get_facilities()
        nearest: tuple[float, dict[str, Any]] | None = None
        
        for facility in facilities:
            if facility.get("floor") != floor:
                continue
            
            if category and facility.get("category") != category:
                continue
            
            fx = facility.get("x_norm")
            fy = facility.get("y_norm")
            
            if fx is None or fy is None:
                continue
            
            distance = normalized_to_meters(x, y, float(fx), float(fy))
            
            if nearest is None or distance < nearest[0]:
                facility_with_distance = dict(facility)
                facility_with_distance["distance_meters"] = distance
                facility_with_distance["distance_formatted"] = format_distance(distance)
                nearest = (distance, facility_with_distance)
        
        return nearest[1] if nearest else None
    
    def find_nearest_shop(
        self,
        x: float,
        y: float,
        floor: str,
        category: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Find the nearest shop to given coordinates.
        
        Args:
            x, y: Normalized coordinates
            floor: Floor level
            category: Optional category filter
        
        Returns:
            Shop dictionary with distance, or None
        """
        shops = self.get_shops()
        nearest: tuple[float, dict[str, Any]] | None = None
        
        for shop in shops:
            if shop.get("floor") != floor:
                continue
            
            if category and shop.get("category") != category:
                continue
            
            sx = shop.get("x_norm")
            sy = shop.get("y_norm")
            
            if sx is None or sy is None:
                continue
            
            distance = normalized_to_meters(x, y, float(sx), float(sy))
            
            if nearest is None or distance < nearest[0]:
                shop_with_distance = dict(shop)
                shop_with_distance["distance_meters"] = distance
                shop_with_distance["distance_formatted"] = format_distance(distance)
                nearest = (distance, shop_with_distance)
        
        return nearest[1] if nearest else None
    
    def enrich_node_with_context(self, node_id: str) -> dict[str, Any]:
        """
        Enrich a graph node with nearby facilities and shops.
        
        Args:
            node_id: Graph node identifier
        
        Returns:
            Dictionary with node info and nearby points of interest
        """
        resolved, resolution = resolve_to_graph_node_id(node_id)
        if not resolved or resolved not in NODES:
            return {"error": "unknown_node", "node_id": node_id, "resolution": resolution}

        canonical_id = resolved
        node = dict(NODES[canonical_id])
        node["id"] = canonical_id
        
        coords = get_node_coordinates(node)
        if not coords:
            return {
                "node": node,
                "nearby_facilities": [],
                "nearby_shops": [],
            }
        
        x, y = coords
        floor = node.get("floor", "L02")
        
        # Find nearby facilities (within 100m)
        facilities = self.get_facilities()
        nearby_facilities: list[dict[str, Any]] = []
        
        for facility in facilities:
            if facility.get("floor") != floor:
                continue
            
            fx = facility.get("x_norm")
            fy = facility.get("y_norm")
            
            if fx is None or fy is None:
                continue
            
            distance = normalized_to_meters(x, y, float(fx), float(fy))
            
            if distance <= 100:
                facility_info = {
                    "name": facility.get("name_display"),
                    "category": facility.get("category"),
                    "distance_meters": distance,
                    "distance_formatted": format_distance(distance),
                    "graph_node_id": facility.get("graph_node_id"),
                }
                nearby_facilities.append((distance, facility_info))
        
        # Find nearby shops (within 100m)
        shops = self.get_shops()
        nearby_shops: list[dict[str, Any]] = []
        
        for shop in shops:
            if shop.get("floor") != floor:
                continue
            
            sx = shop.get("x_norm")
            sy = shop.get("y_norm")
            
            if sx is None or sy is None:
                continue
            
            distance = normalized_to_meters(x, y, float(sx), float(sy))
            
            if distance <= 100:
                shop_info = {
                    "name": shop.get("name_display"),
                    "category": shop.get("category"),
                    "distance_meters": distance,
                    "distance_formatted": format_distance(distance),
                    "graph_node_id": shop.get("graph_node_id"),
                }
                nearby_shops.append((distance, shop_info))
        
        # Sort by distance
        nearby_facilities.sort(key=lambda item: item[0])
        nearby_shops.sort(key=lambda item: item[0])
        
        out: dict[str, Any] = {
            "node": node,
            "coordinates": {"x": x, "y": y},
            "nearby_facilities": [f for _, f in nearby_facilities[:5]],
            "nearby_shops": [s for _, s in nearby_shops[:10]],
        }
        if canonical_id != str(node_id).strip():
            out["requested_node_id"] = node_id
            out["resolved_graph_node_id"] = canonical_id
            out["resolution"] = resolution
        return out
    
    def get_contextual_directions(
        self,
        from_node_id: str,
        to_node_id: str,
        user_query: str | None = None,
    ) -> dict[str, Any]:
        """
        Get directions with contextual information based on user query.
        
        Args:
            from_node_id: Starting node
            to_node_id: Destination node
            user_query: Optional user query for context
        
        Returns:
            Dictionary with directions and relevant context
        """
        from app.services.navigation_service import build_route_payload

        start_resolved, _ = resolve_to_graph_node_id(from_node_id)
        goal_resolved, _ = resolve_to_graph_node_id(to_node_id)
        if not start_resolved:
            return {"ok": False, "error": "unknown_start", "node_id": from_node_id}
        if not goal_resolved:
            return {"ok": False, "error": "unknown_goal", "node_id": to_node_id}

        route = build_route_payload(start_resolved, goal_resolved)
        
        if not route.get("ok"):
            return route

        route["resolved_start_id"] = start_resolved
        route["resolved_goal_id"] = goal_resolved

        start_context = self.enrich_node_with_context(start_resolved)
        goal_context = self.enrich_node_with_context(goal_resolved)
        
        # Add relevant knowledge base chunks if query provided
        kb_context: list[dict[str, Any]] = []
        if user_query:
            kb_context = self.kb_repo.get_relevant_chunks(user_query, limit=3)
        
        route["start_context"] = start_context
        route["goal_context"] = goal_context
        route["knowledge_base_context"] = kb_context
        
        return route
    
    def search_location_by_name(self, query: str) -> list[dict[str, Any]]:
        """
        Search for locations (nodes, facilities, shops) by name.
        
        Args:
            query: Search query
        
        Returns:
            List of matching locations with type and details
        """
        query_lower = query.lower()
        results: list[dict[str, Any]] = []
        
        # Search graph nodes
        for node_id, node_data in NODES.items():
            name = node_data.get("name", "").lower()
            if query_lower in name:
                results.append({
                    "type": "graph_node",
                    "id": node_id,
                    "name": node_data.get("name"),
                    "kind": node_data.get("kind"),
                    "floor": node_data.get("floor"),
                    "zone": node_data.get("zone"),
                })
        
        # Search facilities
        for facility in self.get_facilities():
            name = facility.get("name_display", "").lower()
            if query_lower in name:
                results.append({
                    "type": "facility",
                    "id": facility.get("facility_id"),
                    "name": facility.get("name_display"),
                    "category": facility.get("category"),
                    "floor": facility.get("floor"),
                    "graph_node_id": facility.get("graph_node_id"),
                })
        
        # Search shops
        for shop in self.get_shops():
            name = shop.get("name_display", "").lower()
            if query_lower in name:
                results.append({
                    "type": "shop",
                    "id": shop.get("shop_id"),
                    "name": shop.get("name_display"),
                    "category": shop.get("category"),
                    "floor": shop.get("floor"),
                    "graph_node_id": shop.get("graph_node_id"),
                })
        
        return results[:20]  # Limit results
