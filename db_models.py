from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String(64))
    nickname = Column(String(64), unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    predictions = relationship("Prediction", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    round_accesses = relationship("RoundAccess", back_populates="user")

class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    deadline = Column(DateTime, nullable=False)
    entry_fee = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    matches = relationship("Match", back_populates="round")
    payments = relationship("Payment", back_populates="round")
    round_accesses = relationship("RoundAccess", back_populates="round")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    home_team = Column(String(64), nullable=False)
    away_team = Column(String(64), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    round = relationship("Round", back_populates="matches")
    predictions = relationship("Prediction", back_populates="match")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    amount = Column(Integer, default=100)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    method = Column(String(32), default="card")
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    comment = Column(String(64))
    user = relationship("User", back_populates="payments")
    round = relationship("Round", back_populates="payments")

class RoundAccess(Base):
    __tablename__ = "round_access"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    has_access = Column(Boolean, default=False)
    granted_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="round_accesses")
    round = relationship("Round", back_populates="round_accesses")

class NewsItem(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    author = Column(String(64), default="Редакция")
    emoji = Column(String(8), default="⚽")
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    nickname = Column(String(64))
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)