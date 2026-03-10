from datetime import datetime, timedelta
from senpai_bot.database.connection import db

SCORES = "tod_scores"
SESSIONS = "tod_sessions"
GLOBAL = "tod_global_scores"
MONTHLY = "tod_monthly"
MONTHLY_ARCHIVE = "tod_monthly_archive"

async def get_score(user_id: int, chat_id: int) -> dict:
    doc = await db[SCORES].find_one({"user_id": user_id, "chat_id": chat_id})
    if not doc:
        return {"truths_done": 0, "dares_done": 0, "points": 0}
    return {
        "truths_done": doc.get("truths_done", 0),
        "dares_done": doc.get("dares_done", 0),
        "points": doc.get("points", 0),
    }

async def add_score(user_id: int, chat_id: int, type: str, username: str | None = None, first_name: str | None = None):
    now = datetime.utcnow()
    inc = {"truth": ("truths_done", 5), "dare": ("dares_done", 10)}.get(type)
    if not inc:
        return
    field, pts = inc
    try:
        await db[SCORES].update_one(
            {"user_id": user_id, "chat_id": chat_id},
            {
                "$inc": {field: 1, "points": pts},
                "$setOnInsert": {"user_id": user_id, "chat_id": chat_id},
                "$set": {"updated_at": now},
            },
            upsert=True,
        )
    except Exception:
        pass
    # update global and monthly records as well
    try:
        await update_global_score(user_id, username, first_name, pts)
        await update_monthly_score(user_id, username, first_name, pts)
    except Exception:
        pass

async def get_leaderboard(chat_id: int) -> list:
    cursor = db[SCORES].find({"chat_id": chat_id}).sort("points", -1).limit(10)
    results = []
    async for doc in cursor:
        results.append({
            "user_id": doc.get("user_id"),
            "points": doc.get("points", 0),
            "truths_done": doc.get("truths_done", 0),
            "dares_done": doc.get("dares_done", 0),
        })
    return results


# ranking helpers
async def update_global_score(user_id: int, username: str | None, first_name: str | None, points: int):
    now = datetime.utcnow()
    try:
        await db[GLOBAL].update_one(
            {"user_id": user_id},
            {
                "$inc": {"points": points},
                "$set": {"username": username, "first_name": first_name, "updated_at": now},
                "$setOnInsert": {"user_id": user_id, "truths_done": 0, "dares_done": 0},
            },
            upsert=True,
        )
    except Exception:
        pass

async def update_monthly_score(user_id: int, username: str | None, first_name: str | None, points: int):
    now = datetime.utcnow()
    month = now.strftime("%Y-%m")
    try:
        await db[MONTHLY].update_one(
            {"user_id": user_id, "month": month},
            {
                "$inc": {"points": points},
                "$set": {"username": username, "first_name": first_name},
                "$setOnInsert": {"user_id": user_id, "month": month, "truths_done": 0, "dares_done": 0},
            },
            upsert=True,
        )
    except Exception:
        pass

async def get_global_rank(user_id: int) -> dict:
    doc = await db[GLOBAL].find_one({"user_id": user_id})
    points = doc.get("points", 0) if doc else 0
    higher = await db[GLOBAL].count_documents({"points": {"$gt": points}})
    total = await db[GLOBAL].count_documents({})
    return {"rank": higher + 1, "points": points, "total_users": total}

async def get_group_rank(user_id: int, chat_id: int) -> dict:
    doc = await db[SCORES].find_one({"user_id": user_id, "chat_id": chat_id})
    points = doc.get("points", 0) if doc else 0
    higher = await db[SCORES].count_documents({"chat_id": chat_id, "points": {"$gt": points}})
    total = await db[SCORES].count_documents({"chat_id": chat_id})
    return {"rank": higher + 1, "points": points, "total_users": total}

async def get_monthly_rank(user_id: int) -> dict:
    month = datetime.utcnow().strftime("%Y-%m")
    doc = await db[MONTHLY].find_one({"user_id": user_id, "month": month})
    points = doc.get("points", 0) if doc else 0
    higher = await db[MONTHLY].count_documents({"month": month, "points": {"$gt": points}})
    total = await db[MONTHLY].count_documents({"month": month})
    return {"rank": higher + 1, "points": points, "total_users": total, "month": month}

async def get_global_leaderboard() -> list:
    cursor = db[GLOBAL].find({}).sort("points", -1).limit(10)
    res = []
    async for doc in cursor:
        res.append({"user_id": doc.get("user_id"), "points": doc.get("points", 0)})
    return res

async def get_monthly_leaderboard() -> list:
    month = datetime.utcnow().strftime("%Y-%m")
    cursor = db[MONTHLY].find({"month": month}).sort("points", -1).limit(10)
    res = []
    async for doc in cursor:
        res.append({"user_id": doc.get("user_id"), "points": doc.get("points", 0)})
    return res

async def reset_monthly_scores():
    now = datetime.utcnow()
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    # archive top3
    top3 = []
    cursor = db[MONTHLY].find({"month": last_month}).sort("points", -1).limit(3)
    rank = 1
    async for doc in cursor:
        top3.append({"rank": rank, "user_id": doc.get("user_id"), "first_name": doc.get("first_name"), "points": doc.get("points", 0)})
        rank += 1
    if top3:
        await db["tod_monthly_archive"].insert_one({"month": last_month, "top3": top3, "archived_at": now})
    # nothing else to do; new month will create new docs automatically

async def save_session(chat_id: int, user_id: int, type: str, question: str, expire_at: datetime):
    now = datetime.utcnow()
    try:
        await db[SESSIONS].update_one(
            {"chat_id": chat_id, "user_id": user_id, "completed": False},
            {
                "$set": {
                    "type": type,
                    "question": question,
                    "expire_at": expire_at,
                    "created_at": now,
                    "completed": False,
                }
            },
            upsert=True,
        )
    except Exception:
        pass

async def complete_session(chat_id: int, user_id: int):
    try:
        await db[SESSIONS].update_one(
            {"chat_id": chat_id, "user_id": user_id, "completed": False},
            {"$set": {"completed": True}},
        )
    except Exception:
        pass

async def get_active_session(chat_id: int, user_id: int) -> dict | None:
    doc = await db[SESSIONS].find_one({"chat_id": chat_id, "user_id": user_id, "completed": False})
    if not doc:
        return None
    # check expiry
    exp = doc.get("expire_at")
    if exp and datetime.utcnow() > exp:
        # mark expired
        await complete_session(chat_id, user_id)
        return None
    return doc
