import asyncio
import json
import os

from pyrogram import filters
from pyrogram.errors import ChatWriteForbidden, FloodWait, UserIsBlocked
from pyrogram.types import Message

from senpai_bot import config
from senpai_bot.database.users import get_all_groups, get_all_users
from senpai_bot.data.strings import (
    BROADCAST_DONE,
    BROADCAST_FAIL_REPORT,
    BROADCAST_GROUPS_DONE,
    BROADCAST_NO_GROUPS,
    BROADCAST_NO_USERS,
    BROADCAST_STARTED,
    BROADCAST_USAGE,
    BROADCAST_USER_USAGE,
    NO_PERMISSION,
)
from senpai_bot.utils.smallcaps import sc


def _is_owner(user_id: int) -> bool:
    return str(user_id) == str(config.OWNER_ID)


async def _copy_with_retry(client, target_id: int, src_msg: Message) -> bool:
    """Attempt to copy a message once, handling FloodWait by a single retry.

    Returns True on success, False otherwise.
    """
    try:
        await client.copy_message(target_id, src_msg.chat.id, src_msg.message_id)
        return True
    except (UserIsBlocked, ChatWriteForbidden):
        return False
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await client.copy_message(target_id, src_msg.chat.id, src_msg.message_id)
            return True
        except Exception:
            return False
    except Exception:
        return False


async def _broadcast_handler(client, message: Message):
    if not _is_owner(message.from_user.id):
        await message.reply_text(NO_PERMISSION)
        return

    if not message.reply_to_message:
        # determine which usage message to show based on flag
        if message.text and "-user" in message.text:
            await message.reply_text(BROADCAST_USER_USAGE)
        else:
            await message.reply_text(BROADCAST_USAGE)
        return

    is_user = bool(message.text and "-user" in message.text)

    await message.reply_text(BROADCAST_STARTED)

    # load recipients
    group_docs = await get_all_groups()
    user_docs = await get_all_users() if is_user else []

    if not group_docs and not is_user:
        await message.reply_text(BROADCAST_NO_GROUPS)
        return

    if is_user and not user_docs and not group_docs:
        # nothing at all
        await message.reply_text(BROADCAST_NO_USERS)
        await message.reply_text(BROADCAST_NO_GROUPS)
        return

    # broadcast to groups
    group_success = 0
    group_failed = []
    for idx, doc in enumerate(group_docs, start=1):
        chat_id = doc.get("chat_id")
        ok = await _copy_with_retry(client, chat_id, message.reply_to_message)
        if ok:
            group_success += 1
        else:
            group_failed.append(chat_id)
        if idx % 25 == 0:
            await asyncio.sleep(1)

    # broadcast to users if requested
    user_success = 0
    user_failed = []
    if is_user:
        if not user_docs:
            await message.reply_text(BROADCAST_NO_USERS)
        else:
            for idx, doc in enumerate(user_docs, start=1):
                uid = doc.get("user_id")
                ok = await _copy_with_retry(client, uid, message.reply_to_message)
                if ok:
                    user_success += 1
                else:
                    user_failed.append(uid)
                if idx % 25 == 0:
                    await asyncio.sleep(1)

    # send summary
    if is_user:
        summary = (
            f"👤 users: ✅ {user_success} | ❌ {len(user_failed)}\n"
            f"👥 groups: ✅ {group_success} | ❌ {len(group_failed)}"
        )
        await message.reply_text(sc(summary))
    else:
        stats = f"✅ success: {group_success}\n❌ failed: {len(group_failed)}"
        await message.reply_text(sc(stats))

    # build report if there were failures
    report_path = None
    if is_user:
        if user_failed or group_failed:
            report = {
                "broadcast_type": "user+group",
                "users": {
                    "total": len(user_docs),
                    "success": user_success,
                    "failed": len(user_failed),
                    "failed_ids": user_failed,
                },
                "groups": {
                    "total": len(group_docs),
                    "success": group_success,
                    "failed": len(group_failed),
                    "failed_ids": group_failed,
                },
            }
            report_path = "/tmp/failed_report.json"
    else:
        if group_failed:
            report = {
                "total_groups": len(group_docs),
                "success": group_success,
                "failed": len(group_failed),
                "failed_chat_ids": group_failed,
            }
            report_path = "/tmp/failed_report.json"

    if report_path:
        try:
            with open(report_path, "w") as f:
                json.dump(report, f)
            await message.reply_document(report_path, caption=BROADCAST_FAIL_REPORT)
        finally:
            try:
                os.remove(report_path)
            except OSError:
                pass


# register handler
broadcast_handler = filters.command("broadcast")


def register(client):
    client.add_handler(broadcast_handler, _broadcast_handler)
