from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.db import Base


# =========================
# PRODUCTS
# =========================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False, unique=True)
    sku = Column(String, unique=True, nullable=True)

    unit = Column(String, nullable=False)
    is_loose = Column(Boolean, default=False)

    cost_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    mrp = Column(Float, nullable=True)

    quantity = Column(Float, default=0)
    reorder_level = Column(Float, default=0)

    hsn_code = Column(String, nullable=True)
    gst_rate = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    bill_items = relationship("BillItem", back_populates="product")


# =========================
# CUSTOMERS
# =========================
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    khata_transactions = relationship(
        "KhataTransaction",
        back_populates="customer"
    )


# =========================
# KHATA TRANSACTIONS
# =========================
class KhataTransaction(Base):
    __tablename__ = "khata_transactions"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    transaction_type = Column(
        String,
        nullable=False
    )

    amount = Column(Float, nullable=False)

    reference = Column(String, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    customer = relationship(
        "Customer",
        back_populates="khata_transactions"
    )


# =========================
# BILLS
# =========================
class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)

    bill_number = Column(
        String,
        unique=True,
        nullable=False
    )

    status = Column(
        String,
        default="DRAFT"
    )

    subtotal = Column(Float, default=0)
    cgst = Column(Float, default=0)
    sgst = Column(Float, default=0)
    total = Column(Float, default=0)

    payment_mode = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    items = relationship(
        "BillItem",
        back_populates="bill",
        cascade="all, delete-orphan"
    )


# =========================
# BILL ITEMS
# =========================
class BillItem(Base):
    __tablename__ = "bill_items"

    id = Column(Integer, primary_key=True, index=True)

    bill_id = Column(
        Integer,
        ForeignKey("bills.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity = Column(Float, nullable=False)

    unit_price = Column(
        Float,
        nullable=False
    )

    gst_rate = Column(
        Float,
        default=0
    )

    taxable_amount = Column(
        Float,
        default=0
    )

    cgst = Column(
        Float,
        default=0
    )

    sgst = Column(
        Float,
        default=0
    )

    total = Column(
        Float,
        default=0
    )

    bill = relationship(
        "Bill",
        back_populates="items"
    )

    product = relationship(
        "Product",
        back_populates="bill_items"
    )


# =========================
# OWNER PREFERENCES
# =========================
class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)

    key = Column(
        String,
        unique=True,
        nullable=False
    )

    value = Column(Text, nullable=False)


# =========================
# PROCESSED UPDATES (idempotency)
# =========================
#
# Every inbound Telegram update (or any other channel's message id)
# is recorded here before it is handed to the agent. If the same
# update is ever delivered twice -- Telegram retries a webhook,
# polling re-delivers after a restart, a network blip causes a
# duplicate -- we detect it here and skip re-running the agent, so a
# customer can never be double-billed or double-credited because a
# message was received twice.
class ProcessedUpdate(Base):
    __tablename__ = "processed_updates"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(String, nullable=False)  # e.g. "telegram"
    update_id = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source", "update_id", name="uq_source_update"),
    )


# =========================
# STOCK MOVEMENTS (audit trail)
# =========================
#
# Every change to Product.quantity (receiving stock, a finalized
# sale deducting stock, a manual correction) is appended here. This
# gives an auditable ledger of "how did we get to this stock level"
# and is also what the reorder-suggestion feature uses to compute
# sales velocity independent of the bills table.
class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    change = Column(Float, nullable=False)  # positive=in, negative=out
    reason = Column(String, nullable=False)  # RECEIVE, SALE, ADJUSTMENT
    reference = Column(String, nullable=True)  # e.g. bill number

    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")