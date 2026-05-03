"""Typed models for the non-navigation airport knowledge base."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RawPlaceSeed(BaseModel):
    id: str
    name: str
    terminal: str
    category: str
    description: str
    location_text: str | None = None
    source_type: str
    source_name: str
    source_query: str


class Level(BaseModel):
    level_id: str
    name: str
    zones: list[str] = Field(default_factory=list)


class TerminalStructure(BaseModel):
    terminal_id: str
    name: str
    levels: list[Level]
    source_url: str
    last_verified_at: str
    confidence: float


class PlaceLocation(BaseModel):
    terminal: str
    level: str | None = None
    zone: str | None = None
    location_text: str | None = None
    near_text: list[str] = Field(default_factory=list)


class PreferenceProfile(BaseModel):
    food: list[str] = Field(default_factory=list)
    shopping: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)


class RecommendedForProfile(BaseModel):
    age_groups: list[str] = Field(default_factory=list)
    travel_types: list[str] = Field(default_factory=list)
    budget_levels: list[str] = Field(default_factory=list)
    mobility: list[str] = Field(default_factory=list)
    preferences: PreferenceProfile = Field(default_factory=PreferenceProfile)
    min_time_available: int = 0


class Place(BaseModel):
    id: str
    name: str
    category: str
    sub_category: str
    type: str
    level: str | None = None
    near: list[str] = Field(default_factory=list)
    speed: str = "medium"
    price_level: str = "medium"
    queue_time: int = 5
    avg_time_spent: int = 10
    location: PlaceLocation
    recommended_for: RecommendedForProfile = Field(default_factory=RecommendedForProfile)
    attributes: dict[str, Any] = Field(default_factory=dict)
    service_options: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    offers: list[str] = Field(default_factory=list)
    intents: list[str] = Field(default_factory=list)
    description: str = ""
    aliases: list[str] = Field(default_factory=list)
    source_url: str = ""
    source_type: str = ""
    source_name: str = ""
    last_verified_at: str = ""
    confidence: float = 0.7
    status: str = "active"


class Flight(BaseModel):
    flight_id: str
    airline: str
    type: str
    terminal: str
    gate: str | None = None
    check_in: str | None = None
    timings: dict[str, str] = Field(default_factory=dict)
    status: str
    category: str
    source_url: str
    last_verified_at: str


class Offer(BaseModel):
    offer_id: str
    title: str
    type: str
    description: str
    valid_at: list[str] = Field(default_factory=list)
    valid_till: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_url: str
    last_verified_at: str
    status: str = "active"


class RawDocument(BaseModel):
    id: str
    source_url: str
    source_type: str
    page_type: str
    fetched_at: str
    content: str
    checksum: str


class KnowledgeChunk(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    text: str
    source_url: str | None = None


class KnowledgeBaseSnapshot(BaseModel):
    terminal_structure: TerminalStructure
    places: list[Place]
    flights: list[Flight]
    offers: list[Offer]
    raw_documents: list[RawDocument]
    rag_chunks: list[KnowledgeChunk]
