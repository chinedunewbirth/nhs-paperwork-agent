"""
Form Template System for NHS Standard Forms
Defines templates for discharge summaries, referrals, and risk assessments
"""

from typing import Dict, List
from ..models.schemas import FormTemplate, FormField, FormTypeEnum


class FormTemplateService:
    """Service for managing NHS form templates"""
    
    def __init__(self):
        """Initialize form template service with standard NHS templates"""
        self.templates = self._initialize_templates()
    
    def get_template(self, form_type: FormTypeEnum) -> FormTemplate:
        """Get a specific form template by type"""
        return self.templates.get(form_type)
    
    def get_all_templates(self) -> Dict[FormTypeEnum, FormTemplate]:
        """Get all available form templates"""
        return self.templates
    
    def _initialize_templates(self) -> Dict[FormTypeEnum, FormTemplate]:
        """Initialize all NHS form templates"""
        return {
            FormTypeEnum.DISCHARGE_SUMMARY: self._create_discharge_summary_template(),
            FormTypeEnum.REFERRAL: self._create_referral_template(),
            FormTypeEnum.RISK_ASSESSMENT: self._create_risk_assessment_template(),
        }
    
    def _create_discharge_summary_template(self) -> FormTemplate:
        """Create NHS Discharge Summary template"""
        fields = [
            # Patient Demographics
            FormField(
                field_id="patient_name",
                field_name="Patient Name",
                field_type="text",
                required=True
            ),
            FormField(
                field_id="nhs_number",
                field_name="NHS Number",
                field_type="text",
                required=True,
                validation_pattern=r"^\d{10}$"
            ),
            FormField(
                field_id="date_of_birth",
                field_name="Date of Birth",
                field_type="date",
                required=True
            ),
            FormField(
                field_id="gender",
                field_name="Gender",
                field_type="select",
                options=["Male", "Female", "Other", "Prefer not to say"]
            ),
            FormField(
                field_id="address",
                field_name="Address",
                field_type="textarea"
            ),
            FormField(
                field_id="gp_name",
                field_name="GP Name",
                field_type="text"
            ),
            FormField(
                field_id="gp_practice",
                field_name="GP Practice",
                field_type="text"
            ),
            
            # Clinical Information
            FormField(
                field_id="admission_date",
                field_name="Date of Admission",
                field_type="date",
                required=True
            ),
            FormField(
                field_id="discharge_date",
                field_name="Date of Discharge",
                field_type="date",
                required=True
            ),
            FormField(
                field_id="ward",
                field_name="Ward/Department",
                field_type="text"
            ),
            FormField(
                field_id="consultant",
                field_name="Consultant",
                field_type="text",
                required=True
            ),
            FormField(
                field_id="presenting_complaint",
                field_name="Presenting Complaint",
                field_type="textarea",
                required=True
            ),
            FormField(
                field_id="primary_diagnosis",
                field_name="Primary Diagnosis",
                field_type="text",
                required=True
            ),
            FormField(
                field_id="secondary_diagnoses",
                field_name="Secondary Diagnoses",
                field_type="textarea"
            ),
            FormField(
                field_id="past_medical_history",
                field_name="Past Medical History",
                field_type="textarea"
            ),
            FormField(
                field_id="medications_on_admission",
                field_name="Medications on Admission",
                field_type="textarea"
            ),
            FormField(
                field_id="allergies",
                field_name="Known Allergies",
                field_type="textarea"
            ),
            FormField(
                field_id="clinical_summary",
                field_name="Clinical Summary",
                field_type="textarea",
                required=True
            ),
            FormField(
                field_id="investigation_results",
                field_name="Investigation Results",
                field_type="textarea"
            ),
            FormField(
                field_id="treatment_given",
                field_name="Treatment Given",
                field_type="textarea"
            ),
            FormField(
                field_id="discharge_medications",
                field_name="Discharge Medications",
                field_type="textarea"
            ),
            FormField(
                field_id="follow_up_instructions",
                field_name="Follow-up Instructions",
                field_type="textarea",
                required=True
            ),
            FormField(
                field_id="gp_actions_required",
                field_name="Actions Required by GP",
                field_type="textarea"
            ),
            FormField(
                field_id="discharge_destination",
                field_name="Discharge Destination",
                field_type="select",
                options=["Home", "Care Home", "Another Hospital", "Rehabilitation Unit", "Other"]
            ),
        ]
        
        return FormTemplate(
            form_id="nhs_discharge_summary_v1",
            form_name="NHS Discharge Summary",
            form_type=FormTypeEnum.DISCHARGE_SUMMARY,
            fields=fields
        )
    
    def _create_referral_template(self) -> FormTemplate:
        """Create NHS Referral template"""
        fields = [
            # Patient Demographics
            FormField(
                field_id="patient_name",
                field_name="Patient Name",
                field_type="text",
                required=True
            ),
            FormField(
                field_id="nhs_number",
                field_name="NHS Number",
                field_type="text",
                required=True,
                validation_pattern=r"^\d{10}$"
            ),
            FormField(
                field_id="date_of_birth",
                field_name="Date of Birth",
                field_type="date",
                required=True
            ),
            FormField(
                field_id="gender",
                field_name="Gender",
                field_type="select",
                options=["Male", "Female", "Other", "Prefer not to say"]
            ),
            FormField(
                field_id="address",
                field_name="Address",
                field_type="textarea"
            ),
            FormField(
                field_id="phone_number",
                field_name="Contact Number",
                field_type="text"
            ),
            
            # Referral Details
            FormField(
                field_id="referring_clinician",
                field_name="Referring Clinician",
                field_type="text",
                required=True
            ),
            FormField(
                field_id="referring_department",
                field_name="Referring Department",
                field_type="text"
            ),
            FormField(
                field_id="referral_to",
                field_name="Referring To (Department/Consultant)",
                field_type="text",
                required=True
            ),
            FormField(
                field_id="referral_urgency",
                field_name="Urgency",
                field_type="select",
                options=["Routine", "Urgent", "Emergency", "2-week wait"],
                required=True
            ),
            FormField(
                field_id="referral_reason",
                field_name="Reason for Referral",
                field_type="textarea",
                required=True
            ),
            FormField(
                field_id="clinical_history",
                field_name="Relevant Clinical History",
                field_type="textarea",
                required=True
            ),
            FormField(
                field_id="examination_findings",
                field_name="Examination Findings",
                field_type="textarea"
            ),
            FormField(
                field_id="investigations_completed",
                field_name="Investigations Completed",
                field_type="textarea"
            ),
            FormField(
                field_id="current_medications",
                field_name="Current Medications",
                field_type="textarea"
            ),
            FormField(
                field_id="allergies",
                field_name="Known Allergies",
                field_type="textarea"
            ),
            FormField(
                field_id="social_circumstances",
                field_name="Relevant Social Circumstances",
                field_type="textarea"
            ),
        ]
        
        return FormTemplate(
            form_id="nhs_referral_v1",
            form_name="NHS Referral Form",
            form_type=FormTypeEnum.REFERRAL,
            fields=fields
        )
    
    def _create_risk_assessment_template(self) -> FormTemplate:
        """Create NHS Risk Assessment template"""
        fields = [
            # Patient Demographics
            FormField(
                field_id="patient_name",
                field_name="Patient Name",
                field_type="text",
                required=True
            ),
            FormField(
                field_id="nhs_number",
                field_name="NHS Number",
                field_type="text",
                required=True
            ),
            FormField(
                field_id="date_of_birth",
                field_name="Date of Birth",
                field_type="date",
                required=True
            ),
            FormField(
                field_id="assessment_date",
                field_name="Assessment Date",
                field_type="date",
                required=True
            ),
            FormField(
                field_id="assessor_name",
                field_name="Assessor Name",
                field_type="text",
                required=True
            ),
            
            # Risk Assessment
            FormField(
                field_id="falls_risk",
                field_name="Falls Risk Level",
                field_type="select",
                options=["Low", "Medium", "High"],
                required=True
            ),
            FormField(
                field_id="falls_risk_factors",
                field_name="Falls Risk Factors",
                field_type="textarea"
            ),
            FormField(
                field_id="pressure_ulcer_risk",
                field_name="Pressure Ulcer Risk Level",
                field_type="select",
                options=["Low", "Medium", "High"],
                required=True
            ),
            FormField(
                field_id="pressure_ulcer_factors",
                field_name="Pressure Ulcer Risk Factors",
                field_type="textarea"
            ),
            FormField(
                field_id="nutrition_risk",
                field_name="Nutrition Risk Level",
                field_type="select",
                options=["Low", "Medium", "High"]
            ),
            FormField(
                field_id="mental_health_risk",
                field_name="Mental Health Risk Assessment",
                field_type="textarea"
            ),
            FormField(
                field_id="self_harm_risk",
                field_name="Self-harm Risk Level",
                field_type="select",
                options=["Low", "Medium", "High"]
            ),
            FormField(
                field_id="mobility_assessment",
                field_name="Mobility Assessment",
                field_type="textarea"
            ),
            FormField(
                field_id="cognitive_assessment",
                field_name="Cognitive Assessment",
                field_type="textarea"
            ),
            FormField(
                field_id="risk_mitigation_plan",
                field_name="Risk Mitigation Plan",
                field_type="textarea",
                required=True
            ),
            FormField(
                field_id="review_date",
                field_name="Next Review Date",
                field_type="date",
                required=True
            ),
        ]
        
        return FormTemplate(
            form_id="nhs_risk_assessment_v1",
            form_name="NHS Risk Assessment",
            form_type=FormTypeEnum.RISK_ASSESSMENT,
            fields=fields
        )
