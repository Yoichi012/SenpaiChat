import asyncio
import logging
import os
import random

from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message

from groq.cloud.core.core import ChatCompletion

from senpai_bot import config
from senpai_bot.database.chat_history import add_message, get_history, clear_history
from senpai_bot.utils.smallcaps import sc
from senpai_bot.utils.sticker_helper import (
    save_user_sticker_pack,
    get_user_sticker,
    get_bot_sticker,
    save_bot_pack,
)

# ensure Groq API key is available to library
os.environ.setdefault("GROQ_SECRET_ACCESS_KEY", config.GROQ_API_KEY)

# logging
logger = logging.getLogger(__name__)


async def get_ai_reply(user_id: int, user_message: str) -> str:
    # prepare history pairs for ChatCompletion
    history = await get_history(user_id)
    pairs = []
    temp_user = None
    for msg in history:
        if msg.get("role") == "user":
            temp_user = msg.get("content")
        elif msg.get("role") == "assistant" and temp_user is not None:
            pairs.append((temp_user, msg.get("content")))
            temp_user = None

    # instantiate client per request to avoid cross-user state
    client = ChatCompletion(config.GROQ_MODEL)
    client.set_system_prompt(config.AI_PERSONA)
    if pairs:
        client.update_history(pairs)

    def call_api():
        return client.send_chat(
            user_message,
            max_tokens=300,
            temperature=0.85,
        )

    try:
        response = call_api()
    except Exception as e:
        msg = str(e).lower()
        logger.exception("groq call failed")
        if "timeout" in msg:
            await asyncio.sleep(2)
            try:
                response = call_api()
            except Exception:
                return sc("senpai is thinking... try again!")
        elif "rate" in msg or "429" in msg:
            await asyncio.sleep(5)
            try:
                response = call_api()
            except Exception:
                return sc("senpai is thinking... try again!")
        else:
            return sc("senpai is thinking... try again!")
    # response may be tuple (text, request_id, stats) or a simple string
    reply = None
    if isinstance(response, tuple):
        reply = response[0]
    else:
        reply = response
    if not reply:
        return sc("hmm... senpai got confused, say that again?")
    # save history
    try:
        await add_message(user_id, "user", user_message)
        await add_message(user_id, "assistant", reply)
    except Exception:
        pass
    return reply


async def maybe_send_sticker(client, message: Message, user_id: int) -> bool:
    """Send a sticker based on random chance. Returns True if sticker was sent."""
    sent = False
    # user just sent sticker?
    if message.sticker:
        if random.random() < 0.6:
            # try user's pack first
            file_id = await get_user_sticker(user_id)
            if not file_id:
                file_id = await get_bot_sticker()
            if file_id:
                try:
                    await message.reply_sticker(file_id)
                    sent = True
                except Exception:
                    pass
    else:
        if random.random() < 0.15:
            file_id = await get_bot_sticker()
            if file_id:
                try:
                    await message.reply_sticker(file_id)
                    sent = True
                except Exception:
                    pass
    return sent


async def _private_handler(client, message: Message):
    u = message.from_user
    if not u or u.is_bot:
        return
    text = message.text or message.caption or ""
    if not text:
        return
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    reply = await get_ai_reply(u.id, text)
    await maybe_send_sticker(client, message, u.id)
    await message.reply(reply)


async def _group_handler(client, message: Message):
    u = message.from_user
    if not u or u.is_bot:
        return
    text = message.text or message.caption or ""
    if not text:
        return
    me = await client.get_me()
    lower = text.lower()
    trigger = False
    if "senpai" in lower:
        trigger = True
    if f"@{config.BOT_USERNAME}".lower() in lower:
        trigger = True
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == me.id:
        trigger = True
    if not trigger:
        return
    # clean triggers
    cleaned = lower.replace("senpai", "").replace(f"@{config.BOT_USERNAME}".lower(), "").strip()
    if not cleaned:
        cleaned = text
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    reply = await get_ai_reply(u.id, cleaned)
    await maybe_send_sticker(client, message, u.id)
    await message.reply(reply)


async def _sticker_handler(client, message: Message):
    u = message.from_user
    if not u or u.is_bot:
        return
    pack_name = message.sticker.set_name
    try:
        stickerset = await client.get_sticker_set(pack_name)
        file_ids = [s.file_id for s in stickerset.stickers]
        await save_user_sticker_pack(u.id, pack_name, file_ids)
    except Exception:
        pass
    # maybe send sticker as response
    await maybe_send_sticker(client, message, u.id)
    # ai text reply (use emoji or word)
    user_message = message.sticker.emoji or "sticker"
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    reply = await get_ai_reply(u.id, user_message)
    await message.reply(reply)


async def _reset_handler(client, message: Message):
    await clear_history(message.from_user.id)
    await message.reply(sc("memory cleared! fresh start senpai mode on 🔄"))


async def _loadstickers_handler(client, message: Message):
    if str(message.from_user.id) != str(config.OWNER_ID):
        await message.reply(sc("you can't do that"))
        return
    try:
        pack = await client.get_sticker_set(config.BOT_STICKER_PACK)
        file_ids = [s.file_id for s in pack.stickers]
        await save_bot_pack(file_ids)
        await message.reply(sc(f"loaded {len(file_ids)} stickers"))
    except Exception:
        await message.reply(sc("failed to load stickers"))


def register(client):
    client.add_handler(filters.private & ~filters.command & ~filters.sticker, _private_handler)
    client.add_handler(filters.group & ~filters.command & ~filters.sticker, _group_handler)
    client.add_handler(filters.sticker, _sticker_handler)
    client.add_handler(filters.command("reset") & filters.private, _reset_handler)
    client.add_handler(filters.command("loadstickers"), _loadstickers_handler)
