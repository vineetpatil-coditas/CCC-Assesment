from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from models import ProductModel, OrderModel, OrderStatus, ProductSchema, OrderSchema, Base
from fastapi import HTTPException
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class BaseService(ABC):
    @abstractmethod
    def create(self, db: Session, data: BaseModel) -> Base:
        pass
    @abstractmethod
    def get_by_id(self, db: Session, id: int) -> Optional[Base]:
        pass
    @abstractmethod
    def get_all(self, db: Session) -> List[Base]:
        pass

class ProductService(BaseService):
    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[ProductModel]:
        return db.query(ProductModel).filter(ProductModel.id == product_id).first()

    @staticmethod
    def create(db: Session, product_data: ProductSchema) -> ProductModel:
        if product_data.price <= 0:
            raise HTTPException(status_code=400, detail="Product price must be positive")
            
        new_product = ProductModel(**product_data.model_dump(exclude={'id'}))
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product

    @staticmethod
    def get_all(db: Session) -> List[ProductModel]:
        return db.query(ProductModel).all()

    @staticmethod
    def remove_by_id(db: Session, product_id: int) -> None:
        product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        db.delete(product)
        db.commit()

class OrderService(BaseService):
    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[OrderModel]:
        return db.query(OrderModel).filter(OrderModel.id == order_id).first()

    @staticmethod
    def create(db: Session, order_data: OrderSchema) -> OrderModel:
        logger.info(f"Creating new order with {len(order_data.products)} products")
        try:
            products = OrderService._validate_and_get_products(db, order_data.products)
            total_price = OrderService._calculate_total_price(products)
            
            OrderService._validate_order_total(total_price, order_data.total_amount)
            
            return OrderService._create_order(db, order_data, products)
        except HTTPException as e:
            logger.error(f"Failed to create order: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating order: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @staticmethod
    def _validate_and_get_products(db: Session, product_ids: List[int]) -> List[ProductModel]:
        products = []
        for product_id in product_ids:
            product = ProductService.get_by_id(db, product_id)
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
            products.append(product)
        return products
    
    @staticmethod
    def _calculate_total_price(products: List[ProductModel]) -> Decimal:
        return sum(Decimal(str(product.price)) for product in products)
    
    @staticmethod
    def _validate_order_total(calculated_total: Decimal, order_total: float) -> None:
        order_total_decimal = Decimal(str(order_total))
        if abs(calculated_total - order_total_decimal) > Decimal('0.01'):
            raise HTTPException(
                status_code=400,
                detail=f"Order total {order_total} does not match calculated total {calculated_total}"
            )
    
    @staticmethod
    def _create_order(db: Session, order_data: OrderSchema, products: List[ProductModel]) -> OrderModel:
        new_order = OrderModel(
            total_amount=order_data.total_amount,
            status=OrderStatus.PENDING,
            products=products
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        logger.info(f"Successfully created order {new_order.id}")
        return new_order

    @staticmethod
    def get_all(db: Session) -> List[OrderModel]:
        return db.query(OrderModel).all()

    @staticmethod
    def update_status(db: Session, order_id: int, new_status: OrderStatus) -> OrderModel:
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot update order in {order.status} status"
            )
        
        order.status = new_status
        db.commit()
        db.refresh(order)
        return order
