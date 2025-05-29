import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# تنظیمات ضروری
BOT_TOKEN = "8104124383:AAFrGB8uZmgkRx2EGGMd_H6ldASsLaRQclw"  # توکن ربات خود را از @BotFather بگیرید
ADMIN_USER_ID = 327855654  # آیدی عددی خود را از @userinfobot بگیرید
TOOBIT_LINK = "https://www.toobit.com/fa/register?invite_code=5EQpCT"

# ایجاد پایگاه داده
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT DEFAULT 'fa',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language_code TEXT,
            signal_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# متن‌های چندزبانه
MESSAGES = {
    'fa': {
        'welcome': '🎉 به ربات خوش آمدید!\n\nبرای ثبت نام در توبیت روی لینک زیر کلیک کنید:\n{}\n\nسپس زبان مورد نظر خود را انتخاب کنید:',
        'language_selected': 'زبان فارسی انتخاب شد 🇮🇷',
        'no_signal': 'هنوز سیگنالی برای این زبان ثبت نشده است.',
        'toobit_button': '🚀 ثبت نام در توبیت',
        'admin_button': '📝 ثبت سیگنال',
        'select_lang': 'زبانی که می‌خواهی سیگنال ثبت کنی را انتخاب کن:',
        'enter_signal': '✅ زبان انتخاب شد. لطفا متن سیگنال را وارد کنید:',
        'signal_saved': '✅ سیگنال با موفقیت ثبت شد!'
    },
    'en': {
        'welcome': '🎉 Welcome to the bot!\n\nClick the link below to register on Toobit:\n{}\n\nThen choose your language:',
        'language_selected': 'English language selected 🇺🇸',
        'no_signal': 'No signal has been registered for this language yet.',
        'toobit_button': '🚀 Register on Toobit',
        'admin_button': '📝 Register Signal',
        'select_lang': 'Select the language for your signal:',
        'enter_signal': '✅ Language selected. Please enter the signal text:',
        'signal_saved': '✅ Signal saved successfully!'
    },
    'ar': {
        'welcome': '🎉 مرحباً بكم في البوت!\n\nانقر على الرابط أدناه للتسجيل في توبيت:\n{}\n\nثم اختر لغتك:',
        'language_selected': 'تم اختيار اللغة العربية 🇸🇦',
        'no_signal': 'لم يتم تسجيل أي إشارة لهذه اللغة بعد.',
        'toobit_button': '🚀 التسجيل في توبيت',
        'admin_button': '📝 تسجيل إشارة',
        'select_lang': 'اختر اللغة التي تريد تسجيل الإشارة بها:',
        'enter_signal': '✅ تم اختيار اللغة. يرجى إدخال نص الإشارة:',
        'signal_saved': '✅ تم حفظ الإشارة بنجاح!'
    },
    'ja': {
        'welcome': '🎉 ボットへようこそ！\n\nToobitに登録するには下のリンクをクリック:\n{}\n\n言語を選択してください：',
        'language_selected': '日本語が選択されました 🇯🇵',
        'no_signal': 'この言語のシグナルはまだ登録されていません。',
        'toobit_button': '🚀 Toobitに登録',
        'admin_button': '📝 シグナル登録',
        'select_lang': 'シグナルを登録する言語を選択してください:',
        'enter_signal': '✅ 言語が選択されました。シグナルテキストを入力してください:',
        'signal_saved': '✅ シグナルが正常に保存されました！'
    },
    'ru': {
        'welcome': '🎉 Добро пожаловать в бот!\n\nДля регистрации на Toobit нажмите ссылку:\n{}\n\nВыберите ваш язык:',
        'language_selected': 'Выбран русский язык 🇷🇺',
        'no_signal': 'Для этого языка еще не зарегистрирован сигнал.',
        'toobit_button': '🚀 Регистрация на Toobit',
        'admin_button': '📝 Зарегистрировать сигнал',
        'select_lang': 'Выберите язык для регистрации сигнала:',
        'enter_signal': '✅ Язык выбран. Пожалуйста, введите текст сигнала:',
        'signal_saved': '✅ Сигнал успешно сохранен!'
    },
    'es': {
        'welcome': '🎉 ¡Bienvenido al bot!\n\nHaz clic en el enlace para registrarte en Toobit:\n{}\n\nElige tu idioma:',
        'language_selected': 'Idioma español seleccionado 🇪🇸',
        'no_signal': 'Aún no se ha registrado ninguna señal para este idioma.',
        'toobit_button': '🚀 Registrarse en Toobit',
        'admin_button': '📝 Registrar señal',
        'select_lang': 'Selecciona el idioma para tu señal:',
        'enter_signal': '✅ Idioma seleccionado. Por favor ingresa el texto de la señal:',
        'signal_saved': '✅ ¡Señal guardada con éxito!'
    }
}

# ذخیره کاربر در دیتابیس
def save_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

# دریافت زبان کاربر
def get_user_language(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT language_code FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'fa'

# تنظیم زبان کاربر
def set_user_language(user_id, language_code):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET language_code = ? WHERE user_id = ?
    ''', (language_code, user_id))
    conn.commit()
    conn.close()

# دریافت سیگنال برای زبان خاص
def get_signal(language_code):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT signal_text FROM signals WHERE language_code = ? ORDER BY created_at DESC LIMIT 1', 
                   (language_code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# ذخیره سیگنال
def save_signal(language_code, signal_text):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO signals (language_code, signal_text)
        VALUES (?, ?)
    ''', (language_code, signal_text))
    conn.commit()
    conn.close()

# دریافت تمام کاربران
def get_all_users():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# ایجاد کیبورد اصلی
def create_main_keyboard(user_id, user_lang='fa'):
    toobit_text = MESSAGES.get(user_lang, MESSAGES['fa'])['toobit_button']
    
    keyboard = [
        [InlineKeyboardButton(toobit_text, url=TOOBIT_LINK)],
        [
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa")
        ],
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
            InlineKeyboardButton("🇯🇵 日本語", callback_data="lang_ja")
        ],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")
        ]
    ]
    
    # اضافه کردن دکمه ادمین فقط برای ادمین اصلی
    if user_id == ADMIN_USER_ID:
        admin_text = MESSAGES.get(user_lang, MESSAGES['fa'])['admin_button']
        keyboard.append([InlineKeyboardButton(admin_text, callback_data="admin_signal")])
    
    return InlineKeyboardMarkup(keyboard)

# کیبورد زبان‌ها برای ادمین
def create_admin_lang_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🇺🇸 English", callback_data="admin_en"),
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="admin_fa")
        ],
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="admin_ar"),
            InlineKeyboardButton("🇯🇵 日本語", callback_data="admin_ja")
        ],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="admin_ru"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="admin_es")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username, user.first_name, user.last_name)
    
    user_lang = get_user_language(user.id)
    welcome_text = MESSAGES.get(user_lang, MESSAGES['fa'])['welcome'].format(TOOBIT_LINK)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=create_main_keyboard(user.id, user_lang),
        disable_web_page_preview=True
    )

# مدیریت کلیک روی دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # انتخاب زبان توسط کاربر
    if query.data.startswith('lang_'):
        language_code = query.data.split('_')[1]
        set_user_language(user_id, language_code)
        
        signal = get_signal(language_code)
        selected_msg = MESSAGES.get(language_code, MESSAGES['fa'])['language_selected']
        
        if signal:
            message_text = f"{selected_msg}\n\n📊 **سیگنال:**\n{signal}"
        else:
            no_signal_msg = MESSAGES.get(language_code, MESSAGES['fa'])['no_signal']
            message_text = f"{selected_msg}\n\n{no_signal_msg}"
        
        toobit_link_text = f"\n\n🔗 **لینک توبیت:**\n{TOOBIT_LINK}"
        message_text += toobit_link_text
        
        await query.edit_message_text(
            message_text,
            reply_markup=create_main_keyboard(user_id, language_code),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    # دکمه ثبت سیگنال توسط ادمین
    elif query.data == 'admin_signal':
        if user_id != ADMIN_USER_ID:
            await query.message.reply_text("❌ شما دسترسی ندارید!")
            return
            
        select_lang_text = MESSAGES.get(get_user_language(user_id), MESSAGES['fa'])['select_lang']
        await query.edit_message_text(
            select_lang_text,
            reply_markup=create_admin_lang_keyboard()
        )
    
    # انتخاب زبان توسط ادمین برای ثبت سیگنال
    elif query.data.startswith('admin_'):
        if user_id != ADMIN_USER_ID:
            await query.message.reply_text("❌ شما دسترسی ندارید!")
            return
            
        language_code = query.data.split('_')[1]
        context.user_data['signal_lang'] = language_code
        
        enter_signal_text = MESSAGES.get(get_user_language(user_id), MESSAGES['fa'])['enter_signal']
        await query.edit_message_text(enter_signal_text)

# ذخیره سیگنال ارسالی توسط ادمین
async def save_admin_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        return
    
    if 'signal_lang' not in context.user_data:
        return
    
    language_code = context.user_data['signal_lang']
    signal_text = update.message.text
    
    save_signal(language_code, signal_text)
    del context.user_data['signal_lang']
    
    signal_saved_text = MESSAGES.get(get_user_language(user_id), MESSAGES['fa'])['signal_saved']
    await update.message.reply_text(signal_saved_text)

# دستور ثبت پیام برای ادمین
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما اجازه استفاده از این دستور را ندارید.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 **راهنمای ارسال پیام همگانی:**\n"
            "`/broadcast <متن_پیام>`\n\n"
            "**مثال:**\n"
            "`/broadcast سلام به همه کاربران عزیز!`",
            parse_mode='Markdown'
        )
        return
    
    message_text = ' '.join(context.args)
    users = get_all_users()
    
    if not users:
        await update.message.reply_text("❌ هیچ کاربری در دیتابیس یافت نشد!")
        return
    
    confirm_msg = await update.message.reply_text(
        f"📤 در حال ارسال پیام به {len(users)} کاربر...\n"
        "لطفاً صبر کنید..."
    )
    
    successful_sends = 0
    failed_sends = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(user_id, message_text)
            successful_sends += 1
        except Exception as e:
            failed_sends += 1
            print(f"خطا در ارسال پیام به {user_id}: {e}")
    
    await confirm_msg.edit_text(
        f"📊 **نتیجه ارسال پیام:**\n\n"
        f"✅ موفق: {successful_sends}\n"
        f"❌ ناموفق: {failed_sends}\n"
        f"📈 درصد موفقیت: {(successful_sends*100//len(users)) if users else 0}%",
        parse_mode='Markdown'
    )

# دستور آمار برای ادمین
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما اجازه استفاده از این دستور را ندارید.")
        return
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT language_code, COUNT(*) FROM users GROUP BY language_code')
    lang_stats = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) FROM signals')
    total_signals = cursor.fetchone()[0]
    
    conn.close()
    
    stats_text = f"📊 **آمار کامل ربات:**\n\n"
    stats_text += f"👥 **کل کاربران:** {total_users}\n"
    stats_text += f"📡 **کل سیگنال‌ها:** {total_signals}\n\n"
    stats_text += "🌍 **توزیع زبان‌ها:**\n"
    
    lang_names = {'fa': '🇮🇷 فارسی', 'en': '🇺🇸 انگلیسی', 'ar': '🇸🇦 عربی', 
                  'ja': '🇯🇵 ژاپنی', 'ru': '🇷🇺 روسی', 'es': '🇪🇸 اسپانیایی'}
    
    for lang_code, count in lang_stats:
        lang_name = lang_names.get(lang_code, f"🏳️ {lang_code}")
        percentage = (count * 100) // total_users if total_users > 0 else 0
        stats_text += f"• {lang_name}: {count} ({percentage}%)\n"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# دستور راهنما برای ادمین
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما اجازه استفاده از این دستور را ندارید.")
        return
    
    help_text = """
🔧 **دستورات ادمین:**

📢 `/broadcast <متن_پیام>`
ارسال پیام به تمام کاربران

📊 `/stats`
نمایش آمار کامل ربات

❓ `/help`
نمایش این راهنما
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# تابع اصلی
def main():
    print("🚀 در حال راه‌اندازی ربات...")
    
    # بررسی تنظیمات
    if BOT_TOKEN == "":
        print("❌ خطا: لطفاً توکن ربات را در کد تنظیم کنید!")
        return
    
    if ADMIN_USER_ID == 327855654:
        print("⚠️ هشدار: لطفاً آیدی ادمین را در کد تنظیم کنید!")
    
    # ایجاد پایگاه داده
    try:
        init_db()
        print("✅ پایگاه داده آماده شد")
    except Exception as e:
        print(f"❌ خطا در ایجاد پایگاه داده: {e}")
        return
    
    # ایجاد اپلیکیشن
    try:
        application = Application.builder().token(BOT_TOKEN).build()
    except Exception as e:
        print(f"❌ خطا در ایجاد اپلیکیشن: {e}")
        return
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # هندلر ذخیره سیگنال ادمین
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        save_admin_signal
    ))
    
    # شروع ربات
    print("✅ ربات با موفقیت شروع به کار کرد!")
    print("📱 کاربران می‌توانند با /start شروع کنند")
    print("👑 ادمین می‌تواند با دکمه [ثبت سیگنال] سیگنال جدید ثبت کند")
    print("🛑 برای توقف: Ctrl+C")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"❌ خطا در اجرای ربات: {e}")

if __name__ == '__main__':
    main()  # اصلاح شده: تابع main باید فراخوانی شود ()


