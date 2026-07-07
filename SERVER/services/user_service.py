from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from SERVER.models.user import User, UserRole
from SERVER.models.shop import Shop
from SERVER.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _hash_password(self, password: str) -> str:

        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:

        return self._hash_password(password) == password_hash

    async def create(self, data: UserCreate) -> User:

        user = User(
            email=data.email,
            password_hash=self._hash_password(data.password),
            name=data.name,
            phone=data.phone,
            role=data.role,
            shop_id=data.shop_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:

        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def authenticate(self, email: str, password: str) -> Optional[User]:

        user = await self.get_by_email(email)
        if not user:
            return None
        if not self._verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None


        user.last_login = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_all(
        self,
        role: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:

        query = select(User)
        if role:
            query = query.where(User.role == role)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, user_id: int, data: UserUpdate) -> Optional[User]:

        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int) -> bool:

        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True

    async def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:

        user = await self.get_by_id(user_id)
        if not user:
            return False

        if not self._verify_password(old_password, user.password_hash):
            return False

        user.password_hash = self._hash_password(new_password)
        await self.db.commit()
        return True

    async def generate_reset_token(self, email: str) -> Optional[str]:

        user = await self.get_by_email(email)
        if not user:
            return None


        token = secrets.token_urlsafe(32)


        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        await self.db.commit()
        await self.db.refresh(user)

        return token

    async def verify_reset_token(self, token: str) -> Optional[User]:

        result = await self.db.execute(
            select(User).where(User.reset_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None


        if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
            return None

        return user

    async def reset_password(self, token: str, new_password: str) -> bool:

        user = await self.verify_reset_token(token)
        if not user:
            return False


        user.password_hash = self._hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None

        await self.db.commit()
        return True

    async def get_shop_owners(self) -> List[User]:

        return await self.get_all(role=UserRole.ADMIN.value)

    async def get_customers(self) -> List[User]:

        return await self.get_all(role=UserRole.CUSTOMER.value)

    async def get_platform_stats(self) -> dict:


        total_users = await self.db.execute(select(func.count(User.id)))

        shop_owners = await self.db.execute(
            select(func.count(User.id)).where(User.role == UserRole.ADMIN.value)
        )

        customers = await self.db.execute(
            select(func.count(User.id)).where(User.role == UserRole.CUSTOMER.value)
        )


        active_shops = await self.db.execute(
            select(func.count(Shop.id)).where(Shop.is_active == True)
        )

        verified_shops = await self.db.execute(
            select(func.count(Shop.id)).where(Shop.is_verified == True)
        )


        total_revenue = await self.db.execute(
            select(func.sum(Shop.total_revenue))
        )

        return {
            "total_users": total_users.scalar() or 0,
            "total_shop_owners": shop_owners.scalar() or 0,
            "total_customers": customers.scalar() or 0,
            "total_shops": active_shops.scalar() or 0,
            "verified_shops": verified_shops.scalar() or 0,
            "platform_revenue": total_revenue.scalar() or 0,
        }


async def create_default_users(db: AsyncSession):

    service = UserService(db)


    existing = await service.get_by_email("superadmin@kommandai.com")
    if not existing:

        await service.create(UserCreate(
            email="superadmin@kommandai.com",
            password="qwert12345",
            name="Super Admin",
            role=UserRole.SUPER_ADMIN.value
        ))
        print("Created Super Admin: superadmin@kommandai.com / qwert12345")


    existing = await service.get_by_email("admin@kommandai.com")
    if not existing:

        result = await db.execute(select(Shop).where(Shop.name == "Glamour Beauty Store"))
        shop = result.scalar_one_or_none()
        shop_id = shop.id if shop else None

        await service.create(UserCreate(
            email="admin@kommandai.com",
            password="qwert12345",
            name="Admin",
            role=UserRole.ADMIN.value,
            shop_id=shop_id
        ))
        print("Created Admin (Shop Owner): admin@kommandai.com / qwert12345")


    existing = await service.get_by_email("customer@kommandai.com")
    if not existing:
        await service.create(UserCreate(
            email="customer@kommandai.com",
            password="qwert12345",
            name="Customer",
            role=UserRole.CUSTOMER.value
        ))
        print("Created Customer: customer@kommandai.com / qwert12345")
