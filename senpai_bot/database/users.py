from datetime import datetime
from senpai_bot.database.connection import db

USERS_COLL = "users"
GROUPS_COLL = "groups"

async def upsert_user(user_id: int, username: str | None, first_name: str | None):
    """Insert or update a private user record."""
    now = datetime.utcnow()
    try:
        await db[USERS_COLL].update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "username": username,
                    "first_name": first_name,
                    "chat_type": "private",
                    "is_banned": False,
                },
                "$setOnInsert": {"joined_at": now},
            },
            upsert=True,
        )
    except Exception:
        pass  # silent failure

async def upsert_group(chat_id: int, chat_title: str | None, username: str | None):
    """Insert or update a group record."""
    now = datetime.utcnow()
    try:
        await db[GROUPS_COLL].update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "chat_title": chat_title,
                    "username": username,
                    "is_banned": False,
                },
                "$setOnInsert": {"added_at": now},
            },
            upsert=True,
        )
    except Exception:
        pass

async def get_user(user_id: int) -> dict | None:
    """Fetch a user by their Telegram user_id."""
    return await db[USERS_COLL].find_one({"user_id": user_id})

# broadcast / reporting helpers
async def get_all_users() -> list:
    """Return list of all private users (only user_id)."""
    cursor = db[USERS_COLL].find({}, {"user_id": 1, "_id": 0})
    return await cursor.to_list(length=None)

async def get_all_groups() -> list:
    """Return list of all registered groups (only chat_id)."""
    cursor = db[GROUPS_COLL].find({}, {"chat_id": 1, "_id": 0})
    return await cursor.to_list(length=None)

async def get_total_users() -> int:
    """Count of private users."""
    return await db[USERS_COLL].count_documents({})

async def get_total_groups() -> int:
    """Count of groups."""
    return await db[GROUPS_COLL].count_documents({})
