from app.services.locating_engine import locate_from_query


def test_cases():
    queries = [
        # -----------------------
        # 🔹 Strong regex cases
        # -----------------------
        "I am near gate B12",
        "food near terminal 3",
        "go to terminal 2",
        "navigate to gate A1",

        # -----------------------
        # 🔹 Semantic cases
        # -----------------------
        "I want to eat",
        "lounge",
        "where can I get wifi",
        "atm nearby",

        # -----------------------
        # 🔹 Mixed cases
        # -----------------------
        "coffee near terminal 1",
        "restaurants in terminal 2",
        "shops near t3",

        # -----------------------
        # 🔹 Edge cases
        # -----------------------
        "something to do",
        "help me",
        "random text xyz",
    ]

    for q in queries:
        print("\n" + "=" * 50)
        print("QUERY:", q)

        result = locate_from_query(q)

        print("OUTPUT:")
        for k, v in result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    test_cases()