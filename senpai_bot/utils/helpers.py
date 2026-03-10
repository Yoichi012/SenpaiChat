from typing import Union, List
from pyrogram import Client
from pyrogram.types import InputMediaPhoto, InputMediaVideo


def detect_media_type(url: str) -> str:
    lower = url.lower()
    if any(lower.endswith(ext) for ext in (".mp4", ".mov", ".webm")):
        return "video"
    return "photo"


def is_video(url: str) -> bool:
    return detect_media_type(url) == "video"


async def send_media(client: Client, chat_id: Union[int, str], media: Union[str, List[str]]):
    """Send a single url or list of urls to a chat.

    Returns False if nothing was sent.
    """
    if not media:
        return False

    # normalize
    if isinstance(media, str):
        media_list = [media]
    else:
        media_list = media

    if not media_list:
        return False

    try:
        if len(media_list) == 1:
            url = media_list[0]
            if is_video(url):
                await client.send_video(chat_id, url)
            else:
                await client.send_photo(chat_id, url)
        else:
            inputs = []
            for url in media_list:
                if is_video(url):
                    inputs.append(InputMediaVideo(url))
                else:
                    inputs.append(InputMediaPhoto(url))
            await client.send_media_group(chat_id, inputs)
        return True
    except Exception:
        # silently fail
        return False
