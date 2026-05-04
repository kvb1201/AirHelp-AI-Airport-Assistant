from app.services.locating_engine import locate_from_query
from app.services.context_engine import update_context


def run_tests():
    user_context = {}

    test_cases = [
        "I want food",
        "I want food quickly",
        "I want to relax",
        "lounge",
        "something to do",
    ]

    print("\n" + "="*60)
    print("🧠 CONTEXT ENGINE TEST")
    print("="*60)

    for query in test_cases:
        print(f"\nQUERY: {query}")

        extracted = locate_from_query(query)
        ctx_output = update_context(user_context, extracted, query)

        user_context = ctx_output["context"]

        print("OUTPUT:")
        print(f"  intent              : {user_context.get('intent')}")
        print(f"  source              : {user_context.get('source')}")
        print(f"  behavior            : {user_context.get('behavior')}")
        print(f"  needs_clarification : {ctx_output.get('needs_clarification')}")
        print(f"  message             : {ctx_output.get('clarification_message')}")

        print("-"*50)


if __name__ == "__main__":
    run_tests()