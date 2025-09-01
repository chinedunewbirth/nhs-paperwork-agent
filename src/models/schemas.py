"""
Core data models for NHS Paperwork Automation Agent
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer not to say"


class PriorityEnum(str, Enum):
    ROUTINE = "Routine"
    URGENT = "Urgent"
    EMERGENCY = "Emergency"


class FormTypeEnum(str, Enum):
    DISCHARGE_SUMMARY = "discharge_summary"
    REFERRAL = "referral"
    RISK_ASSESSMENT = "risk_assessment"
    GP_LETTER = "gp_letter"
    COMPLIANCE_CHECK = "compliance_check"


class PatientData(BaseModel):
    """Patient demographic and basic information"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    nhs_number: Optional[str] = Field(None, description="10-digit NHS number")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    address: Optional[str] = None
    postcode: Optional[str] = None
    phone_number: Optional[str] = None
    next_of_kin: Optional[str] = None
    next_of_kin_phone: Optional[str] = None
    gp_name: Optional[str] = None
    gp_practice: Optional[str] = None


class ClinicalInformation(BaseModel):
    """Extracted clinical information from notes"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    primary_diagnosis: Optional[str] = None
    secondary_diagnoses: List[str] = Field(default_factory=list)
    presenting_complaint: Optional[str] = None
    history_of_presenting_complaint: Optional[str] = None
    past_medical_history: List[str] = Field(default_factory=list)
    medications: List[Dict[str, str]] = Field(default_factory=list)  # [{"name": "...", "dose": "...", "frequency": "..."}]
    allergies: List[str] = Field(default_factory=list)
    social_history: Optional[str] = None
    examination_findings: Optional[str] = None
    investigation_results: List[str] = Field(default_factory=list)
    treatment_given: Optional[str] = None
    discharge_medications: List[Dict[str, str]] = Field(default_factory=list)
    follow_up_instructions: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)


class ClinicalNote(BaseModel):
    """Input clinical note data"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: Optional[str] = None
    raw_text: str = Field(..., description="Original clinical note text")
    note_type: str = Field(default="general", description="Type of clinical note")
    author: Optional[str] = None
    ward: Optional[str] = None
    date_created: datetime = Field(default_factory=datetime.now)
    audio_file_path: Optional[str] = None


class ExtractedData(BaseModel):
    """Complete extracted and structured data from clinical notes"""
    
    patient: PatientData
    clinical: ClinicalInformation
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_fields: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)


class FormField(BaseModel):
    """Individual form field definition"""
    
    field_id: str
    field_name: str
    field_type: str  # text, date, select, checkbox, etc.
    required: bool = False
    options: Optional[List[str]] = None  # for select fields
    validation_pattern: Optional[str] = None


class FormTemplate(BaseModel):
    """NHS form template definition"""
    
    form_id: str
    form_name: str
    form_type: FormTypeEnum
    version: str = "1.0"
    fields: List[FormField]
    template_path: Optional[str] = None  # Path to Word/PDF template
    created_at: datetime = Field(default_factory=datetime.now)


class FilledForm(BaseModel):
    """Completed form with filled data"""
    
    form_id: str
    template_id: str
    form_type: FormTypeEnum
    patient_id: Optional[str] = None
    filled_data: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.now)
    file_path: Optional[str] = None
    format: str = "pdf"  # pdf, docx, etc.


class ProcessingRequest(BaseModel):
    """Request to process clinical notes"""
    
    note: ClinicalNote
    form_types: List[FormTypeEnum] = Field(default_factory=lambda: [FormTypeEnum.DISCHARGE_SUMMARY])
    priority: PriorityEnum = PriorityEnum.ROUTINE
    auto_fill_forms: bool = True
    include_suggestions: bool = True


class ProcessingResponse(BaseModel):
    """Response from processing clinical notes"""
    
    request_id: str
    extracted_data: ExtractedData
    generated_forms: List[FilledForm] = Field(default_factory=list)
    processing_time: float
    status: str = "completed"
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AuditLog(BaseModel):
    """Audit log for compliance tracking"""
    
    log_id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class UserSession(BaseModel):
    """User session for tracking usage"""
    
    session_id: str
    user_id: Optional[str] = None
    forms_processed: int = 0
    subscription_tier: str = "free"  # free, pro, enterprise
    monthly_limit: int = 10
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
