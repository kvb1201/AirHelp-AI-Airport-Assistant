"""
Quick test script for turn-by-turn navigation system.
Run: python backend/test_turn_by_turn.py
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.navigation_service import get_route
from app.services.navigation_knowledge import NavigationKnowledgeIntegrator


def test_basic_navigation():
    """Test basic navigation from entrance to gate."""
    print("=" * 80)
    print("TEST 1: Basic Navigation (Entrance → NE Gate)")
    print("=" * 80)
    
    route = get_route("entrance", "gate_ne")
    
    if not route.get("ok"):
        print(f"❌ Error: {route.get('error')}")
        return False
    
    print(f"✓ Route found!")
    print(f"  Start: {route['start_id']}")
    print(f"  Goal: {route['goal_id']}")
    
    summary = route.get("route_summary", {})
    print(f"\n📊 Summary:")
    print(f"  Distance: {summary.get('total_distance_formatted', 'N/A')}")
    print(f"  Time: {summary.get('total_time_minutes', 0)} minutes")
    print(f"  Steps: {summary.get('number_of_steps', 0)}")
    print(f"  Turns: {summary.get('number_of_turns', 0)}")
    print(f"  Floors: {', '.join(summary.get('floors_traversed', []))}")
    
    # Show first few turn-by-turn directions
    directions = route.get("turn_by_turn_directions", [])
    print(f"\n🚶 Turn-by-Turn Directions (first 5):")
    for i, step in enumerate(directions[:5]):
        print(f"\n  Step {step['step']}: {step['type'].upper()}")
        print(f"    {step['instruction']}")
        if step.get('distance_formatted'):
            print(f"    Distance: {step['distance_formatted']}")
        if step.get('nearby_landmarks'):
            landmarks = [lm['name'] for lm in step['nearby_landmarks'][:2]]
            print(f"    Nearby: {', '.join(landmarks)}")
    
    if len(directions) > 5:
        print(f"\n  ... and {len(directions) - 5} more steps")
    
    return True


def test_location_search():
    """Test location search functionality."""
    print("\n" + "=" * 80)
    print("TEST 2: Location Search (Coffee)")
    print("=" * 80)
    
    integrator = NavigationKnowledgeIntegrator()
    results = integrator.search_location_by_name("coffee")
    
    print(f"✓ Found {len(results)} results for 'coffee':")
    
    for i, result in enumerate(results[:5], 1):
        print(f"\n  {i}. {result['name']}")
        print(f"     Type: {result['type']}")
        print(f"     Floor: {result.get('floor', 'N/A')}")
        if result.get('graph_node_id'):
            print(f"     Node: {result['graph_node_id']}")
    
    return len(results) > 0


def test_location_context():
    """Test location context enrichment."""
    print("\n" + "=" * 80)
    print("TEST 3: Location Context (Central Hub)")
    print("=" * 80)
    
    integrator = NavigationKnowledgeIntegrator()
    context = integrator.enrich_node_with_context("t2_hub_02_02")
    
    if context.get("error"):
        print(f"❌ Error: {context['error']}")
        return False
    
    node = context.get("node", {})
    print(f"✓ Location: {node.get('name', 'Unknown')}")
    print(f"  Floor: {node.get('floor', 'N/A')}")
    print(f"  Zone: {node.get('zone', 'N/A')}")
    
    coords = context.get("coordinates", {})
    print(f"  Coordinates: ({coords.get('x', 0):.1f}, {coords.get('y', 0):.1f})")
    
    facilities = context.get("nearby_facilities", [])
    print(f"\n  Nearby Facilities ({len(facilities)}):")
    for fac in facilities[:3]:
        print(f"    • {fac['name']} ({fac['distance_formatted']})")
    
    shops = context.get("nearby_shops", [])
    print(f"\n  Nearby Shops ({len(shops)}):")
    for shop in shops[:5]:
        print(f"    • {shop['name']} ({shop['distance_formatted']})")
    
    return True


def test_contextual_navigation():
    """Test contextual navigation with query."""
    print("\n" + "=" * 80)
    print("TEST 4: Contextual Navigation (Entrance → Security with 'restroom' query)")
    print("=" * 80)
    
    integrator = NavigationKnowledgeIntegrator()
    result = integrator.get_contextual_directions(
        from_node_id="t2_entrance",
        to_node_id="t2_security_intl",
        user_query="restroom",
    )
    
    if not result.get("ok"):
        print(f"❌ Error: {result.get('error')}")
        return False
    
    print(f"✓ Contextual route generated!")
    
    # Show start context
    start_ctx = result.get("start_context", {})
    start_node = start_ctx.get("node", {})
    print(f"\n📍 Start: {start_node.get('name', 'Unknown')}")
    start_facilities = start_ctx.get("nearby_facilities", [])
    if start_facilities:
        print(f"  Nearby: {', '.join(f['name'] for f in start_facilities[:2])}")
    
    # Show goal context
    goal_ctx = result.get("goal_context", {})
    goal_node = goal_ctx.get("node", {})
    print(f"\n🎯 Destination: {goal_node.get('name', 'Unknown')}")
    goal_facilities = goal_ctx.get("nearby_facilities", [])
    if goal_facilities:
        print(f"  Nearby: {', '.join(f['name'] for f in goal_facilities[:2])}")
    
    # Show knowledge base context
    kb_context = result.get("knowledge_base_context", [])
    if kb_context:
        print(f"\n📚 Knowledge Base Context ({len(kb_context)} chunks):")
        for chunk in kb_context[:2]:
            text = chunk.get("text", "")[:100]
            print(f"  • {text}...")
    
    return True


def main():
    """Run all tests."""
    print("\n🧪 Testing Turn-by-Turn Navigation System\n")
    
    tests = [
        ("Basic Navigation", test_basic_navigation),
        ("Location Search", test_location_search),
        ("Location Context", test_location_context),
        ("Contextual Navigation", test_contextual_navigation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
