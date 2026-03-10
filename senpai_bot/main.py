import asyncio
import importlib
import os
from typing import List

from pyrogram import Client

from senpai_bot import config
from senpai_bot.database.connection import db


def load_plugins(client: Client) -> None:
    """Dynamically import all modules in the plugins package and call register(client) if present."""
    # import the *plugins* submodule itself so we can locate its directory
    pkg = importlib.import_module("senpai_bot.plugins")
    pkg_dir = os.path.dirname(pkg.__file__)
    for filename in os.listdir(pkg_dir):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue
        module_name = f"senpai_bot.plugins.{filename[:-3]}"
        module = importlib.import_module(module_name)
        if hasattr(module, "register"):
            try:
                module.register(client)
            except Exception:
                pass  # ignore plugin registration errors


async def main():
    # ensure Mongo connection (lazy)
    try:
        _ = db
    except Exception:
        print("warning: could not connect to database")

    app = Client(
        "senpai_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
    )

    load_plugins(app)

    # schedule periodic tasks
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from senpai_bot.database.tod_db import reset_monthly_scores

        scheduler = AsyncIOScheduler()
        # reset global monthly scores on configured day at midnight UTC
        scheduler.add_job(
            reset_monthly_scores,
            "cron",
            day=config.TOD_MONTHLY_RESET_DAY,
            hour=0,
            minute=0,
        )
        scheduler.start()
    except ImportError:
        # apscheduler not available; monthly reset disabled
        pass

    # start the bot
    async with app:
        print("Senpai Bot is running...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
