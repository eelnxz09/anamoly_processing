"""
Database Models for Transaction and Analysis Storage
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()


class Transaction(Base):
    """Transaction records"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # Optional fields
    merchant_category = Column(String(100))
    location = Column(String(200))
    device_type = Column(String(50))
    
    # Metadata
    source = Column(String(50))  # 'csv', 'google_sheets', 'api'
    ingestion_time = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis_results = relationship("AnalysisResult", back_populates="transaction")
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_amount_timestamp', 'amount', 'timestamp'),
    )


class AnalysisResult(Base):
    """ML analysis results for each transaction"""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), ForeignKey('transactions.transaction_id'), nullable=False)
    
    # Analysis results
    is_anomaly = Column(Boolean)
    risk_score = Column(Float)  # 0-100
    risk_level = Column(String(20))  # Low, Medium, High, Critical
    confidence = Column(Float)  # 0-100
    anomaly_score = Column(Float)  # Raw model score
    
    # Model info
    model_type = Column(String(50))
    model_version = Column(String(20))
    analysis_time = Column(DateTime, default=datetime.utcnow)
    
    # Explanation
    explanation_json = Column(Text)  # JSON string with detailed explanation
    
    # Relationship
    transaction = relationship("Transaction", back_populates="analysis_results")
    
    __table_args__ = (
        Index('idx_risk_score', 'risk_score'),
        Index('idx_analysis_time', 'analysis_time'),
    )


class ModelVersion(Base):
    """Track ML model versions and training history"""
    __tablename__ = 'model_versions'
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), unique=True, nullable=False)
    model_type = Column(String(50), nullable=False)
    
    # Training info
    training_date = Column(DateTime, default=datetime.utcnow)
    training_samples = Column(Integer)
    contamination = Column(Float)
    
    # Performance metrics
    metrics_json = Column(Text)  # JSON with performance metrics
    
    # Model file location
    model_path = Column(String(500))
    
    is_active = Column(Boolean, default=False)


class DataSource(Base):
    """Track data sources (CSV uploads, Google Sheets, etc.)"""
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False)  # 'csv', 'google_sheets'
    source_identifier = Column(String(500))  # filename or sheet URL
    
    # Stats
    upload_time = Column(DateTime, default=datetime.utcnow)
    record_count = Column(Integer)
    status = Column(String(20))  # 'processed', 'failed', 'processing'
    
    # Metadata
    metadata_json = Column(Text)
    error_message = Column(Text)


class User(Base):
    """User behavior profiles"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Behavioral statistics
    total_transactions = Column(Integer, default=0)
    avg_transaction_amount = Column(Float)
    std_transaction_amount = Column(Float)
    first_transaction = Column(DateTime)
    last_transaction = Column(DateTime)
    
    # Risk profile
    anomaly_count = Column(Integer, default=0)
    risk_level = Column(String(20))  # Low, Medium, High
    
    # Updated
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
