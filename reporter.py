# -*- coding: utf-8 -*-
"""
coding by amirwebcode : telegram = @saeqehe
pip install aiogram rubpy pycryptodome flask
"""

import asyncio
import logging
import os
import random
import re
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15 as pkcs1_15_sig

from rubpy import Client as RubikaClient
from rubpy.crypto import Crypto
from rubpy.enums import ReportType

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Update
from aiogram.enums import ButtonStyle, ChatMemberStatus
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8837671005:AAH8RB-6HeRfk2ROReg7zK5Vlcf751g01kM"
ADMIN_IDS: set[int] = {8503523539}
ADMIN_USERNAME = "@Saeqehe"
ADMIN_CARD_NUMBER = "6219861453153586"
PREMIUM_MONTHS = 1

REQUIRED_CHANNELS = ["mrvpn294", "amirwebcode1"]

FREE_LIMIT = 100
PREMIUM_LIMIT = 1000
PREMIUM_PRICE = "350,000 Toman"
REPORT_DELAY = 3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

REPORT_TYPES_MAP: dict[str, tuple[str, ReportType]] = {
    "1": ("🔞 Pornography", ReportType.PORNOGRAPHY),
    "2": ("⚔️ Violence",     ReportType.VIOLENCE),
    "3": ("📛 Spam",          ReportType.SPAM),
    "4": ("👶 Child Abuse",   ReportType.CHILD_ABUSE),
    "5": ("©️ Copyright",     ReportType.COPYRIGHT),
    "6": ("🎣 Fishing",       ReportType.FISHING),
    "7": ("📝 Other",         ReportType.OTHER),
}

user_stop: dict[int, bool] = {}


# ────────────────────────────────────────────────────────────────────────
#  TRANSLATIONS
# ────────────────────────────────────────────────────────────────────────
T = {
    "fa": {
        "choose_lang": "🌐 زبان خود را انتخاب کنید:\nSelect your language:",
        "welcome": "👋 خوش آمدید!",
        "menu_title": "🏠 منوی اصلی",
        "add_account": "➕ افزودن اکانت",
        "report_abuse": "🚨 گزارش تخلف",
        "block_user": "🚫 بلاک کاربر",
        "leave_channel": "🚪 خروج از کانال",
        "join_channel": "🔗 ورود به کانال",
        "account_status": "📊 وضعیت حساب",
        "block_stats": "📊 آمار بلاک",
        "subscription": "💎 خرید اشتراک",
        "daily_reward": "🎁 جایزه روزانه",
        "referral_link": "🔗 لینک دعوت",
        "help": "❓ راهنما",
        "support": "📞 پشتیبانی",
        "web_app": "🌐 وب اپ",
        "back": "🔙 بازگشت",
        "send_phone": "📱 شماره روبیکا را بفرست:\nمثال: 09123456789",
        "phone_btn": "📱 ارسال شماره تماس",
        "sending_code": "⏳ ارسال کد تایید...",
        "code_sent": "✅ کد تایید ارسال شد!\nکد ۶ رقمی را بفرستید:",
        "password_required": "🔑 این حساب رمز دو مرحله‌ای دارد.\nراهنمایی: {hint}\n\nرمز عبور را وارد کنید:",
        "wrong_password": "❌ رمز اشتباه است. راهنمایی: {hint}\nدوباره:",
        "password_verified": "✅ رمز تایید شد!\nکد ۶ رقمی را بفرستید:",
        "enter_code": "⏳ در حال ورود...",
        "login_success": "✅ ورود موفق!",
        "invalid_phone": "❌ شماره نامعتبر.\nیک شماره معتبر ایرانی وارد کنید.",
        "invalid_code": "❌ کد ۴ تا ۸ رقم باید باشد. دوباره:",
        "error": "❌ {error}\nبا /start دوباره تلاش کن.",
        "login_error": "❌ {error}",
        "force_join": "⛔ برای استفاده از ربات ابتدا باید در کانال‌های زیر عضو شوید:\n\nبعد از عضویت، «بررسی عضویت» را بزنید:",
        "check_membership": "✅ بررسی عضویت",
        "not_joined": "❌ هنوز در کانال‌ها عضو نشدید!\nدر هر دو کانال عضو شوید و دوباره بزنید:",
        "membership_verified": "✅ عضویت تایید شد! 👋",
        "choose_guid_method": "🎯 چطور شناسه هدف را وارد کنیم؟\n\n• با یوزرنیم/آیدی، ربات خودش شناسه را پیدا می‌کند.\n• یا شناسه (object_guid) را دستی بفرست.",
        "get_by_username": "🔍 دریافت با یوزرنیم",
        "enter_guid_manually": "✍️ وارد کردن شناسه دستی",
        "enter_username": "👤 یوزرنیم روبیکا را بفرست:\nمثال: @username",
        "enter_guid": "🎯 شناسه (object_guid) کاربر روبیکا را بفرست:\nمثال: u0A1bC2dE3fG4hI5jK6lM7nO8pQ9rS0T",
        "searching_guid": "⏳ در حال جستجوی شناسه...",
        "guid_found": "✅ شناسه پیدا شد:\n<code>{guid}</code>\n\nنوع گزارش را انتخاب کن:",
        "guid_not_found": "❌ شناسه‌ای پیدا نشد.\nیوزرنیم را درست وارد کن یا شناسه دستی بفرست.",
        "select_report_type": "نوع گزارش را انتخاب کن:",
        "start_report": "▶️ شروع گزارش",
        "enter_other_text": "متن گزارش «سایر» را بنویس:",
        "min_3_chars": "❌ حداقل ۳ کاراکتر بنویس.",
        "report_count_question": "انتخاب: {types}\nچند گزارش از هر نوع؟ (حداکثر {limit})",
        "positive_number": "❌ عدد مpositive وارد کن.",
        "limit_exceeded": "❌ محدودیت پلن: {limit} گزارش.\n💎 اشتراک: {admin}\nعدد کمتر:",
        "delay_question": "⏱️ هر چند ثانیه یک گزارش ارسال شود؟\nمثال: ۳",
        "accounts_question": "👥 تعداد کل اکانت‌ها: {total}\nبا چند اکانت گزارش بزنم؟ (۱ تا {total})",
        "no_accounts": "❌ هیچ اکانتی ثبت نشده. ابتدا «افزودن اکانت» بزنید.",
        "too_many_accounts": "❌ فقط {total} اکانت موجود است. عدد کمتر:",
        "no_types_selected": "❌ حداقل یک نوع گزارش انتخاب کن.",
        "guid_not_found_err": "❌ شناسه یافت نشد. /start بزن.",
        "report_sending": "🚀 ارسال {count} گزارش (هر {delay} ثانیه) با {accounts} اکانت...\n⛔ /stop برای توقف",
        "stop": "⛔ توقف",
        "report_result": "📊 گزارش:\n{lines}",
        "menu_label": "🔵 منو:",
        "start_block": "🚫 بلاک کاربر\n\nشناسه یا یوزرنیم کاربر را بفرست:\nمثال: u0A1b... یا: @username",
        "block_found": "✅ شناسه پیدا شد:\n<code>{guid}</code>\n\n👥 تعداد اکانت‌ها: {total}\nبا چند اکانت بلاک کنم؟ (۱ تا {total})",
        "block_accounts": "⏱️ هر چند ثانیه یک بلاک؟\nمثال: ۲",
        "block_sending": "🚫 شروع بلاک...\n🎯 <code>{guid}</code>\n📱 با {accounts} اکانت\n⏱️ هر {delay} ثانیه\n\n⛔ /stop برای توقف",
        "block_result": "📊 نتیجه بلاک:\n\n🎯 شناسه: <code>{guid}</code>\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📱 با {accounts} اکانت\n\n🏆 مجموع بلاک‌ها: {total}",
        "start_leave": "🚪 خروج از کانال/گروه\n\nشناسه یا یوزرنیم کانال/گروه را بفرست:",
        "leaving": "⏳ در حال خروج از <code>{guid}</code> با {total} اکانت...",
        "leave_result": "📊 نتیجه خروج:\n\n✅ موفق: {success}\n❌ ناموفق: {fail}",
        "start_join": "🔗 ورود به کانال/گروه\n\nلینک دعوت را بفرست:\nمثال: https://rubika.ir/channel/...",
        "invalid_link": "❌ لینک نامعتبر. لینک دعوت را بفرست.",
        "joining": "⏳ در حال ورود با {total} اکانت...",
        "join_result": "📊 نتیجه ورود:\n\n✅ موفق: {success}\n❌ نامINUX: {fail}",
        "block_stats_title": "📊 آمار بلاک کاربر\n\n🏆 مجموع: {total}\n\nاخیراً:",
        "no_blocks": "🚫 هیچ بلاکی ثبت نشده.",
        "block_stat_item": "👤 {name}\n   📱 با {accounts} اکانت | 🚫 {blocks} بار\n   📅 {date}",
        "account_status_title": "📊 وضعیت حساب\n\nپلن: {plan}\nمحدودیت: {limit}\n📊 گزارشات: {reports}\n🚫 بلاک‌ها: {blocks}\n📱 شماره: {phone}",
        "plan_premium": "👑 اشتراکی",
        "plan_free": "🆓 رایگان",
        "sub_active": "👑 اشتراک تا {date} فعال است.",
        "sub_buy": "💎 خرید اشتراک یک ماهه\n📊 {limit} گزارش\n💰 مبلغ: {price}\n\n💳 شماره کارت:\n{card}\n\n📸 عکس رسید را بفرستید.",
        "receipt_sent": "✅ رسید برای ادمین ارسال شد!\n💰 مبلغ: {price}\n⏳ منتظر تایید ادمین.",
        "help_text": (
            "❓ راهنما\n\n"
            "🚀 قابلیت‌ها:\n\n"
            "➕ افزودن اکانت: شماره روبیکا اضافه کن\n"
            "🚨 گزارش تخلف: با چند اکانت گزارش بزن\n"
            "🚫 بلاک کاربر: کاربر را بلاک کن\n"
            "🚪 خروج از کانال: از کانال/گروه خارج شو\n"
            "🔗 ورود به کانال: به کانال/گروه وارد شو\n\n"
            f"🆓 رایگان: {FREE_LIMIT} گزارش\n"
            f"💎 اشتراکی: {PREMIUM_LIMIT} گزارش\n\n"
            "برای توقف /stop"
        ),
        "referral_text": "🔗 لینک دعوت شما\n\n📱 لینک:\n{link}\n\n👥 تعداد دعوت‌ها: {invites}\n\n🎁 ۱ ساعت اشتراک رایگان به ازای هر نفر!",
        "support_text": "📞 پشتیبانی\n\nپیام، عکس یا فایل خود را بفرستید.",
        "support_sent": "✅ پیام برای پشتیبانی ارسال شد.\nمنتظر پاسخ بمانید.",
        "support_fail": "❌ ارسال ناموفق. بعداً تلاش کنید.",
        "daily_no_reward": "⏳ جایزه بعدی در {hours} ساعت و {minutes} دقیقه",
        "daily_rolling": "🎲",
        "daily_6": "🏆 شماره ۶! اشتراک ۳ روزه برنده شدید!",
        "daily_45": "🎉 شماره ۴ یا ۵! اشتراک ۱ روزه برنده شدید!",
        "daily_loose": "😔 شماره {roll} آمد. برنده نشدید!",
        "daily_prize": "\n\n👑 اشتراک تا {date} فعال است.\n📊 محدودیت: {limit} گزارش",
        "daily_try_again": "\n\n💡 فردا دوباره امتحان کنید!",
        "ref_start": "🎁 یک نفر با لینک دعوت شما عضو شد!\n👑 ۱ ساعت اشتراک رایگان اضافه شد.\n📊 مجموع دعوت‌ها: {count}",
        "grant_usage": "/grant <telegram_id> [months]",
        "grant_done": "✅ اشتراک {months} ماهه برای {target}",
        "grant_error": "خطا در آرگومان‌ها.",
        "stats_title": "📊 آمار\n👥 {total}\n👑 {premium}\n📢 {reports}\n🚫 {blocks}",
        "admin_panel": "🛠 پنل مدیریت",
        "admin_broadcast": "📢 پیام همگانی\nپیام، عکس یا فایل را بفرستید:",
        "admin_broadcast_done": "✅ پیام همگانی ارسال شد.\nموفق: {success}\nناموفق: {fail}",
        "admin_stats": (
            "📊 آمار ربات\n\n"
            "👥 کل کاربران: {total}\n"
            "👑 اشتراکی‌ها: {premium}\n"
            "🔐 سشن‌های فعال: {sessions}\n"
            "📢 کل گزارشات: {reports}\n"
            "🚫 کل بلاک‌ها: {blocks}"
        ),
        "admin_grant": "👑 تمدید اشتراک\nفرمت: <telegram_id> <months>\nمثال: 123456789 1",
        "admin_support": "💬 پشتیبانی\nوقتی کاربری پیام بفرستد، فوروارد می‌شود.",
        "admin_list_title": "📨 لیست کاربران (آخرین ۳۰ نفر):",
        "admin_no_users": "هیچ کاربری ثبت نشده.",
        "admin_block_stats": "📊 آمار بلاک کل\n\nتعداد کل: {total}",
        "admin_no_blocks": "هیچ آمار بلاکی ثبت نشده.",
        "admin_reply": "💬 در حال پاسخ به کاربر {target}\nپیام را بفرستید:",
        "admin_reply_sent": "✅ پاسخ برای کاربر ارسال شد.",
        "admin_reply_fail": "❌ ارسال پاسخ ناموفق: {error}",
        "admin_ticket_closed": "\n\n🚫 تیکت بسته شد.",
        "need_login": "❌ ابتدا /start بزن و وارد حساب روبیکا شو.",
        "session_expired": "❌ سشن منقضی شده. /start بزن و دوباره لاگین کن.",
        "session_invalid": "❌ سشن معتبر نیست. /start بزن.",
        "positive_seconds": "❌ عدد مثبت (ثانیه) وارد کن.",
        "grant_format_error": "❌ فرمت نادرست. مثال: 123456789 1",
        "reply_usage": "/reply <telegram_id> متن پاسخ",
        "reply_sent": "✅ پاسخ ارسال شد.",
        "reply_error": "❌ خطا: {error}",
        "error_generic": "❌ خطا:\n{error}",
        "ticket_reply_label": "💬 پاسخ پشتیبانی:\n{text}",
        "support_forward": "📨 پیام پشتیبانی جدید\n👤 کاربر: {phone}\n🆔 تلگرام: {tg_id}",
        "approve_yes": "✅ تایید",
        "approve_no": "❌ رد",
        "receipt_caption": (
            "💎 رسید پرداخت اشتراک\n\n"
            "👤 کاربر: {phone}\n"
            "🆔 تلگرام: {tg_id}\n"
            "💰 مبلغ: {price}\n"
            "⏰ تاریخ: {date}"
        ),
        "sub_approved": "✅ اشتراک فعال شد!\n👤 کاربر: {target}",
        "sub_approved_user": "🎉 اشتراک شما فعال شد!\n\n👑 تا {date} فعال\n📊 محدودیت: {limit} گزارش",
        "sub_rejected": "❌ درخواست رد شد.\n👤 کاربر: {target}",
        "sub_rejected_user": "❌ درخواست اشتراک شما رد شد.\nبا ادمین تماس بگیرید.",
        "close_ticket": "🚫 بستن",
        "reply_to_user": "💬 پاسخ به کاربر",
    },
    "en": {
        "choose_lang": "🌐 Choose your language:\nزبان خود را انتخاب کنید:",
        "welcome": "👋 Welcome!",
        "menu_title": "🏠 Main Menu",
        "add_account": "➕ Add Account",
        "report_abuse": "🚨 Report Abuse",
        "block_user": "🚫 Block User",
        "leave_channel": "🚪 Leave Channel",
        "join_channel": "🔗 Join Channel",
        "account_status": "📊 Account Status",
        "block_stats": "📊 Block Stats",
        "subscription": "💎 Subscription",
        "daily_reward": "🎁 Daily Reward",
        "referral_link": "🔗 Referral Link",
        "help": "❓ Help",
        "support": "📞 Support",
        "web_app": "🌐 Web App",
        "back": "🔙 Back",
        "send_phone": "📱 Send your Rubika phone number:\nExample: 09123456789",
        "phone_btn": "📱 Send Phone Number",
        "sending_code": "⏳ Sending verification code...",
        "code_sent": "✅ Code sent!\nEnter the 6-digit code:",
        "password_required": "🔑 This account has 2FA.\nHint: {hint}\n\nEnter your password:",
        "wrong_password": "❌ Wrong password. Hint: {hint}\nTry again:",
        "password_verified": "✅ Password verified!\nEnter the 6-digit code:",
        "enter_code": "⏳ Logging in...",
        "login_success": "✅ Login successful!",
        "invalid_phone": "❌ Invalid phone.\nEnter a valid Iranian number.",
        "invalid_code": "❌ Code must be 4-8 digits. Try again:",
        "error": "❌ {error}\nTry /start again.",
        "login_error": "❌ {error}",
        "force_join": "⛔ You must join these channels first:\n\nAfter joining, tap «Check Membership»:",
        "check_membership": "✅ Check Membership",
        "not_joined": "❌ Not a member yet!\nJoin both channels and try again:",
        "membership_verified": "✅ Membership verified! 👋",
        "choose_guid_method": "🎯 How to enter target ID?\n\n• Username: bot resolves it automatically.\n• Or enter object_guid manually.",
        "get_by_username": "🔍 Get by Username",
        "enter_guid_manually": "✍️ Enter GUID Manually",
        "enter_username": "👤 Enter Rubika username:\nExample: @username",
        "enter_guid": "🎯 Enter user object_guid:\nExample: u0A1bC2dE3fG4hI5jK6lM7nO8pQ9rS0T",
        "searching_guid": "⏳ Searching for ID...",
        "guid_found": "✅ ID found:\n<code>{guid}</code>\n\nSelect report type:",
        "guid_not_found": "❌ ID not found.\nCheck username or enter GUID manually.",
        "select_report_type": "Select report type:",
        "start_report": "▶️ Start Report",
        "enter_other_text": "Enter custom report text:",
        "min_3_chars": "❌ Minimum 3 characters.",
        "report_count_question": "Selected: {types}\nHow many reports per type? (max {limit})",
        "positive_number": "❌ Enter a positive number.",
        "limit_exceeded": "❌ Plan limit: {limit} reports.\n💎 Subscription: {admin}\nEnter lower:",
        "delay_question": "⏱️ Report interval in seconds?\nExample: 3",
        "accounts_question": "👥 Total accounts: {total}\nHow many to use? (1 to {total})",
        "no_accounts": "❌ No accounts registered. Tap «Add Account» first.",
        "too_many_accounts": "❌ Only {total} accounts available. Enter lower:",
        "no_types_selected": "❌ Select at least one report type.",
        "guid_not_found_err": "❌ ID not found. Try /start.",
        "report_sending": "🚀 Sending {count} reports (every {delay}s) with {accounts} accounts...\n⛔ /stop to stop",
        "stop": "⛔ Stopped",
        "report_result": "📊 Report:\n{lines}",
        "menu_label": "🔵 Menu:",
        "start_block": "🚫 Block User\n\nEnter user ID or username:\nExample: u0A1b... or: @username",
        "block_found": "✅ ID found:\n<code>{guid}</code>\n\n👥 Accounts: {total}\nHow many to block with? (1 to {total})",
        "block_accounts": "⏱️ Block interval in seconds?\nExample: 2",
        "block_sending": "🚫 Blocking...\n🎯 <code>{guid}</code>\n📱 {accounts} accounts\n⏱️ Every {delay}s\n\n⛔ /stop to stop",
        "block_result": "📊 Block Result:\n\n🎯 ID: <code>{guid}</code>\n✅ Success: {sent}\n❌ Failed: {failed}\n📱 {accounts} accounts\n\n🏆 Total blocks: {total}",
        "start_leave": "🚪 Leave Channel/Group\n\nEnter channel/group ID or username:",
        "leaving": "⏳ Leaving <code>{guid}</code> with {total} accounts...",
        "leave_result": "📊 Leave Result:\n\n✅ Success: {success}\n❌ Failed: {fail}",
        "start_join": "🔗 Join Channel/Group\n\nEnter invite link:\nExample: https://rubika.ir/channel/...",
        "invalid_link": "❌ Invalid link. Enter the invite link.",
        "joining": "⏳ Joining with {total} accounts...",
        "join_result": "📊 Join Result:\n\n✅ Success: {success}\n❌ Failed: {fail}",
        "block_stats_title": "📊 Block Stats\n\n🏆 Total: {total}\n\nRecent:",
        "no_blocks": "🚫 No blocks recorded.",
        "block_stat_item": "👤 {name}\n   📱 {accounts} accounts | 🚫 {blocks} times\n   📅 {date}",
        "account_status_title": "📊 Account Status\n\nPlan: {plan}\nLimit: {limit}\n📊 Reports: {reports}\n🚫 Blocks: {blocks}\n📱 Phone: {phone}",
        "plan_premium": "👑 Premium",
        "plan_free": "🆓 Free",
        "sub_active": "👑 Subscription active until {date}.",
        "sub_buy": "💎 Buy 1-month subscription\n📊 {limit} reports\n💰 Price: {price}\n\n💳 Card number:\n{card}\n\n📸 Send payment receipt photo.",
        "receipt_sent": "✅ Receipt sent to admin!\n💰 Price: {price}\n⏳ Waiting for admin approval.",
        "help_text": (
            "❓ Help\n\n"
            "🚀 Features:\n\n"
            "➕ Add Account: Add Rubika account\n"
            "🚨 Report Abuse: Report with multiple accounts\n"
            "🚫 Block User: Block a user\n"
            "🚪 Leave Channel: Leave a channel/group\n"
            "🔗 Join Channel: Join a channel/group\n\n"
            f"🆓 Free: {FREE_LIMIT} reports\n"
            f"💎 Premium: {PREMIUM_LIMIT} reports\n\n"
            "Use /stop to stop"
        ),
        "referral_text": "🔗 Your Referral Link\n\n📱 Link:\n{link}\n\n👥 Invites: {invites}\n\n🎁 1 hour free subscription per invite!",
        "support_text": "📞 Support\n\nSend your message, photo or file.",
        "support_sent": "✅ Message sent to support.\nWait for a response.",
        "support_fail": "❌ Failed to send. Try later.",
        "daily_no_reward": "⏳ Next reward in {hours}h {minutes}m",
        "daily_rolling": "🎲",
        "daily_6": "🏆 Rolled 6! 3-day premium subscription!",
        "daily_45": "🎉 Rolled 4 or 5! 1-day premium subscription!",
        "daily_loose": "😔 Rolled {roll}. Better luck next time!",
        "daily_prize": "\n\n👑 Active until {date}\n📊 Limit: {limit} reports",
        "daily_try_again": "\n\n💡 Try again tomorrow!",
        "ref_start": "🎁 Someone joined via your referral!\n👑 1 hour free subscription added.\n📊 Total invites: {count}",
        "grant_usage": "/grant <telegram_id> [months]",
        "grant_done": "✅ {months}-month subscription for {target}",
        "grant_error": "Invalid arguments.",
        "stats_title": "📊 Stats\n👥 {total}\n👑 {premium}\n📢 {reports}\n🚫 {blocks}",
        "admin_panel": "🛠 Admin Panel",
        "admin_broadcast": "📢 Broadcast\nSend message, photo or file:",
        "admin_broadcast_done": "✅ Broadcast sent.\nSuccess: {success}\nFailed: {fail}",
        "admin_stats": (
            "📊 Bot Stats\n\n"
            "👥 Total Users: {total}\n"
            "👑 Premium: {premium}\n"
            "🔐 Active Sessions: {sessions}\n"
            "📢 Total Reports: {reports}\n"
            "🚫 Total Blocks: {blocks}"
        ),
        "admin_grant": "👑 Grant Subscription\nFormat: <telegram_id> <months>\nExample: 123456789 1",
        "admin_support": "💬 Support\nUser messages will be forwarded here.",
        "admin_list_title": "📨 User List (last 30):",
        "admin_no_users": "No users registered.",
        "admin_block_stats": "📊 Block Stats\n\nTotal: {total}",
        "admin_no_blocks": "No block stats recorded.",
        "admin_reply": "💬 Replying to user {target}\nSend your message:",
        "admin_reply_sent": "✅ Reply sent to user.",
        "admin_reply_fail": "❌ Reply failed: {error}",
        "admin_ticket_closed": "\n\n🚫 Ticket closed.",
        "need_login": "❌ Please /start and login first.",
        "session_expired": "❌ Session expired. /start and login again.",
        "session_invalid": "❌ Invalid session. /start.",
        "positive_seconds": "❌ Enter a positive number (seconds).",
        "grant_format_error": "❌ Wrong format. Example: 123456789 1",
        "reply_usage": "/reply <telegram_id> reply text",
        "reply_sent": "✅ Reply sent.",
        "reply_error": "❌ Error: {error}",
        "error_generic": "❌ Error:\n{error}",
        "ticket_reply_label": "💬 Support Reply:\n{text}",
        "support_forward": "📨 New Support Message\n👤 User: {phone}\n🆔 Telegram: {tg_id}",
        "approve_yes": "✅ Approve",
        "approve_no": "❌ Reject",
        "receipt_caption": (
            "💎 Subscription Payment Receipt\n\n"
            "👤 User: {phone}\n"
            "🆔 Telegram: {tg_id}\n"
            "💰 Amount: {price}\n"
            "⏰ Date: {date}"
        ),
        "sub_approved": "✅ Subscription activated!\n👤 User: {target}",
        "sub_approved_user": "🎉 Your subscription is active!\n\n👑 Until {date}\n📊 Limit: {limit} reports",
        "sub_rejected": "❌ Request rejected.\n👤 User: {target}",
        "sub_rejected_user": "❌ Subscription request rejected.\nContact admin.",
        "close_ticket": "🚫 Close",
        "reply_to_user": "💬 Reply to User",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    text = T.get(lang, T["en"]).get(key, T["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


# ────────────────────────────────────────────────────────────────────────
#  FSM
# ────────────────────────────────────────────────────────────────────────
class Form(StatesGroup):
    choose_lang       = State()
    main_menu         = State()
    phone             = State()
    password          = State()
    code              = State()
    report_guid       = State()
    report_resolve    = State()
    report_types      = State()
    report_other_text = State()
    report_count      = State()
    report_delay      = State()
    report_accounts   = State()
    receipt           = State()
    support_message   = State()
    admin_panel       = State()
    broadcast         = State()
    admin_reply       = State()
    block_guid        = State()
    block_count       = State()
    block_delay       = State()
    leave_guid        = State()
    join_link         = State()


# ────────────────────────────────────────────────────────────────────────
#  DB
# ────────────────────────────────────────────────────────────────────────
def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id        INTEGER PRIMARY KEY,
                phone              TEXT,
                rubika_session     TEXT,
                rubika_auth        TEXT,
                rubika_private_key TEXT,
                is_premium         INTEGER DEFAULT 0,
                premium_until      TEXT,
                coins              INTEGER DEFAULT 0,
                total_reports      INTEGER DEFAULT 0,
                total_invites      INTEGER DEFAULT 0,
                language           TEXT DEFAULT 'fa',
                last_daily_reward  TEXT,
                created_at         TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS block_stats (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                target_guid  TEXT,
                target_name  TEXT,
                blocker_tg   INTEGER,
                accounts_used INTEGER DEFAULT 1,
                total_blocks INTEGER DEFAULT 1,
                blocked_at   TEXT DEFAULT (datetime('now'))
            )
        """)
        for col, ctype in [
            ("rubika_auth", "TEXT"),
            ("rubika_private_key", "TEXT"),
            ("last_daily_reward", "TEXT"),
            ("language", "TEXT DEFAULT 'fa'"),
        ]:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} {ctype}")
            except sqlite3.OperationalError:
                pass
        conn.commit()

def get_user(telegram_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return dict(row) if row else None

def upsert_user(telegram_id: int, **kwargs) -> None:
    existing = get_user(telegram_id)
    with sqlite3.connect(DB_PATH) as conn:
        if existing:
            sets = ", ".join(f"{k} = ?" for k in kwargs)
            conn.execute(
                f"UPDATE users SET {sets} WHERE telegram_id = ?",
                (*kwargs.values(), telegram_id),
            )
        else:
            kwargs["telegram_id"] = telegram_id
            cols = ", ".join(kwargs.keys())
            placeholders = ", ".join("?" * len(kwargs))
            conn.execute(
                f"INSERT INTO users ({cols}) VALUES ({placeholders})",
                tuple(kwargs.values()),
            )
        conn.commit()

def add_stats(telegram_id: int, sent: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET total_reports = total_reports + ? WHERE telegram_id = ?",
            (sent, telegram_id),
        )
        conn.commit()

def get_all_users() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM users").fetchall()
    return [dict(r) for r in rows]

def count_users() -> int:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

def get_all_valid_sessions() -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT rubika_session FROM users WHERE rubika_session IS NOT NULL"
        ).fetchall()
    return [r["rubika_session"] for r in rows if session_exists(r["rubika_session"])]

def is_premium_active(user: dict) -> bool:
    if not user.get("is_premium"):
        return False
    until = user.get("premium_until")
    if not until:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(until)
    except (ValueError, TypeError):
        return False

def set_premium(telegram_id: int, months: int = 1) -> None:
    until = (datetime.now() + timedelta(days=30 * months)).isoformat()
    upsert_user(telegram_id, is_premium=1, premium_until=until)


# ────────────────────────────────────────────────────────────────────────
#  Block Stats DB
# ────────────────────────────────────────────────────────────────────────
def record_block(target_guid: str, target_name: str, blocker_tg: int, accounts_used: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT id FROM block_stats WHERE target_guid = ? AND blocker_tg = ?",
            (target_guid, blocker_tg),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE block_stats SET total_blocks = total_blocks + 1, accounts_used = ?, blocked_at = datetime('now') WHERE id = ?",
                (accounts_used, existing[0]),
            )
        else:
            conn.execute(
                "INSERT INTO block_stats (target_guid, target_name, blocker_tg, accounts_used, total_blocks) VALUES (?, ?, ?, ?, 1)",
                (target_guid, target_name, blocker_tg, accounts_used),
            )
        conn.commit()

def get_block_stats(telegram_id: int) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM block_stats WHERE blocker_tg = ? ORDER BY blocked_at DESC",
            (telegram_id,),
        ).fetchall()
    return [dict(r) for r in rows]

def get_total_blocks(telegram_id: int) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute(
            "SELECT COALESCE(SUM(total_blocks), 0) FROM block_stats WHERE blocker_tg = ?",
            (telegram_id,),
        ).fetchone()
        return result[0] if result else 0

def get_all_block_stats() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM block_stats ORDER BY blocked_at DESC").fetchall()
    return [dict(r) for r in rows]


# ────────────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────────────
def _normalize_phone(phone: str) -> Optional[str]:
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    phone = phone.translate(trans)
    phone = re.sub(r"[^\d+]", "", phone)
    if phone.startswith("+98"):
        phone = "98" + phone[3:]
    elif phone.startswith("0098"):
        phone = "98" + phone[4:]
    elif phone.startswith("0"):
        phone = "98" + phone[1:]
    elif not phone.startswith("98") and len(phone) == 10:
        phone = "98" + phone
    if re.match(r"^98\d{10}$", phone):
        return phone
    return None

SESSION_EXTENSIONS = (".rp", ".rubika", ".session")

def session_exists(session_path: str | None) -> bool:
    if not session_path:
        return False
    return any(os.path.isfile(session_path + ext) for ext in SESSION_EXTENSIONS) or os.path.isfile(session_path)

GUID_PREFIXES = ("u0", "c0", "g0", "b0", "m0", "s0", "o0", "p0", "ch0", "t0", "e0")

def looks_like_guid(text: str) -> bool:
    text = text.strip()
    if any(text.startswith(p) for p in GUID_PREFIXES):
        return bool(re.match(r"^(u0|c0|g0|b0|m0|s0|o0|p0|ch0|t0|e0)[A-Za-z0-9_\-]{6,}$", text))
    return False

def cleanup_session_files(session_path: str | None) -> None:
    if not session_path:
        return
    for f in [session_path] + [session_path + ext for ext in SESSION_EXTENSIONS]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

def get_lang(user: dict | None) -> str:
    if user and user.get("language"):
        return user["language"]
    return "fa"


# ────────────────────────────────────────────────────────────────────────
#  Force Join
# ────────────────────────────────────────────────────────────────────────
async def check_user_membership(bot: Bot, user_id: int) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                return False
        except Exception:
            return False
    return True

def kb_force_join(lang: str) -> InlineKeyboardMarkup:
    buttons = []
    for ch in REQUIRED_CHANNELS:
        buttons.append([InlineKeyboardButton(text=f"📢 @{ch}", url=f"https://t.me/{ch}", style=ButtonStyle.PRIMARY)])
    buttons.append([InlineKeyboardButton(text=t(lang, "check_membership"), callback_data="check_join", style=ButtonStyle.SUCCESS)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ────────────────────────────────────────────────────────────────────────
#  Rubika auth
# ────────────────────────────────────────────────────────────────────────
async def rubika_send_code(phone: str, pass_key: str = None) -> dict:
    tmp_path = os.path.join(SESSIONS_DIR, f"tmp_{phone}")
    client = RubikaClient(name=tmp_path)
    await client.connect()
    try:
        kwargs = {"phone_number": phone, "send_type": "SMS"}
        if pass_key is not None:
            kwargs["pass_key"] = pass_key
        result = await client.send_code(**kwargs)
        return {
            "status": result.status,
            "phone_code_hash": result.phone_code_hash,
            "hint_pass_key": getattr(result, "hint_pass_key", None),
        }
    except Exception as e:
        raise RuntimeError(str(e))
    finally:
        await client.disconnect()
        cleanup_session_files(tmp_path)

async def rubika_sign_in(phone: str, code: str, phone_code_hash: str) -> dict:
    session_name = f"user_{phone}"
    session_path = os.path.join(SESSIONS_DIR, session_name)
    client = RubikaClient(name=session_path)
    await client.connect()
    try:
        public_key, private_key = Crypto.create_keys()
        result = await client.sign_in(
            phone_code=code,
            phone_number=phone,
            phone_code_hash=phone_code_hash,
            public_key=public_key,
        )
        if result.status != "OK":
            raise RuntimeError(f"Login failed: {result.status}")

        decrypted_auth = Crypto.decrypt_RSA_OAEP(private_key, result.auth)

        client.auth = decrypted_auth
        client.key = Crypto.passphrase(decrypted_auth)
        client.decode_auth = Crypto.decode_auth(decrypted_auth)
        client.import_key = pkcs1_15_sig.new(RSA.import_key(private_key.encode()))
        client.private_key = private_key
        client.guid = result.user.user_guid

        client.session.insert(
            auth=decrypted_auth,
            guid=result.user.user_guid,
            user_agent=client.user_agent,
            phone_number=phone,
            private_key=private_key,
        )

        await client.register_device(device_model=session_name)
        await client.disconnect()

        return {
            "session_path": session_path,
            "auth": decrypted_auth,
            "private_key": private_key,
        }
    except Exception as e:
        await client.disconnect()
        cleanup_session_files(session_path)
        raise RuntimeError(str(e))


# ────────────────────────────────────────────────────────────────────────
#  Keyboards
# ────────────────────────────────────────────────────────────────────────
def kb_phone(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "phone_btn"), request_contact=True)]],
        resize_keyboard=True,
    )

def kb_main(lang: str, premium: bool) -> InlineKeyboardMarkup:
    plan_label = t(lang, "subscription")
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "add_account"), callback_data="add_account", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text=t(lang, "report_abuse"), callback_data="start_report", style=ButtonStyle.DANGER),
        ],
        [
            InlineKeyboardButton(text=t(lang, "block_user"), callback_data="start_block", style=ButtonStyle.DANGER),
            InlineKeyboardButton(text=t(lang, "leave_channel"), callback_data="start_leave", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(text=t(lang, "join_channel"), callback_data="start_join", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=t(lang, "account_status"), callback_data="account_status", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(text=t(lang, "block_stats"), callback_data="block_stats", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=t(lang, "daily_reward"), callback_data="daily_reward", style=ButtonStyle.SUCCESS),
        ],
        [
            InlineKeyboardButton(text=t(lang, "referral_link"), callback_data="referral_link", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=t(lang, "help"), callback_data="help", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(text=t(lang, "web_app"), url="https://reporter-rubika-production.up.railway.app", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text=t(lang, "support"), callback_data="support", style=ButtonStyle.DANGER),
        ],
    ])

def kb_menu_return(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "back"), callback_data="back_menu", style=ButtonStyle.PRIMARY)],
    ])

def kb_lang_choice() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="lang_fa", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en", style=ButtonStyle.PRIMARY)],
    ])

def kb_admin_panel(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 " + ("همگانی" if lang == "fa" else "Broadcast"), callback_data="admin_broadcast", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text=t(lang, "account_status"), callback_data="admin_stats", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(text="👑 " + ("تمدید" if lang == "fa" else "Grant"), callback_data="admin_grant", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text=t(lang, "support"), callback_data="admin_support", style=ButtonStyle.DANGER),
        ],
        [
            InlineKeyboardButton(text=t(lang, "block_stats"), callback_data="admin_block_stats", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="📨 " + ("کاربران" if lang == "fa" else "Users"), callback_data="admin_list", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(text="🚪 " + ("خروج" if lang == "fa" else "Exit"), callback_data="admin_exit", style=ButtonStyle.DANGER),
        ],
    ])

def kb_support(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "back"), callback_data="back_menu", style=ButtonStyle.PRIMARY)],
    ])

def kb_admin_reply(user_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "reply_to_user"), callback_data=f"admin_reply_{user_id}", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text=t(lang, "close_ticket"), callback_data="admin_close_ticket", style=ButtonStyle.DANGER)],
    ])

def kb_report_types(lang: str, selected: set) -> InlineKeyboardMarkup:
    buttons = []
    report_labels = {
        "fa": {"1": "🔞 مستهجن", "2": "⚔️ خشونت", "3": "📛 اسپم", "4": "👶 کودک‌آزاری", "5": "©️ نقض حق‌نشر", "6": "🎣 فیشینگ", "7": "📝 سایر"},
        "en": {"1": "🔞 Pornography", "2": "⚔️ Violence", "3": "📛 Spam", "4": "👶 Child Abuse", "5": "©️ Copyright", "6": "🎣 Fishing", "7": "📝 Other"},
    }
    labels = report_labels.get(lang, report_labels["en"])
    for k in ["1", "2", "3", "4", "5", "6", "7"]:
        mark = "✅" if k in selected else "⬜"
        style = ButtonStyle.SUCCESS if k in selected else ButtonStyle.PRIMARY
        buttons.append([InlineKeyboardButton(text=f"{mark} {labels[k]}", callback_data=f"rt_{k}", style=style)])
    buttons.append([InlineKeyboardButton(text=t(lang, "start_report"), callback_data="rt_confirm", style=ButtonStyle.SUCCESS)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def kb_report_guid_choice(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "get_by_username"), callback_data="get_by_username", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text=t(lang, "enter_guid_manually"), callback_data="enter_guid", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text=t(lang, "back"), callback_data="back_menu", style=ButtonStyle.PRIMARY)],
    ])


# ────────────────────────────────────────────────────────────────────────
#  Resolve GUID
# ────────────────────────────────────────────────────────────────────────
async def resolve_object_guid(session_path: str, text: str) -> Optional[str]:
    text = text.strip().lstrip("@").strip()
    if looks_like_guid(text):
        return text
    try:
        client = RubikaClient(name=session_path)
        async with client:
            result = await client.get_object_by_username(text)
            for attr in ("object_guid", "user_guid", "guid", "group_guid", "channel_guid"):
                val = getattr(result, attr, None)
                if val and looks_like_guid(val):
                    return val
            found = _search_guid_in(result)
            if found:
                return found
            return None
    except Exception as exc:
        logger.error("resolve_object_guid: %s", exc)
        return None

def _search_guid_in(obj, _seen: set | None = None) -> Optional[str]:
    if _seen is None:
        _seen = set()
    if obj is None or isinstance(obj, (int, float, bool)):
        return None
    if isinstance(obj, str):
        return obj if looks_like_guid(obj) else None
    try:
        if id(obj) in _seen:
            return None
        _seen.add(id(obj))
    except TypeError:
        pass
    if isinstance(obj, dict):
        for v in obj.values():
            r = _search_guid_in(v, _seen)
            if r:
                return r
    else:
        for attr in dir(obj):
            if attr.startswith("_"):
                continue
            try:
                v = getattr(obj, attr)
            except Exception:
                continue
            if callable(v):
                continue
            r = _search_guid_in(v, _seen)
            if r:
                return r
    return None


# ────────────────────────────────────────────────────────────────────────
#  Rubika Block / Leave / Join
# ────────────────────────────────────────────────────────────────────────
async def rubika_block_user(session_path: str, user_guid: str) -> bool:
    try:
        client = RubikaClient(name=session_path)
        async with client:
            await client.set_block_user(user_guid, action="Block")
            return True
    except Exception as exc:
        logger.error("rubika_block_user: %s", exc)
        return False

async def rubika_leave_chat(session_path: str, object_guid: str) -> bool:
    try:
        client = RubikaClient(name=session_path)
        async with client:
            await client.leave_chat(object_guid)
            return True
    except Exception as exc:
        logger.error("rubika_leave_chat: %s", exc)
        return False

async def rubika_join_chat(session_path: str, link: str) -> bool:
    try:
        client = RubikaClient(name=session_path)
        async with client:
            await client.join_chat(link)
            return True
    except Exception as exc:
        logger.error("rubika_join_chat: %s", exc)
        return False


# ────────────────────────────────────────────────────────────────────────
#  /start
# ────────────────────────────────────────────────────────────────────────
async def cmd_start(message: Message, command: CommandStart, state: FSMContext) -> None:
    tg_id = message.from_user.id
    await state.clear()

    user = get_user(tg_id)
    if user and user.get("language"):
        lang = user["language"]
    else:
        await message.answer(
            "🌐 Choose your language:\nزبان خود را انتخاب کنید:",
            reply_markup=kb_lang_choice(),
        )
        await state.set_state(Form.choose_lang)
        return

    args = (command.args or "").split()
    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0][4:])
            if referrer_id != tg_id:
                await state.update_data(referrer_id=referrer_id)
        except (ValueError, IndexError):
            pass

    is_member = await check_user_membership(message.bot, tg_id)
    if not is_member:
        await message.answer(t(lang, "force_join"), reply_markup=kb_force_join(lang))
        return

    if user and user.get("rubika_session") and session_exists(user["rubika_session"]):
        premium = is_premium_active(user)
        await message.answer(t(lang, "welcome"), reply_markup=kb_main(lang, premium))
        await state.set_state(Form.main_menu)
        return

    premium = is_premium_active(user) if user else False
    await message.answer(t(lang, "welcome"), reply_markup=kb_main(lang, premium))
    await state.set_state(Form.main_menu)


# ────────────────────────────────────────────────────────────────────────
#  Language choice
# ────────────────────────────────────────────────────────────────────────
async def choose_language(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = callback.data
    tg_id = callback.from_user.id

    if data == "lang_fa":
        lang = "fa"
    elif data == "lang_en":
        lang = "en"
    else:
        return

    upsert_user(tg_id, language=lang)
    user = get_user(tg_id)

    is_member = await check_user_membership(callback.bot, tg_id)
    if not is_member:
        await callback.message.answer(t(lang, "force_join"), reply_markup=kb_force_join(lang))
        return

    premium = is_premium_active(user) if user else False
    await callback.message.answer(t(lang, "welcome"), reply_markup=kb_main(lang, premium))
    await state.set_state(Form.main_menu)


# ────────────────────────────────────────────────────────────────────────
#  Phone / Password / Code (Add Account)
# ────────────────────────────────────────────────────────────────────────
async def receive_phone(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    if message.contact:
        phone_raw = message.contact.phone_number
    else:
        phone_raw = message.text.strip()

    normalized = _normalize_phone(phone_raw)
    if not normalized:
        await message.answer(t(lang, "invalid_phone"), reply_markup=kb_phone(lang))
        return

    await state.update_data(phone=normalized)
    await message.answer(t(lang, "sending_code"), reply_markup=ReplyKeyboardRemove())

    try:
        result = await rubika_send_code(normalized)
        await state.update_data(phone_code_hash=result["phone_code_hash"])

        if result.get("status") == "SendPassKey":
            hint = result.get("hint_pass_key", "")
            await state.update_data(needs_password=True)
            await message.answer(t(lang, "password_required", hint=hint))
            await state.set_state(Form.password)
            return

        await state.update_data(needs_password=False)
        await message.answer(t(lang, "code_sent"))
        await state.set_state(Form.code)

    except Exception as exc:
        logger.error("send_code: %s", exc)
        await message.answer(t(lang, "error", error=str(exc)))
        await state.clear()


async def receive_password(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    password = message.text.strip() if message.text else ""
    data = await state.get_data()
    phone = data.get("phone", "")

    if not password:
        await message.answer(t(lang, "wrong_password", hint=""))
        return

    await message.answer(t(lang, "enter_code"))

    try:
        result = await rubika_send_code(phone, pass_key=password)
        await state.update_data(phone_code_hash=result["phone_code_hash"])

        if result.get("status") == "SendPassKey":
            hint = result.get("hint_pass_key", "")
            await message.answer(t(lang, "wrong_password", hint=hint))
            return

        await message.answer(t(lang, "password_verified"))
        await state.set_state(Form.code)

    except Exception as exc:
        logger.error("send_code passkey: %s", exc)
        await message.answer(t(lang, "login_error", error=str(exc)))


async def receive_code(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    code_digits = re.sub(r"\D", "", message.text or "")
    data = await state.get_data()
    phone = data.get("phone", "")
    phone_code_hash = data.get("phone_code_hash", "")

    if len(code_digits) < 4 or len(code_digits) > 8:
        await message.answer(t(lang, "invalid_code"))
        return

    await message.answer(t(lang, "enter_code"))

    try:
        login_data = await rubika_sign_in(phone, code_digits, phone_code_hash)

        upsert_user(
            tg_id,
            phone=phone,
            rubika_session=login_data["session_path"],
            rubika_auth=login_data["auth"],
            rubika_private_key=login_data["private_key"],
        )

        referrer_id = data.get("referrer_id")
        if referrer_id:
            referrer = get_user(referrer_id)
            if referrer:
                ref_lang = get_lang(referrer)
                upsert_user(referrer_id, total_invites=(referrer.get("total_invites", 0) + 1))
                now = datetime.now()
                if is_premium_active(referrer):
                    current_until = datetime.fromisoformat(referrer["premium_until"])
                    new_until = current_until + timedelta(hours=1)
                else:
                    new_until = now + timedelta(hours=1)
                upsert_user(referrer_id, is_premium=1, premium_until=new_until.isoformat())
                try:
                    await message.bot.send_message(
                        chat_id=referrer_id,
                        text=t(ref_lang, "ref_start", count=referrer.get("total_invites", 0) + 1),
                    )
                except Exception:
                    pass
            await state.update_data(referrer_id=None)

        await asyncio.sleep(0.5)
        await message.answer(t(lang, "login_success"), reply_markup=kb_main(lang, False))
        await state.set_state(Form.main_menu)

    except Exception as exc:
        logger.error("sign_in: %s", exc)
        await message.answer(t(lang, "login_error", error=str(exc)))


# ────────────────────────────────────────────────────────────────────────
#  Callbacks
# ────────────────────────────────────────────────────────────────────────
async def check_join_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    is_member = await check_user_membership(callback.bot, tg_id)
    if not is_member:
        await callback.message.answer(t(lang, "not_joined"), reply_markup=kb_force_join(lang))
        return

    if user and user.get("rubika_session") and session_exists(user["rubika_session"]):
        premium = is_premium_active(user)
        await callback.message.answer(t(lang, "membership_verified"), reply_markup=kb_main(lang, premium))
        await state.set_state(Form.main_menu)
        return

    premium = is_premium_active(user) if user else False
    await callback.message.answer(t(lang, "membership_verified"), reply_markup=kb_main(lang, premium))
    await state.set_state(Form.main_menu)


async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    premium = is_premium_active(user) if user else False
    await callback.message.answer(t(lang, "menu_title"), reply_markup=kb_main(lang, premium))
    await state.set_state(Form.main_menu)


async def process_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = callback.data
    tg_id = callback.from_user.id
    bot = callback.bot
    user = get_user(tg_id)
    lang = get_lang(user)

    if data == "back_menu":
        premium = is_premium_active(user) if user else False
        await callback.message.answer(t(lang, "menu_title"), reply_markup=kb_main(lang, premium))
        await state.set_state(Form.main_menu)
        return

    # ── Add Account ──
    if data == "add_account":
        await callback.message.answer(t(lang, "send_phone"), reply_markup=kb_phone(lang))
        await state.set_state(Form.phone)
        return

    # ── Start Report ──
    if data == "start_report":
        if not user or not user.get("rubika_session"):
            await callback.message.answer(t(lang, "need_login"))
            return
        if not session_exists(user["rubika_session"]):
            await callback.message.answer(t(lang, "session_expired"))
            upsert_user(tg_id, rubika_session=None, rubika_auth=None, rubika_private_key=None)
            return
        await callback.message.answer(t(lang, "choose_guid_method"), reply_markup=kb_report_guid_choice(lang))
        await state.set_state(Form.report_guid)
        return

    if data == "get_by_username":
        await callback.message.answer(t(lang, "enter_username"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.report_resolve)
        return

    if data == "enter_guid":
        await callback.message.answer(t(lang, "enter_guid"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.report_guid)
        return

    # ── Start Block ──
    if data == "start_block":
        if not user or not user.get("rubika_session"):
            await callback.message.answer(t(lang, "need_login"))
            return
        if not session_exists(user["rubika_session"]):
            await callback.message.answer(t(lang, "session_expired"))
            upsert_user(tg_id, rubika_session=None, rubika_auth=None, rubika_private_key=None)
            return
        await callback.message.answer(t(lang, "start_block"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.block_guid)
        return

    # ── Start Leave ──
    if data == "start_leave":
        if not user or not user.get("rubika_session"):
            await callback.message.answer(t(lang, "need_login"))
            return
        if not session_exists(user["rubika_session"]):
            await callback.message.answer(t(lang, "session_expired"))
            upsert_user(tg_id, rubika_session=None, rubika_auth=None, rubika_private_key=None)
            return
        await callback.message.answer(t(lang, "start_leave"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.leave_guid)
        return

    # ── Start Join ──
    if data == "start_join":
        if not user or not user.get("rubika_session"):
            await callback.message.answer(t(lang, "need_login"))
            return
        if not session_exists(user["rubika_session"]):
            await callback.message.answer(t(lang, "session_expired"))
            upsert_user(tg_id, rubika_session=None, rubika_auth=None, rubika_private_key=None)
            return
        await callback.message.answer(t(lang, "start_join"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.join_link)
        return

    # ── Block Stats ──
    if data == "block_stats":
        stats = get_block_stats(tg_id)
        total = get_total_blocks(tg_id)
        if not stats:
            await callback.message.answer(t(lang, "no_blocks"), reply_markup=kb_menu_return(lang))
        else:
            lines = [t(lang, "block_stats_title", total=total)]
            for s in stats[:10]:
                lines.append(t(lang, "block_stat_item",
                    name=s.get("target_name", s["target_guid"]),
                    accounts=s["accounts_used"],
                    blocks=s["total_blocks"],
                    date=s["blocked_at"][:16],
                ))
            await callback.message.answer("\n".join(lines), reply_markup=kb_menu_return(lang))
        return

    # ── Account Status ──
    if data == "account_status":
        premium = is_premium_active(user) if user else False
        limit = PREMIUM_LIMIT if premium else FREE_LIMIT
        plan = t(lang, "plan_premium") if premium else t(lang, "plan_free")
        total_blk = get_total_blocks(tg_id)
        await callback.message.answer(
            t(lang, "account_status_title",
                plan=plan, limit=limit,
                reports=user.get("total_reports", 0) if user else 0,
                blocks=total_blk,
                phone=user.get("phone", "-") if user else "-",
            ),
            reply_markup=kb_menu_return(lang),
        )
        return

    # ── Subscription ──
    if data == "subscription":
        premium = is_premium_active(user) if user else False
        if premium:
            await callback.message.answer(t(lang, "sub_active", date=user["premium_until"][:10]), reply_markup=kb_menu_return(lang))
        else:
            await callback.message.answer(
                t(lang, "sub_buy", limit=PREMIUM_LIMIT, price=PREMIUM_PRICE, card=ADMIN_CARD_NUMBER),
                reply_markup=kb_menu_return(lang),
            )
            await state.set_state(Form.receipt)
        return

    # ── Help ──
    if data == "help":
        await callback.message.answer(t(lang, "help_text"), reply_markup=kb_menu_return(lang))
        return

    # ── Referral ──
    if data == "referral_link":
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{tg_id}"
        invites = user.get("total_invites", 0) if user else 0
        await callback.message.answer(t(lang, "referral_text", link=ref_link, invites=invites), reply_markup=kb_menu_return(lang))
        return

    # ── Support ──
    if data == "support":
        await callback.message.answer(t(lang, "support_text"), reply_markup=kb_support(lang))
        await state.set_state(Form.support_message)
        return

    # ── Daily Reward ──
    if data == "daily_reward":
        last_reward = user.get("last_daily_reward") if user else None
        now = datetime.now()
        if last_reward:
            try:
                last_dt = datetime.fromisoformat(last_reward)
                diff = now - last_dt
                if diff < timedelta(hours=24):
                    remaining = timedelta(hours=24) - diff
                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60
                    await callback.message.answer(t(lang, "daily_no_reward", hours=hours, minutes=minutes), reply_markup=kb_menu_return(lang))
                    return
            except (ValueError, TypeError):
                pass

        dice_msg = await callback.message.answer("🎲")
        await asyncio.sleep(1)
        roll = random.randint(1, 6)

        if roll == 6:
            prize_days = 3
            emoji = "🏆"
            prize_text = t(lang, "daily_6")
        elif roll in (4, 5):
            prize_days = 1
            emoji = "🎉"
            prize_text = t(lang, "daily_45")
        else:
            prize_days = 0
            emoji = "😔"
            prize_text = t(lang, "daily_loose", roll=roll)

        upsert_user(tg_id, last_daily_reward=now.isoformat())

        result_text = (
            f"{emoji} 🎲 ━━━━━━━━━━━ 🎲\n"
            f"       [ {roll} ]\n"
            f"🎲 ━━━━━━━━━━━ 🎲\n\n"
            f"{prize_text}"
        )

        if prize_days > 0:
            if is_premium_active(user):
                new_until = datetime.fromisoformat(user["premium_until"]) + timedelta(days=prize_days)
            else:
                new_until = now + timedelta(days=prize_days)
            upsert_user(tg_id, is_premium=1, premium_until=new_until.isoformat())
            user = get_user(tg_id)
            premium = is_premium_active(user) if user else False
            result_text += t(lang, "daily_prize", date=new_until.isoformat()[:10], limit=PREMIUM_LIMIT)
            await dice_msg.edit_text(result_text, reply_markup=kb_main(lang, premium))
        else:
            result_text += t(lang, "daily_try_again")
            await dice_msg.edit_text(result_text, reply_markup=kb_menu_return(lang))
        return

    # ── Report Types ──
    if data.startswith("rt_"):
        key = data[3:]
        if key == "confirm":
            state_data = await state.get_data()
            selected: set = state_data.get("selected_types", set())
            if not selected:
                await callback.answer("!", show_alert=True)
                return
            if "7" in selected:
                await callback.message.answer(t(lang, "enter_other_text"), reply_markup=kb_menu_return(lang))
                await state.set_state(Form.report_other_text)
                return
            premium = is_premium_active(user) if user else False
            limit = PREMIUM_LIMIT if premium else FREE_LIMIT
            report_labels_fa = {"1": " مستهجن", "2": " خشونت", "3": " اسپم", "4": " کودک‌آزاری", "5": " نقض حق‌نشر", "6": " فیشینگ", "7": " سایر"}
            report_labels_en = {"1": " Porn", "2": " Violence", "3": " Spam", "4": " Child", "5": " Copyright", "6": " Fishing", "7": " Other"}
            labels_map = report_labels_fa if lang == "fa" else report_labels_en
            labels = [labels_map.get(k, k) for k in selected]
            await callback.message.answer(t(lang, "report_count_question", types=", ".join(labels), limit=limit), reply_markup=kb_menu_return(lang))
            await state.set_state(Form.report_count)
            return

        state_data = await state.get_data()
        selected: set = state_data.get("selected_types", set())
        if key in selected:
            selected.discard(key)
        else:
            selected.add(key)
        await state.update_data(selected_types=selected)
        await callback.message.edit_reply_markup(reply_markup=kb_report_types(lang, selected))
        return


# ────────────────────────────────────────────────────────────────────────
#  Report flow handlers
# ────────────────────────────────────────────────────────────────────────
async def receive_guid(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    guid = message.text.strip()

    if looks_like_guid(guid):
        await state.update_data(object_guid=guid, selected_types=set())
        await message.answer(t(lang, "select_report_type"), reply_markup=kb_report_types(lang, set()))
        await state.set_state(Form.report_types)
        return

    if not user or not user.get("rubika_session") or not session_exists(user["rubika_session"]):
        await message.answer(t(lang, "session_invalid"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    await message.answer(t(lang, "searching_guid"))
    resolved = await resolve_object_guid(user["rubika_session"], guid)
    if not resolved:
        await message.answer(t(lang, "guid_not_found"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    await state.update_data(object_guid=resolved, selected_types=set())
    await message.answer(t(lang, "guid_found", guid=resolved), reply_markup=kb_report_types(lang, set()), parse_mode="HTML")
    await state.set_state(Form.report_types)


async def receive_resolve(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    text = message.text.strip()

    if not user or not user.get("rubika_session"):
        await message.answer(t(lang, "session_invalid"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    session_path = user["rubika_session"]
    if not session_exists(session_path):
        await message.answer(t(lang, "session_expired"), reply_markup=kb_menu_return(lang))
        upsert_user(tg_id, rubika_session=None, rubika_auth=None, rubika_private_key=None)
        await state.set_state(Form.main_menu)
        return

    await message.answer(t(lang, "searching_guid"))
    guid = await resolve_object_guid(session_path, text)
    if not guid:
        await message.answer(t(lang, "guid_not_found"), reply_markup=kb_report_guid_choice(lang))
        await state.set_state(Form.report_guid)
        return

    await state.update_data(object_guid=guid, selected_types=set())
    await message.answer(t(lang, "guid_found", guid=guid), reply_markup=kb_report_types(lang, set()), parse_mode="HTML")
    await state.set_state(Form.report_types)


async def receive_other_text(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    text = message.text.strip()

    if not text or len(text) < 3:
        await message.answer(t(lang, "min_3_chars"), reply_markup=kb_menu_return(lang))
        return

    await state.update_data(other_report_text=text)
    state_data = await state.get_data()
    premium = is_premium_active(user) if user else False
    limit = PREMIUM_LIMIT if premium else FREE_LIMIT
    selected: set = state_data.get("selected_types", set())

    await message.answer(
        t(lang, "report_count_question", types=", ".join(selected), limit=limit),
        reply_markup=kb_menu_return(lang),
    )
    await state.set_state(Form.report_count)


async def receive_count(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    text = message.text.strip()

    if not text.isdigit() or int(text) < 1:
        await message.answer(t(lang, "positive_number"), reply_markup=kb_menu_return(lang))
        return

    count = int(text)
    premium = is_premium_active(user) if user else False
    limit = PREMIUM_LIMIT if premium else FREE_LIMIT

    if count > limit:
        await message.answer(t(lang, "limit_exceeded", limit=limit, admin=ADMIN_USERNAME), reply_markup=kb_menu_return(lang))
        return

    await state.update_data(count=count)
    await message.answer(t(lang, "delay_question"), reply_markup=kb_menu_return(lang))
    await state.set_state(Form.report_delay)


async def receive_delay(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    text = message.text.strip()

    if not text.isdigit() or int(text) < 1:
        await message.answer(t(lang, "positive_seconds"), reply_markup=kb_menu_return(lang))
        return

    delay = int(text)
    all_sessions = get_all_valid_sessions()
    total = len(all_sessions)

    if total == 0:
        await message.answer(t(lang, "no_accounts"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    await state.update_data(report_delay_delay=delay)
    await message.answer(t(lang, "accounts_question", total=total), reply_markup=kb_menu_return(lang))
    await state.set_state(Form.report_accounts)


async def receive_accounts(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    text = message.text.strip()

    if not text.isdigit() or int(text) < 1:
        await message.answer(t(lang, "positive_number"), reply_markup=kb_menu_return(lang))
        return

    all_sessions = get_all_valid_sessions()
    total = len(all_sessions)
    if total == 0:
        await message.answer(t(lang, "no_accounts"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    num_accounts = int(text)
    if num_accounts > total:
        await message.answer(t(lang, "too_many_accounts", total=total), reply_markup=kb_menu_return(lang))
        return

    state_data = await state.get_data()
    object_guid = state_data.get("object_guid", "")
    count = state_data.get("count", 0)
    delay = state_data.get("report_delay_delay", REPORT_DELAY)
    selected = state_data.get("selected_types", set())
    other_text = state_data.get("other_report_text", "")

    if not selected:
        await message.answer(t(lang, "no_types_selected"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    if not object_guid:
        await message.answer(t(lang, "guid_not_found_err"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    session_paths = all_sessions[:num_accounts]
    selected_types = [
        (REPORT_TYPES_MAP[k][0], REPORT_TYPES_MAP[k][1], other_text if k == "7" else "")
        for k in selected
    ]

    await state.update_data(object_guid=None, selected_types=None, other_report_text=None, count=None, report_delay_delay=None)

    await message.answer(t(lang, "report_sending", count=count, delay=delay, accounts=num_accounts))

    asyncio.create_task(_pipeline(tg_id, session_paths, object_guid, selected_types, count, delay, message, lang))
    await state.set_state(Form.main_menu)


async def cmd_stop(message: Message) -> None:
    user_stop[message.from_user.id] = True
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    await message.answer(t(lang, "stop"))


# ────────────────────────────────────────────────────────────────────────
#  Block flow handlers
# ────────────────────────────────────────────────────────────────────────
async def receive_block_guid(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    if not user or not user.get("rubika_session"):
        await message.answer(t(lang, "session_invalid"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    session_path = user["rubika_session"]
    if not session_exists(session_path):
        await message.answer(t(lang, "session_expired"), reply_markup=kb_menu_return(lang))
        upsert_user(tg_id, rubika_session=None, rubika_auth=None, rubika_private_key=None)
        await state.set_state(Form.main_menu)
        return

    await message.answer(t(lang, "searching_guid"))
    text = message.text.strip()
    guid = await resolve_object_guid(session_path, text)
    if not guid:
        await message.answer(t(lang, "guid_not_found"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    all_sessions = get_all_valid_sessions()
    total = len(all_sessions)
    await state.update_data(block_target=guid)
    await message.answer(t(lang, "block_found", guid=guid, total=total), reply_markup=kb_menu_return(lang), parse_mode="HTML")
    await state.set_state(Form.block_count)


async def receive_block_count(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    text = message.text.strip()

    if not text.isdigit() or int(text) < 1:
        await message.answer(t(lang, "positive_number"), reply_markup=kb_menu_return(lang))
        return

    all_sessions = get_all_valid_sessions()
    total = len(all_sessions)
    num_accounts = int(text)

    if num_accounts > total:
        await message.answer(t(lang, "too_many_accounts", total=total), reply_markup=kb_menu_return(lang))
        return

    await state.update_data(block_num_accounts=num_accounts)
    await message.answer(t(lang, "block_accounts"), reply_markup=kb_menu_return(lang))
    await state.set_state(Form.block_delay)


async def receive_block_delay(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)
    text = message.text.strip()

    if not text.isdigit() or int(text) < 1:
        await message.answer(t(lang, "positive_seconds"), reply_markup=kb_menu_return(lang))
        return

    delay = int(text)
    state_data = await state.get_data()
    target_guid = state_data.get("block_target", "")
    num_accounts = state_data.get("block_num_accounts", 1)

    all_sessions = get_all_valid_sessions()
    session_paths = all_sessions[:num_accounts]

    if not target_guid:
        await message.answer(t(lang, "guid_not_found_err"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    await state.update_data(block_target=None, block_num_accounts=None)
    await message.answer(t(lang, "block_sending", guid=target_guid, accounts=num_accounts, delay=delay), parse_mode="HTML")

    asyncio.create_task(_block_pipeline(tg_id, session_paths, target_guid, num_accounts, delay, lang))
    await state.set_state(Form.main_menu)


# ────────────────────────────────────────────────────────────────────────
#  Leave channel handler
# ────────────────────────────────────────────────────────────────────────
async def receive_leave_guid(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    if not user or not user.get("rubika_session"):
        await message.answer(t(lang, "session_invalid"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    session_path = user["rubika_session"]
    if not session_exists(session_path):
        await message.answer(t(lang, "session_expired"), reply_markup=kb_menu_return(lang))
        upsert_user(tg_id, rubika_session=None, rubika_auth=None, rubika_private_key=None)
        await state.set_state(Form.main_menu)
        return

    text = message.text.strip()
    await message.answer(t(lang, "searching_guid"))
    guid = await resolve_object_guid(session_path, text)
    if not guid:
        await message.answer(t(lang, "guid_not_found"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    all_sessions = get_all_valid_sessions()
    num = len(all_sessions)
    await message.answer(t(lang, "leaving", guid=guid, total=num), parse_mode="HTML")

    success = fail = 0
    for sp in all_sessions:
        if await rubika_leave_chat(sp, guid):
            success += 1
        else:
            fail += 1
        await asyncio.sleep(0.5)

    await message.answer(t(lang, "leave_result", success=success, fail=fail), reply_markup=kb_menu_return(lang))
    await state.set_state(Form.main_menu)


# ────────────────────────────────────────────────────────────────────────
#  Join channel handler
# ────────────────────────────────────────────────────────────────────────
async def receive_join_link(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    if not user or not user.get("rubika_session"):
        await message.answer(t(lang, "session_invalid"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    session_path = user["rubika_session"]
    if not session_exists(session_path):
        await message.answer(t(lang, "session_expired"), reply_markup=kb_menu_return(lang))
        upsert_user(tg_id, rubika_session=None, rubika_auth=None, rubika_private_key=None)
        await state.set_state(Form.main_menu)
        return

    text = message.text.strip()
    if not text.startswith("http") and not text.startswith("rubika"):
        await message.answer(t(lang, "invalid_link"), reply_markup=kb_menu_return(lang))
        return

    all_sessions = get_all_valid_sessions()
    num = len(all_sessions)
    await message.answer(t(lang, "joining", total=num))

    success = fail = 0
    for sp in all_sessions:
        if await rubika_join_chat(sp, text):
            success += 1
        else:
            fail += 1
        await asyncio.sleep(0.5)

    await message.answer(t(lang, "join_result", success=success, fail=fail), reply_markup=kb_menu_return(lang))
    await state.set_state(Form.main_menu)


# ────────────────────────────────────────────────────────────────────────
#  Receipt
# ────────────────────────────────────────────────────────────────────────
async def receive_receipt(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    if not message.photo:
        await message.answer(t(lang, "receipt_sent", price=PREMIUM_PRICE), reply_markup=kb_menu_return(lang))
        return

    photo = message.photo[-1]
    approve_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "approve_yes"), callback_data=f"approve_sub_{tg_id}", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text=t(lang, "approve_no"), callback_data=f"reject_sub_{tg_id}", style=ButtonStyle.DANGER),
        ]
    ])

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=t(lang, "receipt_caption", phone=user.get("phone", "-"), tg_id=tg_id, price=PREMIUM_PRICE, date=datetime.now().strftime("%Y-%m-%d %H:%M")),
                reply_markup=approve_keyboard,
            )
        except Exception:
            pass

    await message.answer(t(lang, "receipt_sent", price=PREMIUM_PRICE), reply_markup=kb_menu_return(lang))
    await state.set_state(Form.main_menu)


async def admin_approve_sub(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.from_user.id not in ADMIN_IDS:
        return

    data = callback.data
    if data.startswith("approve_sub_"):
        target_id = int(data.split("_")[-1])
        set_premium(target_id, PREMIUM_MONTHS)
        await callback.message.edit_caption(caption=t("fa", "sub_approved", target=target_id), reply_markup=None)
        try:
            user = get_user(target_id)
            tlang = get_lang(user)
            premium_until = user.get("premium_until", "")[:10] if user else ""
            await callback.bot.send_message(chat_id=target_id, text=t(tlang, "sub_approved_user", date=premium_until, limit=PREMIUM_LIMIT))
        except Exception:
            pass
    elif data.startswith("reject_sub_"):
        target_id = int(data.split("_")[-1])
        await callback.message.edit_caption(caption=t("fa", "sub_rejected", target=target_id), reply_markup=None)
        try:
            user = get_user(target_id)
            tlang = get_lang(user)
            await callback.bot.send_message(chat_id=target_id, text=t(tlang, "sub_rejected_user"))
        except Exception:
            pass


# ────────────────────────────────────────────────────────────────────────
#  Support
# ────────────────────────────────────────────────────────────────────────
async def receive_support_message(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    user = get_user(tg_id)
    lang = get_lang(user)

    sent = False
    for admin_id in ADMIN_IDS:
        try:
            forwarded = await message.forward(chat_id=admin_id)
            await forwarded.reply(
                t(lang, "support_forward", phone=user.get("phone", "-") if user else "-", tg_id=tg_id),
                reply_markup=kb_admin_reply(tg_id, lang),
            )
            sent = True
        except Exception:
            pass

    if sent:
        await message.answer(t(lang, "support_sent"), reply_markup=kb_menu_return(lang))
    else:
        await message.answer(t(lang, "support_fail"))
    await state.set_state(Form.main_menu)


async def admin_reply_to_user(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    await state.update_data(reply_target=target_id)
    await state.set_state(Form.admin_reply)
    await callback.message.answer(t("fa", "admin_reply", target=target_id), reply_markup=kb_menu_return("fa"))


async def admin_close_ticket(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.from_user.id not in ADMIN_IDS:
        return
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        text = (callback.message.text or "") + t("fa", "admin_ticket_closed")
        await callback.message.edit_text(text)
    except Exception:
        pass


async def receive_admin_reply(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    if data.get("grant_mode"):
        await state.update_data(grant_mode=False)
        parts = (message.text or "").split()
        try:
            target_id = int(parts[0])
            months = int(parts[1]) if len(parts) > 1 else 1
            set_premium(target_id, months)
            await message.answer(t("fa", "grant_done", months=months, target=target_id), reply_markup=kb_admin_panel("fa"))
        except (ValueError, IndexError):
            await message.answer(t("fa", "grant_format_error"), reply_markup=kb_admin_panel("fa"))
        await state.set_state(Form.admin_panel)
        return

    target_id = data.get("reply_target")
    if not target_id:
        return
    try:
        await message.forward(chat_id=target_id)
        await message.answer(t("fa", "admin_reply_sent"), reply_markup=kb_admin_panel("fa"))
    except Exception as exc:
        await message.answer(t("fa", "admin_reply_fail", error=str(exc)), reply_markup=kb_admin_panel("fa"))
    await state.set_state(Form.admin_panel)


# ────────────────────────────────────────────────────────────────────────
#  Admin panel
# ────────────────────────────────────────────────────────────────────────
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(t("fa", "admin_panel"), reply_markup=kb_admin_panel("fa"))
    await state.set_state(Form.admin_panel)


async def admin_panel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.from_user.id not in ADMIN_IDS:
        return
    data = callback.data
    lang = "fa"

    if data == "admin_exit":
        await callback.message.answer(t(lang, "back"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.main_menu)
        return

    if data == "admin_broadcast":
        await callback.message.answer(t(lang, "admin_broadcast"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.broadcast)
        return

    if data == "admin_stats":
        total = count_users()
        users = get_all_users()
        prem = sum(1 for u in users if is_premium_active(u))
        reps = sum(u.get("total_reports", 0) for u in users)
        with sqlite3.connect(DB_PATH) as conn:
            sess = conn.execute("SELECT COUNT(*) FROM users WHERE rubika_session IS NOT NULL").fetchone()[0]
            blks = conn.execute("SELECT COALESCE(SUM(total_blocks), 0) FROM block_stats").fetchone()[0]
        await callback.message.answer(
            t(lang, "admin_stats", total=total, premium=prem, sessions=sess, reports=reps, blocks=blks),
            reply_markup=kb_admin_panel(lang),
        )
        return

    if data == "admin_grant":
        await callback.message.answer(t(lang, "admin_grant"), reply_markup=kb_menu_return(lang))
        await state.set_state(Form.admin_reply)
        await state.update_data(grant_mode=True)
        return

    if data == "admin_support":
        await callback.message.answer(t(lang, "admin_support"), reply_markup=kb_admin_panel(lang))
        return

    if data == "admin_block_stats":
        stats = get_all_block_stats()
        if not stats:
            await callback.message.answer(t(lang, "admin_no_blocks"), reply_markup=kb_admin_panel(lang))
            return
        lines = [t(lang, "admin_block_stats", total=len(stats))]
        for s in stats[:20]:
            lines.append(f"👤 {s.get('target_name', s['target_guid'][:20])} | 🚫 {s['total_blocks']} | 📱 {s['accounts_used']} | 🆔 {s['blocker_tg']}")
        await callback.message.answer("\n".join(lines), reply_markup=kb_admin_panel(lang))
        return

    if data == "admin_list":
        users = get_all_users()
        if not users:
            await callback.message.answer(t(lang, "admin_no_users"), reply_markup=kb_admin_panel(lang))
            return
        lines = [t(lang, "admin_list_title")]
        for u in users[-30:]:
            pid = u.get("telegram_id")
            phone = u.get("phone", "-")
            prem = "👑" if is_premium_active(u) else "🆓"
            lines.append(f"{prem} {pid} | {phone}")
        await callback.message.answer("\n".join(lines), reply_markup=kb_admin_panel(lang))
        return


async def receive_broadcast(message: Message, state: FSMContext) -> None:
    users = get_all_users()
    total = len(users)
    success = fail = 0
    await message.answer(f"📤 Sending to {total} users...")
    for u in users:
        uid = u.get("telegram_id")
        if not uid:
            continue
        try:
            await message.forward(chat_id=uid)
            success += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await message.answer(t("fa", "admin_broadcast_done", success=success, fail=fail), reply_markup=kb_admin_panel("fa"))
    await state.set_state(Form.admin_panel)


async def cmd_reply(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(t("fa", "reply_usage"))
        return
    target_id = int(parts[1])
    text = message.text[len(parts[0]) + len(parts[1]) + 2:].strip()
    try:
        await message.bot.send_message(chat_id=target_id, text=t("fa", "ticket_reply_label", text=text))
        await message.answer(t("fa", "reply_sent"))
    except Exception as exc:
        await message.answer(t("fa", "reply_error", error=str(exc)))


# ────────────────────────────────────────────────────────────────────────
#  Global error handler
# ────────────────────────────────────────────────────────────────────────
async def global_error_handler(update: Update, exception: Exception = None) -> bool:
    if exception is None:
        return True
    logger.exception("UNHANDLED EXCEPTION: %s", exception)
    try:
        if update.callback_query:
            await update.callback_query.answer(t("fa", "error_generic", error=str(exception)), show_alert=True)
        elif update.message:
            await update.message.answer(t("fa", "error_generic", error=str(exception)))
    except Exception:
        pass
    return True


# ────────────────────────────────────────────────────────────────────────
#  Pipeline (report)
# ────────────────────────────────────────────────────────────────────────
async def _pipeline(tg_id, session_paths, object_guid, selected_types, count, delay, status_message, lang="fa"):
    user_stop[tg_id] = False

    async def reply(msg):
        try:
            await status_message.answer(msg)
        except Exception:
            pass

    if not session_paths:
        await reply(t(lang, "no_accounts"))
        return

    n = len(session_paths)
    total_sent = 0
    lines = []

    for label, rt_enum, other_text in selected_types:
        per = count // n
        rem = count % n
        tasks = []
        for idx, sp in enumerate(session_paths):
            c = per + (1 if idx < rem else 0)
            if c > 0:
                tasks.append(asyncio.create_task(_single_loop(sp, object_guid, rt_enum, other_text, c, delay, label, tg_id)))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sent = failed = 0
        for r in results:
            if isinstance(r, Exception):
                lines.append(f"❌ {label}: {r}")
            else:
                s, f = r
                sent += s
                failed += f
        total_sent += sent
        lines.append(f"✅ {label}: {sent} sent | {failed} failed")

    add_stats(tg_id, total_sent)
    user = get_user(tg_id)
    premium = is_premium_active(user) if user else False
    await reply(t(lang, "report_result", lines="\n".join(lines)))

    try:
        await status_message.answer(t(lang, "menu_label"), reply_markup=kb_main(lang, premium))
    except Exception:
        pass


async def _single_loop(session_path, object_guid, report_type_enum, other_text, count, delay, label, tg_id):
    sent = failed = 0
    try:
        client = RubikaClient(name=session_path)
        async with client:
            for i in range(1, count + 1):
                if user_stop.get(tg_id):
                    break
                try:
                    if report_type_enum == ReportType.OTHER:
                        await client.report_object(object_guid, report_type_enum, description=other_text)
                    else:
                        await client.report_object(object_guid, report_type_enum)
                    sent += 1
                except Exception as exc:
                    failed += 1
                    logger.error("[%s][%d/%d] %s", label, i, count, exc)
                if i < count:
                    await asyncio.sleep(delay)
    except Exception as exc:
        logger.error("session %s error: %s", session_path, exc)
    return sent, failed


# ────────────────────────────────────────────────────────────────────────
#  Block pipeline
# ────────────────────────────────────────────────────────────────────────
async def _block_pipeline(tg_id, session_paths, target_guid, count, delay, lang="fa"):
    user_stop[tg_id] = False
    target_name = target_guid
    sent = failed = 0

    for idx, sp in enumerate(session_paths):
        if user_stop.get(tg_id):
            break
        try:
            client = RubikaClient(name=sp)
            async with client:
                try:
                    await client.set_block_user(target_guid, action="Block")
                    sent += 1
                except Exception as exc:
                    failed += 1
                    logger.error("block [%d/%d] %s", idx + 1, count, exc)
        except Exception as exc:
            failed += 1
            logger.error("block session error: %s", exc)
        if idx < len(session_paths) - 1:
            await asyncio.sleep(delay)

    record_block(target_guid, target_name, tg_id, sent)
    total_blocks = get_total_blocks(tg_id)

    try:
        await Bot(token=TELEGRAM_TOKEN).send_message(
            chat_id=tg_id,
            text=t(lang, "block_result", guid=target_guid, sent=sent, failed=failed, accounts=len(session_paths), total=total_blocks),
            parse_mode="HTML",
        )
        user = get_user(tg_id)
        premium = is_premium_active(user) if user else False
        await Bot(token=TELEGRAM_TOKEN).send_message(chat_id=tg_id, text=t(lang, "menu_label"), reply_markup=kb_main(lang, premium))
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────────────
#  Admin commands
# ────────────────────────────────────────────────────────────────────────
async def cmd_grant(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    args = (message.text or "").split()[1:]
    if not args:
        await message.answer(t("fa", "grant_usage"))
        return
    try:
        target_id = int(args[0])
        months = int(args[1]) if len(args) > 1 else 1
        set_premium(target_id, months)
        await message.answer(t("fa", "grant_done", months=months, target=target_id))
    except (ValueError, IndexError):
        await message.answer(t("fa", "grant_error"))


async def cmd_stats(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        prem = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()[0]
        reps = conn.execute("SELECT SUM(total_reports) FROM users").fetchone()[0] or 0
        blks = conn.execute("SELECT COALESCE(SUM(total_blocks), 0) FROM block_stats").fetchone()[0]
    await message.answer(t("fa", "stats_title", total=total, premium=prem, reports=reps, blocks=blks))


# ────────────────────────────────────────────────────────────────────────
#  Web App (Flask - Inline)
# ────────────────────────────────────────────────────────────────────────
def _create_flask_app():
    from flask import Flask, render_template_string, jsonify

    flask_app = Flask(__name__)

    def _get_stats():
        with sqlite3.connect(DB_PATH) as conn:
            total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            premium = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()[0]
            sessions = conn.execute("SELECT COUNT(*) FROM users WHERE rubika_session IS NOT NULL").fetchone()[0]
            reports = conn.execute("SELECT COALESCE(SUM(total_reports), 0) FROM users").fetchone()[0]
            blocks = conn.execute("SELECT COALESCE(SUM(total_blocks), 0) FROM block_stats").fetchone()[0]
            invites = conn.execute("SELECT COALESCE(SUM(total_invites), 0) FROM users").fetchone()[0]
        return {"total_users": total, "premium_users": premium, "active_sessions": sessions, "total_reports": reports, "total_blocks": blocks, "total_invites": invites}

    def _get_users():
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def _get_block_stats_web():
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM block_stats ORDER BY blocked_at DESC").fetchall()
        return [dict(r) for r in rows]

    WEB_HTML = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Rubika Reporter</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>*{margin:0;padding:0;box-sizing:border-box}:root{--bg:#0a0a0f;--s1:#12121a;--s2:#1a1a25;--bd:#2a2a3a;--t1:#e8e8f0;--t2:#8888a0;--ac:#6c5ce7;--ac2:#a29bfe;--gr:#00cec9;--rd:#ff6b6b;--or:#fdcb6e;--pk:#fd79a8;--bl:#74b9ff}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--t1);min-height:100vh}
.glow{position:fixed;width:500px;height:500px;border-radius:50%;filter:blur(150px);opacity:.12;pointer-events:none;z-index:0}.g1{top:-200px;left:-200px;background:#6c5ce7}.g2{bottom:-200px;right:-200px;background:#00cec9}
.ct{max-width:1300px;margin:0 auto;padding:20px;position:relative;z-index:1}
header{text-align:center;padding:35px 0 25px}header h1{font-size:2.6em;font-weight:800;background:linear-gradient(135deg,#6c5ce7,#a29bfe);-webkit-background-clip:text;-webkit-text-fill-color:transparent}header p{color:var(--t2);margin-top:6px}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:35px}
.sc{background:var(--s1);border:1px solid var(--bd);border-radius:14px;padding:22px;transition:all .3s}.sc:hover{transform:translateY(-3px);border-color:var(--ac);box-shadow:0 6px 25px rgba(108,92,231,.12)}
.sc .ic{font-size:1.8em;margin-bottom:10px}.sc .vl{font-size:2.2em;font-weight:800;line-height:1}.sc .lb{color:var(--t2);font-size:.85em;margin-top:5px}
.sc:nth-child(1) .vl{color:var(--ac2)}.sc:nth-child(2) .vl{color:var(--gr)}.sc:nth-child(3) .vl{color:var(--or)}.sc:nth-child(4) .vl{color:var(--pk)}.sc:nth-child(5) .vl{color:var(--rd)}.sc:nth-child(6) .vl{color:var(--bl)}
.sec{background:var(--s1);border:1px solid var(--bd);border-radius:14px;padding:24px;margin-bottom:20px}
.sh{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}.sh h2{font-size:1.3em;font-weight:700}
.bdg{background:var(--ac);color:#fff;padding:3px 10px;border-radius:16px;font-size:.8em;font-weight:600}
table{width:100%;border-collapse:collapse}th{text-align:left;padding:10px 14px;color:var(--t2);font-size:.8em;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--bd);font-weight:600}td{padding:12px 14px;border-bottom:1px solid rgba(42,42,58,.4);font-size:.9em}tr:hover td{background:rgba(108,92,231,.04)}
.tg{display:inline-block;padding:2px 8px;border-radius:6px;font-size:.75em;font-weight:600}.tp{background:rgba(108,92,231,.2);color:var(--ac2)}.tf{background:rgba(136,136,160,.2);color:var(--t2)}
.sb{background:var(--s2);border:1px solid var(--bd);border-radius:8px;padding:8px 14px;color:var(--t1);font-size:.9em;outline:none;width:220px;font-family:inherit}.sb:focus{border-color:var(--ac)}
.tabs{display:flex;gap:6px;margin-bottom:20px}.tab{padding:8px 20px;border-radius:8px;background:var(--s2);border:1px solid var(--bd);color:var(--t2);cursor:pointer;font-weight:500;font-family:inherit;font-size:.9em;transition:all .3s}.tab.act,.tab:hover{background:var(--ac);color:#fff;border-color:var(--ac)}
.tc{display:none}.tc.act{display:block}
.es{text-align:center;padding:50px 20px;color:var(--t2)}.es .ic{font-size:2.5em;margin-bottom:12px}
.rc{background:var(--s2);border:1px solid var(--bd);border-radius:10px;padding:16px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;transition:all .3s}.rc:hover{border-color:var(--ac)}.rc .nf h3{font-size:1em;margin-bottom:3px}.rc .nf p{color:var(--t2);font-size:.8em}
.qa{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:25px}
.qa a,.qa .qac{background:var(--s1);border:1px solid var(--bd);border-radius:10px;padding:16px;text-align:center;cursor:pointer;transition:all .3s;text-decoration:none;color:var(--t1)}.qa a:hover,.qa .qac:hover{transform:translateY(-2px);border-color:var(--ac);box-shadow:0 4px 20px rgba(108,92,231,.15)}.qa .ic{font-size:1.8em;margin-bottom:6px}.qa .lb{font-weight:600;font-size:.9em}
.fi{animation:fi .5s ease forwards}@keyframes fi{from{opacity:0;transform:translateY(15px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:768px){header h1{font-size:1.8em}.sg{grid-template-columns:repeat(2,1fr)}.sb{width:100%}.sh{flex-direction:column;gap:10px;align-items:flex-start}}</style>
</head><body>
<div class="glow g1"></div><div class="glow g2"></div>
<div class="ct">
<header class="fi"><h1>Rubika Reporter</h1><p>Dashboard & Management Panel</p></header>
<div class="sg fi" id="sg"></div>
<div class="qa fi">
<a href="https://t.me/reporterrubikaammbot" target="_blank"><div class="ic">🤖</div><div class="lb">Open Bot</div></a>
<div class="qac" onclick="loadAll()"><div class="ic">🔄</div><div class="lb">Refresh</div></div>
<div class="qac" onclick="exportCSV()"><div class="ic">📥</div><div class="lb">Export CSV</div></div>
</div>
<div class="sec fi"><div class="tabs"><button class="tab act" onclick="sw('users',this)">Users</button><button class="tab" onclick="sw('blocks',this)">Block Stats</button></div>
<div id="tu" class="tc act"><div class="sh"><h2>Registered Users</h2><input type="text" class="sb" placeholder="Search..." oninput="fu(this.value)"></div>
<div style="overflow-x:auto"><table><thead><tr><th>Status</th><th>Telegram ID</th><th>Phone</th><th>Reports</th><th>Invites</th><th>Session</th><th>Joined</th></tr></thead><tbody id="ut"></tbody></table></div></div>
<div id="tb" class="tc"><div class="sh"><h2>Block Statistics</h2></div><div id="bl"></div></div>
</div></div>
<script>
let AU=[];
async function ls(){const r=await fetch('/api/stats');const d=await r.json();document.getElementById('sg').innerHTML=`
<div class="sc"><div class="ic">👥</div><div class="vl">${d.total_users}</div><div class="lb">Total Users</div></div>
<div class="sc"><div class="ic">👑</div><div class="vl">${d.premium_users}</div><div class="lb">Premium</div></div>
<div class="sc"><div class="ic">🔐</div><div class="vl">${d.active_sessions}</div><div class="lb">Sessions</div></div>
<div class="sc"><div class="ic">📢</div><div class="vl">${d.total_reports}</div><div class="lb">Reports</div></div>
<div class="sc"><div class="ic">🚫</div><div class="vl">${d.total_blocks}</div><div class="lb">Blocks</div></div>
<div class="sc"><div class="ic">🔗</div><div class="vl">${d.total_invites}</div><div class="lb">Invites</div></div>`}
async function lu(){const r=await fetch('/api/users');AU=await r.json();ru(AU)}
function ru(u){const t=document.getElementById('ut');if(!u.length){t.innerHTML='<tr><td colspan="7" class="es"><div class="ic">📭</div><p>No users</p></td></tr>';return}
t.innerHTML=u.map(x=>{const p=x.is_premium&&x.premium_until&&new Date(x.premium_until)>new Date();return`<tr><td><span class="tg ${p?'tp':'tf'}">${p?'Premium':'Free'}</span></td><td><code>${x.telegram_id}</code></td><td>${x.phone||'-'}</td><td>${x.total_reports||0}</td><td>${x.total_invites||0}</td><td>${x.rubika_session?'✅':'❌'}</td><td>${x.created_at?x.created_at.slice(0,10):'-'}</td></tr>`}).join('')}
function fu(q){q=q.toLowerCase();ru(AU.filter(x=>(x.phone&&x.phone.includes(q))||String(x.telegram_id).includes(q)))}
async function lb(){const r=await fetch('/api/blocks');const b=await r.json();const c=document.getElementById('bl');if(!b.length){c.innerHTML='<div class="es"><div class="ic">🚫</div><p>No blocks</p></div>';return}
c.innerHTML=b.map(x=>`<div class="rc"><div class="nf"><h3>👤 ${x.target_name||x.target_guid}</h3><p>By: ${x.blocker_tg} | ${x.accounts_used} accounts | ${x.total_blocks} blocks</p><p>📅 ${x.blocked_at?x.blocked_at.slice(0,16):'-'}</p></div><div class="bdg">${x.total_blocks}x</div></div>`).join('')}
function sw(n,e){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('act'));document.querySelectorAll('.tc').forEach(t=>t.classList.remove('act'));e.classList.add('act');document.getElementById('t'+n).classList.add('act')}
function loadAll(){ls();lu();lb()}
function exportCSV(){let c='Status,Telegram ID,Phone,Reports,Invites,Session,Language,Joined\\n';AU.forEach(u=>{const p=u.is_premium&&u.premium_until&&new Date(u.premium_until)>new Date();c+=`${p?'Premium':'Free'},${u.telegram_id},${u.phone||''},${u.total_reports||0},${u.total_invites||0},${u.rubika_session?'Yes':'No'},${u.language||'fa'},${u.created_at||''}\\n`});const b=new Blob([c],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='users_export.csv';a.click()}
loadAll();setInterval(loadAll,30000);
</script></body></html>'''

    @flask_app.route("/")
    def index():
        return render_template_string(WEB_HTML)

    @flask_app.route("/api/stats")
    def api_stats():
        return jsonify(_get_stats())

    @flask_app.route("/api/users")
    def api_users():
        return jsonify(_get_users())

    @flask_app.route("/api/blocks")
    def api_blocks():
        return jsonify(_get_block_stats_web())

    return flask_app


def start_web_app() -> None:
    try:
        flask_app = _create_flask_app()
        thread = threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=6080, debug=False), daemon=True)
        thread.start()
        logger.info("🌐 Web app started on https://reporter-rubika-production.up.railway.app")
    except Exception as exc:
        logger.error("Failed to start web app: %s", exc)


# ────────────────────────────────────────────────────────────────────────
#  Main
# ────────────────────────────────────────────────────────────────────────
def build_app() -> tuple[Bot, Dispatcher]:
    init_db()
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    router = Router()

    # ── Language choice ──
    router.callback_query.register(choose_language, F.data.startswith("lang_"))

    # ── Messages ──
    router.message.register(cmd_start, CommandStart())
    router.message.register(receive_phone, Form.phone, F.contact | (F.text & ~F.text.startswith("/")))
    router.message.register(receive_password, Form.password, F.text & ~F.text.startswith("/"))
    router.message.register(receive_code, Form.code, F.text & ~F.text.startswith("/"))
    router.message.register(receive_guid, Form.report_guid, F.text & ~F.text.startswith("/"))
    router.message.register(receive_resolve, Form.report_resolve, F.text & ~F.text.startswith("/"))
    router.message.register(receive_other_text, Form.report_other_text, F.text & ~F.text.startswith("/"))
    router.message.register(receive_count, Form.report_count, F.text & ~F.text.startswith("/"))
    router.message.register(receive_delay, Form.report_delay, F.text & ~F.text.startswith("/"))
    router.message.register(receive_accounts, Form.report_accounts, F.text & ~F.text.startswith("/"))
    router.message.register(receive_receipt, Form.receipt)
    router.message.register(receive_support_message, Form.support_message)
    router.message.register(receive_broadcast, Form.broadcast)
    router.message.register(receive_admin_reply, Form.admin_reply)
    router.message.register(cmd_stop, Command("stop"))
    router.message.register(cmd_grant, Command("grant"))
    router.message.register(cmd_stats, Command("stats"))
    router.message.register(cmd_admin, Command("admin", "panel"))
    router.message.register(cmd_reply, Command("reply"))

    # ── Block ──
    router.message.register(receive_block_guid, Form.block_guid, F.text & ~F.text.startswith("/"))
    router.message.register(receive_block_count, Form.block_count, F.text & ~F.text.startswith("/"))
    router.message.register(receive_block_delay, Form.block_delay, F.text & ~F.text.startswith("/"))

    # ── Leave ──
    router.message.register(receive_leave_guid, Form.leave_guid, F.text & ~F.text.startswith("/"))

    # ── Join ──
    router.message.register(receive_join_link, Form.join_link, F.text & ~F.text.startswith("/"))

    # ── Callbacks ──
    router.callback_query.register(admin_approve_sub, F.data.startswith("approve_sub_") | F.data.startswith("reject_sub_"))
    router.callback_query.register(check_join_callback, F.data == "check_join")
    router.callback_query.register(admin_reply_to_user, F.data.startswith("admin_reply_"))
    router.callback_query.register(admin_close_ticket, F.data == "admin_close_ticket")
    router.callback_query.register(admin_panel_callback, F.data.startswith("admin_"))

    router.callback_query.register(process_callback, Form.main_menu)
    router.callback_query.register(process_callback, Form.report_types)
    router.callback_query.register(process_callback, Form.report_guid)
    router.callback_query.register(back_to_menu, Form.report_resolve, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.report_other_text, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.report_count, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.report_delay, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.report_accounts, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.receipt, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.report_guid, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.support_message, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.admin_panel, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.broadcast, F.data == "back_menu")
    router.callback_query.register(back_to_menu, Form.admin_reply, F.data == "back_menu")

    router.callback_query.register(process_callback)

    dp.include_router(router)
    dp.errors.register(global_error_handler)
    return bot, dp


async def main() -> None:
    start_web_app()
    bot, dp = build_app()
    logger.warning("[POLLING] starting...")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
