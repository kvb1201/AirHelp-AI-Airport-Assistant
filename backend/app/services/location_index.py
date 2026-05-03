# backend/app/services/location_index.py

"""
Lightweight canonical location index for mapping layer.
No RAG dependency.
"""

LOCATION_INDEX = [
    # Terminals
    {"label": "terminal_1", "type": "terminal", "aliases": ["terminal 1", "t1"]},
    {"label": "terminal_2", "type": "terminal", "aliases": ["terminal 2", "t2"]},
    {"label": "terminal_3", "type": "terminal", "aliases": ["terminal 3", "t3"]},

    # Gates
    {"label": "gate_a1", "type": "gate", "aliases": ["gate a1", "a1"]},
    {"label": "gate_b12", "type": "gate", "aliases": ["gate b12", "b12"]},
    {"label": "gate_d3", "type": "gate", "aliases": ["gate d3", "d3"]},

    # Key zones
    {"label": "food_court", "type": "zone", "aliases": ["food court", "restaurant area"]},
    {"label": "lounge", "type": "zone", "aliases": ["lounge", "premium lounge"]},
    {"label": "atm", "type": "service", "aliases": ["atm", "cash machine"]},
    {"label": "restroom", "type": "service", "aliases": ["toilet", "washroom"]},
    {"label": "wifi", "type": "service", "aliases": ["wifi", "internet"]},
]