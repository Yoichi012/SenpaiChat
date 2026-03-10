import motor.motor_asyncio
from senpai_bot.config import MONGO_URI, DB_NAME

clients = {}

def get_db():
    """Return a singleton Motor database instance."""
    if "db" not in clients:
        if not MONGO_URI:
            raise RuntimeError("MONGO_URI is not set in config")
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        clients["db"] = client[DB_NAME]
    return clients["db"]

# export for convenience
db = get_db()
