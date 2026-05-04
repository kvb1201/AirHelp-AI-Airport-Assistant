import asyncio
from app.services.orchestrator import handle_chat

context = {}

async def run():

    queries = [
        "I am at terminal 3",
        "I want food quickly",
        "show options",
    ]

    global context

    for q in queries:
        print("\n==============================")
        print("USER:", q)

        res = await handle_chat(q, context)

        context = res["context"]

        print("BOT:", res["message"])
        print("CONTEXT:", context)

asyncio.run(run())