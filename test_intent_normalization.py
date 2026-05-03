#!/usr/bin/env python3
"""
Test script for intent normalization fix.
Run this to verify the normalize_intent() function works correctly.
"""

import sys
sys.path.insert(0, 'backend')

from app.services.orchestrator import normalize_intent


def test_normalize_intent():
    """Test all intent normalization cases."""
    
    print("=" * 60)
    print("Testing Intent Normalization")
    print("=" * 60)
    
    test_cases = [
        # Recommendation intents
        ("food", "recommendation"),
        ("coffee", "recommendation"),
        ("restaurant", "recommendation"),
        ("eat", "recommendation"),
        ("dining", "recommendation"),
        ("shop", "recommendation"),
        ("shopping", "recommendation"),
        ("buy", "recommendation"),
        ("store", "recommendation"),
        ("retail", "recommendation"),
        ("lounge", "recommendation"),
        ("relax", "recommendation"),
        ("rest", "recommendation"),
        ("atm", "recommendation"),
        ("money", "recommendation"),
        ("cash", "recommendation"),
        ("wifi", "recommendation"),
        ("internet", "recommendation"),
        ("charging", "recommendation"),
        ("restroom", "recommendation"),
        ("toilet", "recommendation"),
        ("washroom", "recommendation"),
        ("prayer", "recommendation"),
        ("meditation", "recommendation"),
        ("facility", "recommendation"),
        ("service", "recommendation"),
        ("recommendation", "recommendation"),  # Already normalized
        
        # Exploration intents
        ("explore", "explore"),
        
        # Navigation intents
        ("navigation", "navigation"),
        ("navigate", "navigation"),
        ("direction", "navigation"),
        ("route", "navigation"),
        
        # General intents
        ("hello", "general"),
        ("help", "general"),
        ("unknown", "general"),
        (None, "general"),
        ("", "general"),
    ]
    
    passed = 0
    failed = 0
    
    for intent, expected in test_cases:
        result = normalize_intent(intent)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | normalize_intent({intent!r:20}) → {result:20} (expected: {expected})")
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


def test_real_world_scenarios():
    """Test real-world user query scenarios."""
    
    print("\n" + "=" * 60)
    print("Real-World Scenario Tests")
    print("=" * 60)
    
    scenarios = [
        {
            "query": "I need coffee",
            "context_intent": "coffee",
            "expected_type": "recommendation",
            "should_trigger_rag": True
        },
        {
            "query": "I'm hungry",
            "context_intent": "food",
            "expected_type": "recommendation",
            "should_trigger_rag": True
        },
        {
            "query": "Where can I relax?",
            "context_intent": "lounge",
            "expected_type": "recommendation",
            "should_trigger_rag": True
        },
        {
            "query": "I need an ATM",
            "context_intent": "atm",
            "expected_type": "recommendation",
            "should_trigger_rag": True
        },
        {
            "query": "What can I do here?",
            "context_intent": "explore",
            "expected_type": "explore",
            "should_trigger_rag": True
        },
        {
            "query": "Take me to gate B12",
            "context_intent": "navigation",
            "expected_type": "navigation",
            "should_trigger_rag": False  # Different flow
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario['query']}")
        print(f"  Context Engine produces: intent = {scenario['context_intent']!r}")
        
        intent_type = normalize_intent(scenario['context_intent'])
        print(f"  Orchestrator normalizes: intent_type = {intent_type!r}")
        
        # Check if RAG would be triggered
        would_trigger_rag = intent_type in ["explore", "recommendation"]
        
        status = "✅" if intent_type == scenario['expected_type'] else "❌"
        print(f"  {status} Expected: {scenario['expected_type']!r}")
        
        rag_status = "✅" if would_trigger_rag == scenario['should_trigger_rag'] else "❌"
        rag_text = "WOULD" if would_trigger_rag else "WOULD NOT"
        print(f"  {rag_status} RAG {rag_text} be triggered (expected: {scenario['should_trigger_rag']})")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n🔥 Intent Normalization Fix - Test Suite\n")
    
    # Run unit tests
    success = test_normalize_intent()
    
    # Run scenario tests
    test_real_world_scenarios()
    
    # Final result
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
