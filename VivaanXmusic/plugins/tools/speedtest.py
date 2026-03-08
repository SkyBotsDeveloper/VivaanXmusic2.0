import asyncio

import speedtest
from pyrogram import filters
from pyrogram.types import Message

from VivaanXmusic import app
from VivaanXmusic.misc import SUDOERS
from VivaanXmusic.utils.decorators.language import language


def testspeed(stage, test=None):
    if stage == "init":
        return speedtest.Speedtest()
    if stage == "server":
        test.get_best_server()
        return test
    if stage == "download":
        test.download()
        return test
    if stage == "upload":
        test.upload()
        return test
    if stage == "share":
        test.results.share()
        return test
    if stage == "result":
        return test.results.dict()
    raise ValueError(f"Unknown speedtest stage: {stage}")


@app.on_message(filters.command(["speedtest", "spt"]) & SUDOERS)
@language
async def speedtest_function(client, message: Message, _):
    m = await message.reply_text(_["server_11"])
    loop = asyncio.get_running_loop()
    try:
        test = await loop.run_in_executor(None, testspeed, "init", None)
        await loop.run_in_executor(None, testspeed, "server", test)
        await m.edit_text(_["server_12"])
        await loop.run_in_executor(None, testspeed, "download", test)
        await m.edit_text(_["server_13"])
        await loop.run_in_executor(None, testspeed, "upload", test)
        await loop.run_in_executor(None, testspeed, "share", test)
        result = await loop.run_in_executor(None, testspeed, "result", test)
        await m.edit_text(_["server_14"])
    except Exception as e:
        return await m.edit_text(f"<code>{e}</code>")
    client_data = result.get("client", {})
    server_data = result.get("server", {})
    output = _["server_15"].format(
        client_data.get("isp", "Unknown"),
        client_data.get("country", "Unknown"),
        server_data.get("name", "Unknown"),
        server_data.get("country", "Unknown"),
        server_data.get("cc", "Unknown"),
        server_data.get("sponsor", "Unknown"),
        server_data.get("latency", "Unknown"),
        result.get("ping", "Unknown"),
    )
    share_link = result.get("share")
    if share_link:
        await message.reply_photo(photo=share_link, caption=output)
    else:
        await message.reply_text(output)
    await m.delete()
