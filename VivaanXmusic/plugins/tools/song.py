import html
import os

from pyrogram import filters
from pyrogram.types import Message

from VivaanXmusic import YouTube, app
from VivaanXmusic.utils.decorators.language import language
from config import BANNED_USERS


def _extract_song_query(message: Message) -> str:
    if message.command and len(message.command) > 1:
        return " ".join(message.command[1:]).strip()
    if message.reply_to_message:
        return (
            (message.reply_to_message.text or message.reply_to_message.caption or "")
            .strip()
        )
    return ""


@app.on_message(filters.command(["song"]) & ~BANNED_USERS)
@language
async def song_download_command(client, message: Message, _):
    query = (await YouTube.url(message)) or _extract_song_query(message)
    if not query:
        return await app.send_message(
            message.chat.id,
            "Usage: /song <song name or YouTube URL>",
        )
    if await YouTube.exists(query) and ("playlist" in query or "list=" in query):
        return await app.send_message(
            message.chat.id,
            "Playlist links are not supported in /song. Send a single YouTube track or search query.",
        )

    status = await app.send_message(
        message.chat.id,
        "Processing your song request...",
    )

    try:
        title, duration_text, duration_sec, _, video_id = await YouTube.details(query)
        await status.edit_text("Downloading mp3...")
        file_path, _direct = await YouTube.download(video_id, status, videoid=True)
        if not os.path.exists(file_path):
            raise RuntimeError("Downloaded audio file was not found.")

        requested_by = (
            message.from_user.mention if message.from_user else "Unknown User"
        )
        caption = (
            f"<b>Title:</b> {html.escape(title)}\n"
            f"<b>Duration:</b> {html.escape(duration_text or 'Unknown')}\n"
            f"<b>Requested by:</b> {requested_by}"
        )

        await status.edit_text("Uploading mp3...")
        await app.send_audio(
            chat_id=message.chat.id,
            audio=file_path,
            caption=caption,
            duration=duration_sec or None,
            title=title,
        )
        await status.delete()
    except Exception as exc:
        error_message = html.escape(str(exc))[:500] or "Unknown error"
        await status.edit_text(f"Failed to download mp3.\n<code>{error_message}</code>")
