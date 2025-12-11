from sqlalchemy import Column, String, Date, Integer, ForeignKey, CheckConstraint, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
import uuid
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    household_size = Column(Integer, default=1)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Numeric, nullable=False)
    category = relationship("Category", back_populates="products")
    # unit existe dans la base, mais pas forcément utilisé côté API → optionnel
    # si tu veux l'exposer, ajoute-le aussi dans tes schémas Pydantic
    expiration_date = Column(Date, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category_rel = relationship("Category", back_populates="products")

    prediction = Column(Integer, default=0)
    message = Column(String, default="✅ Produit sûr")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    owner = relationship("User")


class ConsumptionHistory(Base):
    __tablename__ = "consumption_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    action = Column(String, nullable=False)  # "consumed" ou "wasted"
    amount = Column(Numeric(12, 3), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("action IN ('consumed','wasted')", name="check_action_valid"),
    )


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stat_date = Column(Date, unique=True, nullable=False)
    total_products = Column(Integer, nullable=False)
    expired = Column(Integer, nullable=False)
    risky = Column(Integer, nullable=False)
    safe = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Relation inverse
    products = relationship("Product", back_populates="category_rel")


