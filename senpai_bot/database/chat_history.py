from datetime import datetime
from senpai_bot.config import CHAT_HISTORY_LIMIT
from senpai_bot.database.connection import db

COLL = "chat_histories"

async def add_message(user_id: int, role: str, content: str):
    now = datetime.utcnow()
    # push message and trim
    try:
        await db[COLL].update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "history": {
                        "$each": [{"role": role, "content": content}],
                        "$slice": -CHAT_HISTORY_LIMIT,
                    }
                },
                "$set": {"updated_at": now},
            },
            upsert=True,
        )
    except Exception:
        pass

async def get_history(user_id: int) -> list:
    doc = await db[COLL].find_one({"user_id": user_id})
    if not doc:
        return []
    return doc.get("history", [])

async def clear_history(user_id: int):
    try:
        await db[COLL].delete_one({"user_id": user_id})
    except Exception:
        pass
