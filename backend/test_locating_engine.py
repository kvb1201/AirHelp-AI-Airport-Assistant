# backend/test_locating_engine.py

from app.services.locating_engine import locate_from_query


def run_tests():
    test_cases = [
        "I am near gate B12",
        "go to terminal 2",
        "navigate to gate A1",
        "food near terminal 3",
        "coffee near t1",
    ]

    print("\n" + "="*60)
    print("🔍 LOCATING ENGINE TEST")
    print("="*60)

    for query in test_cases:
        print(f"\nQUERY: {query}")

        result = locate_from_query(query)

        print("OUTPUT:")
        print(f"  source       : {result.get('source')}")
        print(f"  destination  : {result.get('destination')}")
        print(f"  intent       : {result.get('intent')}")
        print(f"  clarification: {result.get('needs_clarification')}")
        print(f"  confidence   : {result.get('confidence')}")

        print("-"*50)


if __name__ == "__main__":
    run_tests()