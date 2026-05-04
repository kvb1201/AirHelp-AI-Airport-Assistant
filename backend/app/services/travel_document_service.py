"""
Offline Travel Document Assistant Service
Provides required travel documents based on destination using local knowledge base.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class TravelDocumentService:
    """Smart rule-based system for travel document requirements."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self._travel_docs: dict[str, Any] | None = None
        self._city_mapping: dict[str, str] | None = None
        
        # Default checklist for fallback
        self.default_documents = [
            "Passport",
            "Visa (if required)",
            "Travel Insurance",
            "Accommodation Proof",
            "Return Ticket",
            "Financial Proof"
        ]
        
        # Regional fallback rules
        self.regional_rules = {
            "Schengen Area": [
                "Valid Passport (6+ months validity)",
                "Schengen Visa",
                "Travel Insurance (€30,000 coverage)",
                "Accommodation Proof",
                "Return Ticket",
                "Financial Proof"
            ],
            "Asia": [
                "Passport",
                "Tourist Visa",
                "Return Ticket",
                "Accommodation Proof"
            ],
            "North America": [
                "Valid Passport",
                "Visa",
                "Financial Proof",
                "Return Ticket"
            ],
            "Europe": [
                "Passport",
                "Visa",
                "Travel Insurance",
                "Accommodation Proof"
            ],
            "Middle East": [
                "Passport",
                "Tourist Visa",
                "Return Ticket",
                "Hotel Booking"
            ],
            "Oceania": [
                "Passport",
                "Visitor Visa",
                "Financial Proof",
                "Return Ticket"
            ]
        }
    
    def _load_travel_documents(self) -> dict[str, Any]:
        """Load travel documents data from JSON file."""
        if self._travel_docs is None:
            with open(self.data_dir / "travel_documents.json", "r", encoding="utf-8") as f:
                self._travel_docs = json.load(f)
        return self._travel_docs
    
    def _load_city_mapping(self) -> dict[str, str]:
        """Load city to country mapping from JSON file."""
        if self._city_mapping is None:
            with open(self.data_dir / "city_country_mapping.json", "r", encoding="utf-8") as f:
                self._city_mapping = json.load(f)
        return self._city_mapping
    
    def extract_destination(self, user_input: str) -> str | None:
        """
        Extract destination from user input.
        
        Args:
            user_input: User's message like "I am going to Paris"
        
        Returns:
            Extracted destination or None
        """
        # Normalize input
        text = user_input.lower().strip()
        
        # Common patterns for destination extraction
        patterns = [
            r"(?:going to|traveling to|visiting|trip to|fly to|travel to)\s+([a-zA-Z\s]+)",
            r"(?:i'm going to|i am going to|we're going to|we are going to)\s+([a-zA-Z\s]+)",
            r"(?:destination|place|city|country)(?:\s+is)?\s+([a-zA-Z\s]+)",
            r"(?:to|in)\s+([a-zA-Z\s]+)(?:\s+for|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                destination = match.group(1).strip()
                # Clean up common words
                destination = re.sub(r'\b(for|vacation|holiday|business|trip|travel)\b.*', '', destination).strip()
                if destination and len(destination) > 1:
                    return destination.title()
        
        # Fallback: look for city names directly in the text
        city_mapping = self._load_city_mapping()
        words = text.split()
        
        # Check for multi-word cities first
        for i in range(len(words)):
            for j in range(i + 2, min(i + 4, len(words) + 1)):  # Check 2-3 word combinations
                phrase = " ".join(words[i:j])
                if phrase in city_mapping:
                    return phrase.title()
        
        # Check single words
        for word in words:
            if word in city_mapping:
                return word.title()
        
        return None
    
    def map_to_country(self, destination: str) -> str | None:
        """
        Map city/destination to country.
        
        Args:
            destination: City or country name
        
        Returns:
            Country name or None
        """
        if not destination:
            return None
        
        destination_lower = destination.lower()
        
        # Check if it's already a country
        travel_docs = self._load_travel_documents()
        for country in travel_docs.keys():
            if country.lower() == destination_lower:
                return country
        
        # Check city mapping
        city_mapping = self._load_city_mapping()
        if destination_lower in city_mapping:
            return city_mapping[destination_lower]
        
        # Check partial matches for cities
        for city, country in city_mapping.items():
            if destination_lower in city or city in destination_lower:
                return country
        
        return None
    
    def get_travel_requirements(self, user_input: str) -> dict[str, Any]:
        """
        Main function to get travel requirements based on user input.
        
        Args:
            user_input: User's message
        
        Returns:
            Dictionary with travel requirements
        """
        # Step 1: Extract destination
        destination = self.extract_destination(user_input)
        
        if not destination:
            return {
                "success": False,
                "error": "Could not extract destination from your message. Please specify where you're traveling to.",
                "example": "Try: 'I am going to Paris' or 'Traveling to Tokyo'"
            }
        
        # Step 2: Map to country
        country = self.map_to_country(destination)
        
        if not country:
            return self._fallback_response(destination, "unknown_destination")
        
        # Step 3: Lookup knowledge base
        travel_docs = self._load_travel_documents()
        
        if country in travel_docs:
            country_data = travel_docs[country]
            return {
                "success": True,
                "destination": destination,
                "country": country,
                "region": country_data.get("region", ""),
                "documents_required": country_data.get("documents_required", []),
                "notes": country_data.get("notes", []),
                "fallback_used": False
            }
        
        # Step 4: Regional fallback
        return self._fallback_response(destination, "no_country_data", country)
    
    def _fallback_response(self, destination: str, reason: str, country: str | None = None) -> dict[str, Any]:
        """
        Generate fallback response when exact data is not available.
        
        Args:
            destination: Original destination
            reason: Reason for fallback
            country: Country if known
        
        Returns:
            Fallback response dictionary
        """
        # Try to guess region for better fallback
        region = self._guess_region(destination, country)
        
        if region and region in self.regional_rules:
            documents = self.regional_rules[region]
            notes = [f"Based on typical {region} requirements"]
        else:
            documents = self.default_documents
            notes = ["Generic travel requirements"]
        
        return {
            "success": True,
            "destination": destination,
            "country": country or "Unknown",
            "region": region or "Unknown",
            "documents_required": documents,
            "notes": notes,
            "fallback_used": True,
            "fallback_reason": reason
        }
    
    def _guess_region(self, destination: str, country: str | None) -> str | None:
        """
        Guess region based on destination or country name.
        
        Args:
            destination: Destination name
            country: Country name if known
        
        Returns:
            Guessed region or None
        """
        # European cities/countries
        european_keywords = [
            "europe", "european", "eu", "schengen",
            "paris", "london", "berlin", "rome", "madrid", "amsterdam"
        ]
        
        # Asian cities/countries
        asian_keywords = [
            "asia", "asian", "tokyo", "bangkok", "singapore", "seoul",
            "kuala lumpur", "jakarta", "manila", "hong kong"
        ]
        
        # North American cities/countries
        na_keywords = [
            "america", "american", "usa", "canada", "new york", "toronto",
            "los angeles", "vancouver", "chicago", "montreal"
        ]
        
        text = f"{destination} {country or ''}".lower()
        
        if any(keyword in text for keyword in european_keywords):
            # Check if it's Schengen area
            schengen_keywords = ["france", "germany", "italy", "spain", "netherlands", "switzerland"]
            if any(keyword in text for keyword in schengen_keywords):
                return "Schengen Area"
            return "Europe"
        
        if any(keyword in text for keyword in asian_keywords):
            return "Asia"
        
        if any(keyword in text for keyword in na_keywords):
            return "North America"
        
        return None
    
    def format_response(self, requirements: dict[str, Any]) -> str:
        """
        Format the response in a user-friendly way.
        
        Args:
            requirements: Requirements dictionary from get_travel_requirements
        
        Returns:
            Formatted response string
        """
        if not requirements.get("success"):
            return requirements.get("error", "An error occurred.")
        
        country = requirements.get("country", "Unknown")
        documents = requirements.get("documents_required", [])
        notes = requirements.get("notes", [])
        fallback_used = requirements.get("fallback_used", False)
        
        # Build response
        response_parts = []
        
        # Header
        if fallback_used:
            response_parts.append(
                f"I don't have exact data for this destination, but based on similar regions:"
            )
            response_parts.append("")
        
        response_parts.append(f"Documents required for {country}:")
        
        # Documents list
        for doc in documents:
            response_parts.append(f"• {doc}")
        
        # Notes
        if notes:
            response_parts.append("")
            response_parts.append("Notes:")
            for note in notes:
                response_parts.append(f"- {note}")
        
        # Bonus question
        response_parts.append("")
        response_parts.append("Would you like me to remind you about visa or document deadlines?")
        
        return "\n".join(response_parts)


# Convenience function for easy usage
def get_travel_requirements(user_input: str) -> str:
    """
    Convenience function to get travel requirements.
    
    Args:
        user_input: User's message about travel destination
    
    Returns:
        Formatted response string
    """
    service = TravelDocumentService()
    requirements = service.get_travel_requirements(user_input)
    return service.format_response(requirements)