"""
Database models for NHS Paperwork Automation Agent
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nhs_number = Column(String(10), unique=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(DateTime)
    gender = Column(String(50))
    address = Column(Text)
    postcode = Column(String(10))
    phone_number = Column(String(20))
    next_of_kin = Column(String(200))
    next_of_kin_phone = Column(String(20))
    gp_name = Column(String(200))
    gp_practice = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notes = relationship("Note", back_populates="patient")
    forms = relationship("Form", back_populates="patient")


class Note(Base):
    __tablename__ = "notes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"))
    raw_text = Column(Text, nullable=False)
    note_type = Column(String(100), default="general")
    author = Column(String(200))
    ward = Column(String(100))
    audio_file_path = Column(String(500))
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="notes")
    extractions = relationship("DataExtraction", back_populates="note")


class DataExtraction(Base):
    __tablename__ = "data_extractions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id = Column(String, ForeignKey("notes.id"))
    extracted_patient_data = Column(JSON)
    extracted_clinical_data = Column(JSON)
    extraction_confidence = Column(Float, default=0.0)
    missing_fields = Column(JSON)  # List of missing fields
    suggested_questions = Column(JSON)  # List of suggested questions
    extraction_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    note = relationship("Note", back_populates="extractions")
    forms = relationship("Form", back_populates="extraction")


class FormTemplate(Base):
    __tablename__ = "form_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    form_name = Column(String(200), nullable=False)
    form_type = Column(String(100), nullable=False)
    version = Column(String(20), default="1.0")
    fields_definition = Column(JSON)  # FormField list
    template_path = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    forms = relationship("Form", back_populates="template")


class Form(Base):
    __tablename__ = "forms"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String, ForeignKey("form_templates.id"))
    patient_id = Column(String, ForeignKey("patients.id"))
    extraction_id = Column(String, ForeignKey("data_extractions.id"))
    filled_data = Column(JSON)
    file_path = Column(String(500))
    format = Column(String(20), default="pdf")
    status = Column(String(50), default="generated")
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    template = relationship("FormTemplate", back_populates="forms")
    patient = relationship("Patient", back_populates="forms")
    extraction = relationship("DataExtraction", back_populates="forms")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100))
    action = Column(String(200), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(200), unique=True, nullable=False)
    user_id = Column(String(100))
    forms_processed = Column(Integer, default=0)
    subscription_tier = Column(String(50), default="free")
    monthly_limit = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
