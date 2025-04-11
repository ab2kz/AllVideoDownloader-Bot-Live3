import os
import socket
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from tinydb import TinyDB, Query
from collections import Counter

BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_LIMIT = 250
ADMIN_ID = 7025548681  # Replace with your actual admin ID

db = TinyDB("users.json")
User = Query()

translations = {
    "download_timeout": {
        "en": "⌛ Download timed out. The video may be too large.",
        "es": "⌛ Tiempo de descarga agotado. El video puede ser demasiado grande.",
        "fr": "⌛ Délai de téléchargement dépassé. La vidéo est peut-être trop volumineuse.",
        "ar": "⌛ انتهت مهلة التنزيل. قد يكون الفيديو كبيرًا جدًا.",
        "zh": "⌛ 下载超时。视频可能太大。",
        "hi": "⌛ डाउनलोड टाइम आउट। वीडियो बहुत बड़ा हो सकता है।"
    },
    "downloading": {
        "en": "⏳ Downloading your video...",
        "es": "⏳ Descargando tu video...",
        "fr": "⏳ Téléchargement de votre vidéo...",
        "ar": "⏳ جاري تحميل الفيديو...",
        "zh": "⏳ 正在下载视频...",
        "hi": "⏳ वीडियो डाउनलोड हो रहा है..."
    },
    "download_error": {
        "en": "❌ Sorry, couldn't download that video.\nError: {error}",
        "es": "❌ Lo siento, no pude descargar ese video.\nError: {error}",
        "fr": "❌ Désolé, impossible de télécharger cette vidéo.\nErreur: {error}",
        "ar": "❌ عذراً، لم نتمكن من تحميل الفيديو.\nخطأ: {error}",
        "zh": "❌ 抱歉，无法下载该视频。\n错误：{error}",
        "hi": "❌ क्षमा करें, वीडियो डाउनलोड नहीं कर सके।\nत्रुटि: {error}"
    },
    "premium_limit": {
        "en": "🔒 You've reached your free downloads limit.\nUpgrade to Premium for unlimited downloads!",
        "es": "🔒 Has alcanzado tu límite de descargas gratuitas.\n¡Actualiza a Premium para descargas ilimitadas!",
        "fr": "🔒 Vous avez atteint votre limite de téléchargements gratuits.\nPassez à Premium pour des téléchargements illimités !",
        "ar": "🔒 لقد وصلت إلى حد التنزيلات المجانية.\nقم بالترقية إلى Premium للحصول على تنزيلات غير محدودة!",
        "zh": "🔒 您已达到免费下载限制。\n升级到Premium享受无限下载！",
        "hi": "🔒 आपने अपनी मुफ्त डाउनलोड सीमा तक पहुंच गए हैं।\nअसीमित डाउनलोड के लिए Premium पर अपग्रेड करें!"
    },
    "start_msg": {
        "en": "👋 Welcome to AllVideoDownloader!\n\nSend me any video link from:\n\n- TikTok\n- Instagram\n- Facebook\n- X (Twitter)\n- YouTube Shorts\n- Snapchat\n- LinkedIn\n- and more...\n\nI'll download it and send it right back — fast and simple.",
        "es": "👋 ¡Bienvenido a AllVideoDownloader!\n\nEnvíame cualquier enlace de video de:\n\n- TikTok\n- Instagram\n- Facebook\n- X (Twitter)\n- YouTube Shorts\n- Snapchat\n- LinkedIn\n- y más...\n\nLo descargaré y te lo enviaré de vuelta — rápido y simple.",
        "fr": "👋 Bienvenue sur AllVideoDownloader!\n\nEnvoyez-moi n'importe quel lien vidéo de:\n\n- TikTok\n- Instagram\n- Facebook\n- X (Twitter)\n- YouTube Shorts\n- Snapchat\n- LinkedIn\n- et plus...\n\nJe le téléchargerai et vous le renverrai — rapide et simple.",
        "ar": "أهلًا بك!",
        "zh": "欢迎！",
        "hi": "स्वागत है!",
        "pt": "Bem-vindo!",
        "ru": "Добро пожаловать!",
        "bn": "আপনাকে স্বাগতম!",
        "ur": "خوش آمدید!",
        "ja": "ようこそ！",
        "yo": "Ẹ kú oríire!",
        "de": "Willkommen!",
        "tr": "Hoş geldiniz!",
        "ko": "환영합니다!",
        "it": "Benvenuto!",
        "vi": "Chào mừng!",
        "fa": "خوش آمدید!",
        "sw": "Karibu!",
        "ha": "Maraba!",
        "tl": "Maligayang pagdating!",
        "ms": "Selamat datang!",
        "th": "ยินดีต้อนรับ!",
        "pl": "Witamy!",
        "uk": "Ласкаво просимо!",
        "id": "Selamat datang!",
        "nl": "Welkom!"
    },
    "help_msg": {
        "en": "ℹ️ *How to Use Me*\n\n1. Send me any video link from social media.\n2. I'll download and send the video back.\n3. Use /account to check your usage or /language to change your language.\n\nCommands:\n/account – check your usage\n/upgrade – unlock Premium features\n/language – set language\n/translate – switch language anytime",
        "es": "ℹ️ *Cómo Usarme*\n\n1. Envíame cualquier enlace de video de redes sociales.\n2. Descargaré y te enviaré el video.\n3. Usa /account para ver tu uso o /language para cambiar tu idioma.\n\nComandos:\n/account – ver tu uso\n/upgrade – desbloquear Premium\n/language – configurar idioma\n/translate – cambiar idioma",
        "fr": "ℹ️ *Comment m'utiliser*\n\n1. Envoyez-moi un lien vidéo des réseaux sociaux.\n2. Je téléchargerai et vous renverrai la vidéo.\n3. Utilisez /account pour vérifier votre utilisation ou /language pour changer de langue.\n\nCommandes:\n/account – vérifier l'utilisation\n/upgrade – débloquer Premium\n/language – définir la langue\n/translate – changer de langue",
        "ar": "كيفية استخدام هذا البوت...",
        "zh": "如何使用这个机器人...",
        "hi": "इस बॉट का उपयोग कैसे करें...",
        "pt": "Como usar este bot...",
        "ru": "Как использовать этого бота...",
        "bn": "এই বট কীভাবে ব্যবহার করবেন...",
        "ur": "اس بوٹ کا استعمال کیسے کریں...",
        "ja": "このボットの使い方...",
        "yo": "Báwo ni a ṣe lo bot yii...",
        "de": "Wie man diesen Bot benutzt...",
        "tr": "Bu botu nasıl kullanırsınız...",
        "ko": "이 봇을 사용하는 방법...",
        "it": "Come usare questo bot...",
        "vi": "Cách sử dụng bot này...",
        "fa": "چگونه از این ربات استفاده کنیم...",
        "sw": "Jinsi ya kutumia bot hii...",
        "ha": "Yadda ake amfani da wannan bot...",
        "tl": "Paano gamitin ang bot na ito...",
        "ms": "Cara menggunakan bot ini...",
        "th": "วิธีใช้บอทนี้...",
        "pl": "Jak korzystać z tego bota...",
        "uk": "Як використовувати цього бота...",
        "id": "Cara menggunakan bot ini...",
        "nl": "Hoe gebruik je deze bot..."
    },
    "account_info": {
        "en": "👤 *Account Info*\n• Downloads used: {downloads}\n• Remaining: {remaining}\n• Status: {status}",
        "es": "👤 *Información de Cuenta*\n• Descargas usadas: {downloads}\n• Restantes: {remaining}\n• Estado: {status}",
        "fr": "👤 *Informations du Compte*\n• Téléchargements utilisés: {downloads}\n• Restants: {remaining}\n• Statut: {status}",
        "ar": "معلومات الحساب...",
        "zh": "帐户信息...",
        "hi": "खाता जानकारी...",
        "pt": "Informações da conta...",
        "ru": "Информация об аккаунте...",
        "bn": "অ্যাকাউন্ট তথ্য...",
        "ur": "اکاؤنٹ کی معلومات...",
        "ja": "アカウント情報...",
        "yo": "Àwọn àlàyé nípa akàwùntì...",
        "de": "Kontoinformationen...",
        "tr": "Hesap Bilgileri...",
        "ko": "계정 정보...",
        "it": "Informazioni sull'account...",
        "vi": "Thông tin tài khoản...",
        "fa": "اطلاعات حساب...",
        "sw": "Taarifa za akaunti...",
        "ha": "Bayanan Asusu...",
        "tl": "Impormasyon ng account...",
        "ms": "Maklumat akaun...",
        "th": "ข้อมูลบัญชี...",
        "pl": "Informacje o koncie...",
        "uk": "Інформація про обліковий запис...",
        "id": "Informasi akun...",
        "nl": "Accountgegevens..."
    }
}


def generate_filename():
    import random, string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '.mp4'

import asyncio
import concurrent.futures
from functools import partial
from collections import defaultdict
from asyncio import Queue

# Create download queues for each user
download_queues = defaultdict(lambda: Queue(maxsize=5))
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

async def download_video_async(url, filename):
    loop = asyncio.get_event_loop()
    ydl_opts = {
        'format': 'bv*[vcodec^=avc1][ext=mp4]+ba[acodec^=mp4a][ext=m4a]/b[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'outtmpl': filename,
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True,
        'socket_timeout': 120,
        'nthreads': 8,
        'concurrent_fragment_downloads': 8,
        'retries': 15,
        'file_access_retries': 15,
        'fragment_retries': 15,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        'max_filesize': 2147483648,  # 2GB limit
        'external_downloader': 'aria2c',
        'external_downloader_args': ['--max-tries=10', '--retry-wait=3', '--max-concurrent-downloads=8'],
        'postprocessor_args': ['-err_detect', 'ignore_err']
    }

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info or not os.path.exists(filename):
                raise Exception("Download failed or file not found.")
            return filename

    try:
        return await loop.run_in_executor(executor, _download)
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm you're not a bot" in error_msg:
            raise Exception("This video requires sign-in to download. Try a different one.")
        elif isinstance(e, socket.timeout):
            raise Exception("Download timed out. The video may be too large or slow.")
        else:
            raise Exception(f"Download error: {error_msg}")

async def process_download_queue(user_id, update, context):
    queue = download_queues[user_id]
    while True:
        try:
            url, lang, status_message = await queue.get()
            try:
                filename = generate_filename()
                file_path = await download_video_async(url, filename)
                
                await status_message.edit_text("✅ Download complete! Sending video...")
                # Check file size
                file_size = os.path.getsize(file_path)
                telegram_limit = 50 * 1024 * 1024  # 50MB Telegram limit

                try:
                    if file_size > telegram_limit:
                        info = yt_dlp.YoutubeDL().extract_info(url, download=False)
                        video_url = info.get('webpage_url') or info.get('url')
                        await update.message.reply_text(
                            f"⚠️ Video is too large to send ({file_size/(1024*1024):.1f}MB).\n"
                            f"Watch it here: {video_url}"
                        )
                    else:
                        with open(file_path, 'rb') as video:
                            await update.message.reply_document(video)
                except Exception as e:
                    error_msg = str(e)
                    if "413" in error_msg:
                        await update.message.reply_text("⚠️ File too large for Telegram. Try a shorter video.")
                    else:
                        await update.message.reply_text(f"❌ Error sending video: {error_msg}")
                finally:
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    await status_message.delete()
                
                # Update download count
                user_data = db.get(User.id == user_id)
                if user_data:
                    db.update({'downloads': user_data.get('downloads', 0) + 1}, User.id == user_id)
                else:
                    db.insert({'id': user_id, 'downloads': 1, 'premium': False})
                
            except Exception as e:
                error_msg = str(e)
                if "timed out" in error_msg.lower():
                    await update.message.reply_text(get_translation("download_timeout", lang))
                else:
                    await update.message.reply_text(get_translation("download_error", lang).format(error=error_msg))
            finally:
                queue.task_done()
        except Exception as e:
            print(f"Queue processing error: {e}")
            await asyncio.sleep(1)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    lang = get_user_language(user_id)

    user_data = db.get(User.id == user_id)
    download_count = user_data['downloads'] if user_data else 0

    if user_data and user_data.get('premium'):
        pass
    elif download_count >= DOWNLOAD_LIMIT:
        keyboard = [[InlineKeyboardButton("🔓 Upgrade to Premium", url="https://example.com/upgrade")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = get_translation("premium_limit", lang)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
        return

    status_message = await update.message.reply_text(get_translation("downloading", lang))
    
    # Start queue processor if not already running
    queue = download_queues[user_id]
    if queue.empty():
        asyncio.create_task(process_download_queue(user_id, update, context))
    
    # Add download request to queue
    try:
        await queue.put((url, lang, status_message))
    except asyncio.QueueFull:
        await update.message.reply_text("Too many pending downloads. Please wait a moment before trying again.")

SUPPORTED_LANGUAGES = ["en", "es", "fr", "ar", "zh", "hi", "pt", "ru", "bn", "ur", "ja", "yo", "de", "tr", "ko", "it", "vi", "fa", "sw", "ha", "tl", "ms", "th", "pl", "uk", "id", "nl"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang = update.effective_user.language_code

    # Set default language to 'en' if user's language is not supported
    lang = user_lang if user_lang in SUPPORTED_LANGUAGES else 'en'

    # Save user's language preference
    db.upsert({'id': user_id, 'lang': lang}, User.id == user_id)

    await update.message.reply_text(get_translation("start_msg", lang))

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get(User.id == user_id)
    lang = get_user_language(user_id)

    if not user_data:
        downloads_used = 0
        is_premium = False
    else:
        downloads_used = user_data.get('downloads', 0)
        is_premium = user_data.get('premium', False)

    remaining = "Unlimited" if is_premium else (DOWNLOAD_LIMIT - downloads_used)
    status = "Premium user" if is_premium else "Free user"

    await update.message.reply_text(get_translation("account_info", lang).format(downloads=downloads_used, remaining=remaining, status=status))

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide a user ID to reset.")
        return

    try:
        target_id = int(context.args[0])
        user = db.get(User.id == target_id)
        if user:
            db.update({'downloads': 0}, User.id == target_id)
            await update.message.reply_text(f"✅ Reset downloads count to 0 for user {target_id}")
        else:
            await update.message.reply_text("❌ User not found in the database.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID format.")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    all_users = db.all()
    total_users = len(all_users)
    sample_users = all_users[:3]  # Get first 3 users as sample

    sample_ids = [f"• {user['id']}" for user in sample_users]
    response = f"📊 Total users: {total_users}\n\nSample user IDs:\n" + "\n".join(sample_ids)
    await update.message.reply_text(response)

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        with open('users.json', 'rb') as file:
            await update.message.reply_document(file, filename='users_backup.json')
        await update.message.reply_text("✅ Database backup sent successfully!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending backup: {str(e)}")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide a message to broadcast.")
        return

    message = " ".join(context.args)
    all_users = db.all()
    success = 0
    failed = 0

    for user in all_users:
        try:
            await context.bot.send_message(chat_id=user['id'], text=message)
            success += 1
        except Exception:
            failed += 1

    summary = f"✅ Broadcast sent to {success} users. ❌ Failed for {failed}."
    await update.message.reply_text(summary)

async def analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    all_users = db.all()
    total_users = len(all_users)
    total_downloads = sum(user.get('downloads', 0) for user in all_users)
    premium_users = len([user for user in all_users if user.get('premium', False)])

    # Sort users by download count and get top 5
    top_users = sorted(all_users, key=lambda x: x.get('downloads', 0), reverse=True)[:5]
    top_users_text = "\n".join([
        f"• User {user['id']}: {user.get('downloads', 0)} downloads"
        for user in top_users
    ])

    language_stats = get_language_stats()

    analytics = (
        "*📊 Bot Analytics*\n\n"
        f"*Overall Stats:*\n"
        f"• Total Users: `{total_users}`\n"
        f"• Total Downloads: `{total_downloads}`\n"
        f"• Premium Users: `{premium_users}`\n\n"
        f"*Top 5 Users by Downloads:*\n{top_users_text}\n\n"
        f"🌍 Languages used:\n{language_stats}"
    )

    await update.message.reply_text(analytics, parse_mode="Markdown")

async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Upgrade Now", url="https://example.com/upgrade")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🚀 *Go Premium – Unlock Everything!*\n\n"
        "• Unlimited video downloads\n"
        "• Fastest processing\n"
        "• All platforms supported\n\n"
        "Tap the button below to upgrade:"
    )

    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ I didn't understand that command. Try /help.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_translation("help_msg", lang))


def get_user_language(user_id):
    user_data = db.get(User.id == user_id)
    return user_data.get('lang', 'en')

def get_translation(key, lang):
    return translations.get(key, {}).get(lang, translations[key].get('en', "Translation not found"))


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(text="English", callback_data='en')],
        [InlineKeyboardButton(text="Spanish", callback_data='es')],
        [InlineKeyboardButton(text="French", callback_data='fr')],
        [InlineKeyboardButton(text="Arabic", callback_data='ar')],
        [InlineKeyboardButton(text="Chinese", callback_data='zh')],
        [InlineKeyboardButton(text="Hindi", callback_data='hi')],
        [InlineKeyboardButton(text="Portuguese", callback_data='pt')],
        [InlineKeyboardButton(text="Russian", callback_data='ru')],
        [InlineKeyboardButton(text="Bengali", callback_data='bn')],
        [InlineKeyboardButton(text="Urdu", callback_data='ur')],
        [InlineKeyboardButton(text="Japanese", callback_data='ja')],
        [InlineKeyboardButton(text="Yoruba", callback_data='yo')],
        [InlineKeyboardButton(text="German", callback_data='de')],
        [InlineKeyboardButton(text="Turkish", callback_data='tr')],
        [InlineKeyboardButton(text="Korean", callback_data='ko')],
        [InlineKeyboardButton(text="Italian", callback_data='it')],
        [InlineKeyboardButton(text="Vietnamese", callback_data='vi')],
        [InlineKeyboardButton(text="Farsi", callback_data='fa')],
        [InlineKeyboardButton(text="Swahili", callback_data='sw')],
        [InlineKeyboardButton(text="Hausa", callback_data='ha')],
        [InlineKeyboardButton(text="Filipino", callback_data='tl')],
        [InlineKeyboardButton(text="Malay", callback_data='ms')],
        [InlineKeyboardButton(text="Thai", callback_data='th')],
        [InlineKeyboardButton(text="Polish", callback_data='pl')],
        [InlineKeyboardButton(text="Ukrainian", callback_data='uk')],
        [InlineKeyboardButton(text="Indonesian", callback_data='id')],
        [InlineKeyboardButton(text="Dutch", callback_data='nl')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose your language:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = query.data
    user_id = query.from_user.id
    db.update({'lang': lang}, User.id == user_id)
    await query.answer()
    await query.edit_message_text(text=f"Language set to {lang}")


def get_language_stats():
    all_users = db.all()
    language_counts = Counter(user.get('lang', 'en') for user in all_users)
    language_stats = "\n".join([f"• {lang}: {count} users" for lang, count in language_counts.most_common()])
    return language_stats

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is healthy")

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
    print("Health check server running on port 8080")
    server.serve_forever()

if __name__ == '__main__':
    # Start health check server
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    # Verify token
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN is not set. Please check your Secrets.")
        exit(1)
    print(f"✓ BOT_TOKEN found: {BOT_TOKEN[:5]}...")

    # Start the bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("account", account))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("analytics", analytics_command))
    app.add_handler(CommandHandler("upgrade", upgrade_command))
    app.add_handler(CommandHandler("language", language))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    print("🤖 Bot is running...")
    app.run_polling()