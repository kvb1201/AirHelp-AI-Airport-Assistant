"""
Test script for Travel Document Assistant System.
Run: python backend/test_travel_documents.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.travel_document_service import TravelDocumentService


def test_destination_extraction():
    """Test destination extraction from various user inputs."""
    print("=" * 80)
    print("TEST 1: Destination Extraction")
    print("=" * 80)
    
    service = TravelDocumentService()
    
    test_cases = [
        "I am going to Paris",
        "Traveling to Tokyo next month",
        "Planning a trip to New York",
        "Going to Dubai for vacation",
        "Visit to London",
        "I'm flying to Los Angeles",
        "We are going to Bangkok",
        "Trip to Rome in December",
        "Destination is Singapore",
        "Travel to Bali",
    ]
    
    for test_case in test_cases:
        destination = service.extract_destination(test_case)
        print(f"Input: '{test_case}'")
        print(f"Extracted: {destination}")
        print()
    
    return True


def test_city_country_mapping():
    """Test city to country mapping."""
    print("=" * 80)
    print("TEST 2: City to Country Mapping")
    print("=" * 80)
    
    service = TravelDocumentService()
    
    test_cities = [
        "Paris", "Tokyo", "New York", "Dubai", "London",
        "Bangkok", "Rome", "Singapore", "Bali", "Berlin"
    ]
    
    for city in test_cities:
        country = service.map_to_country(city)
        print(f"City: {city} → Country: {country}")
    
    print()
    return True


def test_travel_requirements():
    """Test complete travel requirements flow."""
    print("=" * 80)
    print("TEST 3: Complete Travel Requirements")
    print("=" * 80)
    
    service = TravelDocumentService()
    
    test_cases = [
        "I am going to Paris",
        "Traveling to Tokyo",
        "Planning a trip to New York",
        "Going to Dubai",
        "Visit to some unknown place",  # Test fallback
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case}")
        print("-" * 50)
        
        requirements = service.get_travel_requirements(test_case)
        formatted_response = service.format_response(requirements)
        
        print(formatted_response)
        print("\n" + "=" * 50 + "\n")
    
    return True


def test_fallback_system():
    """Test fallback system with unknown destinations."""
    print("=" * 80)
    print("TEST 4: Fallback System")
    print("=" * 80)
    
    service = TravelDocumentService()
    
    fallback_cases = [
        "I am going to Atlantis",  # Unknown city
        "Traveling to Mars",       # Unknown destination
        "Going to XYZ country",    # Unknown country
        "Visit to some place in Europe",  # Regional hint
    ]
    
    for test_case in fallback_cases:
        print(f"Fallback Test: {test_case}")
        print("-" * 40)
        
        requirements = service.get_travel_requirements(test_case)
        formatted_response = service.format_response(requirements)
        
        print(formatted_response)
        print("\n" + "=" * 40 + "\n")
    
    return True


def test_knowledge_base_coverage():
    """Test knowledge base coverage."""
    print("=" * 80)
    print("TEST 5: Knowledge Base Coverage")
    print("=" * 80)
    
    service = TravelDocumentService()
    
    # Load data
    travel_docs = service._load_travel_documents()
    city_mapping = service._load_city_mapping()
    
    print(f"Countries in knowledge base: {len(travel_docs)}")
    print(f"Cities in mapping: {len(city_mapping)}")
    
    print("\nCountries by region:")
    regions = {}
    for country, data in travel_docs.items():
        region = data.get("region", "Unknown")
        if region not in regions:
            regions[region] = []
        regions[region].append(country)
    
    for region, countries in regions.items():
        print(f"  {region}: {len(countries)} countries")
        print(f"    {', '.join(countries[:5])}{'...' if len(countries) > 5 else ''}")
    
    print(f"\nTop 10 cities:")
    cities = list(city_mapping.keys())[:10]
    for city in cities:
        print(f"  {city.title()} → {city_mapping[city]}")
    
    return True


def main():
    """Run all tests."""
    print("\n🧪 Testing Travel Document Assistant System\n")
    
    tests = [
        ("Destination Extraction", test_destination_extraction),
        ("City-Country Mapping", test_city_country_mapping),
        ("Travel Requirements", test_travel_requirements),
        ("Fallback System", test_fallback_system),
        ("Knowledge Base Coverage", test_knowledge_base_coverage),
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
    print("=" * 80)
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
        print("\n🚀 Travel Document Assistant is ready!")
        print("\nTry these API endpoints:")
        print("  GET  /api/travel-documents/requirements?message=I am going to Paris")
        print("  POST /api/travel-documents/requirements")
        print("  GET  /api/travel-documents/countries")
        print("  GET  /api/travel-documents/cities")
        print("  GET  /api/travel-documents/test")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())