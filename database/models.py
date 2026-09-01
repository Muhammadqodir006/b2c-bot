from datetime import datetime
from sqlalchemy import String, BigInteger, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, foreign
import enum


class Base(DeclarativeBase):
    pass


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"
    blocked = "blocked"

class ReferralStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="uz")
    trust_score: Mapped[int] = mapped_column(default=100)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    referrals: Mapped[list["Referral"]] = relationship(
        foreign_keys="Referral.referrer_id"
    )
    referral_code: Mapped["ReferralCode | None"] = relationship(
        back_populates="user",
        uselist=False
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user"
    )
    points: Mapped["UserPoints | None"] = relationship(
        back_populates="user",
        uselist=False
    )

    points_logs: Mapped[list["PointsLog"]] = relationship(
    back_populates="user"
)

    badges: Mapped[list["UserBadge"]] = relationship(
    back_populates="user"
)

class UserPoints(Base):
    __tablename__ = "user_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    total_points: Mapped[int] = mapped_column(default=0)
    current_streak: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="points")

class Salon(Base):
    __tablename__ = "salons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    rating: Mapped[float] = mapped_column(default=0.0)
    is_approved: Mapped[bool] = mapped_column(default=False)
    owner_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    services: Mapped[list["Service"]] = relationship(
        back_populates="salon"
    )
    masters: Mapped[list["Master"]] = relationship(
        back_populates="salon"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(150))
    price: Mapped[int] = mapped_column()
    duration_minutes: Mapped[int] = mapped_column()

    salon: Mapped["Salon"] = relationship(
        back_populates="services"
    )


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=True
    )
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(5), default="uz")

    salon: Mapped["Salon"] = relationship(
        back_populates="masters"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="master"
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    salon_id: Mapped[int] = mapped_column(
        ForeignKey("salons.id")
    )
    master_id: Mapped[int] = mapped_column(
        ForeignKey("masters.id")
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id"), nullable=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        default=BookingStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    user: Mapped["User"] = relationship(
        back_populates="bookings"
    )
    master: Mapped["Master"] = relationship(
        back_populates="bookings"
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id"), unique=True
    )
    rating: Mapped[int] = mapped_column()
    comment: Mapped[str] = mapped_column(
        String(500), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] =mapped_column(primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    referred_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    referrer: Mapped["User"] = relationship(foreign_keys=[referrer_id])
    referred: Mapped["User"] = relationship(foreign_keys=[referred_id])
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus), default=ReferralStatus.pending
    )
    reward_given: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id"), unique=True
)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    user: Mapped["User"] = relationship(back_populates="referral_code")

class PointsLog(Base):
    __tablename__ = "points_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String(50))
    points: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user: Mapped["User"] = relationship(
    back_populates="points_logs"
)

class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    condition_value: Mapped[int] = mapped_column()
    user_badges: Mapped[list["UserBadge"]] = relationship(
    back_populates="badge"
)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id"))
    earned_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user: Mapped["User"] = relationship(
        back_populates="badges"
    )

    badge: Mapped["Badge"] = relationship(
        back_populates="user_badges"    
    )