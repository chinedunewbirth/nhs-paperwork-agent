"""
Streamlit Dashboard for NHS Paperwork Automation Agent
Web interface for uploading notes, viewing extracted data, and downloading forms
"""

import streamlit as st
import requests
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Any
import streamlit.components.v1 as components
import time
# Real-time audio functionality implemented inline

# Configure page
st.set_page_config(
    page_title="NHS Paperwork Agent",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL (configurable)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def main():
    """Main Streamlit application"""
    
    # Title and header
    st.title("🩺 NHS Paperwork Automation Agent")
    st.markdown("*AI-powered automation for NHS clinical forms and documentation*")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select a page:",
            ["Process Clinical Notes", "Audio Transcription", "Real-time Recording", "Live Streaming", "Form Templates", "About"]
        )
        
        # Usage statistics (placeholder)
        st.header("Usage Statistics")
        st.metric("Forms Processed Today", "12", "↑ 3")
        st.metric("Processing Time (avg)", "45s", "↓ 5s")
        st.metric("Extraction Accuracy", "94%", "↑ 2%")
    
    # Main content area
    if page == "Process Clinical Notes":
        process_notes_page()
    elif page == "Audio Transcription":
        audio_transcription_page()
    elif page == "Real-time Recording":
        realtime_recording_page()
    elif page == "Live Streaming":
        live_streaming_page()
    elif page == "Form Templates":
        form_templates_page()
    elif page == "About":
        about_page()


def process_notes_page():
    """Page for processing clinical notes"""
    st.header("Process Clinical Notes")
    
    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Clinical Note Input")
        
        # Text input for clinical notes
        clinical_text = st.text_area(
            "Enter clinical note:",
            height=300,
            placeholder="Type or paste clinical notes here...\n\nExample:\nPatient: John Smith, DOB: 15/03/1965, NHS: 1234567890\nPresenting complaint: Chest pain for 2 days\nHistory: 65-year-old male with hypertension...",
            help="Enter the clinical note text that you want to process"
        )
        
        # Form selection
        st.subheader("Form Generation Options")
        form_options = st.multiselect(
            "Select forms to generate:",
            ["Discharge Summary", "Referral", "Risk Assessment"],
            default=["Discharge Summary"],
            help="Choose which NHS forms to auto-generate"
        )
        
        # Processing options
        col_a, col_b = st.columns(2)
        with col_a:
            auto_fill = st.checkbox("Auto-fill forms", value=True)
        with col_b:
            include_suggestions = st.checkbox("Include suggestions", value=True)
        
        # Process button
        process_button = st.button(
            "🔄 Process Clinical Note",
            type="primary",
            disabled=not clinical_text.strip(),
            help="Extract data and generate forms"
        )
    
    with col2:
        st.subheader("Quick Help")
        with st.expander("💡 Tips for better extraction"):
            st.markdown("""
            **Include these details for best results:**
            - Patient name and NHS number
            - Date of birth
            - Primary diagnosis
            - Current medications
            - Allergies
            - Examination findings
            - Follow-up plans
            
            **Example format:**
            ```
            Patient: Smith, John
            NHS: 1234567890
            DOB: 15/03/1965
            Diagnosis: Acute myocardial infarction
            Medications: Aspirin 75mg OD, Atorvastatin 40mg ON
            Allergies: Penicillin
            ```
            """)
    
    # Process the note when button is clicked
    if process_button and clinical_text.strip():
        with st.spinner("Processing clinical note..."):
            try:
                # Prepare request
                form_type_mapping = {
                    "Discharge Summary": "discharge_summary",
                    "Referral": "referral", 
                    "Risk Assessment": "risk_assessment"
                }
                
                selected_form_types = [form_type_mapping[ft] for ft in form_options]
                
                request_data = {
                    "note": {
                        "raw_text": clinical_text,
                        "note_type": "general",
                        "date_created": datetime.now().isoformat()
                    },
                    "form_types": selected_form_types,
                    "auto_fill_forms": auto_fill,
                    "include_suggestions": include_suggestions,
                    "priority": "Routine"
                }
                
                # Make API request
                response = requests.post(
                    f"{API_BASE_URL}/process",
                    json=request_data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    display_processing_results(result)
                else:
                    st.error(f"Processing failed: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
                st.info("Make sure the API server is running on http://localhost:8000")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")


def display_processing_results(result: Dict[str, Any]):
    """Display the results of clinical note processing"""
    
    st.success(f"✅ Processing completed in {result['processing_time']:.1f}s")
    
    # Display warnings and errors if any
    if result.get('warnings'):
        for warning in result['warnings']:
            st.warning(f"⚠️ {warning}")
    
    if result.get('errors'):
        for error in result['errors']:
            st.error(f"❌ {error}")
    
    # Extracted data section
    st.header("📊 Extracted Data")
    
    extracted_data = result['extracted_data']
    confidence = extracted_data.get('extraction_confidence', 0)
    
    # Confidence indicator
    conf_color = "green" if confidence > 0.8 else "orange" if confidence > 0.5 else "red"
    st.markdown(f"**Extraction Confidence:** :{conf_color}[{confidence:.1%}]")
    
    # Patient data
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Patient Information")
        patient_data = extracted_data['patient']
        
        for field, value in patient_data.items():
            if value:
                field_name = field.replace('_', ' ').title()
                st.text(f"{field_name}: {value}")
    
    with col2:
        st.subheader("🏥 Clinical Information")
        clinical_data = extracted_data['clinical']
        
        # Display key clinical fields
        key_fields = ['primary_diagnosis', 'presenting_complaint', 'examination_findings']
        for field in key_fields:
            value = clinical_data.get(field)
            if value:
                field_name = field.replace('_', ' ').title()
                st.text(f"{field_name}: {value}")
        
        # Display lists
        for field, values in clinical_data.items():
            if isinstance(values, list) and values:
                field_name = field.replace('_', ' ').title()
                st.text(f"{field_name}: {'; '.join(str(v) for v in values)}")
    
    # Missing fields and suggestions
    missing_fields = extracted_data.get('missing_fields', [])
    suggestions = extracted_data.get('suggested_questions', [])
    
    if missing_fields or suggestions:
        st.header("💭 Suggestions for Improvement")
        
        if missing_fields:
            st.subheader("Missing Information")
            for field in missing_fields:
                st.info(f"📝 Missing: {field.replace('_', ' ').title()}")
        
        if suggestions:
            st.subheader("Suggested Questions")
            for suggestion in suggestions:
                st.info(f"❓ {suggestion}")
    
    # Generated forms
    generated_forms = result.get('generated_forms', [])
    if generated_forms:
        st.header("📄 Generated Forms")
        
        # PDF generation options
        col1, col2 = st.columns([2, 1])
        with col1:
            include_signatures = st.checkbox("Include signature placeholders", value=True)
        with col2:
            if len(generated_forms) > 1:
                bundle_option = st.checkbox("Bundle all forms into one PDF", value=True)
            else:
                bundle_option = False
        
        # Bundle download button for multiple forms
        if len(generated_forms) > 1 and bundle_option:
            if st.button("📦 Download All Forms as Bundle PDF", type="primary"):
                download_forms_bundle(extracted_data, [form['form_type'] for form in generated_forms], include_signatures)
        
        # Individual form display and download
        for i, form in enumerate(generated_forms):
            with st.expander(f"Form {i+1}: {form['template_id']} - {form['form_type'].title()}", expanded=True):
                st.json(form['filled_data'])
                
                # Individual PDF download button
                if st.button(
                    f"📥 Download {form['form_type'].title()} PDF",
                    key=f"download_{i}",
                    help="Download this form as a PDF"
                ):
                    download_single_form_pdf(form['form_type'], extracted_data, include_signatures)


def audio_transcription_page():
    """Page for audio transcription"""
    st.header("🎙️ Audio Transcription")
    
    st.markdown("""
    Upload an audio recording of clinical notes to automatically transcribe them to text.
    Supported formats: WAV, MP3, M4A, FLAC
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['wav', 'mp3', 'm4a', 'flac'],
        help="Upload an audio recording of clinical notes"
    )
    
    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/wav')
        
        if st.button("🔄 Transcribe Audio", type="primary"):
            with st.spinner("Transcribing audio..."):
                try:
                    # Prepare file for upload
                    files = {"audio_file": uploaded_file}
                    
                    # Make API request
                    response = requests.post(
                        f"{API_BASE_URL}/transcribe",
                        files=files,
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("✅ Transcription completed!")
                        st.subheader("📝 Transcribed Text")
                        
                        transcribed_text = result['transcribed_text']
                        st.text_area(
                            "Transcribed clinical note:",
                            value=transcribed_text,
                            height=300,
                            help="You can copy this text to the clinical notes processor"
                        )
                        
                        # Option to process immediately
                        if st.button("🔄 Process This Transcription", type="secondary"):
                            st.session_state['transcribed_text'] = transcribed_text
                            st.experimental_rerun()
                    else:
                        st.error(f"Transcription failed: {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")


def realtime_recording_page():
    """Page for real-time audio recording and transcription"""
    st.header("🎙️ Real-time Audio Recording & Transcription")
    
    st.markdown("""
    **NEW: Enhanced Live Recording Feature**
    
    Record clinical notes using your microphone and get immediate transcription and NHS form generation.
    This feature uses OpenAI Whisper for high-accuracy medical transcription.
    """)
    
    # Check API connection first
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if health_response.status_code == 200:
            st.success("✅ Connected to NHS Paperwork Agent API")
        else:
            st.error("⚠️ API server responding with errors")
            return
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to API server")
        st.info("Please start the backend: `python start_api.py`")
        st.stop()
    
    # Main recording interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎤 Audio Recording")
        
        # Use Streamlit's built-in audio input
        st.markdown("**Record Clinical Notes:**")
        audio_input = st.audio_input("Click to record your clinical notes")
        
        if audio_input is not None:
            st.success("✅ Audio recorded successfully!")
            
            # Show audio player for review
            st.audio(audio_input)
            
            # Configuration for processing
            with st.expander("⚙️ Processing Options", expanded=True):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    auto_extract = st.checkbox("Auto-extract clinical data", value=True)
                    form_types = st.multiselect(
                        "Generate NHS forms:",
                        ["discharge_summary", "referral", "risk_assessment"],
                        default=["discharge_summary"]
                    )
                
                with col_b:
                    include_suggestions = st.checkbox("Include improvement suggestions", value=True)
                    transcribe_only = st.checkbox("Transcribe only (no form generation)", value=False)
            
            # Processing buttons
            col_x, col_y = st.columns(2)
            
            with col_x:
                if st.button("🔄 Transcribe Audio Only", type="secondary"):
                    transcribe_audio_only(audio_input)
            
            with col_y:
                if st.button("🚀 Transcribe & Generate Forms", type="primary"):
                    transcribe_and_generate_forms(audio_input, form_types, auto_extract, include_suggestions)
        
        # Alternative manual input
        st.markdown("---")
        st.subheader("🖊️ Alternative: Manual Text Input")
        
        manual_text = st.text_area(
            "Or type/paste clinical notes:",
            height=150,
            placeholder="Type clinical notes here for immediate processing..."
        )
        
        if manual_text.strip():
            if st.button("🔄 Process Manual Notes", type="secondary"):
                process_manual_clinical_notes(manual_text, ["discharge_summary"])
    
    with col2:
        st.subheader("📊 Recording Status")
        
        # Status metrics
        st.metric("Recording Method", "Browser Audio Input")
        st.metric("Transcription Engine", "OpenAI Whisper")
        st.metric("Processing", "Real-time")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("📋 View Available Forms"):
            show_form_templates_summary()
        
        if st.button("🏥 Check System Health"):
            show_system_health_summary()
        
        # Recording guidelines
        with st.expander("💡 Recording Best Practices", expanded=True):
            st.markdown("""
            **For optimal transcription:**
            
            🎯 **Speaking Tips:**
            - Speak clearly at moderate pace
            - Pause between sections
            - Use standard medical terms
            - Spell out important numbers/codes
            
            📋 **Content Guidelines:**
            - Start with patient identifiers
            - State primary diagnosis clearly
            - List medications with doses
            - Mention allergies and contraindications
            - Include follow-up instructions
            
            🔧 **Technical:**
            - Use quiet environment
            - Speak directly into microphone
            - Ensure stable internet connection
            - Keep recording under 5 minutes
            """)


def transcribe_audio_only(audio_file):
    """Transcribe audio without generating forms"""
    try:
        with st.spinner("🎙️ Transcribing audio..."):
            files = {"audio_file": audio_file}
            
            response = requests.post(
                f"{API_BASE_URL}/transcribe",
                files=files,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                transcribed_text = result['transcribed_text']
                
                st.success("✅ Audio transcribed successfully!")
                
                # Display transcription
                st.subheader("📝 Transcription Result")
                st.text_area(
                    "Transcribed Clinical Notes:",
                    value=transcribed_text,
                    height=200,
                    help="Review the transcription for accuracy"
                )
                
                # Option to process further
                if st.button("🔄 Generate NHS Forms from this Transcription", type="primary"):
                    process_transcribed_text_for_forms(transcribed_text, ["discharge_summary"])
                    
            else:
                st.error(f"❌ Transcription failed: {response.text}")
                
    except Exception as e:
        st.error(f"❌ Error during transcription: {str(e)}")


def transcribe_and_generate_forms(audio_file, form_types: list, auto_extract: bool, include_suggestions: bool):
    """Transcribe audio and immediately generate NHS forms"""
    try:
        with st.spinner("🎙️ Transcribing audio and generating forms..."):
            # Step 1: Transcribe audio
            files = {"audio_file": audio_file}
            
            transcribe_response = requests.post(
                f"{API_BASE_URL}/transcribe",
                files=files,
                timeout=120
            )
            
            if transcribe_response.status_code != 200:
                st.error(f"❌ Transcription failed: {transcribe_response.text}")
                return
            
            transcription_result = transcribe_response.json()
            transcribed_text = transcription_result['transcribed_text']
            
            st.success("✅ Audio transcribed successfully!")
            
            # Display transcription
            st.subheader("📝 Transcription")
            st.text_area(
                "Transcribed Text:",
                value=transcribed_text,
                height=150,
                disabled=True
            )
            
            # Step 2: Process for NHS forms if requested
            if auto_extract and transcribed_text.strip():
                st.info("🔄 Processing transcription for NHS forms...")
                process_transcribed_text_for_forms(transcribed_text, form_types, include_suggestions)
                
    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")


def process_transcribed_text_for_forms(text: str, form_types: list, include_suggestions: bool = True):
    """Process transcribed text to generate NHS forms"""
    try:
        with st.spinner("🔄 Extracting clinical data and generating NHS forms..."):
            request_data = {
                "note": {
                    "raw_text": text,
                    "note_type": "audio_transcription",
                    "date_created": datetime.now().isoformat()
                },
                "form_types": form_types,
                "auto_fill_forms": True,
                "include_suggestions": include_suggestions,
                "priority": "Routine"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/process",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                display_realtime_processing_results(result)
            else:
                st.error(f"❌ Processing failed: {response.text}")
                
    except Exception as e:
        st.error(f"❌ Error processing transcription: {str(e)}")


def process_manual_clinical_notes(text: str, form_types: list):
    """Process manually entered clinical notes"""
    process_transcribed_text_for_forms(text, form_types)


def display_realtime_processing_results(result: Dict[str, Any]):
    """Display results from real-time audio processing"""
    st.success(f"✅ Clinical notes processed in {result['processing_time']:.1f} seconds")
    
    # Show warnings and errors
    if result.get('warnings'):
        for warning in result['warnings']:
            st.warning(f"⚠️ {warning}")
    
    if result.get('errors'):
        for error in result['errors']:
            st.error(f"❌ {error}")
    
    # Extracted data display
    st.header("📊 Extracted Clinical Data from Voice Recording")
    
    extracted_data = result['extracted_data']
    confidence = extracted_data.get('extraction_confidence', 0)
    
    # Confidence indicator
    conf_color = "green" if confidence > 0.8 else "orange" if confidence > 0.5 else "red"
    st.markdown(f"**Data Extraction Confidence:** :{conf_color}[{confidence:.1%}]")
    
    # Tabbed display for better organization
    tab1, tab2, tab3 = st.tabs(["👤 Patient Data", "🏥 Clinical Info", "📄 Generated Forms"])
    
    with tab1:
        patient_data = extracted_data['patient']
        if any(patient_data.values()):
            for field, value in patient_data.items():
                if value:
                    st.text(f"**{field.replace('_', ' ').title()}:** {value}")
        else:
            st.info("No patient information extracted. Please mention patient details clearly in your recording.")
    
    with tab2:
        clinical_data = extracted_data['clinical']
        if any(clinical_data.values()):
            # Key clinical fields
            key_fields = ['primary_diagnosis', 'presenting_complaint', 'examination_findings', 'treatment_given']
            for field in key_fields:
                value = clinical_data.get(field)
                if value:
                    st.text(f"**{field.replace('_', ' ').title()}:** {value}")
            
            # Lists (medications, allergies, etc.)
            for field, values in clinical_data.items():
                if isinstance(values, list) and values:
                    st.text(f"**{field.replace('_', ' ').title()}:** {'; '.join(str(v) for v in values)}")
        else:
            st.info("No clinical information extracted. Please include diagnosis, medications, and findings in your recording.")
    
    with tab3:
        generated_forms = result.get('generated_forms', [])
        if generated_forms:
            st.success(f"✅ Generated {len(generated_forms)} NHS form(s) from voice recording")
            
            for i, form in enumerate(generated_forms):
                st.subheader(f"📄 {form['form_type'].replace('_', ' ').title()}")
                
                with st.expander(f"View Form Data", expanded=False):
                    st.json(form['filled_data'])
                
                # PDF download
                if st.button(f"📥 Download {form['form_type'].title()} PDF", key=f"voice_dl_{i}"):
                    download_form_pdf_from_voice(form['form_type'], extracted_data)
                
                st.markdown("---")
        else:
            st.info("No NHS forms were generated. Please ensure your recording includes sufficient clinical information.")
    
    # Improvement suggestions
    missing_fields = extracted_data.get('missing_fields', [])
    suggestions = extracted_data.get('suggested_questions', [])
    
    if missing_fields or suggestions:
        st.header("💡 Suggestions for Better Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if missing_fields:
                st.subheader("Missing Information")
                for field in missing_fields:
                    st.info(f"📝 **Missing:** {field.replace('_', ' ').title()}")
        
        with col2:
            if suggestions:
                st.subheader("Recommended Additions")
                for i, suggestion in enumerate(suggestions[:3]):  # Limit to 3 suggestions
                    st.info(f"❓ {suggestion}")


def download_form_pdf_from_voice(form_type: str, extracted_data: Dict[str, Any]):
    """Download PDF generated from voice recording"""
    try:
        with st.spinner(f"🔄 Generating {form_type.replace('_', ' ').title()} PDF from voice recording..."):
            response = requests.post(
                f"{API_BASE_URL}/forms/pdf",
                json={
                    "form_type": form_type,
                    "extracted_data": extracted_data,
                    "include_signature_placeholder": True
                },
                timeout=60
            )
            
            if response.status_code == 200:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"voice_{form_type}_{timestamp}.pdf"
                
                st.download_button(
                    label=f"📥 Download {form_type.replace('_', ' ').title()} PDF",
                    data=response.content,
                    file_name=filename,
                    mime="application/pdf",
                    key=f"voice_pdf_{form_type}_{timestamp}"
                )
                
                st.success(f"✅ PDF generated from voice recording!")
            else:
                st.error(f"❌ PDF generation failed: {response.text}")
                
    except Exception as e:
        st.error(f"❌ Error generating PDF: {str(e)}")


def show_form_templates_summary():
    """Show a summary of available form templates"""
    try:
        response = requests.get(f"{API_BASE_URL}/templates", timeout=10)
        
        if response.status_code == 200:
            templates_data = response.json()
            templates = templates_data['templates']
            
            st.subheader("📋 Available NHS Form Templates")
            
            for form_type, template_info in templates.items():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.text(f"📄 {template_info['form_name']}")
                with col2:
                    st.text(f"{template_info['field_count']} fields")
        else:
            st.error("Failed to load form templates")
            
    except Exception as e:
        st.error(f"Error loading templates: {str(e)}")


def show_system_health_summary():
    """Show system health summary"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            
            st.subheader("🏥 System Status")
            
            services = health_data['services']
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("NLP Service", "✅ Active" if services['nlp'] else "❌ Inactive")
                st.metric("Form Templates", "✅ Active" if services['form_templates'] else "❌ Inactive")
            
            with col2:
                st.metric("Form Filler", "✅ Active" if services['form_filler'] else "❌ Inactive")
                st.metric("PDF Generator", "✅ Active" if services['pdf_generator'] else "❌ Inactive")
            
            if all(services.values()):
                st.success("✅ All services operational")
            else:
                st.warning("⚠️ Some services may not be available")
        else:
            st.error("❌ System health check failed")
            
    except Exception as e:
        st.error(f"❌ Error checking system health: {str(e)}")


def live_streaming_page():
    """Page for live streaming audio with real-time transcription via WebSocket"""
    st.header("🎵 Live Audio Streaming & Real-time Transcription")
    
    st.markdown("""
    **BETA: Live Streaming Clinical Recording**
    
    Experience true real-time audio transcription with live streaming to the NHS Paperwork Agent.
    Features live audio visualization, instant transcription updates, and seamless form generation.
    """)
    
    # Check API and WebSocket support
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if health_response.status_code != 200:
            st.error("⚠️ API server not responding properly")
            return
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to API server")
        st.info("Please start the backend: `python start_api.py`")
        st.stop()
    
    # WebSocket status check
    st.info("🔗 This page uses WebSocket for real-time communication with the server")
    
    # Main interface layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("🎙️ Live Audio Recorder")
        
        # Load the HTML component
        try:
            with open("C:/warp_project_dir/nhs-paperwork-agent/src/dashboard/realtime_audio_component.html", "r") as f:
                html_content = f.read()
            
            # Embed the HTML component
            components.html(html_content, height=800, scrolling=True)
            
        except FileNotFoundError:
            st.error("❌ Real-time audio component not found")
            st.info("Using fallback interface...")
            
            # Fallback interface
            render_fallback_realtime_interface()
    
    with col2:
        st.subheader("📊 Live Session Monitor")
        
        # Session management
        if st.button("🔄 Refresh Session Status"):
            check_realtime_session_status()
        
        # Live transcription polling
        if "live_session_id" in st.session_state:
            st.markdown("**Active Session:**")
            st.code(st.session_state.live_session_id)
            
            # Auto-refresh transcription updates
            if st.button("📝 Get Latest Transcription"):
                get_live_transcription_updates(st.session_state.live_session_id)
        
        # Form generation from live transcription
        st.subheader("⚡ Quick Actions")
        
        if st.button("📋 Generate Forms from Live Session"):
            if "live_session_id" in st.session_state:
                generate_forms_from_live_session(st.session_state.live_session_id)
            else:
                st.warning("No active live session found")
        
        # Settings
        with st.expander("⚙️ Live Recording Settings", expanded=True):
            transcription_interval = st.slider(
                "Transcription Interval (seconds):",
                min_value=1.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                help="How often to transcribe audio chunks"
            )
            
            audio_quality = st.selectbox(
                "Audio Quality:",
                ["Standard (16kHz)", "High (44kHz)"],
                index=0,
                help="Higher quality uses more bandwidth"
            )
            
            enable_visualization = st.checkbox(
                "Enable Audio Visualization",
                value=True,
                help="Show live audio level visualization"
            )
        
        # Guidelines and tips
        with st.expander("💡 Live Recording Tips", expanded=True):
            st.markdown("""
            **🎯 For optimal live transcription:**
            
            **🔊 Audio Setup:**
            - Use headset or external microphone
            - Minimize background noise
            - Speak 6-12 inches from microphone
            - Test audio levels before recording
            
            **🗣️ Speaking Guidelines:**
            - Speak at steady, moderate pace
            - Use clear pronunciation
            - Pause briefly between sentences
            - Repeat important information if needed
            
            **🏥 Clinical Content:**
            - Start with "Patient [Name], NHS number [Number]"
            - State diagnosis clearly
            - List medications with exact dosages
            - Mention allergies and contraindications
            - Include discharge or follow-up plans
            
            **💻 Technical Notes:**
            - Keep browser tab active during recording
            - Ensure stable internet connection
            - Use Chrome or Firefox for best compatibility
            - Allow microphone permissions when prompted
            """)


def render_fallback_realtime_interface():
    """Fallback interface when HTML component isn't available"""
    st.markdown("**Fallback Real-time Interface**")
    
    # Session management
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🆕 Create Session", type="primary"):
            create_realtime_session()
    
    with col2:
        if st.button("▶️ Start Recording"):
            if "live_session_id" in st.session_state:
                start_realtime_recording(st.session_state.live_session_id)
            else:
                st.warning("Create a session first")
    
    with col3:
        if st.button("⏹️ Stop Recording"):
            if "live_session_id" in st.session_state:
                stop_realtime_recording(st.session_state.live_session_id)
            else:
                st.warning("No active session")
    
    # Display current session info
    if "live_session_id" in st.session_state:
        st.info(f"📡 Active Session: {st.session_state.live_session_id}")
        
        # Real-time status updates
        placeholder = st.empty()
        
        # Check for updates every few seconds
        if st.button("🔄 Check for Updates"):
            with placeholder.container():
                get_live_transcription_updates(st.session_state.live_session_id)


def create_realtime_session():
    """Create a new real-time audio session"""
    try:
        response = requests.post(f"{API_BASE_URL}/audio/session", timeout=10)
        
        if response.status_code == 200:
            session_data = response.json()
            st.session_state.live_session_id = session_data["session_id"]
            st.success(f"✅ Session created: {session_data['session_id']}")
        else:
            st.error(f"❌ Failed to create session: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error creating session: {str(e)}")


def start_realtime_recording(session_id: str):
    """Start real-time recording for session"""
    try:
        response = requests.post(f"{API_BASE_URL}/audio/session/{session_id}/start", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ Recording started: {result['status']}")
        else:
            st.error(f"❌ Failed to start recording: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error starting recording: {str(e)}")


def stop_realtime_recording(session_id: str):
    """Stop real-time recording for session"""
    try:
        response = requests.post(f"{API_BASE_URL}/audio/session/{session_id}/stop", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ Recording stopped: {result['status']}")
            
            # Display final transcription if available
            if "final_transcription" in result and result["final_transcription"]:
                st.subheader("📝 Final Transcription")
                st.text_area(
                    "Complete transcription:",
                    value=result["final_transcription"],
                    height=200
                )
        else:
            st.error(f"❌ Failed to stop recording: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error stopping recording: {str(e)}")


def check_realtime_session_status():
    """Check status of current real-time session"""
    if "live_session_id" not in st.session_state:
        st.warning("No active session to check")
        return
    
    session_id = st.session_state.live_session_id
    
    try:
        response = requests.get(f"{API_BASE_URL}/audio/session/{session_id}/status", timeout=10)
        
        if response.status_code == 200:
            status_data = response.json()
            
            st.subheader("📊 Session Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Session ID", status_data.get("session_id", "Unknown"))
                st.metric("Recording", "🔴 Active" if status_data.get("is_recording") else "⚫ Inactive")
            
            with col2:
                duration = status_data.get("recording_duration", 0)
                st.metric("Duration", f"{duration:.1f}s")
                st.metric("Segments", status_data.get("segment_count", 0))
            
            # Show current transcription
            current_transcription = status_data.get("full_transcription", "")
            if current_transcription:
                st.subheader("📝 Current Transcription")
                st.text_area(
                    "Live transcription:",
                    value=current_transcription,
                    height=150,
                    disabled=True
                )
        else:
            st.error(f"❌ Failed to get session status: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error checking session status: {str(e)}")


def get_live_transcription_updates(session_id: str):
    """Get live transcription updates for session"""
    try:
        response = requests.get(f"{API_BASE_URL}/audio/session/{session_id}/transcription", timeout=10)
        
        if response.status_code == 200:
            transcription_data = response.json()
            
            # Display new segments
            new_segments = transcription_data.get("new_segments", [])
            if new_segments:
                st.subheader("🆕 New Transcription Segments")
                
                for i, segment in enumerate(new_segments):
                    timestamp = datetime.fromisoformat(segment["timestamp"].replace('Z', '+00:00'))
                    formatted_time = timestamp.strftime("%H:%M:%S")
                    confidence = segment.get("confidence", 0.9)
                    
                    st.markdown(f"**{formatted_time}** ({confidence:.1%} confidence)")
                    st.markdown(f"➤ _{segment['text']}_")
                    st.markdown("---")
            
            # Display full transcription
            full_transcription = transcription_data.get("full_transcription", "")
            if full_transcription:
                st.subheader("📄 Complete Transcription")
                st.text_area(
                    "Full live transcription:",
                    value=full_transcription,
                    height=200,
                    disabled=True
                )
        else:
            st.error(f"❌ Failed to get transcription updates: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error getting transcription updates: {str(e)}")


def generate_forms_from_live_session(session_id: str):
    """Generate NHS forms from live session transcription"""
    try:
        # First get the final transcription
        status_response = requests.get(f"{API_BASE_URL}/audio/session/{session_id}/status", timeout=10)
        
        if status_response.status_code != 200:
            st.error("❌ Failed to get session transcription")
            return
        
        status_data = status_response.json()
        transcription = status_data.get("full_transcription", "")
        
        if not transcription.strip():
            st.warning("⚠️ No transcription available to process")
            return
        
        # Process the transcription for forms
        st.info("🔄 Processing live transcription for NHS forms...")
        
        request_data = {
            "note": {
                "raw_text": transcription,
                "note_type": "live_audio_stream",
                "date_created": datetime.now().isoformat()
            },
            "form_types": ["discharge_summary"],
            "auto_fill_forms": True,
            "include_suggestions": True,
            "priority": "Routine"
        }
        
        process_response = requests.post(
            f"{API_BASE_URL}/process",
            json=request_data,
            timeout=60
        )
        
        if process_response.status_code == 200:
            result = process_response.json()
            st.success("✅ Forms generated from live session!")
            display_realtime_processing_results(result)
        else:
            st.error(f"❌ Form processing failed: {process_response.text}")
            
    except Exception as e:
        st.error(f"❌ Error generating forms from live session: {str(e)}")


def form_templates_page():
    """Page for viewing form templates"""
    st.header("📋 Form Templates")
    
    st.markdown("Available NHS form templates that can be auto-filled:")
    
    try:
        # Get templates from API
        response = requests.get(f"{API_BASE_URL}/templates", timeout=10)
        
        if response.status_code == 200:
            templates_data = response.json()
            templates = templates_data['templates']
            
            for form_type, template_info in templates.items():
                with st.expander(f"📄 {template_info['form_name']}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.text(f"Form ID: {template_info['form_id']}")
                        st.text(f"Type: {template_info['form_type']}")
                        st.text(f"Fields: {template_info['field_count']}")
                    
                    with col2:
                        if st.button(f"View Details", key=f"view_{form_type}"):
                            # Get detailed template
                            detail_response = requests.get(
                                f"{API_BASE_URL}/templates/{form_type}",
                                timeout=10
                            )
                            if detail_response.status_code == 200:
                                template_detail = detail_response.json()
                                st.json(template_detail)
        else:
            st.error(f"Failed to load templates: {response.text}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        st.info("Make sure the API server is running on http://localhost:8000")


def about_page():
    """About page with project information"""
    st.header("🩺 About NHS Paperwork Automation Agent")
    
    st.markdown("""
    ## Overview
    
    The NHS Paperwork Automation Agent is an AI-powered solution designed to reduce administrative burden on healthcare professionals by automating the creation of standard NHS forms.
    
    ## Key Features
    
    ### 🎯 **Intelligent Data Extraction**
    - Extracts structured data from unstructured clinical notes
    - Identifies patient demographics, diagnoses, medications, and clinical findings
    - Uses advanced NLP with OpenAI GPT-4 for high accuracy
    
    ### 📋 **Auto-Fill NHS Forms**
    - Supports standard NHS forms: Discharge Summaries, Referrals, Risk Assessments
    - Automatically maps extracted data to appropriate form fields
    - Maintains NHS formatting and compliance standards
    
    ### 🎙️ **Speech-to-Text**
    - Transcribe audio recordings of clinical notes
    - Powered by OpenAI Whisper for medical terminology accuracy
    - Supports multiple audio formats
    
    ### 🔒 **NHS Compliant Security**
    - End-to-end encryption for sensitive data
    - GDPR and NHS Data Security standards compliance
    - Audit logging for all operations
    - Configurable data retention policies
    
    ## Technical Architecture
    
    - **Frontend**: Streamlit web interface
    - **Backend**: FastAPI with Python
    - **AI/NLP**: OpenAI GPT-4 + Whisper
    - **Database**: SQLite (development) / PostgreSQL (production)
    - **Deployment**: Docker containers on AWS
    
    ## Target Users
    
    - **NHS Trusts**: Enterprise deployment for hospitals
    - **Private Clinics**: Professional subscription plans
    - **Individual Clinicians**: Freelance nurses, locums, GPs
    
    ## Current Status: MVP Prototype
    
    This is the initial prototype focusing on core functionality:
    - ✅ Clinical data extraction
    - ✅ Form auto-filling
    - ✅ Speech transcription
    - ✅ PDF generation with NHS styling
    - ✅ Single form and bundle PDF downloads
    - 🔄 Database persistence (in progress)
    
    ---
    
    **For support or feedback, please contact the development team.**
    """)
    
    # System status
    with st.expander("🔧 System Status", expanded=False):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                st.json(health_data)
            else:
                st.error("API health check failed")
        except:
            st.error("Cannot connect to API server")


def download_single_form_pdf(form_type: str, extracted_data: Dict[str, Any], include_signatures: bool = True):
    """Download a single form as PDF"""
    try:
        with st.spinner(f"Generating {form_type.title()} PDF..."):
            response = requests.post(
                f"{API_BASE_URL}/forms/pdf",
                json={
                    "form_type": form_type,
                    "extracted_data": extracted_data,
                    "include_signature_placeholder": include_signatures
                },
                timeout=60
            )
            
            if response.status_code == 200:
                # Save PDF temporarily for download
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                # Provide download button
                with open(tmp_path, "rb") as file:
                    st.download_button(
                        label=f"📥 Download {form_type.title()} PDF",
                        data=file.read(),
                        file_name=f"{form_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        key=f"download_pdf_{form_type}_{datetime.now().timestamp()}"
                    )
                
                # Clean up
                os.unlink(tmp_path)
                st.success(f"✅ {form_type.title()} PDF generated successfully!")
            else:
                st.error(f"Failed to generate PDF: {response.text}")
                
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")


def download_forms_bundle(extracted_data: Dict[str, Any], form_types: list, include_signatures: bool = True):
    """Download multiple forms as a bundle PDF"""
    try:
        with st.spinner("Generating forms bundle PDF..."):
            bundle_name = f"NHS_Forms_Bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            response = requests.post(
                f"{API_BASE_URL}/forms/pdf/bundle",
                json={
                    "form_types": form_types,
                    "extracted_data": extracted_data,
                    "include_signature_placeholder": include_signatures,
                    "bundle_name": bundle_name
                },
                timeout=90
            )
            
            if response.status_code == 200:
                # Save PDF temporarily for download
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                # Provide download button
                with open(tmp_path, "rb") as file:
                    st.download_button(
                        label=f"📦 Download Bundle PDF ({len(form_types)} forms)",
                        data=file.read(),
                        file_name=f"{bundle_name}.pdf",
                        mime="application/pdf",
                        key=f"download_bundle_{datetime.now().timestamp()}"
                    )
                
                # Clean up
                os.unlink(tmp_path)
                st.success(f"✅ Bundle PDF with {len(form_types)} forms generated successfully!")
            else:
                st.error(f"Failed to generate bundle PDF: {response.text}")
                
    except Exception as e:
        st.error(f"Error generating bundle PDF: {str(e)}")


def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None):
    """Helper function to make API requests with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=60)
            else:
                response = requests.post(url, json=data, timeout=60)
        
        return response
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to API server. Make sure it's running.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


if __name__ == "__main__":
    main()
