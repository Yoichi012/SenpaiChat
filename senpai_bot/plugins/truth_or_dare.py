import random
import re
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from senpai_bot import config
from senpai_bot.database.tod_db import (
    get_score,
    add_score,
    save_session,
    complete_session,
    get_active_session,
    get_leaderboard,
    get_global_rank,
    get_group_rank,
    get_monthly_rank,
    get_global_leaderboard,
    get_monthly_leaderboard,
)
from senpai_bot.database.connection import db
from senpai_bot.data.tod_questions import (
    TRUTH_EN,
    TRUTH_HI,
    DARE_EN,
    DARE_HI,
    TRUTH_18,
    DARE_18,
)
from senpai_bot.utils.smallcaps import sc
from senpai_bot.data.strings import get_badge


def is_hindi(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", text))


def _choose_question(lang_list, adult_list, allow_adult: bool) -> str:
    pool = list(lang_list)
    if allow_adult and random.random() < 0.5:
        pool += adult_list
    return random.choice(pool)


async def truth_handler(client, message: Message):
    user = message.from_user
    chat_id = message.chat.id
    if not user:
        return
    active = await get_active_session(chat_id, user.id)
    if active:
        await message.reply(sc("complete your pending dare first! use /done"))
        return
    text = message.text or ""
    lang_hi = is_hindi(text)
    allow_adult = False
    if message.chat.type == "private":
        allow_adult = config.TOD_ADULT_DM
    else:
        allow_adult = chat_id in config.TOD_ADULT_GROUPS
    if lang_hi:
        question = _choose_question(TRUTH_HI, TRUTH_18, allow_adult)
    else:
        question = _choose_question(TRUTH_EN, TRUTH_18, allow_adult)
    await save_session(chat_id, user.id, "truth", question, None)
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ᴅᴏɴᴇ! +5 ᴘᴛꜱ", callback_data=f"tod_done_truth_{user.id}")]
    ])
    await message.reply(
        sc(f"🎭 ᴛʀᴜᴛʜ ᴛɪᴍᴇ!\n{user.mention}, ᴀɴꜱᴡᴇʀ ᴛʜɪꜱ:\n❓ {question}\nᴜꜱᴇ /done ᴡʜᴇɴ ᴀɴꜱᴡᴇʀᴇᴅ ᴛᴏ ɢᴇᴛ +5 ᴘᴏɪɴᴛꜱ! ✨"),
        reply_markup=markup,
    )


async def dare_handler(client, message: Message):
    user = message.from_user
    chat_id = message.chat.id
    if not user:
        return
    active = await get_active_session(chat_id, user.id)
    if active:
        await message.reply(sc("complete your pending dare first! use /done"))
        return
    text = message.text or ""
    lang_hi = is_hindi(text)
    allow_adult = False
    if message.chat.type == "private":
        allow_adult = config.TOD_ADULT_DM
    else:
        allow_adult = chat_id in config.TOD_ADULT_GROUPS
    if lang_hi:
        question = _choose_question(DARE_HI, DARE_18, allow_adult)
    else:
        question = _choose_question(DARE_EN, DARE_18, allow_adult)
    expire = datetime.utcnow() + timedelta(minutes=config.TOD_DARE_TIMER)
    await save_session(chat_id, user.id, "dare", question, expire)
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ᴅᴏɴᴇ! +10 ᴘᴛꜱ", callback_data=f"tod_done_dare_{user.id}"),
            InlineKeyboardButton("❌ ꜱᴋɪᴘ (-5 ᴘᴛꜱ)", callback_data=f"tod_skip_{user.id}"),
        ]
    ])
    await message.reply(
        sc(f"🔥 ᴅᴀʀᴇ ᴛɪᴍᴇ!\n{user.mention}, ᴄᴀɴ ʏᴏᴜ ᴅᴏ ᴛʜɪꜱ? 😈\n💀 {question}\n⏱ ʏᴏᴜ ʜᴀᴠᴇ {config.TOD_DARE_TIMER} ᴍɪɴᴜᴛᴇꜱ!\nᴜꜱᴇ /done ᴡʜᴇɴ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴛᴏ ɢᴇᴛ +10 ᴘᴏɪɴᴛꜱ! 🏆"),
        reply_markup=markup,
    )


async def done_handler(client, message: Message):
    user = message.from_user
    chat_id = message.chat.id
    if not user:
        return
    session = await get_active_session(chat_id, user.id)
    if not session:
        await message.reply(sc("you have no active truth or dare!"))
        return
    # check expiry for dare
    if session.get("type") == "dare":
        exp = session.get("expire_at")
        if exp and datetime.utcnow() > exp:
            # expired: penalty -5 points
            await complete_session(chat_id, user.id)
            # deduct points
            doc = await get_score(user.id, chat_id)
            new_pts = max(doc.get("points", 0) - 5, 0)
            await db["tod_scores"].update_one(
                {"user_id": user.id, "chat_id": chat_id},
                {"$set": {"points": new_pts}},
            )
            await message.reply(sc("time up! dare expired. -5 points penalty ⏰"))
            return
    # mark complete and add score
    await complete_session(chat_id, user.id)
    t = session.get("type")
    pts = 5 if t == "truth" else 10
    await add_score(user.id, chat_id, t, user.username, user.first_name)
    await message.reply(sc(f"✅ ᴡᴇʟʟ ᴅᴏɴᴇ {user.mention}!\n+{pts} ᴘᴏɪɴᴛꜱ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ꜱᴄᴏʀᴇ 🏆"))


async def callback_query_handler(client, query):
    data = query.data or ""
    parts = data.split("_")
    if len(parts) < 4:
        return
    action = parts[1]
    typ = parts[2]
    uid = int(parts[3])
    user = query.from_user
    if not user or user.id != uid:
        await query.answer(sc("ʏᴇ ᴛᴇʀᴀ ɴʜɪ ʜᴀɪ! 😂"), show_alert=True)
        return
    chat_id = query.message.chat.id
    if action == "done":
        # behave like /done
        await done_handler(client, query.message)
        await query.answer()
    elif action == "skip":
        # penalty
        await complete_session(chat_id, uid)
        # deduct 5 points
        doc = await get_score(uid, chat_id)
        new_pts = max(doc.get("points", 0) - 5, 0)
        await db["tod_scores"].update_one(
            {"user_id": uid, "chat_id": chat_id},
            {"$set": {"points": new_pts}},
        )
        await query.message.reply(sc("dare skipped! -5 points. coward mode activated 😂"))
        await query.answer()


async def score_handler(client, message: Message):
    user = message.from_user
    chat_id = message.chat.id
    if not user:
        return
    doc = await get_score(user.id, chat_id)
    await message.reply(
        sc(f"🏅 ʏᴏᴜʀ ꜱᴄᴏʀᴇ\n👤 {user.mention}\n✅ ᴛʀᴜᴛʜꜱ: {doc['truths_done']} (+{doc['truths_done']*5})\n💀 ᴅᴀʀᴇꜱ: {doc['dares_done']} (+{doc['dares_done']*10})\n⭐ ᴛᴏᴛᴀʟ ᴘᴏɪɴᴛꜱ: {doc['points']}"),
    )


async def leaderboard_handler(client, message: Message):
    chat_id = message.chat.id
    board = await get_leaderboard(chat_id)
    lines = ["🏆 ᴛᴏᴘ 10 — ᴛʀᴜᴛʜ ᴏʀ ᴅᴀʀᴇ"]
    for entry in board:
        uid = entry["user_id"]
        pts = entry["points"]
        badge = get_badge(pts)
        lines.append(f"[{uid}](tg://user?id={uid}) — {pts} ᴘᴛꜱ {badge}")
    await message.reply(sc("\n".join(lines)))



async def rank_handler(client, message: Message):
    user = message.from_user
    if not user:
        return
    chat_id = message.chat.id
    # fetch ranks
    global_rank = await get_global_rank(user.id)
    monthly_rank = await get_monthly_rank(user.id)
    badge = get_badge(global_rank["points"])
    # fetch global record for counts
    gdoc = await db[GLOBAL].find_one({"user_id": user.id})
    g_truths = gdoc.get("truths_done", 0) if gdoc else 0
    g_dares = gdoc.get("dares_done", 0) if gdoc else 0
    group_text = ""
    if message.chat.type != "private":
        group_rank = await get_group_rank(user.id, chat_id)
        group_text = f"📍 ɢʀᴏᴜᴘ ʀᴀɴᴋ\n🏆 #{group_rank['rank']} ᴏꜰ {group_rank['total_users']} ᴘʟᴀʏᴇʀꜱ\n⭐ {group_rank['points']} ᴘᴏɪɴᴛꜱ\n"
    if global_rank["points"] == 0 and monthly_rank["points"] == 0 and not group_text:
        await message.reply(sc("you haven't played yet! use /truth or /dare to start 🎮"))
        return
    # build message
    text = (
        f"🏅 ʀᴀɴᴋ ᴄᴀʀᴅ — {user.mention}\n{badge}\n━━━━━━━━━━━━━━━━━━\n"
        f"{group_text}🌍 ɢʟᴏʙᴀʟ ʀᴀɴᴋ\n"
        f"🏆 #{global_rank['rank']} ᴏꜰ {global_rank['total_users']} ᴘʟᴀʏᴇʀꜱ\n"
        f"⭐ {global_rank['points']} ᴘᴏɪɴᴛꜱ\n"
        f"📅 ᴍᴏɴᴛʜʟʏ ʀᴀɴᴋ ({monthly_rank['month']})\n"
        f"🏆 #{monthly_rank['rank']} ᴏꜰ {monthly_rank['total_users']} ᴘʟᴀʏᴇʀꜱ\n"
        f"⭐ {monthly_rank['points']} ᴘᴏɪɴᴛꜱ\n"
        f"✅ ᴛʀᴜᴛʜꜱ: {g_truths} | 💀 ᴅᴀʀᴇꜱ: {g_dares}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    await message.reply(sc(text))

async def rank_top_handler(client, message: Message):
    parts = message.text.split()
    mode = parts[2] if len(parts) > 2 else ""
    if mode == "month":
        board = await get_monthly_leaderboard()
        header = "🌍 ᴍᴏɴᴛʜʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ"
    elif mode == "group" and message.chat.type != "private":
        # reuse existing leaderboard_handler
        await leaderboard_handler(client, message)
        return
    else:
        board = await get_global_leaderboard()
        header = "🌍 ɢʟᴏʙᴀʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ"
    lines = [header]
    rank = 1
    user_rank = None
    for entry in board:
        uid = entry["user_id"]
        pts = entry["points"]
        badge = get_badge(pts)
        lines.append(f"{rank}. [{uid}](tg://user?id={uid}) — {pts} ᴘᴛꜱ {badge}")
        if message.from_user.id == uid:
            user_rank = rank
        rank += 1
    if user_rank:
        lines.append(f"ʏᴏᴜʀ ʀᴀɴᴋ: #{user_rank} ꜱᴛᴀʀ ꜰɪɢʜᴛɪɴɢ! 💪")
    await message.reply(sc("\n".join(lines)))


def register(client):
    # add command handlers
    client.add_handler(filters.command("truth"), truth_handler, group=0)
    client.add_handler(filters.command("dare"), dare_handler, group=0)
    client.add_handler(filters.command("done"), done_handler, group=0)
    client.add_handler(filters.command("score"), score_handler, group=0)
    client.add_handler(filters.command("topleaderboard"), leaderboard_handler, group=0)
    client.add_handler(filters.command("rank"), rank_handler, group=0)
    client.add_handler(filters.command("rank") & filters.regex(r"^rank top"), rank_top_handler, group=0)
    client.add_handler(filters.callback_query(), callback_query_handler, group=0)
