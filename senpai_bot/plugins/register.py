from pyrogram import filters
from pyrogram.errors import ChatWriteForbidden
from pyrogram.types import Message

from senpai_bot.database.users import upsert_user, upsert_group


async def _private_message_reg(client, message: Message):
    # ignore bots
    u = message.from_user
    if not u or u.is_bot:
        return
    await upsert_user(u.id, u.username, u.first_name)


async def _group_new_member_reg(client, message: Message):
    # if bot added to group, register group
    new_members = getattr(message, "new_chat_members", [])
    if not new_members:
        return
    me = await client.get_me()
    for member in new_members:
        if member.id == me.id:
            try:
                chat = message.chat
                await upsert_group(chat.id, chat.title, chat.username)
            except ChatWriteForbidden:
                pass
            break


async def _group_message_reg(client, message: Message):
    # register group itself
    chat = message.chat
    try:
        await upsert_group(chat.id, chat.title, chat.username)
    except Exception:
        pass

    # register sender as a user
    u = message.from_user
    if not u or u.is_bot:
        return
    try:
        await upsert_user(u.id, u.username, u.first_name)
    except Exception:
        pass


def register(client):
    # run early (group=-1)
    client.add_handler(
        filters.private & filters.incoming,
        _private_message_reg,
        group=-1,
    )
    client.add_handler(
        filters.group & filters.new_chat_members,
        _group_new_member_reg,
        group=-1,
    )
    client.add_handler(
        filters.group,
        _group_message_reg,
        group=-1,
    )
