import asyncio
import importlib
import os
import subprocess
from typing import List

import pyrogram
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


async def sync_time():
    """Sync system time with NTP servers to fix BadMsgNotification[16] error."""
    # Try system commands to sync time
    try:
        subprocess.run(
            ["sudo", "ntpdate", "-u", "pool.ntp.org"],
            capture_output=True,
            timeout=10,
        )
        print("✓ System time synced via ntpdate")
    except Exception as e:
        print(f"ntpdate failed: {e}")
        pass
    
    try:
        subprocess.run(
            ["sudo", "timedatectl", "set-ntp", "true"],
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass


async def main():
    # Sync system time before connecting to Telegram
    await sync_time()

    # Configure Pyrogram session for reliability
    pyrogram.session.Session.MAX_RETRIES = 5

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

    # Attempt start with time offset recovery
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            await app.start()
            print("✓ Bot started successfully")
            break
        except pyrogram.errors.BadMsgNotification as e:
            if "[16]" in str(e):  # Time sync error
                print(f"BadMsgNotification [16]: Time sync needed")
                # Try to disconnect to reset state
                try:
                    await app.disconnect()
                except Exception:
                    pass
                
                retry_count += 1
                if retry_count >= max_retries:
                    print("Error: Cannot sync with Telegram servers after multiple retries.")
                    raise
                print(f"Time offset detected, retrying... ({retry_count}/{max_retries})")
                await asyncio.sleep(4)
            else:
                raise
        except ConnectionError as e:
            # If already connected from a previous attempt, disconnect and retry
            if "already connected" in str(e).lower():
                print(f"Connection reset needed, disconnecting...")
                try:
                    await app.disconnect()
                except Exception:
                    pass
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                await asyncio.sleep(2)
            else:
                raise
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            raise

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

    # Bot is now started, run forever
    print("Senpai Bot is running...")
    try:
        await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
