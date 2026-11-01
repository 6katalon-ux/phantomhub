"""
Aiogram 3 Telegram Bot Message and Callback Handlers.
Implements auto user registration, plan buying, free trials, service lookups,
wallet topups, payment receipt submission, and gift codes.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import math
import html

from app.models.models import User, Plan, Service, Payment, GiftCode, GiftRedemption
from app.core.database import AsyncSessionLocal
from app.core.config import config
from typing import Optional
from app.services.vpn_provisioner import vpn_provisioner
from app.services.wallet import wallet_service
from app.bot.keyboards import (
    main_menu_keyboard, plans_keyboard, plan_confirm_keyboard,
    service_actions_keyboard, cancel_keyboard,
    wallet_topup_keyboard, admin_payment_review_keyboard
)
from app.services.telegram_notify import get_admin_telegram_ids, send_telegram_notification
from app.core.logging import logger

router = Router()

class FormStates(StatesGroup):
    waiting_for_custom_amount = State()
    waiting_for_payment_receipt = State()
    waiting_for_gift_code = State()

def parse_persian_number(val: str) -> Optional[int]:
    """Extract and parse numbers with support for Persian and Arabic digits"""
    if not val:
        return None
    persian_to_eng = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    }
    cleaned = str(val).replace(',', '').replace('،', '').replace('.', '').replace(' ', '')
    for k, v in persian_to_eng.items():
        cleaned = cleaned.replace(k, v)
    import re
    nums = re.findall(r'\d+', cleaned)
    if nums:
        try:
            return int(nums[0])
        except Exception:
            return None
    return None


async def get_or_create_user(session: AsyncSession, msg: Message) -> User:
    """Ensure user is registered in SQLite with latest profile details"""
    tg_id = msg.from_user.id
    res = await session.execute(select(User).where(User.telegram_id == tg_id))
    user = res.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=tg_id,
            username=msg.from_user.username or "",
            first_name=msg.from_user.first_name or "",
            last_name=msg.from_user.last_name or "",
            wallet_balance=0,
            trial_used=0,
            is_blocked=0
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Registered new user from Telegram: {tg_id} (@{msg.from_user.username})")
    else:
        # Keep username, names fresh and heal null wallet_balance
        dirty = False
        if msg.from_user.username and user.username != msg.from_user.username:
            user.username = msg.from_user.username
            dirty = True
        if msg.from_user.first_name and user.first_name != msg.from_user.first_name:
            user.first_name = msg.from_user.first_name
            dirty = True
        if msg.from_user.last_name and user.last_name != msg.from_user.last_name:
            user.last_name = msg.from_user.last_name
            dirty = True
        if user.wallet_balance is None:
            user.wallet_balance = 0
            dirty = True
        if dirty:
            await session.commit()
    return user


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if config.get_bool("bot_maintenance", False):
        await message.answer("⚠️ ربات موقتاً در حال ارتقا و نگهداری است. لطفاً دقایقی دیگر مراجعه فرمایید.")
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        if user.is_blocked:
            await message.answer("⛔ حساب کاربری شما توسط مدیریت مسدود شده است.")
            return

    welcome_msg = config.get(
        "bot_welcome_msg",
        "سلام! به ربات رسمی خرید و مدیریت اشتراک خوش آمدید.\nجهت ادامه یکی از گزینه‌های زیر را انتخاب نمایید:"
    )
    await message.answer(welcome_msg, reply_markup=main_menu_keyboard())

# --- 1. Buy VPN ---
@router.message(F.text.contains("خرید اشتراک") | F.text.contains("Buy VPN") | Command("buy"))
async def handle_buy_menu(message: Message, state: FSMContext):
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        if user.is_blocked:
            return

        res = await session.execute(
            select(Plan).where(Plan.is_active == 1).order_by(Plan.sort_order.asc(), Plan.price.asc())
        )
        plans = res.scalars().all()

        if not plans:
            await message.answer("⚠️ در حال حاضر هیچ پلن فعالی در فروشگاه تعریف نشده است.")
            return

        currency = config.get("currency", "تومان")
        wallet_bal = user.wallet_balance if user.wallet_balance is not None else 0
        text = f"🛍️ *لیست پلن‌های اشتراک VPN*\n\n"
        text += f"💰 موجودی فعلی کیف پول شما: *{wallet_bal:,} {currency}*\n\n"
        text += "لطفاً پلن مورد نظر خود را از دکمه‌های زیر انتخاب فرمایید:"
        await message.answer(text, parse_mode="Markdown", reply_markup=plans_keyboard(plans))

@router.callback_query(F.data.startswith("buy_plan_"))
async def callback_select_plan(callback: CallbackQuery):
    plan_id = int(callback.data.split("_")[2])
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Plan).where(Plan.id == plan_id))
        plan = res.scalar_one_or_none()
        if not plan:
            await callback.answer("پلن یافت نشد!", show_alert=True)
            return

        res_user = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = res_user.scalar_one_or_none()
        currency = config.get("currency", "تومان")
        wallet_bal = user.wallet_balance if (user and user.wallet_balance is not None) else 0

        text = f"📦 *جزئیات پلن انتخابی:*\n\n"
        text += f"🔹 نام: *{plan.name}*\n"
        text += f"🔹 حجم: *{plan.traffic_gb} گیگابایت*\n"
        text += f"🔹 مدت اعتبار: *{plan.duration_days} روز*\n"
        text += f"🔹 قیمت: *{plan.price:,} {currency}*\n"
        text += f"🔹 حداکثر کاربر: *{plan.max_ips} کاربر همزمان*\n\n"
        text += f"💰 موجودی کیف پول شما: *{wallet_bal:,} {currency}*\n"

        if wallet_bal < plan.price:
            shortage = plan.price - wallet_bal
            text += f"\n❌ *موجودی شما کافی نیست.* برای خرید این پلن نیاز به شارژ *{shortage:,} {currency}* دیگر دارید.\nاز منوی اصلی روی «افزایش موجودی» بزنید."
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            return

        text += "\nآیا مایل به خرید این اشتراک و کسر هزینه از کیف پول خود هستید؟"
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=plan_confirm_keyboard(plan.id))
        await callback.answer()

@router.callback_query(F.data.startswith("confirm_buy_"))
async def callback_confirm_purchase(callback: CallbackQuery):
    plan_id = int(callback.data.split("_")[2])
    await callback.message.edit_text("⏳ در حال اتصال به سرور و ایجاد کانفیگ اختصاصی شما... لطفاً چند لحظه صبر کنید.")

    async with AsyncSessionLocal() as session:
        res_u = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = res_u.scalar_one_or_none()
        if not user:
            await callback.answer("کاربر یافت نشد", show_alert=True)
            return

        success, service, msg = await vpn_provisioner.purchase_plan(
            session=session,
            user_id=user.id,
            telegram_id=user.telegram_id,
            plan_id=plan_id
        )

        if not success:
            await callback.message.edit_text(f"❌ خطا در فعال‌سازی سرویس:\n{msg}")
            return

        expire_date = datetime.fromtimestamp(service.expire_time_ms / 1000).strftime("%Y-%m-%d")
        total_gb = service.total_traffic_bytes / (1024**3)

        response_text = f"🎉 *اشتراک شما با موفقیت فعال شد!*\n\n"
        response_text += f"🔑 شناسه سرویس: `{service.id}`\n"
        response_text += f"📊 حجم کل: `{total_gb:.1f} گیگابایت`\n"
        response_text += f"📅 تاریخ انقضا: `{expire_date}`\n\n"
        response_text += f"📋 *کانفیگ اتصال شما:*\n`{service.config_link}`\n\n"
        response_text += f"💡 _کانفیگ بالا را کپی کرده و در برنامه v2rayNG (اندروید) یا v2box / Streisand (آیفون) وارد فرمایید._"

        await callback.message.edit_text(response_text, parse_mode="Markdown", reply_markup=service_actions_keyboard(service.id))
        await callback.answer("خرید با موفقیت انجام شد ✅")

# --- 2. Free Trial ---
@router.message(F.text.contains("تست رایگان") | F.text.contains("Free Trial") | Command("trial"))
async def handle_free_trial(message: Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        if user.trial_used:
            await message.answer("⚠️ شما پیش از این یک بار تست رایگان را دریافت کرده‌اید و مجاز به دریافت مجدد نیستید.")
            return

        await message.answer("⏳ در حال ایجاد اکانت تست رایگان برای شما...")
        success, service, msg = await vpn_provisioner.claim_free_trial(
            session=session,
            user_id=user.id,
            telegram_id=user.telegram_id
        )

        if not success:
            await message.answer(f"❌ خطا در ایجاد تست رایگان: {msg}")
            return

        expire_date = datetime.fromtimestamp(service.expire_time_ms / 1000).strftime("%Y-%m-%d")
        traffic_gb = config.get("trial_traffic_gb", 1)

        text = f"🎁 *اکانت تست رایگان شما آماده شد!*\n\n"
        text += f"📊 حجم: *{traffic_gb} گیگابایت*\n"
        text += f"📅 مهلت استفاده: `{expire_date}`\n\n"
        text += f"📋 *کانفیگ تست:*\n`{service.config_link}`\n\n"
        text += "پس از تست، می‌توانید از بخش خرید اشتراک پلن اصلی خود را سفارش دهید."
        await message.answer(text, parse_mode="Markdown", reply_markup=service_actions_keyboard(service.id))

# --- 3. My Account ---
@router.message(
    F.text.contains("حساب کاربری") |
    F.text.contains("حساب من") |
    F.text.contains("حساب") |
    F.text.contains("پروفایل") |
    F.text.contains("My Account") |
    F.text.contains("Account") |
    Command("account") |
    Command("profile")
)
async def handle_my_account(message: Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        res = await session.execute(select(Service).where(Service.user_id == user.id))
        services = res.scalars().all()
        currency = config.get("currency", "تومان")

        reg_date = user.created_at.strftime("%Y-%m-%d") if user.created_at else "نامشخص"
        active_count = sum(1 for s in services if s.is_active)
        wallet_bal = user.wallet_balance if user.wallet_balance is not None else 0
        trial_status = "دریافت شده" if user.trial_used else "قابل دریافت"

        safe_first = html.escape(user.first_name or "")
        safe_last = html.escape(user.last_name or "")
        full_name = f"{safe_first} {safe_last}".strip() or "کاربر گرامی"
        username_str = f"@{html.escape(user.username)}" if user.username else "ندارد"

        text = (
            f"👤 <b>مشخصات حساب کاربری شما:</b>\n\n"
            f"🆔 شناسه کاربری عددی: <code>{user.telegram_id}</code>\n"
            f"👤 نام: <b>{full_name}</b>\n"
            f"🏷️ نام کاربری: <b>{username_str}</b>\n"
            f"💰 موجودی کیف پول: <b>{wallet_bal:,} {currency}</b>\n"
            f"📡 تعداد سرویس‌های فعال: <b>{active_count} عدد</b>\n"
            f"🎁 وضعیت تست رایگان: <b>{trial_status}</b>\n"
            f"📅 تاریخ عضویت: <code>{reg_date}</code>\n"
        )

        try:
            await message.answer(text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"HTML send failed for my_account ({e}), falling back to plain text")
            plain_text = (
                f"👤 مشخصات حساب کاربری شما:\n\n"
                f"🆔 شناسه کاربری عددی: {user.telegram_id}\n"
                f"👤 نام: {user.first_name or ''} {user.last_name or ''}\n"
                f"🏷️ نام کاربری: @{user.username or 'ندارد'}\n"
                f"💰 موجودی کیف پول: {wallet_bal:,} {currency}\n"
                f"📡 تعداد سرویس‌های فعال: {active_count} عدد\n"
                f"🎁 وضعیت تست رایگان: {trial_status}\n"
                f"📅 تاریخ عضویت: {reg_date}\n"
            )
            await message.answer(plain_text)

# --- 4. My Services ---
@router.message(F.text.contains("سرویس‌های من") | F.text.contains("My Services") | Command("services"))
async def handle_my_services(message: Message, state: FSMContext):
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        res = await session.execute(
            select(Service).where(Service.user_id == user.id).order_by(Service.id.desc())
        )
        services = res.scalars().all()

        if not services:
            await message.answer("📡 شما در حال حاضر هیچ اشتراکی ندارید.\nبرای خرید اشتراک از منوی اصلی اقدام فرمایید.")
            return

        await message.answer(f"📡 *لیست اشتراک‌های شما ({len(services)} مورد):*", parse_mode="Markdown")

        for s in services[:5]: # Show up to 5 latest
            used_gb = s.used_traffic_bytes / (1024**3)
            total_gb = s.total_traffic_bytes / (1024**3)
            expire_date = datetime.fromtimestamp(s.expire_time_ms / 1000).strftime("%Y-%m-%d")
            status_badge = "🟢 فعال" if s.is_active else "🔴 منقضی / غیرفعال"

            card = f"📌 *سرویس شماره {s.id}* ({status_badge})\n"
            card += f"📊 مصرف: *{used_gb:.2f} / {total_gb:.1f} گیگابایت*\n"
            card += f"📅 تاریخ انقضا: `{expire_date}`\n"
            card += f"📋 کانفیگ:\n`{s.config_link}`"

            await message.answer(card, parse_mode="Markdown", reply_markup=service_actions_keyboard(s.id))

# --- 5. Payment & Wallet Top-up ---
@router.message(F.text.contains("کارت به کارت") | F.text.contains("افزایش موجودی") | F.text.contains("Payment") | F.text.contains("Wallet") | Command("wallet") | Command("pay"))
async def handle_payment_menu(message: Message, state: FSMContext):
    await state.clear()

    card_number = config.get("card_number", "6037-9975-0000-0000")
    card_holder = config.get("card_holder", "صاحب حساب")
    crypto_wallet = config.get("crypto_wallet", "")
    instructions = config.get("payment_instructions", "")
    currency = config.get("currency", "تومان")

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        user_balance = user.wallet_balance if user.wallet_balance is not None else 0

    text = f"💰 *مدیریت کیف پول و افزایش موجودی*\n\n"
    text += f"👤 کاربر: *{message.from_user.first_name or ''}*\n"
    text += f"💵 موجودی فعلی: *{user_balance:,} {currency}*\n\n"
    text += f"💳 *شماره کارت بانکی (لمس جهت کپی):*\n`{card_number}`\n"
    text += f"👤 *به نام:* {card_holder}\n\n"
    if crypto_wallet:
        text += f"🪙 *آدرس کیف پول تتر / کریپتو:*\n`{crypto_wallet}`\n\n"
    if instructions:
        text += f"ℹ️ *توضیحات:* {instructions}\n\n"
    text += f"👇 لطفاً یکی از مبالغ زیر را جهت افزایش موجودی انتخاب فرمایید، یا گزینه *مبلغ دلخواه* را لمس کنید:"

    await message.answer(text, parse_mode="Markdown", reply_markup=wallet_topup_keyboard())

@router.callback_query(F.data.startswith("topup_amt_"))
async def handle_topup_amount_selection(callback: CallbackQuery, state: FSMContext):
    card_number = config.get("card_number", "6037-9975-0000-0000")
    card_holder = config.get("card_holder", "صاحب حساب")
    currency = config.get("currency", "تومان")

    if callback.data == "topup_amt_custom":
        await state.set_state(FormStates.waiting_for_custom_amount)
        text = (
            f"✏️ *ورود مبلغ دلخواه*\n\n"
            f"لطفاً مبلغ مورد نظر خود را به *{currency}* ارسال فرمایید:\n"
            f"💡 _حداقل مبلغ قابل افزایش: ۱۰,۰۰۰ {currency}_"
        )
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard())
        except Exception:
            await callback.message.answer(text, parse_mode="Markdown", reply_markup=cancel_keyboard())
        await callback.answer()
        return

    amount_str = callback.data.replace("topup_amt_", "")
    try:
        amount = int(amount_str)
    except ValueError:
        await callback.answer("خطا در انتخاب مبلغ", show_alert=True)
        return

    await state.update_data(topup_amount=amount)
    await state.set_state(FormStates.waiting_for_payment_receipt)

    text = (
        f"💳 *افزایش موجودی به مبلغ: {amount:,} {currency}*\n\n"
        f"لطفاً مبلغ فوق را به شماره کارت زیر انتقال دهید:\n\n"
        f"💳 *شماره کارت (لمس جهت کپی):*\n`{card_number}`\n"
        f"👤 *به نام:* {card_holder}\n\n"
        f"📸 *مرحله بعد:* پس از واریز وجه، لطفاً *تصویر فیش واریزی* (یا شماره پیگیری) را همینجا ارسال فرمایید."
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=cancel_keyboard())
    await callback.answer()

def is_navigation_or_cancel(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in [
        "/start", "/cancel", "لغو", "انصراف",
        "خرید اشتراک", "buy", "تست رایگان", "trial",
        "حساب", "account", "سرویس", "service",
        "موجودی", "کارت", "wallet", "payment",
        "کد هدیه", "gift", "پشتیبانی", "support"
    ])

async def handle_navigation_fallback(message: Message, state: FSMContext):
    await state.clear()
    t = (message.text or "").lower()
    if any(c in t for c in ["/cancel", "لغو", "انصراف"]):
        await message.answer("عملیات لغو شد.", reply_markup=main_menu_keyboard())
        return
    if "حساب" in t or "account" in t or "پروفایل" in t:
        await handle_my_account(message, state)
        return
    if "سرویس" in t or "service" in t:
        await handle_my_services(message, state)
        return
    if "خرید" in t or "buy" in t:
        await handle_buy_menu(message, state)
        return
    if "تست" in t or "trial" in t:
        await handle_free_trial(message, state)
        return
    if "پشتیبانی" in t or "support" in t:
        await handle_support(message, state)
        return
    if "موجودی" in t or "کارت" in t or "wallet" in t or "payment" in t:
        await handle_payment_menu(message, state)
        return
    if "کد هدیه" in t or "gift" in t:
        await handle_gift_code_prompt(message, state)
        return
    await message.answer("به منوی اصلی بازگشتید.", reply_markup=main_menu_keyboard())

@router.message(FormStates.waiting_for_custom_amount)
async def process_custom_amount(message: Message, state: FSMContext):
    if message.text and is_navigation_or_cancel(message.text):
        await handle_navigation_fallback(message, state)
        return

    currency = config.get("currency", "تومان")
    amount = parse_persian_number(message.text or "")
    if not amount or amount < 10000:
        await message.answer(
            f"⚠️ *مبلغ وارد شده معتبر نیست!*\n\n"
            f"لطفاً مبلغی حداقل معادل *۱۰,۰۰۰ {currency}* به صورت عدد وارد فرمایید.\n"
            f"مثال: `150000`\n"
            f"برای انصراف دکمه زیر را لمس کنید.",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard()
        )
        return

    await state.update_data(topup_amount=amount)
    await state.set_state(FormStates.waiting_for_payment_receipt)

    card_number = config.get("card_number", "6037-9975-0000-0000")
    card_holder = config.get("card_holder", "صاحب حساب")

    text = (
        f"💳 *افزایش موجودی به مبلغ: {amount:,} {currency}*\n\n"
        f"لطفاً مبلغ فوق را به کارت زیر واریز فرمایید:\n\n"
        f"💳 *شماره کارت (لمس جهت کپی):*\n`{card_number}`\n"
        f"👤 *به نام:* {card_holder}\n\n"
        f"📸 *مرحله بعد:* پس از واریز وجه، لطفاً *تصویر فیش واریزی* (یا متن شماره پیگیری) را همینجا ارسال فرمایید."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=cancel_keyboard())

@router.message(FormStates.waiting_for_payment_receipt)
async def process_payment_receipt(message: Message, state: FSMContext):
    if message.text and not message.photo and is_navigation_or_cancel(message.text):
        await handle_navigation_fallback(message, state)
        return

    data = await state.get_data()
    amount = data.get("topup_amount")
    currency = config.get("currency", "تومان")


    # If amount was missing from state, try extracting from text/caption
    if not amount:
        content_text = message.text or message.caption or ""
        parsed = parse_persian_number(content_text)
        if parsed and parsed >= 10000:
            amount = parsed
        else:
            await message.answer(
                f"⚠️ *مبلغ واریزی مشخص نیست!*\n\n"
                f"لطفاً ابتدا مبلغ افزایش موجودی را تعیین فرمایید:",
                parse_mode="Markdown",
                reply_markup=wallet_topup_keyboard()
            )
            await state.clear()
            return

    # Check for photo or document
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        photo_file_id = message.document.file_id

    receipt_note = message.caption or message.text or ""
    if photo_file_id:
        full_note = f"[تصویر فیش] {receipt_note}".strip()
    else:
        full_note = receipt_note.strip()
        if len(full_note) < 3:
            await message.answer(
                "⚠️ لطفاً تصویر فیش واریزی یا شماره پیگیری معتبر ارسال فرمایید.",
                reply_markup=cancel_keyboard()
            )
            return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)

        payment = Payment(
            user_id=user.id,
            amount=amount,
            method="card",
            reference_id=str(message.message_id),
            receipt_note=full_note,
            status="pending"
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)

        # Acknowledge to customer
        await message.answer(
            f"✅ *اطلاعات فیش واریزی با موفقیت ثبت شد.*\n\n"
            f"🧾 شناسه پیگیری فیش: `#{payment.id}`\n"
            f"💰 مبلغ واریزی: *{payment.amount:,} {currency}*\n"
            f"⏳ وضعیت: *در انتظار بررسی و تایید مدیریت*\n\n"
            f"💡 به محض تایید توسط مدیریت، کیف پول شما به صورت آنی شارژ شده و پیام تایید برای شما ارسال خواهد شد.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

        # Notify Telegram Admin(s) with inline review keyboard!
        admin_ids = get_admin_telegram_ids()
        admin_text = (
            f"🔔 *درخواست جدید افزایش موجودی (کارت‌به‌کارت)*\n\n"
            f"🧾 شناسه پرداخت: `#{payment.id}`\n"
            f"👤 کاربر: *{user.first_name or ''} {user.last_name or ''}*\n"
            f"🏷️ نام کاربری: @{user.username or 'ندارد'}\n"
            f"🆔 شناسه عددی: `{user.telegram_id}`\n"
            f"💰 مبلغ درخواستی: *{payment.amount:,} {currency}*\n"
            f"📝 متن/پیگیری: {receipt_note or 'فیش تصویری بدون متن'}\n"
            f"📅 تاریخ: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        review_kb = admin_payment_review_keyboard(payment.id, payment.amount)

        for adm_id in admin_ids:
            try:
                if photo_file_id:
                    await message.bot.send_photo(
                        chat_id=adm_id,
                        photo=photo_file_id,
                        caption=admin_text,
                        parse_mode="Markdown",
                        reply_markup=review_kb
                    )
                else:
                    await message.bot.send_message(
                        chat_id=adm_id,
                        text=admin_text,
                        parse_mode="Markdown",
                        reply_markup=review_kb
                    )
            except Exception as e:
                logger.error(f"Failed to forward payment #{payment.id} to admin {adm_id}: {e}")

    await state.clear()

# --- Admin Payment Inline Review Handlers ---
@router.callback_query(F.data.startswith("adm_pay_app_") | F.data.startswith("adm_pay_rej_"))
async def handle_admin_payment_action(callback: CallbackQuery):
    admin_ids = get_admin_telegram_ids()
    if admin_ids and callback.from_user.id not in admin_ids:
        await callback.answer("⛔ شما به عنوان ادمین مجاز در سیستم ثبت نشده‌اید.", show_alert=True)
        return

    is_approve = callback.data.startswith("adm_pay_app_")
    prefix = "adm_pay_app_" if is_approve else "adm_pay_rej_"
    try:
        payment_id = int(callback.data.replace(prefix, ""))
    except ValueError:
        await callback.answer("شناسه پرداخت نامعتبر است", show_alert=True)
        return

    currency = config.get("currency", "تومان")
    admin_tag = f"@{callback.from_user.username}" if callback.from_user.username else (callback.from_user.first_name or str(callback.from_user.id))

    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = res.scalar_one_or_none()

        if not payment:
            await callback.answer("پرداخت یافت نشد", show_alert=True)
            return

        if payment.status != "pending":
            await callback.answer(f"این پرداخت قبلاً پردازش شده است ({payment.status})", show_alert=True)
            status_tag = f"\n\n⚠️ *این فیش قبلاً تعیین وضعیت شده است: {payment.status}*"
            try:
                if callback.message.caption:
                    await callback.message.edit_caption(caption=f"{callback.message.caption}{status_tag}", reply_markup=None)
                else:
                    await callback.message.edit_text(text=f"{callback.message.text}{status_tag}", reply_markup=None)
            except Exception:
                pass
            return

        res_u = await session.execute(select(User).where(User.id == payment.user_id))
        user = res_u.scalar_one_or_none()

        if is_approve:
            payment.status = "approved"
            payment.reviewed_at = datetime.utcnow()
            payment.admin_note = f"Approved in Telegram by {admin_tag}"
            ok, new_bal, msg = await wallet_service.add_funds(
                session=session,
                user_id=payment.user_id,
                amount=payment.amount,
                tx_type="topup",
                description=f"Telegram approved payment #{payment.id}"
            )
            await session.commit()

            status_text = f"\n\n✅ *تایید شد:* مبلغ *{payment.amount:,} {currency}* توسط {admin_tag} تایید و به کیف پول کاربر اضافه گردید."
            try:
                if callback.message.caption:
                    await callback.message.edit_caption(caption=f"{callback.message.caption}{status_text}", parse_mode="Markdown", reply_markup=None)
                else:
                    await callback.message.edit_text(text=f"{callback.message.text}{status_text}", parse_mode="Markdown", reply_markup=None)
            except Exception:
                pass

            await callback.answer(f"✅ فیش تایید شد و {payment.amount:,} {currency} شارژ شد.", show_alert=True)

            # Send instant notification to customer!
            if user and user.telegram_id:
                user_msg = (
                    f"🎉 *کیف پول شما با موفقیت شارژ شد!*\n\n"
                    f"✅ شناسه پرداخت: `#{payment.id}`\n"
                    f"💰 مبلغ افزوده شده: *{payment.amount:,} {currency}*\n"
                    f"💵 موجودی فعلی کیف پول: *{new_bal:,} {currency}*\n\n"
                    f"هم‌اکنون می‌توانید از طریق منوی اصلی اقدام به خرید یا تمدید اشتراک نمایید. 👇"
                )
                await send_telegram_notification(user.telegram_id, user_msg)

        else: # Reject
            payment.status = "rejected"
            payment.reviewed_at = datetime.utcnow()
            payment.admin_note = f"Rejected in Telegram by {admin_tag}"
            await session.commit()

            status_text = f"\n\n❌ *رد شد:* این فیش توسط {admin_tag} رد شد."
            try:
                if callback.message.caption:
                    await callback.message.edit_caption(caption=f"{callback.message.caption}{status_text}", parse_mode="Markdown", reply_markup=None)
                else:
                    await callback.message.edit_text(text=f"{callback.message.text}{status_text}", parse_mode="Markdown", reply_markup=None)
            except Exception:
                pass

            await callback.answer("❌ فیش واریزی رد گردید.", show_alert=True)

            # Send rejection notification to customer!
            if user and user.telegram_id:
                user_msg = (
                    f"❌ *عدم تایید فیش واریزی*\n\n"
                    f"کاربر گرامی، فیش واریزی شما با شناسه `#{payment.id}` به مبلغ *{payment.amount:,} {currency}* توسط مدیریت تایید نشد.\n\n"
                    f"در صورت نیاز به بررسی یا بروز مشکل، لطفاً با پشتیبانی در ارتباط باشید."
                )
                await send_telegram_notification(user.telegram_id, user_msg)


# --- 6. Gift Code ---
@router.message(F.text.contains("کد هدیه") | F.text.contains("Gift Code") | Command("gift"))
async def handle_gift_code_prompt(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎟️ لطفاً کد هدیه دریافتی خود را ارسال فرمایید:", reply_markup=cancel_keyboard())
    await state.set_state(FormStates.waiting_for_gift_code)

@router.message(FormStates.waiting_for_gift_code)
async def process_gift_code(message: Message, state: FSMContext):
    if message.text and is_navigation_or_cancel(message.text):
        await handle_navigation_fallback(message, state)
        return

    code_str = (message.text or "").strip().upper()

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        res = await session.execute(select(GiftCode).where(GiftCode.code == code_str, GiftCode.is_active == 1))
        gift = res.scalar_one_or_none()

        if not gift:
            await message.answer("❌ کد هدیه وارد شده نامعتبر، اشتباه یا غیرفعال است.", reply_markup=main_menu_keyboard())
            await state.clear()
            return

        # Check if expired
        if gift.expire_at and datetime.utcnow() > gift.expire_at:
            await message.answer("❌ مهلت استفاده از این کد هدیه به پایان رسیده است.", reply_markup=main_menu_keyboard())
            await state.clear()
            return

        # Check redemption limits
        if gift.redeemed_count >= gift.max_redemptions:
            await message.answer("❌ ظرفیت استفاده از این کد هدیه تکمیل شده است.", reply_markup=main_menu_keyboard())
            await state.clear()
            return

        # Check duplicate redemption by same user
        dup = await session.execute(
            select(GiftRedemption).where(GiftRedemption.gift_id == gift.id, GiftRedemption.user_id == user.id)
        )
        if dup.scalar_one_or_none():
            await message.answer("⚠️ شما پیش از این از این کد هدیه استفاده کرده‌اید.", reply_markup=main_menu_keyboard())
            await state.clear()
            return

        # Credit user wallet atomically
        currency = config.get("currency", "تومان")
        await wallet_service.add_funds(
            session=session,
            user_id=user.id,
            amount=gift.amount,
            tx_type="topup",
            description=f"Redeemed gift code {gift.code}"
        )

        gift.redeemed_count += 1
        redemption = GiftRedemption(
            gift_id=gift.id,
            user_id=user.id,
            amount=gift.amount
        )
        session.add(redemption)
        await session.commit()

        await message.answer(
            f"🎉 تبریک! مبلغ *{gift.amount:,} {currency}* به موجودی کیف پول شما افزوده شد.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    await state.clear()

# --- 7. Support ---
@router.message(F.text.contains("پشتیبانی") | F.text.contains("Support") | Command("support"))
async def handle_support(message: Message, state: FSMContext):
    await state.clear()
    sup_username = config.get("bot_support_username", "@support_vpn")
    text = f"💬 *پشتیبانی فنی و فروش*\n\n"
    text += f"جهت پاسخگویی به هرگونه سوال، راهنمایی نصب یا گزارش قطعی، با آیدی پشتیبانی در ارتباط باشید:\n\n"
    text += f"👉 *{sup_username}*"
    await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "cancel_action")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("عملیات لغو شد.")
    await callback.answer()
