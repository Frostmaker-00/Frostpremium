
import os
import sqlite3
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# =========================================================
# SOZLAMALAR
# =========================================================

try:
    from config import BOT_TOKEN
except ImportError:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")


if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi!\n\n"
        "config.py faylida:\n"
        "BOT_TOKEN = \"BOT_TOKENINGIZ\"\n\n"
        "yoki CMD'da:\n"
        "set BOT_TOKEN=SIZNING_BOT_TOKENINGIZ"
    )


# =========================================================
# ADMIN
# =========================================================

ADMIN_IDS = {
    6383248812,
}


# =========================================================
# TO'LOV MA'LUMOTLARI
# =========================================================

# Siz bergan Hamkorbank karta
HAMKORBANK_CARD = "9860160649862903"

# Karta egasi
CARD_OWNER = "Nurmamatov Jamshid"

# Admin lichkaga o'tish uchun Telegram ID
ADMIN_ID = 6383248812


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "@hsshsgsgsgsg"


# =========================================================
# BOSHLANG'ICH NARXLAR
# =========================================================

STARS_PRICES = {
    50: 11000,
    100: 22000,
    200: 44000,
    300: 66000,
    500: 110000,
    1000: 220000,
}

PREMIUM_ACCOUNT_PRICES = {
    1: 40000,
    12: 310000,
}

PREMIUM_GIFT_PRICES = {
    3: 170000,
    6: 230000,
    12: 395000,
}


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def db():
    return sqlite3.connect(DB_NAME)


# =========================================================
# DATABASE INIT
# =========================================================

def init_db():

    conn = db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ORDERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_type TEXT NOT NULL,
            product_name TEXT NOT NULL,
            catalog_price INTEGER NOT NULL,
            xtr_price INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            telegram_charge_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # SETTINGS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # STARS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stars_prices (
            stars INTEGER PRIMARY KEY,
            uzs_price INTEGER NOT NULL
        )
    """)

    # PREMIUM ACCOUNT
    cur.execute("""
        CREATE TABLE IF NOT EXISTS premium_account_prices (
            months INTEGER PRIMARY KEY,
            uzs_price INTEGER NOT NULL
        )
    """)

    # PREMIUM GIFT
    cur.execute("""
        CREATE TABLE IF NOT EXISTS premium_gift_prices (
            months INTEGER PRIMARY KEY,
            uzs_price INTEGER NOT NULL
        )
    """)

    # REQUIRED CHANNELS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS required_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # INITIAL STARS
    for stars, price in STARS_PRICES.items():

        cur.execute("""
            INSERT OR IGNORE INTO stars_prices
            (stars, uzs_price)
            VALUES (?, ?)
        """, (stars, price))

    # INITIAL ACCOUNT PREMIUM
    for months, price in PREMIUM_ACCOUNT_PRICES.items():

        cur.execute("""
            INSERT OR IGNORE INTO premium_account_prices
            (months, uzs_price)
            VALUES (?, ?)
        """, (months, price))

    # INITIAL GIFT PREMIUM
    for months, price in PREMIUM_GIFT_PRICES.items():

        cur.execute("""
            INSERT OR IGNORE INTO premium_gift_prices
            (months, uzs_price)
            VALUES (?, ?)
        """, (months, price))

    conn.commit()
    conn.close()

    print("✅ Database tayyor")


# =========================================================
# USER SAQLASH
# =========================================================

def save_user(user):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username or "",
        user.first_name or "",
    ))

    conn.commit()
    conn.close()


# =========================================================
# ADMIN TEKSHIRISH
# =========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# =========================================================
# SETTINGS
# =========================================================

def get_setting(key, default=""):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "SELECT value FROM settings WHERE key = ?",
        (key,)
    )

    row = cur.fetchone()

    conn.close()

    return row[0] if row else default


def set_setting(key, value):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO settings
        (key, value)
        VALUES (?, ?)
    """, (
        key,
        value
    ))

    conn.commit()
    conn.close()


# =========================================================
# KANALLAR
# =========================================================

def get_required_channels():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, channel
        FROM required_channels
        ORDER BY id ASC
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


def add_required_channel(channel):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO required_channels
        (channel)
        VALUES (?)
    """, (channel,))

    added = cur.rowcount > 0

    conn.commit()
    conn.close()

    return added


def delete_required_channel(channel):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM required_channels
        WHERE channel = ?
    """, (channel,))

    deleted = cur.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


# =========================================================
# NARXLAR
# =========================================================

def get_stars_prices():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT stars, uzs_price
        FROM stars_prices
        ORDER BY stars
    """)

    rows = cur.fetchall()

    conn.close()

    return dict(rows)


def get_account_prices():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT months, uzs_price
        FROM premium_account_prices
        ORDER BY months
    """)

    rows = cur.fetchall()

    conn.close()

    return dict(rows)


def get_gift_prices():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT months, uzs_price
        FROM premium_gift_prices
        ORDER BY months
    """)

    rows = cur.fetchall()

    conn.close()

    return dict(rows)


# =========================================================
# ADMIN BILAN BOG'LANISH
# =========================================================

def admin_contact_button():

    return InlineKeyboardButton(
        "👨‍💼 Admin bilan bog‘lanish",
        url=f"tg://user?id={ADMIN_ID}"
    )


# =========================================================
# TO'LOV MA'LUMOTI
# =========================================================

def payment_text(product_name, price, order_id):

    return (
        f"💳 TO‘LOV MA’LUMOTI\n\n"

        f"🛍 Mahsulot: {product_name}\n"
        f"💰 Narxi: {price:,} so‘m\n"
        f"🧾 Buyurtma: #{order_id}\n\n"

        f"🏦 Bank: Hamkorbank\n"
        f"💳 Karta: {HAMKORBANK_CARD}\n"
        f"👤 Karta egasi: {CARD_OWNER}\n\n"

        "📌 To‘lovni yuqoridagi karta raqamiga "
        "amalga oshiring.\n\n"

        "To‘lovdan keyin:\n"
        "📸 Chek yoki to‘lov skrinshotini "
        "shu botga yuboring.\n\n"

        "⚠️ Chek yuborilgandan keyin admin "
        "to‘lovni tekshiradi va buyurtmani bajaradi."
    )


# =========================================================
# OBUNA TEKSHIRISH
# =========================================================

async def is_subscribed(bot, user_id):

    if is_admin(user_id):
        return True

    channels = get_required_channels()

    if not channels:
        return True

    for channel_id, channel in channels:

        try:

            member = await bot.get_chat_member(
                chat_id=channel,
                user_id=user_id
            )

            if member.status not in (
                "creator",
                "administrator",
                "member",
            ):
                return False

        except Exception as e:

            logger.warning(
                "Obuna tekshirish xatosi %s: %s",
                channel,
                e
            )

            return False

    return True


# =========================================================
# SUBSCRIPTION REQUIRED
# =========================================================

async def subscription_required(update, context):

    user = update.effective_user

    if is_admin(user.id):
        return True

    channels = get_required_channels()

    if not channels:
        return True

    subscribed = await is_subscribed(
        context.bot,
        user.id
    )

    if subscribed:
        return True

    keyboard = []

    for channel_id, channel in channels:

        username = channel.lstrip("@")

        keyboard.append([
            InlineKeyboardButton(
                f"📢 {channel}",
                url=f"https://t.me/{username}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "✅ Obunani tekshirish",
            callback_data="check_sub"
        )
    ])

    text = (
        "🔒 Botdan foydalanish uchun "
        "quyidagi kanallarga obuna bo‘ling.\n\n"
        "📢 Barcha kanallarga obuna bo‘lgach "
        "«Obunani tekshirish» tugmasini bosing."
    )

    if update.callback_query:

        await update.callback_query.answer()

        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif update.message:

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return False


# =========================================================
# START
# =========================================================

async def start(update, context):

    user = update.effective_user

    save_user(user)

    if not await subscription_required(
        update,
        context
    ):
        return

    await show_home(
        update,
        context
    )


# =========================================================
# HOME
# =========================================================

async def show_home(update, context):

    keyboard = [

        [
            InlineKeyboardButton(
                "⭐ Stars",
                callback_data="stars"
            )
        ],

        [
            InlineKeyboardButton(
                "💎 Premium",
                callback_data="premium"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 Buyurtmalarim",
                callback_data="orders"
            )
        ],

        [
            InlineKeyboardButton(
                "📞 Yordam",
                callback_data="help"
            )
        ],
    ]

    if is_admin(update.effective_user.id):

        keyboard.append([
            InlineKeyboardButton(
                "👑 Admin panel",
                callback_data="admin"
            )
        ])

    text = (
        "🤖 FrostShop\n\n"
        "⭐ Telegram Stars\n"
        "💎 Telegram Premium\n"
        "🎁 Premium Gift\n\n"
        "Kerakli xizmatni tanlang:"
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================================================
# STARS MENU
# =========================================================

async def stars_menu(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    prices = get_stars_prices()

    keyboard = []

    for stars, price in prices.items():

        keyboard.append([
            InlineKeyboardButton(
                f"⭐ {stars} Stars — {price:,} so‘m",
                callback_data=f"buy_stars_{stars}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Orqaga",
            callback_data="home"
        )
    ])

    await query.edit_message_text(
        "⭐ Telegram Stars\n\n"
        "Kerakli paketni tanlang:\n\n"
        "💳 To‘lov Hamkorbank karta orqali.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# STARS BUY - MANUAL PAYMENT
# =========================================================

async def buy_stars(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    try:

        stars = int(
            query.data.replace(
                "buy_stars_",
                ""
            )
        )

    except ValueError:

        await query.answer(
            "Noto‘g‘ri paket!",
            show_alert=True
        )

        return

    prices = get_stars_prices()

    if stars not in prices:

        await query.answer(
            "Bu paket mavjud emas!",
            show_alert=True
        )

        return

    price = prices[stars]

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders
        (
            user_id,
            product_type,
            product_name,
            catalog_price,
            xtr_price,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        query.from_user.id,
        "stars",
        f"{stars} Telegram Stars",
        price,
        0,
        "waiting_payment"
    ))

    order_id = cur.lastrowid

    conn.commit()
    conn.close()

    keyboard = [

        [
            InlineKeyboardButton(
                "📸 Chek yuborish",
                callback_data=f"receipt_{order_id}"
            )
        ],

        [
            admin_contact_button()
        ],

        [
            InlineKeyboardButton(
                "⬅️ Stars",
                callback_data="stars"
            )
        ],

    ]

    await query.message.reply_text(
        payment_text(
            f"{stars} Telegram Stars",
            price,
            order_id
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# PREMIUM MENU
# =========================================================

async def premium_menu(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    keyboard = [

        [
            InlineKeyboardButton(
                "🔐 Akkountga kirib olish",
                callback_data="premium_account"
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 Gift sifatida yuborish",
                callback_data="premium_gift"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Orqaga",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        "💎 Telegram Premium\n\n"
        "Premium turini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# PREMIUM ACCOUNT
# =========================================================

async def premium_account(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    prices = get_account_prices()

    keyboard = []

    for months, price in prices.items():

        keyboard.append([
            InlineKeyboardButton(
                f"💎 {months} oy — {price:,} so‘m",
                callback_data=f"account_{months}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Orqaga",
            callback_data="premium"
        )
    ])

    await query.edit_message_text(

        "🔐 Akkountga kirib olinadigan Premium\n\n"

        "💡 Bu xizmat admin tomonidan bajariladi.\n\n"

        "⚠️ Telegram login kodi yoki 2FA "
        "parolini botga yubormang.\n\n"

        "💳 To‘lov Hamkorbank karta orqali.",

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# PREMIUM GIFT
# =========================================================

async def premium_gift(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    prices = get_gift_prices()

    keyboard = []

    # Gift ko'rinishidagi tugmalar
    gift_emojis = {
        3: "🧸",
        6: "❤️",
        12: "🌹",
    }

    for months, price in prices.items():

        emoji = gift_emojis.get(
            months,
            "🎁"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} {months} oy — {price:,} so‘m",
                callback_data=f"gift_{months}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Orqaga",
            callback_data="premium"
        )
    ])

    await query.edit_message_text(

        "🎁 PREMIUM GIFT\n\n"

        "🧸 3 oy\n"
        "❤️ 6 oy\n"
        "🌹 12 oy\n\n"

        "Premiumni boshqa Telegram "
        "akkauntiga yuborish xizmati.\n\n"

        "Kerakli Gift paketini tanlang:",

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ACCOUNT PREMIUM ORDER
# =========================================================

async def account_order(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    try:

        months = int(
            query.data.replace(
                "account_",
                ""
            )
        )

    except ValueError:

        await query.answer(
            "Xato!",
            show_alert=True
        )

        return

    prices = get_account_prices()

    if months not in prices:

        await query.answer(
            "Bu paket mavjud emas.",
            show_alert=True
        )

        return

    price = prices[months]

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders
        (
            user_id,
            product_type,
            product_name,
            catalog_price,
            xtr_price,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        query.from_user.id,
        "premium_account",
        f"Premium {months} oy — Akkount",
        price,
        0,
        "waiting_payment"
    ))

    order_id = cur.lastrowid

    conn.commit()
    conn.close()

    keyboard = [

        [
            InlineKeyboardButton(
                "📸 Chek yuborish",
                callback_data=f"receipt_{order_id}"
            )
        ],

        [
            admin_contact_button()
        ],

        [
            InlineKeyboardButton(
                "⬅️ Premium",
                callback_data="premium"
            )
        ],

    ]

    await query.message.reply_text(

        payment_text(
            f"💎 Premium {months} oy — Akkount",
            price,
            order_id
        ),

        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await notify_admin_new_order(
        context,
        order_id,
        query.from_user,
        f"💎 Premium {months} oy — Akkount",
        price
    )


# =========================================================
# GIFT ORDER
# =========================================================

async def gift_order(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    try:

        months = int(
            query.data.replace(
                "gift_",
                ""
            )
        )

    except ValueError:

        await query.answer(
            "Xato!",
            show_alert=True
        )

        return

    prices = get_gift_prices()

    if months not in prices:

        await query.answer(
            "Bu paket mavjud emas.",
            show_alert=True
        )

        return

    price = prices[months]

    gift_emojis = {
        3: "🧸",
        6: "❤️",
        12: "🌹",
    }

    emoji = gift_emojis.get(
        months,
        "🎁"
    )

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders
        (
            user_id,
            product_type,
            product_name,
            catalog_price,
            xtr_price,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        query.from_user.id,
        "premium_gift",
        f"{emoji} Premium Gift {months} oy",
        price,
        0,
        "waiting_payment"
    ))

    order_id = cur.lastrowid

    conn.commit()
    conn.close()

    keyboard = [

        [
            InlineKeyboardButton(
                "📸 Chek yuborish",
                callback_data=f"receipt_{order_id}"
            )
        ],

        [
            admin_contact_button()
        ],

        [
            InlineKeyboardButton(
                "⬅️ Premium",
                callback_data="premium"
            )
        ],

    ]

    await query.message.reply_text(

        payment_text(
            f"{emoji} Premium Gift {months} oy",
            price,
            order_id
        ),

        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await notify_admin_new_order(
        context,
        order_id,
        query.from_user,
        f"{emoji} Premium Gift {months} oy",
        price
    )


# =========================================================
# ADMIN YANGI BUYURTMA XABARI
# =========================================================

async def notify_admin_new_order(
    context,
    order_id,
    user,
    product,
    price
):

    for admin_id in ADMIN_IDS:

        try:

            username = (
                f"@{user.username}"
                if user.username
                else "yo‘q"
            )

            await context.bot.send_message(

                chat_id=admin_id,

                text=(

                    "🔔 YANGI BUYURTMA\n\n"

                    f"🧾 Buyurtma: #{order_id}\n"
                    f"👤 User ID: {user.id}\n"
                    f"👤 Username: {username}\n"
                    f"👤 Ism: {user.first_name or 'yo‘q'}\n\n"

                    f"🛍 Mahsulot: {product}\n"
                    f"💰 Narx: {price:,} so‘m\n\n"

                    "📌 Holat: TO‘LOV KUTILMOQDA"
                )
            )

        except Exception as e:

            logger.warning(
                "Admin notification error: %s",
                e
            )


# =========================================================
# RECEIPT BUTTON
# =========================================================

async def receipt_request(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    try:

        order_id = int(
            query.data.replace(
                "receipt_",
                ""
            )
        )

    except ValueError:

        await query.answer(
            "Buyurtma raqami noto‘g‘ri.",
            show_alert=True
        )

        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            product_name,
            catalog_price,
            status
        FROM orders
        WHERE id = ?
        AND user_id = ?
    """, (
        order_id,
        query.from_user.id
    ))

    row = cur.fetchone()

    conn.close()

    if not row:

        await query.answer(
            "Buyurtma topilmadi.",
            show_alert=True
        )

        return

    order_id, product, price, status = row

    if status not in (
        "waiting_payment",
        "receipt_sent"
    ):

        await query.answer(
            "Bu buyurtma uchun chek yuborish mumkin emas.",
            show_alert=True
        )

        return

    context.user_data["receipt_order_id"] = order_id

    await query.message.reply_text(

        f"🧾 Buyurtma #{order_id}\n\n"

        f"🛍 {product}\n"
        f"💰 {price:,} so‘m\n\n"

        "📸 Endi to‘lov chekini yoki "
        "to‘lov skrinshotini shu yerga yuboring.\n\n"

        "Masalan:\n"
        "📷 Rasm yuboring\n"
        "yoki\n"
        "📄 Chek faylini yuboring."

    )


# =========================================================
# RECEIPT PHOTO
# =========================================================

async def receipt_photo(update, context):

    user = update.effective_user

    if not await subscription_required(
        update,
        context
    ):
        return

    order_id = context.user_data.get(
        "receipt_order_id"
    )

    if not order_id:

        await update.message.reply_text(

            "ℹ️ Avval buyurtma tanlang.\n\n"

            "⭐ Stars yoki 💎 Premium "
            "bo‘limidan buyurtma bering."

        )

        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            product_name,
            catalog_price,
            user_id
        FROM orders
        WHERE id = ?
    """, (order_id,))

    row = cur.fetchone()

    if not row:

        conn.close()

        await update.message.reply_text(
            "❌ Buyurtma topilmadi."
        )

        return

    product, price, order_user_id = row

    cur.execute("""
        UPDATE orders
        SET status = 'receipt_sent'
        WHERE id = ?
        AND user_id = ?
    """, (
        order_id,
        user.id
    ))

    conn.commit()
    conn.close()

    # Userga
    await update.message.reply_text(

        "✅ Chek qabul qilindi!\n\n"

        f"🧾 Buyurtma: #{order_id}\n"
        f"🛍 {product}\n"
        f"💰 {price:,} so‘m\n\n"

        "⏳ Admin to‘lovni tekshiradi.\n"
        "Keyin buyurtmangiz bajariladi.\n\n"

        "Agar tezroq bog‘lanmoqchi bo‘lsangiz:",

        reply_markup=InlineKeyboardMarkup([
            [admin_contact_button()]
        ])

    )

    # Admin
    for admin_id in ADMIN_IDS:

        try:

            username = (
                f"@{user.username}"
                if user.username
                else "yo‘q"
            )

            await context.bot.send_message(

                chat_id=admin_id,

                text=(

                    "📸 YANGI CHEK KELDI!\n\n"

                    f"🧾 Buyurtma: #{order_id}\n"
                    f"👤 User ID: {user.id}\n"
                    f"👤 Username: {username}\n"
                    f"👤 Ism: {user.first_name or 'yo‘q'}\n\n"

                    f"🛍 Mahsulot: {product}\n"
                    f"💰 Narx: {price:,} so‘m\n\n"

                    "📌 Holat: CHEK TEKSHIRILISHI KERAK"
                ),

                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "👤 Mijoz bilan bog‘lanish",
                            url=f"tg://user?id={user.id}"
                        )
                    ]
                ])
            )

            # Chekni adminning chatiga forward qilish
            await update.message.forward(
                chat_id=admin_id
            )

        except Exception as e:

            logger.warning(
                "Receipt admin send error: %s",
                e
            )

    context.user_data.pop(
        "receipt_order_id",
        None
    )


# =========================================================
# RECEIPT DOCUMENT
# =========================================================

async def receipt_document(update, context):

    user = update.effective_user

    if not await subscription_required(
        update,
        context
    ):
        return

    order_id = context.user_data.get(
        "receipt_order_id"
    )

    if not order_id:

        await update.message.reply_text(
            "ℹ️ Avval buyurtma tanlang."
        )

        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            product_name,
            catalog_price
        FROM orders
        WHERE id = ?
        AND user_id = ?
    """, (
        order_id,
        user.id
    ))

    row = cur.fetchone()

    if not row:

        conn.close()

        await update.message.reply_text(
            "❌ Buyurtma topilmadi."
        )

        return

    product, price = row

    cur.execute("""
        UPDATE orders
        SET status = 'receipt_sent'
        WHERE id = ?
        AND user_id = ?
    """, (
        order_id,
        user.id
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(

        "✅ Chek fayli qabul qilindi!\n\n"

        f"🧾 Buyurtma: #{order_id}\n"
        "⏳ Admin tekshirmoqda.\n\n"

        "Savol bo‘lsa, admin bilan bog‘laning:",

        reply_markup=InlineKeyboardMarkup([
            [admin_contact_button()]
        ])
    )

    for admin_id in ADMIN_IDS:

        try:

            username = (
                f"@{user.username}"
                if user.username
                else "yo‘q"
            )

            await context.bot.send_message(

                chat_id=admin_id,

                text=(

                    "📄 YANGI CHEK FAYLI!\n\n"

                    f"🧾 Buyurtma: #{order_id}\n"
                    f"👤 User ID: {user.id}\n"
                    f"👤 Username: {username}\n"
                    f"👤 Ism: {user.first_name or 'yo‘q'}\n\n"

                    f"🛍 Mahsulot: {product}\n"
                    f"💰 Narx: {price:,} so‘m"
                ),

                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "👤 Mijoz bilan bog‘lanish",
                            url=f"tg://user?id={user.id}"
                        )
                    ]
                ])
            )

            await update.message.forward(
                chat_id=admin_id
            )

        except Exception as e:

            logger.warning(
                "Document receipt error: %s",
                e
            )

    context.user_data.pop(
        "receipt_order_id",
        None
    )


# =========================================================
# ORDERS
# =========================================================

async def orders(update, context):

    query = update.callback_query

    if not await subscription_required(
        update,
        context
    ):
        return

    await query.answer()

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            product_name,
            catalog_price,
            status,
            created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 15
    """, (
        query.from_user.id,
    ))

    rows = cur.fetchall()

    conn.close()

    if not rows:

        text = (
            "📦 Sizda hali buyurtmalar yo‘q."
        )

    else:

        text = "📦 Buyurtmalarim\n\n"

        for (
            order_id,
            product,
            price,
            status,
            created_at
        ) in rows:

            status_text = {

                "pending":
                    "⏳ Kutilmoqda",

                "waiting_payment":
                    "💳 To‘lov kutilmoqda",

                "receipt_sent":
                    "📸 Chek yuborildi",

                "paid":
                    "✅ To‘langan",

                "completed":
                    "🎉 Bajarildi",

                "pending_admin":
                    "👨‍💼 Admin bajaradi",

                "cancelled":
                    "❌ Bekor qilingan",

            }.get(
                status,
                status
            )

            text += (

                f"🧾 #{order_id}\n"
                f"🛍 {product}\n"
                f"💰 {price:,} so‘m\n"
                f"📌 {status_text}\n"
                f"🕐 {created_at}\n\n"

            )

    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Orqaga",
            callback_data="home"
        )
    ]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# HELP
# =========================================================

async def help_menu(update, context):

    query = update.callback_query

    await query.answer()

    keyboard = [

        [
            admin_contact_button()
        ],

        [
            InlineKeyboardButton(
                "⬅️ Orqaga",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(

        "📞 Yordam\n\n"

        "Buyurtma yoki to‘lov bo‘yicha "
        "muammo bo‘lsa, admin bilan bog‘laning.\n\n"

        "💳 To‘lov Hamkorbank karta orqali.\n"
        "📸 To‘lovdan keyin chek yuboriladi.\n"
        "👨‍💼 Admin to‘lovni tekshiradi.",

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_command(update, context):

    user = update.effective_user

    if not is_admin(user.id):

        await update.message.reply_text(
            "⛔ Siz admin emassiz."
        )

        return

    await show_admin_panel(
        update,
        context
    )


async def show_admin_panel(update, context):

    keyboard = [

        [
            InlineKeyboardButton(
                "📊 Statistika",
                callback_data="admin_stats"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 Buyurtmalar",
                callback_data="admin_orders"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Foydalanuvchilar",
                callback_data="admin_users"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 Stars narxlari",
                callback_data="admin_stars"
            )
        ],

        [
            InlineKeyboardButton(
                "💎 Premium narxlari",
                callback_data="admin_premium"
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Majburiy kanallar",
                callback_data="admin_channels"
            )
        ],

    ]

    text = (
        "👨‍💼 FrostShop Admin Panel\n\n"
        "Kerakli bo‘limni tanlang:"
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================================================
# ADMIN STATS
# =========================================================

async def admin_stats(update, context):

    query = update.callback_query

    if not is_admin(query.from_user.id):

        await query.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    await query.answer()

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )

    users = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM orders"
    )

    orders_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status IN (
            'paid',
            'receipt_sent',
            'waiting_payment',
            'completed'
        )
    """)

    active_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'completed'
    """)

    completed = cur.fetchone()[0]

    conn.close()

    text = (

        "📊 STATISTIKA\n\n"

        f"👥 Foydalanuvchilar: {users}\n"
        f"📦 Buyurtmalar: {orders_count}\n"
        f"🔄 Aktiv buyurtmalar: {active_orders}\n"
        f"✅ Bajarilgan: {completed}\n"

    )

    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Admin panel",
            callback_data="admin"
        )
    ]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADMIN USERS
# =========================================================

async def admin_users(update, context):

    query = update.callback_query

    if not is_admin(query.from_user.id):

        await query.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    await query.answer()

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, username, first_name
        FROM users
        ORDER BY created_at DESC
        LIMIT 20
    """)

    rows = cur.fetchall()

    conn.close()

    if not rows:

        text = "👥 Hali foydalanuvchilar yo‘q."

    else:

        text = "👥 So‘nggi foydalanuvchilar:\n\n"

        for (
            user_id,
            username,
            first_name
        ) in rows:

            text += (

                f"🆔 {user_id}\n"
                f"👤 {first_name or 'yo‘q'}\n"
                f"@{username or 'yo‘q'}\n\n"

            )

    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Admin panel",
            callback_data="admin"
        )
    ]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADMIN ORDERS
# =========================================================

async def admin_orders(update, context):

    query = update.callback_query

    if not is_admin(query.from_user.id):

        await query.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    await query.answer()

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            user_id,
            product_name,
            catalog_price,
            status,
            created_at
        FROM orders
        ORDER BY id DESC
        LIMIT 30
    """)

    rows = cur.fetchall()

    conn.close()

    if not rows:

        text = "📦 Hali buyurtmalar yo‘q."

    else:

        text = "📦 SO‘NGGI BUYURTMALAR\n\n"

        for row in rows:

            (
                order_id,
                user_id,
                product,
                price,
                status,
                created_at
            ) = row

            text += (

                f"#{order_id} | User: {user_id}\n"
                f"🛍 {product}\n"
                f"💰 {price:,} so‘m\n"
                f"📌 {status}\n"
                f"🕐 {created_at}\n\n"

            )

    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Admin panel",
            callback_data="admin"
        )
    ]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADMIN STARS
# =========================================================

async def admin_stars(update, context):

    query = update.callback_query

    if not is_admin(query.from_user.id):

        await query.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    await query.answer()

    prices = get_stars_prices()

    text = "⭐ STARS NARXLARI\n\n"

    for stars, price in prices.items():

        text += (
            f"{stars} ⭐ = {price:,} so‘m\n"
        )

    text += (

        "\nNarxni o‘zgartirish:\n"
        "/setstars STARS NARX\n\n"

        "Misol:\n"
        "/setstars 200 40000"

    )

    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Admin panel",
            callback_data="admin"
        )
    ]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADMIN PREMIUM
# =========================================================

async def admin_premium(update, context):

    query = update.callback_query

    if not is_admin(query.from_user.id):

        await query.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    await query.answer()

    account = get_account_prices()
    gift = get_gift_prices()

    text = "💎 PREMIUM NARXLARI\n\n"

    text += "🔐 Akkountga:\n"

    for months, price in account.items():

        text += (
            f"{months} oy = {price:,} so‘m\n"
        )

    text += "\n🎁 Gift:\n"

    for months, price in gift.items():

        text += (
            f"{months} oy = {price:,} so‘m\n"
        )

    text += (

        "\nAkkount narxi:\n"
        "/setaccount 1 40000\n"
        "/setaccount 12 310000\n\n"

        "Gift narxi:\n"
        "/setgift 3 170000\n"
        "/setgift 6 230000\n"
        "/setgift 12 395000"

    )

    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Admin panel",
            callback_data="admin"
        )
    ]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADMIN CHANNELS
# =========================================================

async def admin_channels(update, context):

    query = update.callback_query

    if not is_admin(query.from_user.id):

        await query.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    await query.answer()

    channels = get_required_channels()

    text = "📢 MAJBURIY KANALLAR\n\n"

    if not channels:

        text += "❌ Hozircha majburiy kanal yo‘q.\n\n"

    else:

        for index, (channel_id, channel) in enumerate(
            channels,
            start=1
        ):

            text += f"{index}. {channel}\n"

        text += "\n"

    text += (

        "➕ Kanal qo‘shish:\n"
        "/addchannel @kanal\n\n"

        "🗑 Kanal o‘chirish:\n"
        "/delchannel @kanal\n\n"

        "⚠️ Bot kanalga admin sifatida "
        "qo‘shilgan bo‘lishi kerak."

    )

    keyboard = [

        [
            InlineKeyboardButton(
                "🔄 Yangilash",
                callback_data="admin_channels"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Admin panel",
                callback_data="admin"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADD CHANNEL
# =========================================================

async def addchannel(update, context):

    if not is_admin(
        update.effective_user.id
    ):
        return

    if len(context.args) != 1:

        await update.message.reply_text(

            "❌ Format noto‘g‘ri.\n\n"
            "/addchannel @kanal_username"

        )

        return

    channel = context.args[0].strip()

    if not channel.startswith("@"):

        channel = "@" + channel

    if len(channel) <= 1:

        await update.message.reply_text(
            "❌ Kanal username noto‘g‘ri."
        )

        return

    added = add_required_channel(channel)

    if added:

        await update.message.reply_text(

            "✅ Majburiy kanal qo‘shildi!\n\n"
            f"📢 {channel}\n\n"
            "⚠️ Bot kanalga admin sifatida "
            "qo‘shilgan bo‘lishi kerak."

        )

    else:

        await update.message.reply_text(
            "ℹ️ Bu kanal allaqachon mavjud."
        )


# =========================================================
# DELETE CHANNEL
# =========================================================

async def delchannel(update, context):

    if not is_admin(
        update.effective_user.id
    ):
        return

    if len(context.args) != 1:

        await update.message.reply_text(
            "/delchannel @kanal_username"
        )

        return

    channel = context.args[0].strip()

    if not channel.startswith("@"):

        channel = "@" + channel

    deleted = delete_required_channel(channel)

    if deleted:

        await update.message.reply_text(
            f"✅ Kanal o‘chirildi: {channel}"
        )

    else:

        await update.message.reply_text(
            "❌ Kanal topilmadi."
        )


# =========================================================
# SET STARS
# =========================================================

async def setstars(update, context):

    if not is_admin(
        update.effective_user.id
    ):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "/setstars STARS NARX\n\n"
            "Misol:\n"
            "/setstars 200 40000"
        )

        return

    try:

        stars = int(context.args[0])
        price = int(context.args[1])

    except ValueError:

        await update.message.reply_text(
            "❌ Sonlarni to‘g‘ri kiriting."
        )

        return

    if stars <= 0 or price <= 0:

        await update.message.reply_text(
            "❌ Sonlar 0 dan katta bo‘lishi kerak."
        )

        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO stars_prices
        (stars, uzs_price)
        VALUES (?, ?)
    """, (
        stars,
        price
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ {stars} Stars = {price:,} so‘m"
    )


# =========================================================
# SET ACCOUNT PREMIUM
# =========================================================

async def setaccount(update, context):

    if not is_admin(
        update.effective_user.id
    ):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "/setaccount OY NARX\n\n"
            "Misol:\n"
            "/setaccount 1 40000"
        )

        return

    try:

        months = int(context.args[0])
        price = int(context.args[1])

    except ValueError:

        await update.message.reply_text(
            "❌ Noto‘g‘ri son."
        )

        return

    if months <= 0 or price <= 0:

        await update.message.reply_text(
            "❌ Sonlar 0 dan katta bo‘lishi kerak."
        )

        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO premium_account_prices
        (months, uzs_price)
        VALUES (?, ?)
    """, (
        months,
        price
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Premium {months} oy = {price:,} so‘m"
    )


# =========================================================
# SET GIFT
# =========================================================

async def setgift(update, context):

    if not is_admin(
        update.effective_user.id
    ):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "/setgift OY NARX\n\n"
            "Misol:\n"
            "/setgift 3 170000"
        )

        return

    try:

        months = int(context.args[0])
        price = int(context.args[1])

    except ValueError:

        await update.message.reply_text(
            "❌ Noto‘g‘ri son."
        )

        return

    if months <= 0 or price <= 0:

        await update.message.reply_text(
            "❌ Sonlar 0 dan katta bo‘lishi kerak."
        )

        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO premium_gift_prices
        (months, uzs_price)
        VALUES (?, ?)
    """, (
        months,
        price
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Gift {months} oy = {price:,} so‘m"
    )


# =========================================================
# ADMIN CALLBACK ROUTER
# =========================================================

async def admin_router(update, context):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    data = query.data

    if data == "admin":

        await query.answer()

        await show_admin_panel(
            update,
            context
        )

    elif data == "admin_stats":

        await admin_stats(
            update,
            context
        )

    elif data == "admin_orders":

        await admin_orders(
            update,
            context
        )

    elif data == "admin_users":

        await admin_users(
            update,
            context
        )

    elif data == "admin_stars":

        await admin_stars(
            update,
            context
        )

    elif data == "admin_premium":

        await admin_premium(
            update,
            context
        )

    elif data == "admin_channels":

        await admin_channels(
            update,
            context
        )


# =========================================================
# GENERAL CALLBACK ROUTER
# =========================================================

async def callback_router(update, context):

    query = update.callback_query

    data = query.data

    # ADMIN
    if (
        data == "admin"
        or data.startswith("admin_")
    ):

        await admin_router(
            update,
            context
        )

        return

    # CHECK SUB
    if data == "check_sub":

        if is_admin(query.from_user.id):

            await query.answer(
                "👑 Admin uchun obuna shart emas.",
                show_alert=True
            )

            await show_home(
                update,
                context
            )

            return

        if await is_subscribed(
            context.bot,
            query.from_user.id
        ):

            await query.answer(
                "✅ Barcha obunalar tasdiqlandi!",
                show_alert=True
            )

            await show_home(
                update,
                context
            )

        else:

            await query.answer(
                "❌ Hali barcha kanallarga "
                "obuna bo‘lmagansiz.",
                show_alert=True
            )

            await subscription_required(
                update,
                context
            )

        return

    # SUBSCRIPTION
    if not await is_subscribed(
        context.bot,
        query.from_user.id
    ):

        await subscription_required(
            update,
            context
        )

        return

    # HOME
    if data == "home":

        await query.answer()

        await show_home(
            update,
            context
        )

    # STARS
    elif data == "stars":

        await stars_menu(
            update,
            context
        )

    elif data.startswith("buy_stars_"):

        await buy_stars(
            update,
            context
        )

    # PREMIUM
    elif data == "premium":

        await premium_menu(
            update,
            context
        )

    elif data == "premium_account":

        await premium_account(
            update,
            context
        )

    elif data.startswith("account_"):

        await account_order(
            update,
            context
        )

    elif data == "premium_gift":

        await premium_gift(
            update,
            context
        )

    elif data.startswith("gift_"):

        await gift_order(
            update,
            context
        )

    # RECEIPT
    elif data.startswith("receipt_"):

        await receipt_request(
            update,
            context
        )

    # ORDERS
    elif data == "orders":

        await orders(
            update,
            context
        )

    # HELP
    elif data == "help":

        await help_menu(
            update,
            context
        )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):

    logger.error(
        "Bot xatosi:",
        exc_info=context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    init_db()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # =========================================
    # COMMANDS
    # =========================================

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "admin",
            admin_command
        )
    )

    app.add_handler(
        CommandHandler(
            "setstars",
            setstars
        )
    )

    app.add_handler(
        CommandHandler(
            "setaccount",
            setaccount
        )
    )

    app.add_handler(
        CommandHandler(
            "setgift",
            setgift
        )
    )

    app.add_handler(
        CommandHandler(
            "addchannel",
            addchannel
        )
    )

    app.add_handler(
        CommandHandler(
            "delchannel",
            delchannel
        )
    )

    # =========================================
    # CALLBACKS
    # =========================================

    app.add_handler(
        CallbackQueryHandler(
            callback_router
        )
    )

    # =========================================
    # RECEIPT PHOTO
    # =========================================

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            receipt_photo
        )
    )

    # =========================================
    # RECEIPT DOCUMENT
    # =========================================

    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            receipt_document
        )
    )

    # =========================================
    # ERROR
    # =========================================

    app.add_error_handler(
        error_handler
    )

    print("================================")
    print("🤖 FrostShop ishga tushdi...")
    print("💳 Hamkorbank manual payment: ON")
    print("⭐ Stars payment: MANUAL")
    print("💎 Premium payment: MANUAL")
    print("🎁 Gift payment: MANUAL")
    print("================================")

    app.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()

