from senpai_bot.utils.smallcaps import sc

# Broadcast strings
BROADCAST_USAGE = sc("Send a message to reply with /broadcast command")
BROADCAST_GROUPS_USAGE = sc("Reply to a message and use /broadcast")
BROADCAST_USER_USAGE = sc("Reply to a message and use /broadcast -user")
BROADCAST_STARTED = sc("Broadcast started...")
BROADCAST_DONE = sc("Broadcast completed!")
BROADCAST_GROUPS_DONE = sc("Group broadcast done!")
BROADCAST_NO_USERS = sc("No registered users found!")
BROADCAST_NO_GROUPS = sc("No registered groups found!")
BROADCAST_FAIL_REPORT = sc("Failed broadcast report attached below")
NO_PERMISSION = sc("You are not allowed to use this command")

# rank badge definitions
RANK_BADGES = [
    {"min": 0,    "max": 49,   "badge": "🪨 ɴᴏᴏʙ"},
    {"min": 50,   "max": 149,  "badge": "🥉 ʙʀᴏɴᴢᴇ"},
    {"min": 150,  "max": 299,  "badge": "🥈 ꜱɪʟᴠᴇʀ"},
    {"min": 300,  "max": 499,  "badge": "🥇 ɢᴏʟᴅ"},
    {"min": 500,  "max": 999,  "badge": "💎 ᴅɪᴀᴍᴏɴᴅ"},
    {"min": 1000, "max": 1999, "badge": "👑 ʟᴇɢᴇɴᴅ"},
    {"min": 2000, "max": 99999,"badge": "🔱 ꜱᴇɴᴘᴀɪ ɢᴏᴅ"},
]

def get_badge(points: int) -> str:
    for b in RANK_BADGES:
        if b["min"] <= points <= b["max"]:
            return b["badge"]
    return "🔱 ꜱᴇɴᴘᴀɪ ɢᴏᴅ"
