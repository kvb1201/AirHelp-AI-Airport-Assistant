"""
Travel Documents API endpoints for offline document assistant.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.travel_document_service import TravelDocumentService

router = APIRouter()


class TravelQuery(BaseModel):
    """Request model for travel document queries."""
    message: str


class TravelRequirementsResponse(BaseModel):
    """Response model for travel requirements."""
    success: bool
    destination: str | None = None
    country: str | None = None
    region: str | None = None
    documents_required: list[str] = []
    notes: list[str] = []
    fallback_used: bool = False
    formatted_response: str
    error: str | None = None


@router.post("/requirements", response_model=TravelRequirementsResponse)
def get_travel_requirements(query: TravelQuery):
    """
    Get travel document requirements based on user message.
    
    Example requests:
    - "I am going to Paris"
    - "Traveling to Tokyo next month"
    - "Planning a trip to New York"
    """
    service = TravelDocumentService()
    requirements = service.get_travel_requirements(query.message)
    formatted_response = service.format_response(requirements)
    
    return TravelRequirementsResponse(
        success=requirements.get("success", False),
        destination=requirements.get("destination"),
        country=requirements.get("country"),
        region=requirements.get("region"),
        documents_required=requirements.get("documents_required", []),
        notes=requirements.get("notes", []),
        fallback_used=requirements.get("fallback_used", False),
        formatted_response=formatted_response,
        error=requirements.get("error")
    )


@router.get("/requirements")
def get_travel_requirements_get(
    message: str = Query(..., description="Travel message like 'I am going to Paris'")
):
    """
    Get travel document requirements via GET request.
    
    Example: /api/travel-documents/requirements?message=I am going to Paris
    """
    service = TravelDocumentService()
    requirements = service.get_travel_requirements(message)
    formatted_response = service.format_response(requirements)
    
    return {
        "success": requirements.get("success", False),
        "destination": requirements.get("destination"),
        "country": requirements.get("country"),
        "region": requirements.get("region"),
        "documents_required": requirements.get("documents_required", []),
        "notes": requirements.get("notes", []),
        "fallback_used": requirements.get("fallback_used", False),
        "formatted_response": formatted_response,
        "error": requirements.get("error")
    }


@router.get("/countries")
def list_supported_countries():
    """
    List all supported countries in the knowledge base.
    """
    service = TravelDocumentService()
    travel_docs = service._load_travel_documents()
    
    countries = []
    for country, data in travel_docs.items():
        countries.append({
            "country": country,
            "region": data.get("region", ""),
            "document_count": len(data.get("documents_required", [])),
            "has_notes": len(data.get("notes", [])) > 0
        })
    
    return {
        "total_countries": len(countries),
        "countries": sorted(countries, key=lambda x: x["country"])
    }


@router.get("/cities")
def list_supported_cities():
    """
    List all supported cities in the mapping.
    """
    service = TravelDocumentService()
    city_mapping = service._load_city_mapping()
    
    cities_by_country = {}
    for city, country in city_mapping.items():
        if country not in cities_by_country:
            cities_by_country[country] = []
        cities_by_country[country].append(city.title())
    
    # Sort cities within each country
    for country in cities_by_country:
        cities_by_country[country].sort()
    
    return {
        "total_cities": len(city_mapping),
        "total_countries": len(cities_by_country),
        "cities_by_country": cities_by_country
    }


@router.get("/test")
def test_examples():
    """
    Test the system with example queries.
    """
    service = TravelDocumentService()
    
    test_cases = [
        "I am going to Paris",
        "Traveling to Tokyo next month",
        "Planning a trip to New York",
        "Going to Dubai for vacation",
        "Visit to London",
        "Trip to some unknown place"  # Test fallback
    ]
    
    results = []
    for test_case in test_cases:
        requirements = service.get_travel_requirements(test_case)
        formatted_response = service.format_response(requirements)
        
        results.append({
            "input": test_case,
            "destination": requirements.get("destination"),
            "country": requirements.get("country"),
            "fallback_used": requirements.get("fallback_used", False),
            "response": formatted_response
        })
    
    return {
        "test_cases": len(test_cases),
        "results": results
    }