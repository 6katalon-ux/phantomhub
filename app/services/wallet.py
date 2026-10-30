"""
Atomic Wallet Management Service.
Guarantees transaction integrity, prevents double-spending, and handles refunds and manual adjustments.
"""

from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.models import User, Transaction
from app.core.logging import logger

class WalletService:
    @staticmethod
    async def get_balance(session: AsyncSession, user_id: int) -> int:
        res = await session.execute(select(User.wallet_balance).where(User.id == user_id))
        val = res.scalar()
        return val if val is not None else 0

    @staticmethod
    async def add_funds(
        session: AsyncSession,
        user_id: int,
        amount: int,
        tx_type: str = "topup",
        description: str = ""
    ) -> Tuple[bool, int, str]:
        """Atomically credit user wallet balance and create audit transaction"""
        if amount <= 0:
            return False, 0, "Amount must be strictly positive"

        # Lock user row for update
        stmt = (
            select(User)
            .where(User.id == user_id)
            .with_for_update()
        )
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return False, 0, "User not found"

        user.wallet_balance += amount
        new_balance = user.wallet_balance

        tx = Transaction(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            type=tx_type,
            description=description
        )
        session.add(tx)
        await session.flush()
        return True, new_balance, "Funds added successfully"

    @staticmethod
    async def deduct_funds(
        session: AsyncSession,
        user_id: int,
        amount: int,
        description: str = ""
    ) -> Tuple[bool, int, str]:
        """Atomically deduct funds if user has sufficient balance"""
        if amount <= 0:
            return False, 0, "Amount must be strictly positive"

        stmt = (
            select(User)
            .where(User.id == user_id)
            .with_for_update()
        )
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return False, 0, "User not found"

        if user.wallet_balance < amount:
            return False, user.wallet_balance, "Insufficient wallet balance"

        user.wallet_balance -= amount
        new_balance = user.wallet_balance

        tx = Transaction(
            user_id=user_id,
            amount=-amount,
            balance_after=new_balance,
            type="purchase",
            description=description
        )
        session.add(tx)
        await session.flush()
        return True, new_balance, "Deduction successful"

    @staticmethod
    async def refund_funds(
        session: AsyncSession,
        user_id: int,
        amount: int,
        reason: str = "Automatic refund due to provisioning failure"
    ) -> Tuple[bool, int, str]:
        """Refund funds to user in case 3X-UI creation fails"""
        return await WalletService.add_funds(
            session=session,
            user_id=user_id,
            amount=amount,
            tx_type="refund",
            description=reason
        )

wallet_service = WalletService()
