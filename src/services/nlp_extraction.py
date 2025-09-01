"""
NLP Extraction Service for NHS Paperwork Automation Agent
Extracts structured clinical data from unstructured notes using OpenAI GPT-4
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import openai
from pydantic import ValidationError

from ..models.schemas import (
    ClinicalNote, 
    ExtractedData, 
    PatientData, 
    ClinicalInformation
)

logger = logging.getLogger(__name__)


class NLPExtractionService:
    """Service for extracting structured data from clinical notes using LLM"""
    
    def __init__(self, openai_api_key: str):
        """Initialize the extraction service"""
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = "gpt-4-1106-preview"  # Use GPT-4 Turbo for better JSON output
        
    def extract_clinical_data(self, note: ClinicalNote) -> ExtractedData:
        """
        Extract structured clinical data from a clinical note
        
        Args:
            note: ClinicalNote object containing raw text
            
        Returns:
            ExtractedData: Structured patient and clinical information
        """
        try:
            # Create the extraction prompt
            prompt = self._create_extraction_prompt(note.raw_text)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )
            
            # Parse the JSON response
            extracted_json = json.loads(response.choices[0].message.content)
            
            # Convert to our data models
            patient_data = PatientData(**extracted_json.get("patient", {}))
            clinical_data = ClinicalInformation(**extracted_json.get("clinical", {}))
            
            # Calculate confidence score based on completeness
            confidence = self._calculate_confidence(patient_data, clinical_data)
            
            # Identify missing fields
            missing_fields = self._identify_missing_fields(patient_data, clinical_data)
            
            # Generate suggestions for missing information
            suggestions = self._generate_suggestions(missing_fields, note.raw_text)
            
            return ExtractedData(
                patient=patient_data,
                clinical=clinical_data,
                extraction_confidence=confidence,
                missing_fields=missing_fields,
                suggested_questions=suggestions,
                metadata={
                    "model_used": self.model,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "note_id": note.id,
                    "raw_text_length": len(note.raw_text)
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting clinical data: {str(e)}")
            # Return empty structure with error information
            return ExtractedData(
                patient=PatientData(),
                clinical=ClinicalInformation(),
                extraction_confidence=0.0,
                missing_fields=["extraction_failed"],
                suggested_questions=[f"Please review the original note - extraction failed: {str(e)}"],
                metadata={"error": str(e)}
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for clinical data extraction"""
        return """You are a clinical data extraction specialist for the NHS. Your task is to extract structured information from clinical notes and convert it into a standardized JSON format.

IMPORTANT RULES:
1. Only extract information that is explicitly mentioned in the text
2. Do not infer or guess information that isn't clearly stated
3. Use proper medical terminology when available
4. Format dates as YYYY-MM-DD
5. Be precise with medication details (name, dose, frequency)
6. Maintain patient confidentiality - only extract necessary clinical information

Extract information into the following JSON structure:
{
  "patient": {
    "nhs_number": "string or null",
    "first_name": "string or null",
    "last_name": "string or null", 
    "date_of_birth": "YYYY-MM-DD or null",
    "gender": "Male/Female/Other/Prefer not to say or null",
    "address": "string or null",
    "postcode": "string or null",
    "phone_number": "string or null",
    "next_of_kin": "string or null",
    "next_of_kin_phone": "string or null",
    "gp_name": "string or null",
    "gp_practice": "string or null"
  },
  "clinical": {
    "primary_diagnosis": "string or null",
    "secondary_diagnoses": ["list of strings"],
    "presenting_complaint": "string or null",
    "history_of_presenting_complaint": "string or null",
    "past_medical_history": ["list of strings"],
    "medications": [{"name": "string", "dose": "string", "frequency": "string"}],
    "allergies": ["list of strings"],
    "social_history": "string or null",
    "examination_findings": "string or null",
    "investigation_results": ["list of strings"],
    "treatment_given": "string or null",
    "discharge_medications": [{"name": "string", "dose": "string", "frequency": "string"}],
    "follow_up_instructions": "string or null",
    "risk_factors": ["list of strings"]
  }
}

Return only the JSON object, no additional text."""

    def _create_extraction_prompt(self, raw_text: str) -> str:
        """Create the extraction prompt for the given clinical note"""
        return f"""Please extract structured clinical information from the following clinical note:

--- CLINICAL NOTE ---
{raw_text}
--- END CLINICAL NOTE ---

Extract the information following the JSON schema provided in the system prompt. Only include information that is explicitly mentioned in the note."""

    def _calculate_confidence(self, patient: PatientData, clinical: ClinicalInformation) -> float:
        """Calculate confidence score based on data completeness"""
        
        # Key fields for confidence calculation
        patient_fields = [
            patient.first_name, patient.last_name, patient.date_of_birth, 
            patient.nhs_number, patient.gender
        ]
        clinical_fields = [
            clinical.primary_diagnosis, clinical.presenting_complaint,
            clinical.examination_findings
        ]
        
        # Count non-empty fields
        filled_patient = sum(1 for field in patient_fields if field is not None)
        filled_clinical = sum(1 for field in clinical_fields if field is not None)
        
        # Add points for lists with content
        if clinical.medications:
            filled_clinical += 1
        if clinical.past_medical_history:
            filled_clinical += 1
        if clinical.allergies:
            filled_clinical += 1
            
        total_filled = filled_patient + filled_clinical
        total_possible = len(patient_fields) + len(clinical_fields) + 3  # +3 for the lists
        
        return min(total_filled / total_possible, 1.0)
    
    def _identify_missing_fields(self, patient: PatientData, clinical: ClinicalInformation) -> List[str]:
        """Identify missing critical fields"""
        missing = []
        
        # Critical patient fields
        if not patient.first_name:
            missing.append("patient_first_name")
        if not patient.last_name:
            missing.append("patient_last_name")
        if not patient.date_of_birth:
            missing.append("patient_date_of_birth")
        if not patient.nhs_number:
            missing.append("patient_nhs_number")
            
        # Critical clinical fields
        if not clinical.primary_diagnosis:
            missing.append("primary_diagnosis")
        if not clinical.presenting_complaint:
            missing.append("presenting_complaint")
            
        return missing
    
    def _generate_suggestions(self, missing_fields: List[str], raw_text: str) -> List[str]:
        """Generate suggestions for gathering missing information"""
        suggestions = []
        
        field_suggestions = {
            "patient_first_name": "Please confirm the patient's first name",
            "patient_last_name": "Please confirm the patient's surname",
            "patient_date_of_birth": "Please provide the patient's date of birth",
            "patient_nhs_number": "Please provide the patient's NHS number",
            "primary_diagnosis": "Please clarify the primary diagnosis",
            "presenting_complaint": "Please provide the main presenting complaint",
            "medications": "Please list current medications with doses",
            "allergies": "Please confirm any known allergies",
            "follow_up_instructions": "Please specify follow-up care requirements"
        }
        
        for field in missing_fields:
            if field in field_suggestions:
                suggestions.append(field_suggestions[field])
                
        return suggestions[:5]  # Limit to 5 suggestions

    async def process_audio_note(self, audio_file_path: str) -> str:
        """
        Convert audio file to text using OpenAI Whisper
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                return transcript
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise e
