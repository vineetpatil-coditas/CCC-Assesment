from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from database import Base
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy Models
class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Association table for order-product relationship
order_products = Table(
    'order_products', Base.metadata,
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('product_id', Integer, ForeignKey('products.id'))
)

class ProductModel(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    price = Column(Float)
    description = Column(String(500))

class OrderModel(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    created_at = Column(DateTime, default=datetime.now)
    products = relationship("ProductModel", secondary=order_products)

# Pydantic Models (Schemas)
class ProductSchema(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=500)

    class Config:
        from_attributes = True

class OrderSchema(BaseModel):
    id: Optional[int] = None
    products: List[int] = Field(..., min_items=1)
    total_amount: float = Field(..., gt=0)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True
