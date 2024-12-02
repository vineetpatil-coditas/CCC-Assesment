from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db, engine, Base
from models import ProductSchema, OrderSchema, OrderStatus
from services import ProductService, OrderService

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Order Management API",
    description="API for managing products and orders",
    version="1.0.0"
)

# Product Routes
@app.post("/api/v1/products", response_model=ProductSchema, tags=["Products"])
async def create_product(
    product_data: ProductSchema, 
    db: Session = Depends(get_db)
):
    """Create a new product in the system"""
    try:
        return ProductService.create(db, product_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products", response_model=List[ProductSchema], tags=["Products"])
async def get_all_products(db: Session = Depends(get_db)):
    """Retrieve all products from the system"""
    return ProductService.get_all(db)

@app.delete("/api/v1/products/{product_id}", tags=["Products"])
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Remove a product from the system by ID"""
    ProductService.remove_by_id(db, product_id)
    return {"message": "Product successfully removed"}

@app.get("/api/v1/products/{product_id}", response_model=ProductSchema, tags=["Products"])
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Retrieve a single product by ID"""
    product = ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Order Routes
@app.post("/api/v1/orders", response_model=OrderSchema, tags=["Orders"])
async def create_order(
    order_data: OrderSchema, 
    db: Session = Depends(get_db)
):
    """Create a new order in the system"""
    return OrderService.create(db, order_data)

@app.get("/api/v1/orders", response_model=List[OrderSchema], tags=["Orders"])
async def get_all_orders(db: Session = Depends(get_db)):
    """Retrieve all orders from the system"""
    return OrderService.get_all(db)

@app.put("/api/v1/orders/{order_id}/status/cancel", tags=["Orders"])
async def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """Cancel a pending order"""
    OrderService.update_status(db, order_id, OrderStatus.CANCELLED)
    return {"message": "Order successfully cancelled"}

@app.get("/api/v1/orders/{order_id}", response_model=OrderSchema, tags=["Orders"])
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Retrieve a single order by ID"""
    order = OrderService.get_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
