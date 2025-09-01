"""
Form Auto-Fill Engine for NHS Paperwork Automation Agent
Maps extracted clinical data to form fields and generates filled forms
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, date

from ..models.schemas import (
    ExtractedData, 
    FormTemplate, 
    FilledForm, 
    FormTypeEnum,
    PatientData,
    ClinicalInformation
)

logger = logging.getLogger(__name__)


class FormFillerService:
    """Service for auto-filling NHS forms with extracted data"""
    
    def __init__(self):
        """Initialize the form filler service"""
        self.field_mappings = self._initialize_field_mappings()
    
    def fill_form(self, template: FormTemplate, extracted_data: ExtractedData) -> FilledForm:
        """
        Fill a form template with extracted clinical data
        
        Args:
            template: FormTemplate to fill
            extracted_data: ExtractedData containing patient and clinical information
            
        Returns:
            FilledForm: Form with filled data
        """
        try:
            filled_data = {}
            
            # Get the appropriate mapping function for this form type
            mapping_func = self.field_mappings.get(template.form_type)
            if not mapping_func:
                raise ValueError(f"No mapping function found for form type: {template.form_type}")
            
            # Apply the mapping
            filled_data = mapping_func(extracted_data)
            
            # Create the filled form
            form_id = f"{template.form_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return FilledForm(
                form_id=form_id,
                template_id=template.form_id,
                form_type=template.form_type,
                filled_data=filled_data,
                format="json"  # Will be converted to PDF later
            )
            
        except Exception as e:
            logger.error(f"Error filling form {template.form_id}: {str(e)}")
            raise e
    
    def _initialize_field_mappings(self) -> Dict[FormTypeEnum, callable]:
        """Initialize field mapping functions for each form type"""
        return {
            FormTypeEnum.DISCHARGE_SUMMARY: self._map_discharge_summary,
            FormTypeEnum.REFERRAL: self._map_referral,
            FormTypeEnum.RISK_ASSESSMENT: self._map_risk_assessment,
        }
    
    def _map_discharge_summary(self, data: ExtractedData) -> Dict[str, Any]:
        """Map extracted data to discharge summary form fields"""
        patient = data.patient
        clinical = data.clinical
        
        # Format patient name
        patient_name = self._format_patient_name(patient.first_name, patient.last_name)
        
        # Format medications
        medications_text = self._format_medications(clinical.medications)
        discharge_meds_text = self._format_medications(clinical.discharge_medications)
        
        # Format diagnoses
        secondary_diag_text = "; ".join(clinical.secondary_diagnoses) if clinical.secondary_diagnoses else ""
        
        # Format past medical history
        pmh_text = "; ".join(clinical.past_medical_history) if clinical.past_medical_history else ""
        
        # Format allergies
        allergies_text = "; ".join(clinical.allergies) if clinical.allergies else "NKDA"
        
        # Format investigation results
        investigations_text = "; ".join(clinical.investigation_results) if clinical.investigation_results else ""
        
        return {
            # Patient Demographics
            "patient_name": patient_name,
            "nhs_number": patient.nhs_number,
            "date_of_birth": patient.date_of_birth.strftime("%d/%m/%Y") if patient.date_of_birth else "",
            "gender": patient.gender,
            "address": patient.address,
            "gp_name": patient.gp_name,
            "gp_practice": patient.gp_practice,
            
            # Clinical Information
            "admission_date": "",  # Not typically in notes, would need to be added
            "discharge_date": datetime.now().strftime("%d/%m/%Y"),  # Default to today
            "ward": "",  # Would need to be extracted or provided
            "consultant": "",  # Would need to be extracted or provided
            "presenting_complaint": clinical.presenting_complaint,
            "primary_diagnosis": clinical.primary_diagnosis,
            "secondary_diagnoses": secondary_diag_text,
            "past_medical_history": pmh_text,
            "medications_on_admission": medications_text,
            "allergies": allergies_text,
            "clinical_summary": clinical.history_of_presenting_complaint,
            "examination_findings": clinical.examination_findings,
            "investigation_results": investigations_text,
            "treatment_given": clinical.treatment_given,
            "discharge_medications": discharge_meds_text,
            "follow_up_instructions": clinical.follow_up_instructions,
            "gp_actions_required": "",  # Could be derived from follow-up instructions
            "discharge_destination": "Home",  # Default assumption
        }
    
    def _map_referral(self, data: ExtractedData) -> Dict[str, Any]:
        """Map extracted data to referral form fields"""
        patient = data.patient
        clinical = data.clinical
        
        patient_name = self._format_patient_name(patient.first_name, patient.last_name)
        medications_text = self._format_medications(clinical.medications)
        allergies_text = "; ".join(clinical.allergies) if clinical.allergies else "NKDA"
        investigations_text = "; ".join(clinical.investigation_results) if clinical.investigation_results else ""
        
        return {
            # Patient Demographics
            "patient_name": patient_name,
            "nhs_number": patient.nhs_number,
            "date_of_birth": patient.date_of_birth.strftime("%d/%m/%Y") if patient.date_of_birth else "",
            "gender": patient.gender,
            "address": patient.address,
            "phone_number": patient.phone_number,
            
            # Referral Details
            "referring_clinician": "",  # Would need to be provided
            "referring_department": "",  # Would need to be provided
            "referral_to": "",  # Would need to be specified
            "referral_urgency": "Routine",  # Default
            "referral_reason": clinical.presenting_complaint,
            "clinical_history": f"{clinical.history_of_presenting_complaint or ''} Past Medical History: {'; '.join(clinical.past_medical_history) if clinical.past_medical_history else 'None documented'}",
            "examination_findings": clinical.examination_findings,
            "investigations_completed": investigations_text,
            "current_medications": medications_text,
            "allergies": allergies_text,
            "social_circumstances": clinical.social_history,
        }
    
    def _map_risk_assessment(self, data: ExtractedData) -> Dict[str, Any]:
        """Map extracted data to risk assessment form fields"""
        patient = data.patient
        clinical = data.clinical
        
        patient_name = self._format_patient_name(patient.first_name, patient.last_name)
        
        # Analyze risk factors from clinical data
        falls_risk = self._assess_falls_risk(clinical.risk_factors, clinical.past_medical_history)
        pressure_risk = self._assess_pressure_ulcer_risk(clinical.risk_factors)
        
        return {
            # Patient Demographics
            "patient_name": patient_name,
            "nhs_number": patient.nhs_number,
            "date_of_birth": patient.date_of_birth.strftime("%d/%m/%Y") if patient.date_of_birth else "",
            "assessment_date": datetime.now().strftime("%d/%m/%Y"),
            "assessor_name": "",  # Would need to be provided
            
            # Risk Assessment
            "falls_risk": falls_risk,
            "falls_risk_factors": "; ".join([rf for rf in clinical.risk_factors if "fall" in rf.lower()]),
            "pressure_ulcer_risk": pressure_risk,
            "pressure_ulcer_factors": "; ".join([rf for rf in clinical.risk_factors if "pressure" in rf.lower() or "mobility" in rf.lower()]),
            "nutrition_risk": "Medium",  # Default - would need specialized assessment
            "mental_health_risk": clinical.social_history if clinical.social_history else "",
            "self_harm_risk": "Low",  # Default - would need specialized assessment
            "mobility_assessment": clinical.examination_findings if clinical.examination_findings else "",
            "cognitive_assessment": "",  # Would need specialized assessment
            "risk_mitigation_plan": clinical.follow_up_instructions if clinical.follow_up_instructions else "Standard care protocols to be followed",
            "review_date": "",  # Would need to be calculated based on risk levels
        }
    
    def _format_patient_name(self, first_name: str, last_name: str) -> str:
        """Format patient name for forms"""
        if first_name and last_name:
            return f"{last_name.upper()}, {first_name.title()}"
        elif last_name:
            return last_name.upper()
        elif first_name:
            return first_name.title()
        else:
            return ""
    
    def _format_medications(self, medications: List[Dict[str, str]]) -> str:
        """Format medications list for form fields"""
        if not medications:
            return ""
        
        formatted_meds = []
        for med in medications:
            name = med.get("name", "")
            dose = med.get("dose", "")
            frequency = med.get("frequency", "")
            
            med_string = name
            if dose:
                med_string += f" {dose}"
            if frequency:
                med_string += f" {frequency}"
            
            formatted_meds.append(med_string)
        
        return "; ".join(formatted_meds)
    
    def _assess_falls_risk(self, risk_factors: List[str], medical_history: List[str]) -> str:
        """Assess falls risk based on clinical information"""
        high_risk_indicators = [
            "previous falls", "mobility issues", "confusion", "medication affecting balance",
            "visual impairment", "postural hypotension"
        ]
        
        all_factors = risk_factors + medical_history
        all_text = " ".join(all_factors).lower()
        
        for indicator in high_risk_indicators:
            if indicator in all_text:
                return "High"
        
        # Check for medium risk indicators
        medium_risk_indicators = ["elderly", "frail", "walking aid", "previous injury"]
        for indicator in medium_risk_indicators:
            if indicator in all_text:
                return "Medium"
        
        return "Low"
    
    def _assess_pressure_ulcer_risk(self, risk_factors: List[str]) -> str:
        """Assess pressure ulcer risk based on clinical information"""
        high_risk_indicators = [
            "immobile", "bed bound", "malnourished", "previous pressure ulcer",
            "diabetes", "reduced sensation"
        ]
        
        all_text = " ".join(risk_factors).lower()
        
        for indicator in high_risk_indicators:
            if indicator in all_text:
                return "High"
        
        return "Low"
