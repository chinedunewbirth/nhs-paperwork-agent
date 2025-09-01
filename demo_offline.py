"""
Offline Demo for NHS Paperwork Automation Agent
Demonstrates system capabilities without requiring OpenAI API key
"""

import json
import os
import sys
from datetime import datetime, date

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models.schemas import (
    ClinicalNote, FormTypeEnum, ExtractedData, 
    PatientData, ClinicalInformation
)
from src.services.form_templates import FormTemplateService
from src.services.form_filler import FormFillerService
from src.services.pdf_generator import PDFGeneratorService
from src.core.config import ensure_directories


def create_mock_extracted_data() -> ExtractedData:
    """Create mock extracted data to simulate AI extraction"""
    
    patient_data = PatientData(
        nhs_number="1234567890",
        first_name="John",
        last_name="Smith",
        date_of_birth=date(1965, 3, 15),
        gender="Male",
        address="123 High Street, London, SW1A 1AA",
        phone_number="07700 900123",
        gp_name="Dr. Sarah Johnson",
        gp_practice="Riverside Medical Practice"
    )
    
    clinical_data = ClinicalInformation(
        primary_diagnosis="ST Elevation Myocardial Infarction (Inferior)",
        secondary_diagnoses=["Type 2 Diabetes Mellitus", "Hypertension"],
        presenting_complaint="65-year-old male presented with acute onset chest pain radiating to left arm, associated with shortness of breath and nausea",
        history_of_presenting_complaint="Pain started 2 hours ago while at rest. No previous episodes of similar pain.",
        past_medical_history=[
            "Hypertension (diagnosed 2018)",
            "Type 2 Diabetes Mellitus (diagnosed 2020)", 
            "Ex-smoker (quit 2019, 30 pack-year history)"
        ],
        medications=[
            {"name": "Amlodipine", "dose": "5mg", "frequency": "once daily"},
            {"name": "Metformin", "dose": "500mg", "frequency": "twice daily"},
            {"name": "Atorvastatin", "dose": "20mg", "frequency": "once daily at night"}
        ],
        allergies=["Penicillin (rash)"],
        social_history="Lives independently with wife. Retired engineer. Ex-smoker.",
        examination_findings="Alert and orientated. Chest pain 8/10 severity. BP 165/95, HR 95 regular, RR 22, O2 sats 94% on air",
        investigation_results=[
            "ECG: ST elevation in leads II, III, aVF consistent with inferior STEMI",
            "Troponin I: 15.2 ng/mL (significantly elevated)",
            "FBC: Hb 13.2, WCC 8.5, Platelets 245"
        ],
        treatment_given="Primary PCI performed - RCA stented with drug-eluting stent. Dual antiplatelet therapy commenced.",
        discharge_medications=[
            {"name": "Aspirin", "dose": "75mg", "frequency": "once daily"},
            {"name": "Clopidogrel", "dose": "75mg", "frequency": "once daily"},
            {"name": "Atorvastatin", "dose": "80mg", "frequency": "once daily at night"},
            {"name": "Ramipril", "dose": "2.5mg", "frequency": "once daily"},
            {"name": "Metoprolol", "dose": "25mg", "frequency": "twice daily"}
        ],
        follow_up_instructions="Cardiology clinic in 6 weeks. GP follow-up in 1 week for medication review. Cardiac rehabilitation referral.",
        risk_factors=["Previous smoker", "Diabetes", "Hypertension"]
    )
    
    return ExtractedData(
        patient=patient_data,
        clinical=clinical_data,
        extraction_confidence=0.92,
        missing_fields=["ward", "consultant"],
        suggested_questions=[
            "Please specify the ward/department",
            "Please provide the consultant's name"
        ],
        metadata={
            "demo_mode": True,
            "extraction_timestamp": datetime.now().isoformat()
        }
    )


def main():
    """Run the offline demo"""
    print("🩺 NHS Paperwork Automation Agent - Offline Demo")
    print("=" * 60)
    print("This demo shows system capabilities without requiring OpenAI API")
    print("=" * 60)
    
    try:
        # Ensure directories exist
        ensure_directories()
        
        print("1️⃣ Initializing services...")
        
        # Initialize services (no OpenAI key needed for this demo)
        template_service = FormTemplateService()
        filler_service = FormFillerService()
        pdf_service = PDFGeneratorService()
        
        print("✅ Services initialized successfully")
        
        # Create mock extracted data (simulating AI extraction)
        print("\n2️⃣ Using mock clinical data (simulating AI extraction)...")
        extracted_data = create_mock_extracted_data()
        
        print(f"✅ Mock extraction completed with {extracted_data.extraction_confidence:.1%} confidence")
        
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
                    if field == 'medications' or field == 'discharge_medications':
                        # Format medications nicely
                        med_strings = []
                        for med in value:
                            if isinstance(med, dict):
                                med_str = f"{med.get('name', '')} {med.get('dose', '')} {med.get('frequency', '')}".strip()
                                med_strings.append(med_str)
                            else:
                                med_strings.append(str(med))
                        print(f"  {field_name}: {'; '.join(med_strings)}")
                    else:
                        print(f"  {field_name}: {'; '.join(str(v) for v in value)}")
                else:
                    print(f"  {field_name}: {value}")
        
        # Show suggestions
        if extracted_data.missing_fields:
            print(f"\n⚠️ Missing Fields: {', '.join(extracted_data.missing_fields)}")
        
        if extracted_data.suggested_questions:
            print("\n💭 Suggestions:")
            for suggestion in extracted_data.suggested_questions:
                print(f"  • {suggestion}")
        
        # Generate forms
        print("\n3️⃣ Generating NHS forms...")
        
        form_types = [
            FormTypeEnum.DISCHARGE_SUMMARY, 
            FormTypeEnum.REFERRAL, 
            FormTypeEnum.RISK_ASSESSMENT
        ]
        generated_forms = []
        
        for form_type in form_types:
            try:
                print(f"📋 Generating {form_type.value.replace('_', ' ').title()}...")
                
                # Get template and fill form
                template = template_service.get_template(form_type)
                if template:
                    filled_form = filler_service.fill_form(template, extracted_data)
                    
                    # Show some of the filled data
                    print(f"   📝 Filled {len(filled_form.filled_data)} fields")
                    
                    # Generate PDF
                    pdf_path = pdf_service.generate_pdf(filled_form, form_type)
                    filled_form.file_path = pdf_path
                    filled_form.format = "pdf"
                    
                    generated_forms.append(filled_form)
                    print(f"   ✅ Generated PDF: {pdf_path}")
                else:
                    print(f"   ❌ Template not found for {form_type}")
                
            except Exception as e:
                print(f"❌ Error generating {form_type.value}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎉 Demo completed! Generated {len(generated_forms)} forms.")
        
        # Show sample form data
        if generated_forms:
            print("\n📄 Sample Form Data (Discharge Summary):")
            discharge_form = next((f for f in generated_forms if "discharge" in f.template_id), None)
            if discharge_form:
                sample_fields = [
                    "patient_name", "nhs_number", "primary_diagnosis", 
                    "presenting_complaint", "discharge_medications"
                ]
                for field in sample_fields:
                    value = discharge_form.filled_data.get(field, "")
                    if value:
                        print(f"  {field.replace('_', ' ').title()}: {value}")
        
        print("\n📁 Generated PDF files:")
        for form in generated_forms:
            if form.file_path and os.path.exists(form.file_path):
                file_size = os.path.getsize(form.file_path) / 1024  # KB
                print(f"  • {form.file_path} ({file_size:.1f} KB)")
        
        # Summary
        print(f"\n📈 Demo Summary:")
        print(f"  • Extraction Confidence: {extracted_data.extraction_confidence:.1%}")
        print(f"  • Forms Generated: {len(generated_forms)}")
        print(f"  • Missing Fields: {len(extracted_data.missing_fields)}")
        print(f"  • PDF Files Created: {len([f for f in generated_forms if f.file_path])}")
        
        print("\n🚀 Ready for real deployment!")
        print("\nTo use with real AI:")
        print("1. Add OPENAI_API_KEY to .env file")
        print("2. Run: python demo.py (for AI-powered extraction)")
        print("3. Or start the web interface: python start_api.py & python start_dashboard.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
