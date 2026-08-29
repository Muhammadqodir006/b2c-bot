from sqlalchemy.ext.asyncio import AsyncSession
from random import choice
from string import ascii_letters, digits
from database.models import Referral, ReferralCode, User
from database.engine import async_session
from sqlalchemy import select


async def generate_referral_code() -> str:
    """Generate a unique referral code."""
    characters = ascii_letters + digits
    code_length = 8

    async with async_session() as session:
        while True:
            # Generate a random code
            code = ''.join(choice(characters) for _ in range(code_length))

            # Check if the code already exists in the database
            select_stmt = select(ReferralCode).where(ReferralCode.code == code)
            existing_code = await session.execute(select_stmt)
            
            if not existing_code.scalar():
                return code

async def create_referral_code(user_id: int) -> ReferralCode:
    """Create a referral code for a user."""
    code = await generate_referral_code()
    new_referral_code = ReferralCode(user_id=user_id, code=code)

    async with async_session() as session:
        session.add(new_referral_code)
        await session.commit()
        await session.refresh(new_referral_code)

    return new_referral_code

async def create_referral_code_for_user(user_id: int) -> ReferralCode:
    """Create a referral code for a user if they don't already have one."""
    async with async_session() as session:
        select_stmt = select(ReferralCode).where(
            ReferralCode.user_id == user_id
        )
        result = await session.execute(select_stmt)
        existing_code = result.scalar_one_or_none()

        if existing_code:
            return existing_code

    return await create_referral_code(user_id)

async def create_referral(
    referrer_id: int,
    referred_id: int
) -> Referral:
    """Create a referral relationship between two users."""

    async with async_session() as session:
        referral = Referral(
            referrer_id=referrer_id,
            referred_id=referred_id
        )

        session.add(referral)
        await session.commit()
        await session.refresh(referral)

        return referral

async def get_user_by_referral_code(code: str) -> User | None:
    """Find a user by their referral code."""

    async with async_session() as session:
        result = await session.execute(
            select(ReferralCode)
            .where(ReferralCode.code == code)
        )

        referral_code = result.scalar_one_or_none()

        if referral_code is None:
            return None

        result = await session.execute(
            select(User)
            .where(User.id == referral_code.user_id)
        )

        return result.scalar_one_or_none()