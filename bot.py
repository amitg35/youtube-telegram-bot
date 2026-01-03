import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import yt_dlp

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

ydl_opts_info = {
    "quiet": True,
    "skip_download": True
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Send any YouTube link\n\nI will give you all video & audio download options."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title")
        thumb = info.get("thumbnail")

        keyboard = [
            [InlineKeyboardButton("🎥 4K (2160p)", callback_data=f"v|2160|{url}")],
            [InlineKeyboardButton("🎥 1440p", callback_data=f"v|1440|{url}")],
            [InlineKeyboardButton("🎥 1080p", callback_data=f"v|1080|{url}")],
            [InlineKeyboardButton("🎥 720p", callback_data=f"v|720|{url}")],
            [InlineKeyboardButton("🎥 480p", callback_data=f"v|480|{url}")],
            [InlineKeyboardButton("🎵 MP3", callback_data=f"a|mp3|{url}")],
            [InlineKeyboardButton("🎵 M4A", callback_data=f"a|m4a|{url}")]
        ]

        await update.message.reply_photo(
            photo=thumb,
            caption=f"📌 *{title}*\n\nChoose quality:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text("❌ Invalid or unsupported link")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode, quality, url = query.data.split("|")

    ydl_opts = {
        "outtmpl": "download.%(ext)s",
        "quiet": True
    }

    if mode == "v":
        ydl_opts["format"] = f"bestvideo[height<={quality}]+bestaudio/best"
    else:
        ydl_opts["format"] = "bestaudio"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": quality
        }]

    try:
        await query.edit_message_caption("⏳ Downloading...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file = next(f for f in os.listdir() if f.startswith("download"))

        await context.bot.send_document(
            chat_id=query.message.chat.id,
            document=open(file, "rb")
        )

        os.remove(file)

    except Exception:
        await query.edit_message_caption("❌ Download failed")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(download))

    app.run_polling()

if __name__ == "__main__":
    main()
          
