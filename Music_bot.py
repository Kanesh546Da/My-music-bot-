import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls, idle
from pytgcalls.types.input_stream import InputStream, AudioPiped
from yt_dlp import YoutubeDL
from collections import deque

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("music-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

QUEUE = {}  # chat_id: deque([audio_url])
YDL_OPTS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'quiet': True
}

def download_audio(url):
    with YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url'], info['title']

async def start_stream(chat_id: int):
    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return
    url, title = QUEUE[chat_id][0]
    await pytgcalls.join_group_call(
        chat_id,
        InputStream(
            AudioPiped(url)
        ),
        stream_type='local'
    )

@app.on_message(filters.command("play") & filters.group)
async def play(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Send a YouTube link or search term to play.")
    url = message.text.split(None, 1)[1]

    msg = await message.reply("🔍 Fetching audio...")

    try:
        audio_url, title = download_audio(url)
    except Exception as e:
        return await msg.edit(f"❌ Error: {e}")

    chat_id = message.chat.id
    if chat_id not in QUEUE:
        QUEUE[chat_id] = deque()

    QUEUE[chat_id].append((audio_url, title))

    if len(QUEUE[chat_id]) == 1:
        await start_stream(chat_id)
        await msg.edit(f"▶️ Now playing: **{title}**")
    else:
        await msg.edit(f"✅ Added to queue: **{title}**")

@app.on_message(filters.command("skip") & filters.group)
async def skip(_, message: Message):
    chat_id = message.chat.id
    if chat_id in QUEUE and QUEUE[chat_id]:
        QUEUE[chat_id].popleft()
        if QUEUE[chat_id]:
            await start_stream(chat_id)
            await message.reply(f"⏭ Skipped. Now playing: **{QUEUE[chat_id][0][1]}**")
        else:
            await pytgcalls.leave_group_call(chat_id)
            await message.reply("⏹ Queue ended. Left VC.")
    else:
        await message.reply("❌ Nothing to skip.")

@app.on_message(filters.command("pause") & filters.group)
async def pause(_, message: Message):
    await pytgcalls.pause_stream(message.chat.id)
    await message.reply("⏸ Paused.")

@app.on_message(filters.command("resume") & filters.group)
async def resume(_, message: Message):
    await pytgcalls.resume_stream(message.chat.id)
    await message.reply("▶️ Resumed.")

@app.on_message(filters.command("stop") & filters.group)
async def stop(_, message: Message):
    chat_id = message.chat.id
    if chat_id in QUEUE:
        QUEUE.pop(chat_id)
    await pytgcalls.leave_group_call(chat_id)
    await message.reply("⏹ Stopped and left VC.")

@app.on_message(filters.command("queue") & filters.group)
async def queue(_, message: Message):
    chat_id = message.chat.id
    if chat_id in QUEUE and QUEUE[chat_id]:
        msg = "**🎶 Current Queue:**\n"
        for i, song in enumerate(QUEUE[chat_id], 1):
            msg += f"{i}. {song[1]}\n"
        await message.reply(msg)
    else:
        await message.reply("❌ No songs in queue.")

@app.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply("🎵 I'm a Music Bot. Add me to a group and use `/play` to start!")

# Start the bot
async def main():
    await app.start()
    await pytgcalls.start()
    print("Bot is running...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
          
