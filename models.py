from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    phone = Column(String, unique=True, index=True)
    notes = Column(String, default="")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    
    # إضافة ميزة الحذف التلقائي (Cascade)
    products = relationship("Product", back_populates="department", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    name = Column(String, index=True)
    price = Column(Float)
    description = Column(String)
    
    # إضافات جديدة مهمة للسوبر ماركت
    stock_quantity = Column(Integer, default=0)  # كمية المخزون
    is_active = Column(Boolean, default=True)    # حالة المنتج (متوفر/مخفي)
    
    department = relationship("Department", back_populates="products")
