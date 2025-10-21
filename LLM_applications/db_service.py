import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    plan = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)
    order_id = Column(String, unique=True)
    amount = Column(Integer)  # in paise
    currency = Column(String, default="INR")
    status = Column(String, default="created")  # created, paid, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_message(username, role, content):
    db = SessionLocal()
    try:
        db.add(Message(username=username, role=role, content=content))
        db.commit()
    finally:
        db.close()

def create_order(username, order_id, amount, currency):
    db = SessionLocal()
    try:
        db.add(Order(username=username, order_id=order_id, amount=amount, currency=currency, status="created"))
        db.commit()
    finally:
        db.close()

def mark_order_paid(order_id):
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.status = "paid"
            order.paid_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
