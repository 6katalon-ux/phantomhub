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

from app.models.models import User, Plan, Service, Payment, GiftCode, GiftRedemption
from app.core.database import AsyncSessionLocal
from app.core.config import config
from app.services.vpn_provisioner import vpn_provisioner
from app.services.wallet import wallet_service
from app.bot.keyboards import (
    main_menu_keyboard, plans_keyboard, plan_confirm_keyboard,
    service_actions_keyboard, cancel_keyboard
)
from app.core.logging import logger

router = Router()

class FormStates(StatesGroup):
    waiting_for_payment_receipt = State()
    waiting_for_gift_code = State()

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
        # Keep username fresh
        if msg.from_user.username and user.username != msg.from_user.username:
            user.username = msg.from_user.username
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
@router.message(F.text.contains("خرید اشتراک") | F.text.contains("Buy VPN"))
async def handle_buy_menu(message: Message):
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
        text = f"🛍️ *لیست پلن‌های اشتراک VPN*\n\n"
        text += f"💰 موجودی فعلی کیف پول شما: *{user.wallet_balance:,} {currency}*\n\n"
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

        text = f"📦 *جزئیات پلن انتخابی:*\n\n"
        text += f"🔹 نام: *{plan.name}*\n"
        text += f"🔹 حجم: *{plan.traffic_gb} گیگابایت*\n"
        text += f"🔹 مدت اعتبار: *{plan.duration_days} روز*\n"
        text += f"🔹 قیمت: *{plan.price:,} {currency}*\n"
        text += f"🔹 حداکثر کاربر: *{plan.max_ips} کاربر همزمان*\n\n"
        text += f"💰 موجودی کیف پول شما: *{user.wallet_balance:,} {currency}*\n"

        if user.wallet_balance < plan.price:
            shortage = plan.price - user.wallet_balance
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
@router.message(F.text.contains("تست رایگان") | F.text.contains("Free Trial"))
async def handle_free_trial(message: Message):
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
@router.message(F.text.contains("حساب کاربری") | F.text.contains("My Account"))
async def handle_my_account(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        res = await session.execute(select(Service).where(Service.user_id == user.id))
        services = res.scalars().all()
        currency = config.get("currency", "تومان")

        reg_date = user.created_at.strftime("%Y-%m-%d") if user.created_at else "نامشخص"
        active_count = sum(1 for s in services if s.is_active)

        text = f"👤 *مشخصات حساب کاربری شما:*\n\n"
        text += f"🆔 شناسه کاربری عددی: `{user.telegram_id}`\n"
        text += f"👤 نام: *{user.first_name or ''} {user.last_name or ''}*\n"
        text += f"🏷️ نام کاربری: @{user.username or 'ندارد'}\n"
        text += f"💰 موجودی کیف پول: *{user.wallet_balance:,} {currency}*\n"
        text += f"📡 تعداد سرویس‌های فعال: *{active_count} عدد*\n"
        text += f"🎁 وضعیت تست رایگان: *{'دریافت شده' if user.trial_used else 'قابل دریافت'}*\n"
        text += f"📅 تاریخ عضویت: `{reg_date}`\n"

        await message.answer(text, parse_mode="Markdown")

# --- 4. My Services ---
@router.message(F.text.contains("سرویس‌های من") | F.text.contains("My Services"))
async def handle_my_services(message: Message):
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
@router.message(F.text.contains("کارت به کارت") | F.text.contains("افزایش موجودی") | F.text.contains("Payment") | F.text.contains("Wallet"))
async def handle_payment_menu(message: Message, state: FSMContext):
    card_number = config.get("card_number", "6037-9975-0000-0000")
    card_holder = config.get("card_holder", "صاحب کارت")
    crypto_wallet = config.get("crypto_wallet", "")
    instructions = config.get("payment_instructions", "لطفاً مبلغ مورد نظر را واریز کرده و مشخصات واریزی را ارسال کنید.")
    currency = config.get("currency", "تومان")

    text = f"💳 *راهنمای افزایش موجودی و پرداخت*\n\n"
    text += f"💳 شماره کارت بانکی:\n`{card_number}`\n"
    text += f"👤 به نام: *{card_holder}*\n\n"
    if crypto_wallet:
        text += f"🪙 آدرس ولت تتر یا رمزارز:\n`{crypto_wallet}`\n\n"
    text += f"📝 *توضیحات:*\n{instructions}\n\n"
    text += f"⚠️ *مرحله بعد:* لطفاً مبلغ واریزی (به {currency}) و شماره پیگیری یا عکس فیش را همینجا ارسال فرمایید."

    await message.answer(text, parse_mode="Markdown", reply_markup=cancel_keyboard())
    await state.set_state(FormStates.waiting_for_payment_receipt)

@router.message(FormStates.waiting_for_payment_receipt)
async def process_payment_receipt(message: Message, state: FSMContext):
    content = message.text or message.caption or "فیش ارسالی تصویری"
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        
        # Extract numbers if present, otherwise default to 0
        import re
        nums = re.findall(r'\d+', content.replace(',', ''))
        amount = int(nums[0]) if nums else 100000

        payment = Payment(
            user_id=user.id,
            amount=amount,
            method="card",
            reference_id=str(message.message_id),
            receipt_note=content,
            status="pending"
        )
        session.add(payment)
        await session.commit()

        currency = config.get("currency", "تومان")
        await message.answer(
            f"✅ *اطلاعات پرداخت شما ثبت گردید.*\n"
            f"شناسه پیگیری فیش: `{payment.id}`\n\n"
            f"همکاران ما در پنل مدیریت صحت واریزی را بررسی کرده و به زودی کیف پول شما را شارژ خواهند نمود.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    await state.clear()

# --- 6. Gift Code ---
@router.message(F.text.contains("کد هدیه") | F.text.contains("Gift Code"))
async def handle_gift_code_prompt(message: Message, state: FSMContext):
    await message.answer("🎟️ لطفاً کد هدیه دریافتی خود را ارسال فرمایید:", reply_markup=cancel_keyboard())
    await state.set_state(FormStates.waiting_for_gift_code)

@router.message(FormStates.waiting_for_gift_code)
async def process_gift_code(message: Message, state: FSMContext):
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
@router.message(F.text.contains("پشتیبانی") | F.text.contains("Support"))
async def handle_support(message: Message):
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
