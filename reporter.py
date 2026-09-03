import time
import asyncio
from collections import defaultdict
from datetime import datetime

from bale import Bot, Message, InlineKeyboardMarkup, InlineKeyboardButton
from bale.helpers import create_deep_linked_url

TOKEN = "707960807:aUG8oSYTujBr_umVJ3iJ-oRzmz13d282aEg" # توکنتو از بله  خودت @botfather بگیر اینجا بزار 
ADMIN_ID = 1494308062 #ایدی عددی خودت رو اینجا بزار

bot = Bot(token=TOKEN)

# داده‌ها
user_custom_text = {}
user_state = {}
click_timestamps = defaultdict(list)
blocked_until = {}
click_history = defaultdict(list)
user_blocked_clickers = defaultdict(set)
reports = defaultdict(list)
banned_users = set()
user_join_time = {}
user_last_activity = {}
user_message_count = defaultdict(int)

DEFAULT_TEXT = "متاسفانه شما گیر تله فضول یاب رایگان ما شدید\nببخشید اما اینجا نمیتونی جلوگیری کنی 💔"

def is_blocked(user_id):
    if user_id in blocked_until and time.time() < blocked_until[user_id]:
        return True
    if user_id in blocked_until:
        del blocked_until[user_id]
    return False

def is_banned(user_id):
    return user_id in banned_users

def check_spam(user_id):
    now = time.time()
    click_timestamps[user_id] = [t for t in click_timestamps[user_id] if now - t < 60]
    click_timestamps[user_id].append(now)
    if len(click_timestamps[user_id]) >= 3:
        blocked_until[user_id] = now + 120
        click_timestamps[user_id].clear()
        return True
    return False

def get_user_name(user):
    return f"{user.first_name} {user.last_name or ''}".strip() or "ناشناس"

def get_user_link(user_id, name=None):
    if not name:
        return f"[کاربر {user_id}](uid:{user_id})"
    return f"[{name}](uid:{user_id})"

async def show_user_profile(message, user_id):
    name = "کاربر"
    for hist in click_history.get(user_id, []):
        if hist["id"] == user_id:
            name = hist["name"]
            break
    
    clicks = len(click_history.get(user_id, []))
    custom_text = user_custom_text.get(user_id, DEFAULT_TEXT)
    join_time = datetime.fromtimestamp(user_join_time.get(user_id, time.time())).strftime("%Y-%m-%d %H:%M")
    total_msgs = user_message_count[user_id]
    is_banned = user_id in banned_users
    blocked_count = len(user_blocked_clickers.get(user_id, set()))
    
    txt = (
        f"👤 **پروفایل کاربر**\n\n"
        f"🧾 نام: {name}\n"
        f"🆔 آیدی: `{user_id}`\n"
        f"🔗 لینک: {get_user_link(user_id, name)}\n\n"
        f"📅 تاریخ ثبت: {join_time}\n"
        f"👀 تعداد کلیک: {clicks}\n"
        f"💬 تعداد پیام: {total_msgs}\n"
        f"🚫 بلاک‌ها: {blocked_count}\n"
        f"⛔ وضعیت بن: {'✅ بله' if is_banned else '❌ خیر'}\n\n"
        f"📝 متن تنظیم شده:\n_{custom_text}_"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✏️ تغییر متن", callback_data=f"admin_edit_text_{user_id}"))
    markup.add(InlineKeyboardButton("🔨 بن/آنبن", callback_data=f"admin_toggle_ban_{user_id}"), row=1)
    markup.add(InlineKeyboardButton("📩 ارسال پیام", callback_data=f"admin_sendto_{user_id}"), row=2)
    markup.add(InlineKeyboardButton("📊 کلیک‌ها", callback_data=f"admin_user_clicks_{user_id}"), row=3)
    
    await message.reply(txt, components=markup)

@bot.listen("on_ready")
async def on_ready():
    me = await bot.get_me()
    print(f"🤖 ربات @{me.username} آماده شد! | ادمین: {ADMIN_ID} 🔥")

@bot.listen("on_message")
async def on_message(message: Message):
    if not message.text: 
        return
    user_id = message.author.id
    text = message.text.strip()
    
    if user_id not in user_join_time:
        user_join_time[user_id] = time.time()
    user_last_activity[user_id] = time.time()
    user_message_count[user_id] += 1

    if is_banned(user_id):
        await message.reply("⛔ شما بن شده‌اید.")
        return
    if is_blocked(user_id):
        return

    if user_id == ADMIN_ID:
        if user_state.get(user_id) == "admin_broadcast":
            msg = text
            count = 0
            for uid in list(user_join_time.keys()):
                try:
                    await bot.send_message(uid, f"📢 **پیام همگانی از ادمین:**\n\n{msg}")
                    count += 1
                    await asyncio.sleep(0.1)
                except: 
                    pass
            await message.reply(f"✅ پیام به {count} نفر ارسال شد.")
            del user_state[user_id]
            return
        
        elif user_state.get(user_id) == "admin_ban_user":
            try:
                target_id = int(text)
                banned_users.add(target_id)
                await message.reply(f"✅ کاربر {target_id} بن شد.")
            except:
                await message.reply("❌ آیدی نامعتبر!")
            del user_state[user_id]
            return
        
        elif user_state.get(user_id) == "admin_unban_user":
            try:
                target_id = int(text)
                banned_users.discard(target_id)
                await message.reply(f"✅ کاربر {target_id} آنبن شد.")
            except:
                await message.reply("❌ آیدی نامعتبر!")
            del user_state[user_id]
            return
        
        elif user_state.get(user_id, "").startswith("admin_edit_text_"):
            try:
                target_id = int(user_state[user_id].split("_")[3])
                user_custom_text[target_id] = text
                await message.reply(f"✅ متن کاربر {target_id} تغییر کرد!")
            except:
                await message.reply("❌ خطا در تغییر متن!")
            del user_state[user_id]
            return
        
        elif user_state.get(user_id, "").startswith("admin_sendto_"):
            try:
                target_id = int(user_state[user_id].split("_")[2])
                await bot.send_message(target_id, f"📩 **پیام از ادمین:**\n\n{text}")
                await message.reply(f"✅ پیام به کاربر {target_id} ارسال شد.")
            except:
                await message.reply("❌ خطا در ارسال پیام!")
            del user_state[user_id]
            return

    if text.startswith("/start ") and len(text.split()) > 1:
        try:
            target_id = int(text.split(maxsplit=1)[1])
            clicker = message.author

            if check_spam(target_id): 
                await message.reply("🪱 کرم داری؟\nدو دقیقه مسدود شدی")
                return

            if clicker.id in user_blocked_clickers[target_id]:
                await message.reply("🚫 شما توسط این کاربر بلاک شده‌اید.")
                return

            click_history[target_id].append({
                "id": clicker.id,
                "name": get_user_name(clicker),
                "username": clicker.username,
                "time": time.strftime("%H:%M")
            })

            custom_text = user_custom_text.get(target_id, DEFAULT_TEXT)

            await message.reply(
                f"⌛ **شما در تله فضول یاب افتادید!**\n\n"
                f"📝 متن تنظیم شده:\n_{custom_text}_\n\n"
                f"📌 متاسفانه نمی‌تونی جلوش رو بگیری 😏"
            )

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔴 گزارش متن", callback_data=f"report_{target_id}"))
            await message.reply("متن بد بود؟ گزارش کن 👇", components=markup)

            try:
                name = get_user_name(clicker)
                username = f"@{clicker.username}" if clicker.username else "ندارد"
                notify = (
                    f"👀 **فضول جدید پیدا شد!** 🔥\n\n"
                    f"🧾 نام: {name}\n"
                    f"🧾 آیدی عددی: `{clicker.id}`\n"
                    f"🧾 آیدی اصلی: {username}\n\n"
                    f"🚀 ورود سریع:\n{get_user_link(clicker.id, name)}"
                )
                await bot.send_message(target_id, notify)
            except:
                pass
            return
        except:
            pass

    if text.startswith("/start"):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎗️ لینک من", callback_data="my_link"))
        markup.add(InlineKeyboardButton("📊 آمار من", callback_data="mystats"), row=1)
        markup.add(InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="user_settings"), row=2)
        
        if user_id == ADMIN_ID:
            markup.add(InlineKeyboardButton("👑 پنل مدیریت", callback_data="admin_panel"), row=3)
        
        await message.reply(
            "❤️ به **مچ‌گیر فضول** خوش اومدی!\n\n"
            "لینک خودت رو بساز و فضول‌ها رو زنده زنده بگیر 😈",
            components=markup
        )
        return

    if user_state.get(user_id) == "set_custom":
        user_custom_text[user_id] = text
        del user_state[user_id]
        me = await bot.get_me()
        deep_link = create_deep_linked_url(me.username, str(user_id))
        await message.reply(f"✅ متن با موفقیت تغییر کرد!\n\n{deep_link}")
        return

    if user_state.get(user_id) == "block_user":
        try:
            target_id = int(text)
            user_blocked_clickers[user_id].add(target_id)
            await message.reply(f"✅ کاربر {target_id} بلاک شد.")
        except:
            await message.reply("❌ آیدی نامعتبر!")
        del user_state[user_id]
        return

    if user_state.get(user_id) == "unblock_user":
        try:
            target_id = int(text)
            user_blocked_clickers[user_id].discard(target_id)
            await message.reply(f"✅ کاربر {target_id} آنبلاک شد.")
        except:
            await message.reply("❌ آیدی نامعتبر!")
        del user_state[user_id]
        return

    if user_state.get(user_id, "").startswith("report_"):
        target_id = int(user_state[user_id].split("_")[1])
        reports[target_id].append({"from": user_id, "reason": text, "time": time.strftime("%Y-%m-%d %H:%M")})
        await message.reply("🗞️ گزارش شما به ادمین ارسال شد. ممنون!")
        del user_state[user_id]
        try:
            await bot.send_message(ADMIN_ID, f"🚨 گزارش جدید\nاز: {user_id}\nدرباره: {target_id}\nدلیل: {text}")
        except:
            pass
        return

    if user_id == ADMIN_ID:
        if text.startswith("/ozv"):
            try:
                member_id = int(text.replace("/ozv", ""))
                await show_user_profile(message, member_id)
                return
            except:
                await message.reply("❌ فرمت اشتباه! از `/ozv123456789` استفاده کن.")
                return
        
        if text.startswith("/sendto "):
            parts = text.split(maxsplit=2)
            if len(parts) >= 3:
                try:
                    target_id = int(parts[1])
                    msg = parts[2]
                    await bot.send_message(target_id, f"📩 **پیام از ادمین:**\n\n{msg}")
                    await message.reply(f"✅ پیام به کاربر {target_id} ارسال شد.")
                except:
                    await message.reply("❌ فرمت: `/sendto آیدی پیام`")
            return

@bot.listen("on_callback")
async def on_callback(callback):
    user_id = callback.from_user.id
    data = callback.data

    if is_banned(user_id):
        await callback.answer("⛔ بن شده‌اید", show_alert=True)
        return

    if data == "my_link":
        me = await bot.get_me()
        deep_link = create_deep_linked_url(me.username, str(user_id))
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("👀 پیش‌فرض", callback_data="use_default"))
        markup.add(InlineKeyboardButton("✍️ تنظیم متن", callback_data="set_custom"), row=1)
        markup.add(InlineKeyboardButton("📊 آمار من", callback_data="mystats"), row=2)

        await callback.message.reply(f"🔗 **لینک اختصاصی تو:**\n`{deep_link}`", components=markup)
        await callback.answer("✅ لینک آماده شد")

    elif data == "use_default":
        user_custom_text[user_id] = DEFAULT_TEXT
        await callback.message.reply("✅ متن پیش‌فرض فعال شد!")
        await callback.answer()

    elif data == "set_custom":
        user_state[user_id] = "set_custom"
        await callback.message.reply("📝 متن جدید رو برام بنویس:")
        await callback.answer()

    elif data == "mystats":
        clicks = len(click_history.get(user_id, []))
        last = click_history[user_id][-1]["name"] if click_history.get(user_id) else "هنوز کسی نیومده"
        await callback.message.reply(
            f"📊 **آمار تو**\n\n"
            f"👥 تعداد فضول‌ها: **{clicks}** نفر\n"
            f"🕒 آخرین فضول: {last}\n\n"
            f"لینکتو بیشتر پخش کن تا بیشتر بگیری 😈"
        )
        await callback.answer()

    elif data == "user_settings":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔒 بلاک کاربر", callback_data="block_user"))
        markup.add(InlineKeyboardButton("🔓 آنبلاک", callback_data="unblock_user"), row=1)
        markup.add(InlineKeyboardButton("👥 لیست بلاک‌ها", callback_data="my_blocked_list"), row=2)
        markup.add(InlineKeyboardButton("📊 آمار کامل", callback_data="full_stats"), row=3)
        await callback.message.reply("⚙️ **تنظیمات پیشرفته**", components=markup)
        await callback.answer()

    elif data == "block_user":
        user_state[user_id] = "block_user"
        await callback.message.reply("🆔 آیدی عددی کاربر مورد نظر رو بفرست:")
        await callback.answer()

    elif data == "unblock_user":
        user_state[user_id] = "unblock_user"
        await callback.message.reply("🆔 آیدی عددی کاربری که می‌خوای آنبلاک کنی رو بفرست:")
        await callback.answer()

    elif data == "my_blocked_list":
        blocked = user_blocked_clickers.get(user_id, set())
        if not blocked:
            await callback.message.reply("📭 هنوز کسی رو بلاک نکردی!")
        else:
            txt = "🚫 **لیست بلاک‌ها:**\n\n"
            for uid in list(blocked)[:20]:
                txt += f"• {get_user_link(uid)}\n"
            await callback.message.reply(txt)
        await callback.answer()

    elif data == "full_stats":
        clicks = len(click_history.get(user_id, []))
        total_msgs = user_message_count[user_id]
        join_time = datetime.fromtimestamp(user_join_time.get(user_id, time.time())).strftime("%Y-%m-%d %H:%M")
        txt = (
            f"📊 **آمار کامل شما**\n\n"
            f"📅 تاریخ ثبت‌نام: {join_time}\n"
            f"👥 کلیک‌ها: {clicks}\n"
            f"💬 پیام‌ها: {total_msgs}\n"
            f"🚫 بلاک‌ها: {len(user_blocked_clickers.get(user_id, set()))}\n"
        )
        await callback.message.reply(txt)
        await callback.answer()

    elif data == "admin_panel":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 ارسال همگانی", callback_data="admin_broadcast"))
        markup.add(InlineKeyboardButton("👥 لیست اعضا", callback_data="admin_members"), row=1)
        markup.add(InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats"), row=2)
        markup.add(InlineKeyboardButton("🚫 مدیریت بن", callback_data="admin_ban"), row=3)
        markup.add(InlineKeyboardButton("📋 گزارش‌ها", callback_data="admin_reports"), row=4)
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"), row=5)
        
        await callback.message.reply("👑 **پنل مدیریت حرفه‌ای**", components=markup)
        await callback.answer()

    elif data == "admin_broadcast":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        user_state[user_id] = "admin_broadcast"
        await callback.message.reply("📢 **پیام همگانی**\n\nمتن مورد نظر رو بنویس:")
        await callback.answer()

    elif data == "admin_members":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        
        members = list(user_join_time.keys())
        if not members:
            await callback.message.reply("📭 هنوز عضوی ثبت نشده!")
            await callback.answer()
            return
        
        txt = "👥 **لیست اعضا:**\n\n"
        for idx, uid in enumerate(members[:50], 1):
            name = "کاربر"
            for hist in click_history.get(uid, []):
                if hist["id"] == uid:
                    name = hist["name"]
                    break
            txt += f"{idx}. {get_user_link(uid, name)} `/ozv{uid}`\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📥 بیشتر", callback_data="admin_members_more"))
        
        await callback.message.reply(txt, components=markup)
        await callback.answer()

    elif data == "admin_members_more":
        await callback.answer("🔜 در حال توسعه...", show_alert=True)

    elif data == "admin_stats":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        
        total_users = len(user_join_time)
        total_clicks = sum(len(v) for v in click_history.values())
        total_reports = sum(len(v) for v in reports.values())
        total_banned = len(banned_users)
        
        txt = (
            f"📊 **آمار کلی ربات**\n\n"
            f"👥 کل کاربران: {total_users}\n"
            f"👀 کل کلیک‌ها: {total_clicks}\n"
            f"📋 گزارش‌ها: {total_reports}\n"
            f"🚫 کاربران بن شده: {total_banned}\n"
            f"⏰ زمان آپدیت: {datetime.now().strftime('%H:%M:%S')}"
        )
        await callback.message.reply(txt)
        await callback.answer()

    elif data == "admin_ban":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔨 بن کردن", callback_data="admin_ban_user"))
        markup.add(InlineKeyboardButton("🔓 آنبن کردن", callback_data="admin_unban_user"), row=1)
        markup.add(InlineKeyboardButton("📋 لیست بن‌ها", callback_data="admin_banned_list"), row=2)
        
        await callback.message.reply("🚫 **مدیریت بن**", components=markup)
        await callback.answer()

    elif data == "admin_ban_user":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        user_state[user_id] = "admin_ban_user"
        await callback.message.reply("🆔 آیدی کاربر مورد نظر برای بن رو بفرست:")
        await callback.answer()

    elif data == "admin_unban_user":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        user_state[user_id] = "admin_unban_user"
        await callback.message.reply("🆔 آیدی کاربر مورد نظر برای آنبن رو بفرست:")
        await callback.answer()

    elif data == "admin_banned_list":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        
        if not banned_users:
            await callback.message.reply("📭 هیچ کاربری بن نیست!")
        else:
            txt = "🚫 **لیست بن‌ها:**\n\n"
            for uid in list(banned_users)[:20]:
                txt += f"• {get_user_link(uid)}\n"
            await callback.message.reply(txt)
        await callback.answer()

    elif data == "admin_reports":
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        
        if not reports:
            await callback.message.reply("📭 هیچ گزارشی موجود نیست!")
            await callback.answer()
            return
        
        txt = "📋 **لیست گزارش‌ها:**\n\n"
        for target_id, report_list in list(reports.items())[:10]:
            txt += f"🔹 کاربر {target_id} - {len(report_list)} گزارش\n"
            for r in report_list[:3]:
                txt += f"   • از {r['from']}: {r['reason'][:30]}...\n"
            txt += "\n"
        
        await callback.message.reply(txt)
        await callback.answer()

    elif data == "back_to_main":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎗️ لینک من", callback_data="my_link"))
        markup.add(InlineKeyboardButton("🎗️ لینک من", callback_data="my_link"))
        markup.add(InlineKeyboardButton("📊 آمار من", callback_data="mystats"), row=1)
        markup.add(InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="user_settings"), row=2)
        
        if user_id == ADMIN_ID:
            markup.add(InlineKeyboardButton("👑 پنل مدیریت", callback_data="admin_panel"), row=3)
        
        await callback.message.reply(
            "❤️ به **مچ‌گیر فضول** خوش اومدی!\n\n"
            "لینک خودت رو بساز و فضول‌ها رو زنده زنده بگیر 😈",
            components=markup
        )
        await callback.answer()

    elif data.startswith("report_"):
        target_id = int(data.split("_")[1])
        user_state[user_id] = f"report_{target_id}"
        await callback.message.reply("📌 مشکل چیه؟ دلیل گزارش رو بنویس:")
        await callback.answer()

    elif data.startswith("admin_edit_text_"):
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        target_id = int(data.split("_")[3])
        user_state[user_id] = f"admin_edit_text_{target_id}"
        await callback.message.reply(f"📝 متن جدید برای کاربر {target_id} رو بنویس:")
        await callback.answer()

    elif data.startswith("admin_toggle_ban_"):
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        target_id = int(data.split("_")[3])
        if target_id in banned_users:
            banned_users.discard(target_id)
            await callback.message.reply(f"✅ کاربر {target_id} آنبن شد.")
        else:
            banned_users.add(target_id)
            await callback.message.reply(f"✅ کاربر {target_id} بن شد.")
        await callback.answer()

    elif data.startswith("admin_sendto_"):
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        target_id = int(data.split("_")[2])
        user_state[user_id] = f"admin_sendto_{target_id}"
        await callback.message.reply(f"📩 پیام خودت رو برای کاربر {target_id} بنویس:")
        await callback.answer()

    elif data.startswith("admin_user_clicks_"):
        if user_id != ADMIN_ID:
            await callback.answer("⛔ فقط ادمین", show_alert=True)
            return
        target_id = int(data.split("_")[3])
        clicks = click_history.get(target_id, [])
        if not clicks:
            await callback.message.reply(f"📭 کاربر {target_id} هیچ کلیکی نداشته!")
        else:
            txt = f"👀 **لیست کلیک‌های کاربر {target_id}**\n\n"
            for idx, click in enumerate(clicks[:20], 1):
                txt += f"{idx}. {click['name']} - {click['time']}\n"
            await callback.message.reply(txt)
        await callback.answer()

# اجرای ربات
if __name__ == "__main__":
    try:
        print("🚀 ربات در حال اجراست...")
        bot.run()
    except Exception as e:
        print(f"❌ خطا: {e}")
