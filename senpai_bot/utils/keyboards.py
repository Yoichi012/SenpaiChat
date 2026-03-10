from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from senpai_bot import config


def main_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    buttons = []
    # row 1 add me
    if bot_username:
        buttons.append(
            [InlineKeyboardButton("👾 ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ 👾", url=f"t.me/{bot_username}")]
        )
    # row 2 support and channel
    row2 = []
    if config.SUPPORT_GROUP:
        row2.append(InlineKeyboardButton("🫂 ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=config.SUPPORT_GROUP))
    if config.CHANNEL_LINK:
        row2.append(InlineKeyboardButton("📢 ᴄʜᴀɴɴᴇʟ", url=config.CHANNEL_LINK))
    if row2:
        buttons.append(row2)
    # row 3 owner and friends
    row3 = []
    if config.OWNER_LINK:
        row3.append(InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", url=config.OWNER_LINK))
    row3.append(InlineKeyboardButton("👥 ꜰʀɪᴇɴᴅꜱ", callback_data="cb_friends"))
    buttons.append(row3)
    return InlineKeyboardMarkup(buttons)


def friends_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for item in config.FRIEND_GCS:
        name = item.get("name")
        link = item.get("link")
        if name and link:
            rows.append([InlineKeyboardButton(name, url=link)])
    # back button
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="cb_back_main")])
    return InlineKeyboardMarkup(rows)
