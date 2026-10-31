"""
Aiogram 3 Keyboards for Telegram Bot.
Includes Main Menu, Plan selection list, Account view, Payment options, and Service actions.
"""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from typing import List
from app.models.models import Plan, Service

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent 8-button responsive main menu keyboard"""
    kb = [
        [
            KeyboardButton(text="🛍️ خرید اشتراک (Buy VPN)"),
            KeyboardButton(text="🎁 تست رایگان (Free Trial)")
        ],
        [
            KeyboardButton(text="👤 حساب کاربری (My Account)"),
            KeyboardButton(text="📡 سرویس‌های من (My Services)")
        ],
        [
            KeyboardButton(text="💰 افزایش موجودی (Wallet)"),
            KeyboardButton(text="💳 کارت به کارت (Payment)")
        ],
        [
            KeyboardButton(text="🎟️ کد هدیه (Gift Code)"),
            KeyboardButton(text="💬 پشتیبانی (Support)")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def plans_keyboard(plans: List[Plan]) -> InlineKeyboardMarkup:
    """List available VPN plans as inline buttons"""
    buttons = []
    for p in plans:
        btn_text = f"{p.name} | {p.traffic_gb}GB | {p.price:,} تومان"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"buy_plan_{p.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plan_confirm_keyboard(plan_id: int) -> InlineKeyboardMarkup:
    """Confirm plan purchase with wallet balance deduction"""
    kb = [
        [
            InlineKeyboardButton(text="✅ تایید و خرید آنی", callback_data=f"confirm_buy_{plan_id}"),
            InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_buy")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def service_actions_keyboard(service_id: int) -> InlineKeyboardMarkup:
    """Actions for a specific user service"""
    kb = [
        [
            InlineKeyboardButton(text="📋 کپی کانفیگ", callback_data=f"copy_cfg_{service_id}"),
            InlineKeyboardButton(text="🔄 دریافت لینک ساب", callback_data=f"get_sub_{service_id}")
        ],
        [
            InlineKeyboardButton(text="📊 استعلام حجم باقیمانده", callback_data=f"check_traffic_{service_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cancel_keyboard() -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text="❌ لغو و بازگشت", callback_data="cancel_action")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def wallet_topup_keyboard() -> InlineKeyboardMarkup:
    """Quick amount selection keyboard for wallet deposit"""
    kb = [
        [
            InlineKeyboardButton(text="۵۰,۰۰۰ تومان", callback_data="topup_amt_50000"),
            InlineKeyboardButton(text="۱۰۰,۰۰۰ تومان", callback_data="topup_amt_100000")
        ],
        [
            InlineKeyboardButton(text="۲۰۰,۰۰۰ تومان", callback_data="topup_amt_200000"),
            InlineKeyboardButton(text="۵۰۰,۰۰۰ تومان", callback_data="topup_amt_500000")
        ],
        [
            InlineKeyboardButton(text="✏️ مبلغ دلخواه", callback_data="topup_amt_custom")
        ],
        [
            InlineKeyboardButton(text="❌ لغو و بازگشت", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_payment_review_keyboard(payment_id: int, amount: int) -> InlineKeyboardMarkup:
    """Inline keyboard sent to admin Telegram to approve/reject payment receipts"""
    kb = [
        [
            InlineKeyboardButton(text=f"✅ تایید و شارژ ({amount:,} تومان)", callback_data=f"adm_pay_app_{payment_id}")
        ],
        [
            InlineKeyboardButton(text="❌ رد فیش واریزی", callback_data=f"adm_pay_rej_{payment_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

