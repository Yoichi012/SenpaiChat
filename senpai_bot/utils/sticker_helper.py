import random
from datetime import datetime

from senpai_bot.config import BOT_STICKER_PACK
from senpai_bot.database.connection import db

COLL = "sticker_packs"

async def save_user_sticker_pack(user_id: int, pack_name: str, file_ids: list):
    now = datetime.utcnow()
    try:
        await db[COLL].update_one(
            {"user_id": user_id, "pack_name": pack_name},
            {
                "$set": {"file_ids": file_ids, "saved_at": now},
                "$setOnInsert": {"user_id": user_id, "pack_name": pack_name},
            },
            upsert=True,
        )
    except Exception:
        pass

async def get_user_sticker(user_id: int) -> str | None:
    try:
        docs = await db[COLL].find({"user_id": user_id}).to_list(length=None)
        if not docs:
            return None
        pack = random.choice(docs)
        ids = pack.get("file_ids", [])
        if not ids:
            return None
        return random.choice(ids)
    except Exception:
        return None

async def get_bot_sticker() -> str | None:
    # return random sticker from bot pack if stored
    try:
        doc = await db[COLL].find_one({"user_id": 0, "pack_name": BOT_STICKER_PACK})
        if not doc:
            return None
        ids = doc.get("file_ids", [])
        if not ids:
            return None
        return random.choice(ids)
    except Exception:
        return None

async def save_bot_pack(file_ids: list):
    now = datetime.utcnow()
    try:
        await db[COLL].update_one(
            {"user_id": 0, "pack_name": BOT_STICKER_PACK},
            {
                "$set": {"file_ids": file_ids, "saved_at": now},
                "$setOnInsert": {"user_id": 0, "pack_name": BOT_STICKER_PACK},
            },
            upsert=True,
        )
    except Exception:
        pass
