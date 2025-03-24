import os
import tempfile
from googletrans import Translator
from gtts import gTTS
from pydub import AudioSegment
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, ContextTypes,
    CommandHandler, CallbackQueryHandler
)

user_lang_prefs = {}
translator = Translator()
BOT_TOKEN = os.getenv("BOT_TOKEN")

LANG_OPTIONS = {
    "🇫🇷 French": "fr",
    "🇬🇧 English": "en",
    "🇪🇸 Spanish": "es",
    "🇩🇪 German": "de",
    "🇮🇹 Italian": "it",
    "🇵🇹 Portuguese": "pt"
}

def get_lang_keyboard():
    keyboard = [[InlineKeyboardButton(text, callback_data=code)] for text, code in LANG_OPTIONS.items()]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Voice Translator Bot!\nChoose your target language:",
                                    reply_markup=get_lang_keyboard())

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_lang_prefs[query.from_user.id] = query.data
    await query.edit_message_text(text=f"✅ Language set to: {query.data.upper()}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target_lang = user_lang_prefs.get(user_id, "fr")

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        ogg_path = os.path.join(tmpdir, "audio.ogg")
        wav_path = os.path.join(tmpdir, "audio.wav")
        tts_path = os.path.join(tmpdir, "reply.mp3")

        await file.download_to_drive(ogg_path)
        AudioSegment.from_file(ogg_path).export(wav_path, format="wav")

        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
            try:
                text = r.recognize_google(audio)
            except:
                await update.message.reply_text("Couldn't understand the audio 😔")
                return

        detected = translator.detect(text).lang
        translated = translator.translate(text, src=detected, dest=target_lang).text

        tts = gTTS(translated, lang=target_lang)
        tts.save(tts_path)

        await update.message.reply_text(f"🗣 Detected ({detected}) text: {text}\n\n🌐 Translation ({target_lang}): {translated}")
        await update.message.reply_voice(voice=open(tts_path, "rb"))

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("Bot is running with UI...")
    app.run_polling()