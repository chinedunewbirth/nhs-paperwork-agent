"""
Demo Script for NHS Paperwork Automation Agent
Tests the core functionality with sample clinical notes
"""

import json
import os
import sys
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models.schemas import ClinicalNote, FormTypeEnum
from src.services.nlp_extraction import NLPExtractionService
from src.services.form_templates import FormTemplateService
from src.services.form_filler import FormFillerService
from src.services.pdf_generator import PDFGeneratorService
from src.core.config import ensure_directories


def main():
    """Run the demo"""
    print("🩺 NHS Paperwork Automation Agent - Demo")
    print("=" * 50)
    
    # Ensure directories exist
    ensure_directories()
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key:")
        print("1. Copy .env.template to .env")
        print("2. Add your OpenAI API key to the .env file")
        return
    
    # Sample clinical note
    sample_note = """
    Patient: Smith, John
    NHS Number: 1234567890
    DOB: 15/03/1965
    Gender: Male
    Address: 123 High Street, London, SW1A 1AA
    GP: Dr. Sarah Johnson, Riverside Medical Practice
    
    Presenting Complaint: 
    65-year-old male presented to A&E with acute onset chest pain radiating to left arm, 
    associated with shortness of breath and nausea. Pain started 2 hours ago while at rest.
    
    Past Medical History:
    - Hypertension (diagnosed 2018)
    - Type 2 Diabetes Mellitus (diagnosed 2020)
    - Ex-smoker (quit 2019, 30 pack-year history)
    
    Medications on Admission:
    - Amlodipine 5mg once daily
    - Metformin 500mg twice daily
    - Atorvastatin 20mg once daily at night
    
    Allergies: Penicillin (rash)
    
    Examination Findings:
    Alert and orientated. Chest pain 8/10 severity. BP 165/95, HR 95 regular, 
    RR 22, O2 sats 94% on air. Heart sounds normal, chest clear. 
    No peripheral edema.
    
    Investigations:
    - ECG: ST elevation in leads II, III, aVF consistent with inferior STEMI
    - Troponin I: 15.2 ng/mL (significantly elevated)
    - FBC: Hb 13.2, WCC 8.5, Platelets 245
    - U&E: Normal
    
    Diagnosis: ST Elevation Myocardial Infarction (Inferior)
    
    Treatment:
    Primary PCI performed - RCA stented with drug-eluting stent. 
    Dual antiplatelet therapy commenced.
    
    Discharge Medications:
    - Aspirin 75mg once daily
    - Clopidogrel 75mg once daily  
    - Atorvastatin 80mg once daily at night
    - Ramipril 2.5mg once daily
    - Metoprolol 25mg twice daily
    - Metformin 500mg twice daily
    
    Follow-up:
    Cardiology clinic in 6 weeks
    GP follow-up in 1 week for medication review
    Cardiac rehabilitation referral
    """
    
    try:
        print("1️⃣ Initializing services...")
        
        # Initialize services
        nlp_service = NLPExtractionService(openai_api_key)
        template_service = FormTemplateService()
        filler_service = FormFillerService()
        pdf_service = PDFGeneratorService()
        
        print("✅ Services initialized successfully")
        
        # Create clinical note
        print("\n2️⃣ Processing clinical note...")
        note = ClinicalNote(
            raw_text=sample_note,
            note_type="discharge_note",
            author="Dr. Emily Wilson",
            ward="Cardiology"
        )
        
        # Extract clinical data
        print("🧠 Extracting clinical data with AI...")
        extracted_data = nlp_service.extract_clinical_data(note)
        
        print(f"✅ Extraction completed with {extracted_data.extraction_confidence:.1%} confidence")
        
        # Display extracted data
        print("\n📊 Extracted Patient Data:")
        patient_dict = extracted_data.patient.model_dump()
        for field, value in patient_dict.items():
            if value:
                print(f"  {field.replace('_', ' ').title()}: {value}")
        
        print("\n🏥 Extracted Clinical Data:")
        clinical_dict = extracted_data.clinical.model_dump()
        for field, value in clinical_dict.items():
            if value:
                field_name = field.replace('_', ' ').title()
                if isinstance(value, list):
                    print(f"  {field_name}: {'; '.join(str(v) for v in value)}")
                else:
                    print(f"  {field_name}: {value}")
        
        # Show suggestions if any
        if extracted_data.missing_fields:
            print(f"\n⚠️ Missing Fields: {', '.join(extracted_data.missing_fields)}")
        
        if extracted_data.suggested_questions:
            print("\n💭 Suggestions:")
            for suggestion in extracted_data.suggested_questions:
                print(f"  • {suggestion}")
        
        # Generate forms
        print("\n3️⃣ Generating NHS forms...")
        
        form_types = [FormTypeEnum.DISCHARGE_SUMMARY, FormTypeEnum.REFERRAL, FormTypeEnum.RISK_ASSESSMENT]
        generated_forms = []
        
        for form_type in form_types:
            try:
                print(f"📋 Generating {form_type.value.replace('_', ' ').title()}...")
                
                # Get template and fill form
                template = template_service.get_template(form_type)
                filled_form = filler_service.fill_form(template, extracted_data)
                
                # Generate PDF
                pdf_path = pdf_service.generate_pdf(filled_form, form_type)
                filled_form.file_path = pdf_path
                filled_form.format = "pdf"
                
                generated_forms.append(filled_form)
                print(f"✅ Generated PDF: {pdf_path}")
                
            except Exception as e:
                print(f"❌ Error generating {form_type.value}: {str(e)}")
        
        print(f"\n🎉 Demo completed! Generated {len(generated_forms)} forms.")
        print("\n📁 Generated files:")
        for form in generated_forms:
            if form.file_path:
                print(f"  • {form.file_path}")
        
        # Summary
        print(f"\n📈 Processing Summary:")
        print(f"  • Extraction Confidence: {extracted_data.extraction_confidence:.1%}")
        print(f"  • Forms Generated: {len(generated_forms)}")
        print(f"  • Missing Fields: {len(extracted_data.missing_fields)}")
        print(f"  • PDF Files Created: {len([f for f in generated_forms if f.file_path])}")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
