#!/usr/bin/env python3
"""
Test script for PDF API endpoints
Tests the new PDF generation functionality through the FastAPI endpoints
"""

import requests
import json
import os
from datetime import datetime


def test_pdf_endpoints():
    """Test the PDF generation API endpoints"""
    
    # API base URL
    base_url = "http://localhost:8000"
    
    # Test data - sample extracted clinical data
    test_extracted_data = {
        "patient": {
            "name": "John Smith",
            "nhs_number": "1234567890",
            "date_of_birth": "1965-03-15",
            "address": "123 High Street, Manchester, M1 1AA",
            "phone": "0161 123 4567",
            "emergency_contact": "Jane Smith - Wife (0161 765 4321)"
        },
        "clinical": {
            "primary_diagnosis": "Acute myocardial infarction",
            "presenting_complaint": "Chest pain for 2 days",
            "examination_findings": "Elevated cardiac enzymes, ST elevation on ECG",
            "current_medications": ["Aspirin 75mg OD", "Atorvastatin 40mg ON", "Metoprolol 25mg BD"],
            "allergies": ["Penicillin"],
            "discharge_plan": "Cardiology follow-up in 2 weeks",
            "treatment_provided": "Thrombolysis administered, cardiac monitoring"
        },
        "extraction_confidence": 0.92,
        "missing_fields": [],
        "suggested_questions": []
    }
    
    print("🧪 Testing PDF API Endpoints")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health check passed")
            print(f"   Services status: {health['services']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure to start the API server first with: python start_api.py")
        return
    
    # Test 2: Single form PDF generation
    print("\n2. Testing single form PDF generation...")
    try:
        response = requests.post(
            f"{base_url}/forms/pdf",
            json={
                "form_type": "discharge_summary",
                "extracted_data": test_extracted_data,
                "include_signature_placeholder": True
            }
        )
        
        if response.status_code == 200:
            # Save the PDF
            filename = f"test_discharge_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join("data", "forms", filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Single form PDF generated successfully")
            print(f"   Saved as: {filepath}")
            print(f"   File size: {len(response.content):,} bytes")
        else:
            print(f"❌ Single form PDF generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error testing single form PDF: {e}")
    
    # Test 3: Forms bundle PDF generation
    print("\n3. Testing forms bundle PDF generation...")
    try:
        response = requests.post(
            f"{base_url}/forms/pdf/bundle",
            json={
                "form_types": ["discharge_summary", "referral", "risk_assessment"],
                "extracted_data": test_extracted_data,
                "include_signature_placeholder": True,
                "bundle_name": f"Test_NHS_Bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        )
        
        if response.status_code == 200:
            # Save the bundle PDF
            filename = f"test_forms_bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join("data", "forms", filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Forms bundle PDF generated successfully")
            print(f"   Saved as: {filepath}")
            print(f"   File size: {len(response.content):,} bytes")
            print(f"   Contains 3 forms: discharge_summary, referral, risk_assessment")
        else:
            print(f"❌ Forms bundle PDF generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error testing forms bundle PDF: {e}")
    
    # Test 4: PDF from clinical note (complete pipeline)
    print("\n4. Testing complete pipeline (note → extract → PDF)...")
    try:
        clinical_note = {
            "raw_text": """
Patient: John Smith, DOB: 15/03/1965, NHS: 1234567890
Presenting complaint: Chest pain for 2 days, radiating to left arm
History: 58-year-old male with hypertension and hyperlipidemia
Examination: BP 140/90, HR 88, chest pain on palpation
Assessment: Acute myocardial infarction
Plan: Thrombolysis, cardiac monitoring, cardiology referral
Medications: Aspirin 75mg OD, Atorvastatin 40mg ON
Allergies: Penicillin
Discharge: Home with cardiology follow-up in 2 weeks
            """.strip(),
            "note_type": "general",
            "date_created": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{base_url}/forms/pdf/from-note",
            json={
                "note": clinical_note,
                "form_types": ["discharge_summary", "referral"],
                "include_signature_placeholder": True
            }
        )
        
        if response.status_code == 200:
            # Save the PDF
            filename = f"test_complete_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join("data", "forms", filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Complete pipeline PDF generated successfully")
            print(f"   Saved as: {filepath}")
            print(f"   File size: {len(response.content):,} bytes")
            print(f"   Pipeline: Clinical note → NLP extraction → Form filling → PDF generation")
        else:
            print(f"❌ Complete pipeline PDF generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error testing complete pipeline: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 PDF API Testing Complete!")
    print("\nGenerated PDFs saved in data/forms/ directory")
    print("You can open them to verify the NHS-styled formatting")


if __name__ == "__main__":
    test_pdf_endpoints()
