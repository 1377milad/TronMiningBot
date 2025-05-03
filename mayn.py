import asyncio
import random
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# تنظیمات اولیه
TOKEN = "7799468905:AAGKkcW68RZNvYnRf8bWJl_V3sfVz1IeSLY"
ADMIN_ID = 327855654
USER_DATA_FILE = "user_data.json"

# آدرس کیف پول‌ها
TRON_ADDRESS = "TAXB65Gnizfuc486FqycEi3F4Eyg1ArPqN"
DOGE_ADDRESS = "DLM2KeNDVq5r6Wr6gvCiQxHLSFysvdskZv"
BITCOIN_ADDRESS = ""
ETHEREUM_ADDRESS = ""
RIPPLE_ADDRESS = ""

# سیستم ذخیره و بازیابی داده‌ها
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data():
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_db, f)

user_db = load_user_data()

# تابع تولید لینک رفرال اختصاصی
async def generate_referral_code(user_id: int):
    return f"ref_{user_id}_{random.randint(1000, 9999)}"

# ==================== توابع اصلی ربات ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # تشخیص نوع درخواست (پیام جدید یا callback)
        if update.message is None:
            query = update.callback_query
            await query.answer()
            user_id = query.from_user.id
            message = query.message
        else:
            user_id = update.effective_user.id
            message = None
        
        # پردازش لینک رفرال
        if update.message and len(context.args) > 0:
            referral_input = context.args[0]
            
            # حالت‌های مختلف لینک رفرال
            if referral_input.startswith('ref_'):
                try:
                    referrer_id = int(referral_input.split('_')[1])
                    if referrer_id in user_db and referrer_id != user_id:
                        if 'referred_by' not in user_db.get(user_id, {}):
                            user_db[user_id]['referred_by'] = referrer_id
                            if 'referrals' not in user_db[referrer_id]:
                                user_db[referrer_id]['referrals'] = []
                            user_db[referrer_id]['referrals'].append(user_id)
                            user_db[referrer_id]['tron'] += 0.001
                            user_db[referrer_id]['doge'] += 0.001
                            save_user_data()
                except (IndexError, ValueError):
                    pass
            elif referral_input.isdigit():
                referrer_id = int(referral_input)
                if referrer_id in user_db and referrer_id != user_id:
                    if 'referred_by' not in user_db.get(user_id, {}):
                        user_db[user_id]['referred_by'] = referrer_id
                        if 'referrals' not in user_db[referrer_id]:
                            user_db[referrer_id]['referrals'] = []
                        user_db[referrer_id]['referrals'].append(user_id)
                        user_db[referrer_id]['tron'] += 0.001
                        user_db[referrer_id]['doge'] += 0.001
                        save_user_data()
        
        # ایجاد کاربر جدید با لینک رفرال اختصاصی
        if user_id not in user_db:
            referral_code = await generate_referral_code(user_id)
            bot_username = (await context.bot.get_me()).username
            referral_link = f"https://t.me/{bot_username}?start={referral_code}"
            
            user_db[user_id] = {
                'tron': 0.0,
                'doge': 0.0,
                'bitcoin': 0.0,
                'ethereum': 0.0,
                'ripple': 0.0,
                'mining_rate': 0.3,
                'referrals': [],
                'referred_by': None,
                'referral_code': referral_code,
                'referral_link': referral_link
            }
            save_user_data()
        
        # ساخت منوی اصلی
        buttons = [
            [InlineKeyboardButton("💰 TRON Wallet", callback_data='tron_wallet'),
             InlineKeyboardButton("💰 DOGE Wallet", callback_data='doge_wallet')],
            [InlineKeyboardButton("💰 Bitcoin Wallet", callback_data='bitcoin_wallet'),
             InlineKeyboardButton("💰 Ethereum Wallet", callback_data='ethereum_wallet')],
            [InlineKeyboardButton("💰 Ripple Wallet", callback_data='ripple_wallet')],
            [InlineKeyboardButton("⛏️ Start Mining", callback_data='start_mining')],
            [InlineKeyboardButton("📤 Withdraw", callback_data='withdraw')],
            [InlineKeyboardButton("📢 Get Referral Link", callback_data='referral')],
            [InlineKeyboardButton("Win $300K", callback_data='win_300k')]
        ]
        
        text = "🔷 Welcome to Crypto Mining Bot!\n\nPlease select an option:"
        if message:
            await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        print(f"Error in start: {e}")

async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        wallet_type = query.data.split('_')[0]
        
        wallets = {
            'tron': {'name': "TRON", 'address': TRON_ADDRESS},
            'doge': {'name': "DOGE", 'address': DOGE_ADDRESS},
            'bitcoin': {'name': "Bitcoin", 'address': BITCOIN_ADDRESS},
            'ethereum': {'name': "Ethereum", 'address': ETHEREUM_ADDRESS},
            'ripple': {'name': "Ripple", 'address': RIPPLE_ADDRESS}
        }
        
        if wallet_type not in wallets:
            await query.edit_message_text("❌ Invalid wallet type!")
            return
        
        wallet = wallets[wallet_type]
        await query.edit_message_text(
            f"💰 {wallet['name']} Wallet:\n\n"
            f"Balance: {user_db[user_id][wallet_type]:.8f}\n"
            f"Address: `{wallet['address']}`\n\n"
            "Click the address to copy it.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
            ])
        )
    except Exception as e:
        print(f"Error in show_wallet: {e}")

async def start_mining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        context.user_data['mining'] = {'running': True}
        
        asyncio.create_task(mining_process(query, context, user_id))
        
        await query.edit_message_text(
            "⛏️ Mining in progress...\n\n"
            "Speed: Low\n"
            "Please wait...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏹ Stop Mining", callback_data='stop_mining')]
            ])
        )
    except Exception as e:
        print(f"Error in start_mining: {e}")

async def mining_process(query, context: ContextTypes.DEFAULT_TYPE, user_id):
    try:
        while context.user_data.get('mining', {}).get('running', False):
            # افزایش موجودی تمام ارزها
            user_db[user_id]['tron'] += random.uniform(0.00001, 0.00003)
            user_db[user_id]['doge'] += random.uniform(0.00001, 0.00003)
            user_db[user_id]['bitcoin'] += random.uniform(0.000001, 0.000003)
            user_db[user_id]['ethereum'] += random.uniform(0.000001, 0.000003)
            user_db[user_id]['ripple'] += random.uniform(0.0001, 0.0003)
            save_user_data()
            
            # نمایش اطلاعات با فاصله‌گذاری درخواستی
            mining_text = (
                f"⛏️ Mining in progress...\n\n"
                f"TRON: {user_db[user_id]['tron']:.8f}\n"
                f"DOGE: {user_db[user_id]['doge']:.8f}\n\n"
                f"Bitcoin: {user_db[user_id]['bitcoin']:.8f}\n"
                f"Ethereum: {user_db[user_id]['ethereum']:.8f}\n\n"
                f"Ripple: {user_db[user_id]['ripple']:.8f}\n\n"
                "Please wait..."
            )
            
            try:
                await query.edit_message_text(
                    mining_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⏹ Stop Mining", callback_data='stop_mining')]
                    ])
                )
            except:
                break
            
            await asyncio.sleep(5)
    except Exception as e:
        print(f"Error in mining_process: {e}")

async def stop_mining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        context.user_data['mining']['running'] = False
        
        await query.edit_message_text(
            f"⏹ Mining stopped\n\n"
            f"Final balance:\n"
            f"TRON: {user_db[user_id]['tron']:.8f}\n"
            f"DOGE: {user_db[user_id]['doge']:.8f}\n\n"
            f"Bitcoin: {user_db[user_id]['bitcoin']:.8f}\n"
            f"Ethereum: {user_db[user_id]['ethereum']:.8f}\n\n"
            f"Ripple: {user_db[user_id]['ripple']:.8f}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
            ])
        )
    except Exception as e:
        print(f"Error in stop_mining: {e}")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        context.user_data['withdraw_stage'] = 'select_coin'
        
        buttons = [
            [InlineKeyboardButton("TRON", callback_data='withdraw_tron'),
             InlineKeyboardButton("DOGE", callback_data='withdraw_doge')],
            [InlineKeyboardButton("Bitcoin", callback_data='withdraw_bitcoin'),
             InlineKeyboardButton("Ethereum", callback_data='withdraw_ethereum')],
            [InlineKeyboardButton("Ripple", callback_data='withdraw_ripple')],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
        ]
        
        await query.edit_message_text(
            "Select coin to withdraw:",
            reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        print(f"Error in withdraw: {e}")

async def handle_withdraw_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        coin = query.data.split('_')[1]
        context.user_data['withdraw_coin'] = coin
        
        await query.edit_message_text(
            f"Enter amount of {coin.upper()} to withdraw:\n"
            f"(Your balance: {user_db[user_id][coin]:.8f})\n\n"
            "Your funds will be processed within 20 days.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='withdraw'),
                 InlineKeyboardButton("🏠 Main Menu", callback_data='menu')]
            ]))
    except Exception as e:
        print(f"Error in handle_withdraw_coin: {e}")

async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        coin = context.user_data['withdraw_coin']
        
        try:
            amount = float(update.message.text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
                
            if amount > user_db[user_id][coin]:
                await update.message.reply_text(
                    f"❌ Insufficient balance! You have {user_db[user_id][coin]:.8f} {coin.upper()}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data='withdraw'),
                         InlineKeyboardButton("🏠 Main Menu", callback_data='menu')]
                    ]))
                return
                
            user_db[user_id][coin] -= amount
            save_user_data()
            
            address_mapping = {
                'tron': TRON_ADDRESS,
                'doge': DOGE_ADDRESS,
                'bitcoin': BITCOIN_ADDRESS,
                'ethereum': ETHEREUM_ADDRESS,
                'ripple': RIPPLE_ADDRESS
            }
            
            await update.message.reply_text(
                f"✅ Withdrawal request received!\n\n"
                f"Amount: {amount:.8f} {coin.upper()}\n"
                f"Processing time: 20 days\n\n"
                "We will notify you when completed.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data='menu')]
                ]))
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📌 New withdrawal request:\n\n"
                    f"User: @{update.message.from_user.username}\n"
                    f"Amount: {amount:.8f} {coin.upper()}\n"
                    f"Address: {address_mapping[coin]}"
                )
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a positive number:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data='withdraw'),
                     InlineKeyboardButton("🏠 Main Menu", callback_data='menu')]
                ]))
    except Exception as e:
        print(f"Error in process_withdrawal: {e}")

async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        referral_count = len(user_db[user_id]['referrals'])
        referral_link = user_db[user_id]['referral_link']
        
        await query.edit_message_text(
            f"📢 Your Personal Referral Program\n\n"
            f"🔗 Your unique referral link:\n{referral_link}\n\n"
            f"👥 Total referrals: {referral_count}\n"
            f"💰 Bonus per referral: 0.001 TRX + 0.001 DOGE\n\n"
            "Share your personal link and earn crypto!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
            ])
        )
    except Exception as e:
        print(f"Error in show_referral: {e}")

async def handle_win_300k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        wallet_info = [
            ("TRON", user_db[user_id]['tron'], TRON_ADDRESS),
            ("DOGE", user_db[user_id]['doge'], DOGE_ADDRESS),
            ("Bitcoin", user_db[user_id]['bitcoin'], BITCOIN_ADDRESS),
            ("Ethereum", user_db[user_id]['ethereum'], ETHEREUM_ADDRESS),
            ("Ripple", user_db[user_id]['ripple'], RIPPLE_ADDRESS)
        ]
        
        message_text = "🎉 Congratulations! You won $300K!\n\n📌 Your current wallets:\n\n"
        for name, balance, address in wallet_info:
            message_text += f"{name}: {balance:.8f}\nAddress: `{address}`\n\n"
        
        message_text += "Click addresses to copy them."
        
        await query.edit_message_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
            ])
        )
    except Exception as e:
        print(f"Error in handle_win_300k: {e}")

async def admin_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Access denied! Admin only command.")
            return
            
        if len(context.args) < 3:
            await update.message.reply_text(
                "Usage: /withdraw [user_id] [coin] [amount]\n"
                "Example: /withdraw 123456789 tron 0.5"
            )
            return
            
        try:
            target_user = int(context.args[0])
            coin = context.args[1].lower()
            amount = float(context.args[2])
            
            if target_user not in user_db:
                await update.message.reply_text("❌ User not found!")
                return
                
            valid_coins = ['tron', 'doge', 'bitcoin', 'ethereum', 'ripple']
            if coin not in valid_coins:
                await update.message.reply_text(
                    f"❌ Invalid coin. Use {', '.join(valid_coins)}"
                )
                return
                
            if amount <= 0:
                await update.message.reply_text("❌ Amount must be positive!")
                return
                
            if amount > user_db[target_user][coin]:
                await update.message.reply_text(
                    f"❌ User doesn't have enough balance "
                    f"(Current: {user_db[target_user][coin]:.8f} {coin.upper()})"
                )
                return
                
            user_db[target_user][coin] -= amount
            save_user_data()
            
            await update.message.reply_text(
                f"✅ Successfully withdrew {amount:.8f} {coin.upper()} "
                f"from user {target_user}\n"
                f"New balance: {user_db[target_user][coin]:.8f} {coin.upper()}"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid input. Make sure you're using correct numbers.")
            
    except Exception as e:
        print(f"Error in admin_withdraw: {e}")
        await update.message.reply_text("❌ An error occurred while processing withdrawal")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error occurred: {context.error}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_error_handler(error_handler)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("withdraw", admin_withdraw))
    
    app.add_handler(CallbackQueryHandler(start, pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(show_wallet, pattern='^(tron|doge|bitcoin|ethereum|ripple)_wallet$'))
    app.add_handler(CallbackQueryHandler(start_mining, pattern='^start_mining$'))
    app.add_handler(CallbackQueryHandler(stop_mining, pattern='^stop_mining$'))
    app.add_handler(CallbackQueryHandler(withdraw, pattern='^withdraw$'))
    app.add_handler(CallbackQueryHandler(handle_withdraw_coin, pattern='^withdraw_(tron|doge|bitcoin|ethereum|ripple)$'))
    app.add_handler(CallbackQueryHandler(show_referral, pattern='^referral$'))
    app.add_handler(CallbackQueryHandler(handle_win_300k, pattern='^win_300k$'))
    
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d+\.?\d*$'),
        process_withdrawal
    ))
    
    app.run_polling()

if __name__ == "__main__":
    maine()
