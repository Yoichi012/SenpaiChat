from pyrogram import filters
from pyrogram.types import CallbackQuery, Message

from senpai_bot import config, messages
from senpai_bot.database import users as user_db
from senpai_bot.utils import keyboards, helpers


async def _send_welcome_media(client, chat_id):
    if config.START_MEDIA:
        # helpers.send_media returns False on invalid/empty
        await helpers.send_media(client, chat_id, config.START_MEDIA)


async def _start_handler(client, message: Message):
    # differentiate between private and group
    if message.chat.type == "private":
        await _send_welcome_media(client, message.chat.id)
        await message.reply_text(
            messages.DM_WELCOME or "", reply_markup=keyboards.main_keyboard(client.username)
        )
        chat_type = "private"
    else:
        if config.SEND_MEDIA_IN_GROUP:
            await _send_welcome_media(client, message.chat.id)
        group_name = message.chat.title or "this group"
        await message.reply_text(
            messages.format_group_welcome(group_name),
            reply_markup=keyboards.main_keyboard(client.username),
        )
        chat_type = "group"

    await user_db.upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        chat_type,
    )


async def _cb_friends(client, query: CallbackQuery):
    kb = keyboards.friends_keyboard()
    if not kb.keyboard or len(kb.keyboard) == 0:
        text = "ɴᴏ ɢʀᴏᴜᴘꜱ ʏᴇᴛ 😅"
        await query.message.edit_text(text, reply_markup=keyboards.main_keyboard(client.username))
    else:
        await query.message.edit_text(query.message.text or "", reply_markup=kb)
    await query.answer()


async def _cb_back_main(client, query: CallbackQuery):
    await query.message.edit_text(messages.DM_WELCOME or "", reply_markup=keyboards.main_keyboard(client.username))
    await query.answer()


def register(client):
    client.add_handler(
        filters.command("start") & (filters.chat_type.private | filters.chat_type.groups),
        _start_handler,
        group=0,
    )
    client.add_handler(
        filters.callback_query(filters.regex("^cb_friends$")),
        _cb_friends,
        group=0,
    )
    client.add_handler(
        filters.callback_query(filters.regex("^cb_back_main$")),
        _cb_back_main,
        group=0,
    )
