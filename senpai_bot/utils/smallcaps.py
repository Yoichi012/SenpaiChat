"""Utility for converting text to Unicode small caps."""

SMALL_MAP = {
    "a": "ᴀ",
    "b": "ʙ",
    "c": "ᴄ",
    "d": "ᴅ",
    "e": "ᴇ",
    "f": "ꜰ",
    "g": "ɢ",
    "h": "ʜ",
    "i": "ɪ",
    "j": "ᴊ",
    "k": "ᴋ",
    "l": "ʟ",
    "m": "ᴍ",
    "n": "ɴ",
    "o": "ᴏ",
    "p": "ᴘ",
    "q": "ǫ",
    "r": "ʀ",
    "s": "ꜱ",
    "t": "ᴛ",
    "u": "ᴜ",
    "v": "ᴠ",
    "w": "ᴡ",
    "x": "x",
    "y": "ʏ",
    "z": "ᴢ",
}


def sc(text: str) -> str:
    """Return a small‑caps version of *text*.

    Only letters a–z are transformed; other characters pass through unchanged.
    Case is ignored by lowercasing before conversion.
    """
    result_chars = []
    for ch in text:
        lower = ch.lower()
        if lower in SMALL_MAP:
            result_chars.append(SMALL_MAP[lower])
        else:
            result_chars.append(ch)
    return "".join(result_chars)
