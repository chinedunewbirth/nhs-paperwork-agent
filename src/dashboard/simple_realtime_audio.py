"""
Simplified Real-time Audio Recording for Streamlit Dashboard
Uses streamlit-webrtc for browser-based audio capture
"""

import streamlit as st
import requests
import json
import io
import tempfile
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
import soundfile as sf
from queue import Queue
import wave

# Session state initialization
def init_session_state():
    """Initialize session state variables for audio recording"""
    if 'recording_active' not in st.session_state:
        st.session_state.recording_active = False
    if 'transcription_text' not in st.session_state:
        st.session_state.transcription_text = ""
    if 'audio_chunks' not in st.session_state:
        st.session_state.audio_chunks = []
    if 'recording_start_time' not in st.session_state:
        st.session_state.recording_start_time = None


def simple_realtime_audio_page():
    """Streamlit page for simplified real-time audio recording"""
    st.header("🎙️ Real-time Audio Recording & Transcription")
    
    st.markdown("""
    **Enhanced Live Recording Feature**
    
    This page provides real-time audio recording with live transcription capabilities.
    Record clinical notes by speaking into your microphone and see transcription appear in real-time.
    """)
    
    init_session_state()
    
    # Check API connection
    api_url = 'http://localhost:8000'
    
    # Connection status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🔗 System Status")
    with col2:
        if st.button("🔄 Check Connection"):
            st.rerun()
    
    try:
        health_response = requests.get(f"{api_url}/health", timeout=3)
        if health_response.status_code == 200:
            st.success("✅ Connected to NHS Paperwork Agent API")
        else:
            st.error("⚠️ API server responding with errors")
            return
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to API server")
        st.info("Please start the backend: `python start_api.py`")
        return
    
    # Recording configuration
    with st.expander("⚙️ Recording Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            transcription_interval = st.slider(
                "Transcription Interval (seconds)",
                min_value=2,
                max_value=10,
                value=5,
                help="How often to send audio for transcription"
            )
            
            auto_extract = st.checkbox(
                "Auto-extract clinical data",
                value=True,
                help="Automatically extract structured data from transcription"
            )
        
        with col2:
            audio_quality = st.selectbox(
                "Audio Quality",
                ["Standard (16kHz)", "High (44kHz)"],
                index=0,
                help="Audio sample rate for recording"
            )
            
            form_types = st.multiselect(
                "Auto-generate forms",
                ["discharge_summary", "referral", "risk_assessment"],
                default=["discharge_summary"],
                help="NHS forms to auto-generate from transcription"
            )
    
    # Main recording interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎤 Audio Recording Controls")
        
        # Simple recording interface using Streamlit's audio input
        st.markdown("**Browser-based Audio Recording**")
        
        # Audio input widget (requires microphone permissions)
        audio_input = st.audio_input("Record your clinical notes:")
        
        if audio_input is not None:
            st.success("✅ Audio recorded successfully!")
            
            # Show audio player
            st.audio(audio_input)
            
            # Transcription button
            if st.button("🔄 Transcribe & Process Audio", type="primary"):
                transcribe_and_process_audio(audio_input, form_types, auto_extract)
        
        # Alternative: Manual text input for testing
        st.markdown("---")
        st.subheader("🖊️ Alternative: Manual Input")
        
        manual_text = st.text_area(
            "Or type clinical notes manually:",
            height=150,
            placeholder="Enter clinical notes here for immediate processing..."
        )
        
        if manual_text.strip() and st.button("🔄 Process Manual Notes", type="secondary"):
            process_manual_notes(manual_text, form_types)
    
    with col2:
        st.subheader("📊 Recording Status")
        
        # Status indicators
        st.metric("Recording Method", "Browser Audio Input")
        st.metric("Transcription Engine", "OpenAI Whisper")
        
        # Recording tips
        with st.expander("💡 Recording Tips", expanded=True):
            st.markdown("""
            **For optimal results:**
            
            🎯 **Speaking Guidelines:**
            - Speak clearly and at moderate pace
            - Pause between sentences
            - Use standard medical terminology
            - Include patient identifiers clearly
            
            📋 **Clinical Information:**
            - State patient name and NHS number
            - Mention primary diagnosis
            - List current medications with doses
            - Include allergies and contraindications
            - Specify follow-up requirements
            
            🔧 **Technical Tips:**
            - Ensure microphone permissions are enabled
            - Use a quiet environment
            - Speak directly into microphone
            - Keep browser tab active during recording
            """)
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("📋 View Form Templates"):
            show_available_templates()
        
        if st.button("📊 System Health Check"):
            show_system_health()


def transcribe_and_process_audio(audio_file, form_types: list, auto_extract: bool = True):
    """Transcribe audio and optionally process for NHS forms"""
    
    try:
        with st.spinner("🎙️ Transcribing audio..."):
            # Prepare file for API
            files = {"audio_file": audio_file}
            
            # Transcribe using existing API endpoint
            api_url = 'http://localhost:8000'
            response = requests.post(
                f"{api_url}/transcribe",
                files=files,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                transcribed_text = result['transcribed_text']
                
                st.success("✅ Audio transcribed successfully!")
                
                # Display transcription
                st.subheader("📝 Transcribed Text")
                st.text_area(
                    "Transcription Result:",
                    value=transcribed_text,
                    height=200,
                    help="Review and edit if needed before processing"
                )
                
                # Auto-process if requested
                if auto_extract and transcribed_text.strip():
                    st.info("🔄 Auto-processing transcription for NHS forms...")
                    process_transcribed_text(transcribed_text, form_types)
                else:
                    # Manual processing option
                    if st.button("🔄 Process Transcription for NHS Forms", type="primary"):
                        process_transcribed_text(transcribed_text, form_types)
                        
            else:
                st.error(f"❌ Transcription failed: {response.text}")
                
    except Exception as e:
        st.error(f"❌ Error during transcription: {str(e)}")


def process_manual_notes(text: str, form_types: list):
    """Process manually entered clinical notes"""
    process_transcribed_text(text, form_types)


def process_transcribed_text(text: str, form_types: list):
    """Process transcribed or manual text to generate NHS forms"""
    
    if not text.strip():
        st.warning("⚠️ No text to process")
        return
    
    try:
        with st.spinner("🔄 Processing clinical notes..."):
            # Prepare request
            request_data = {
                "note": {
                    "raw_text": text,
                    "note_type": "audio_transcription",
                    "date_created": datetime.now().isoformat()
                },
                "form_types": form_types,
                "auto_fill_forms": True,
                "include_suggestions": True,
                "priority": "Routine"
            }
            
            # Make API request
            api_url = 'http://localhost:8000'
            response = requests.post(
                f"{api_url}/process",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                display_processing_results_realtime(result)
            else:
                st.error(f"❌ Processing failed: {response.text}")
                
    except Exception as e:
        st.error(f"❌ Error processing text: {str(e)}")


def display_processing_results_realtime(result: Dict[str, Any]):
    """Display processing results from real-time transcription"""
    
    st.success(f"✅ Clinical notes processed in {result['processing_time']:.1f} seconds")
    
    # Show any warnings or errors
    if result.get('warnings'):
        for warning in result['warnings']:
            st.warning(f"⚠️ {warning}")
    
    if result.get('errors'):
        for error in result['errors']:
            st.error(f"❌ {error}")
    
    # Extracted data display
    st.header("📊 Extracted Clinical Data")
    
    extracted_data = result['extracted_data']
    confidence = extracted_data.get('extraction_confidence', 0)
    
    # Confidence meter
    st.metric(
        "Extraction Confidence",
        f"{confidence:.1%}",
        delta=f"{'High' if confidence > 0.8 else 'Medium' if confidence > 0.6 else 'Low'} confidence"
    )
    
    # Data display
    tab1, tab2, tab3 = st.tabs(["👤 Patient Info", "🏥 Clinical Data", "📋 Generated Forms"])
    
    with tab1:
        patient_data = extracted_data['patient']
        if any(patient_data.values()):
            for field, value in patient_data.items():
                if value:
                    st.text(f"**{field.replace('_', ' ').title()}:** {value}")
        else:
            st.info("No patient information extracted. Please ensure patient details are mentioned clearly.")
    
    with tab2:
        clinical_data = extracted_data['clinical']
        if any(clinical_data.values()):
            # Key clinical information
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
            st.info("No clinical information extracted. Please include diagnosis, medications, and clinical findings.")
    
    with tab3:
        generated_forms = result.get('generated_forms', [])
        if generated_forms:
            st.success(f"✅ Generated {len(generated_forms)} NHS form(s)")
            
            # Form download options
            for i, form in enumerate(generated_forms):
                st.subheader(f"📄 {form['form_type'].replace('_', ' ').title()}")
                
                with st.expander(f"View {form['form_type'].title()} Data", expanded=False):
                    st.json(form['filled_data'])
                
                # PDF download
                if st.button(f"📥 Download {form['form_type'].title()} PDF", key=f"dl_{i}"):
                    download_form_pdf_realtime(form['form_type'], extracted_data)
                
                st.markdown("---")
        else:
            st.info("No forms generated. Please check the extracted data and try again.")
    
    # Suggestions for improvement
    missing_fields = extracted_data.get('missing_fields', [])
    suggestions = extracted_data.get('suggested_questions', [])
    
    if missing_fields or suggestions:
        st.header("💡 Suggestions for Improvement")
        
        if missing_fields:
            st.subheader("Missing Information")
            for field in missing_fields:
                st.info(f"📝 **Missing:** {field.replace('_', ' ').title()}")
        
        if suggestions:
            st.subheader("Recommended Questions")
            for i, suggestion in enumerate(suggestions):
                st.info(f"❓ **Question {i+1}:** {suggestion}")


def download_form_pdf_realtime(form_type: str, extracted_data: Dict[str, Any]):
    """Generate and download PDF from real-time transcription"""
    
    try:
        with st.spinner(f"🔄 Generating {form_type.replace('_', ' ').title()} PDF..."):
            api_url = 'http://localhost:8000'
            
            response = requests.post(
                f"{api_url}/forms/pdf",
                json={
                    "form_type": form_type,
                    "extracted_data": extracted_data,
                    "include_signature_placeholder": True
                },
                timeout=60
            )
            
            if response.status_code == 200:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"realtime_{form_type}_{timestamp}.pdf"
                
                st.download_button(
                    label=f"📥 Download {form_type.replace('_', ' ').title()} PDF",
                    data=response.content,
                    file_name=filename,
                    mime="application/pdf",
                    key=f"pdf_download_{form_type}_{timestamp}"
                )
                
                st.success(f"✅ PDF generated successfully!")
                
            else:
                st.error(f"❌ PDF generation failed: {response.text}")
                
    except Exception as e:
        st.error(f"❌ Error generating PDF: {str(e)}")


def show_available_templates():
    """Display available form templates"""
    try:
        api_url = 'http://localhost:8000'
        response = requests.get(f"{api_url}/templates", timeout=10)
        
        if response.status_code == 200:
            templates_data = response.json()
            templates = templates_data['templates']
            
            st.subheader("📋 Available NHS Form Templates")
            
            for form_type, template_info in templates.items():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.text(f"📄 {template_info['form_name']}")
                
                with col2:
                    st.text(f"Fields: {template_info['field_count']}")
                
                with col3:
                    st.text(f"Type: {template_info['form_type']}")
        else:
            st.error("Failed to load templates")
            
    except Exception as e:
        st.error(f"Error loading templates: {str(e)}")


def show_system_health():
    """Display system health information"""
    try:
        api_url = 'http://localhost:8000'
        response = requests.get(f"{api_url}/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            
            st.subheader("🏥 System Health Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("API Status", health_data['status'].title())
                st.metric("NLP Service", "✅ Active" if health_data['services']['nlp'] else "❌ Inactive")
            
            with col2:
                st.metric("Form Templates", "✅ Active" if health_data['services']['form_templates'] else "❌ Inactive")
                st.metric("PDF Generator", "✅ Active" if health_data['services']['pdf_generator'] else "❌ Inactive")
            
            st.json(health_data)
        else:
            st.error("Health check failed")
            
    except Exception as e:
        st.error(f"Error checking system health: {str(e)}")


# JavaScript-based audio recorder component
def audio_recorder_component():
    """HTML/JavaScript component for audio recording"""
    
    html_code = """
    <div style="padding: 20px; border: 2px solid #4CAF50; border-radius: 10px; background-color: #f9f9f9;">
        <h3 style="text-align: center; color: #333;">🎙️ Voice Recorder</h3>
        
        <div style="text-align: center; margin: 20px 0;">
            <button id="startBtn" onclick="startRecording()" 
                    style="background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin: 5px; cursor: pointer;">
                🔴 Start Recording
            </button>
            <button id="stopBtn" onclick="stopRecording()" disabled
                    style="background: #f44336; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin: 5px; cursor: pointer;">
                ⏹️ Stop Recording
            </button>
        </div>
        
        <div id="status" style="text-align: center; margin: 10px 0; font-weight: bold;">
            Ready to record
        </div>
        
        <div style="margin: 20px 0;">
            <canvas id="visualizer" width="400" height="100" 
                    style="width: 100%; height: 100px; background: #333; border-radius: 5px;"></canvas>
        </div>
        
        <div id="transcription" style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0; min-height: 100px; border-left: 4px solid #2196F3;">
            <em>Live transcription will appear here...</em>
        </div>
    </div>
    
    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;
        let audioContext;
        let analyser;
        let microphone;
        let dataArray;
        
        function updateStatus(message, color = '#333') {
            document.getElementById('status').innerHTML = message;
            document.getElementById('status').style.color = color;
        }
        
        function visualizeAudio() {
            if (!analyser) return;
            
            const canvas = document.getElementById('visualizer');
            const ctx = canvas.getContext('2d');
            const width = canvas.width;
            const height = canvas.height;
            
            analyser.getByteFrequencyData(dataArray);
            
            ctx.fillStyle = '#333';
            ctx.fillRect(0, 0, width, height);
            
            const barWidth = width / dataArray.length;
            let x = 0;
            
            for (let i = 0; i < dataArray.length; i++) {
                const barHeight = (dataArray[i] / 255) * height;
                
                const red = (i / dataArray.length) * 255;
                const green = 255 - red;
                ctx.fillStyle = `rgb(${red}, ${green}, 50)`;
                
                ctx.fillRect(x, height - barHeight, barWidth, barHeight);
                x += barWidth;
            }
            
            if (isRecording) {
                requestAnimationFrame(visualizeAudio);
            }
        }
        
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        sampleRate: 16000,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true
                    }
                });
                
                // Set up audio visualization
                audioContext = new AudioContext();
                analyser = audioContext.createAnalyser();
                microphone = audioContext.createMediaStreamSource(stream);
                microphone.connect(analyser);
                
                analyser.fftSize = 256;
                dataArray = new Uint8Array(analyser.frequencyBinCount);
                
                // Start visualization
                visualizeAudio();
                
                // Set up recording
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = function(event) {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = function() {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    // Update transcription area with recorded audio info
                    document.getElementById('transcription').innerHTML = 
                        `<strong>✅ Recording completed!</strong><br>
                         Duration: ${(audioChunks.length * 1000 / 1000).toFixed(1)}s<br>
                         <em>Use the Streamlit audio input above to upload and transcribe this recording.</em>`;
                };
                
                mediaRecorder.start(1000); // 1-second chunks
                isRecording = true;
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
                updateStatus('🔴 Recording... Speak your clinical notes now', '#ff4444');
                
            } catch (error) {
                console.error('Error accessing microphone:', error);
                updateStatus('❌ Error: Could not access microphone', '#ff4444');
                alert('Please enable microphone permissions and try again.');
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                
                // Stop all tracks
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                
                // Close audio context
                if (audioContext) {
                    audioContext.close();
                }
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                
                updateStatus('⏹️ Recording stopped. Use Streamlit audio input to transcribe.', '#2196F3');
            }
        }
        
        // Initialize
        updateStatus('Ready to record clinical notes', '#4CAF50');
    </script>
    """
    
    return html_code


# Advanced real-time features
def show_realtime_features():
    """Display information about real-time features"""
    
    st.header("🚀 Real-time Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Current Capabilities")
        st.markdown("""
        - **Browser Audio Input**: Record directly in browser
        - **OpenAI Whisper Transcription**: High-accuracy medical transcription
        - **Live Processing**: Immediate extraction and form generation
        - **Multiple NHS Forms**: Auto-generate standard forms
        - **PDF Export**: Download forms immediately
        - **Confidence Scoring**: Quality assessment of extraction
        """)
    
    with col2:
        st.subheader("🔮 Planned Enhancements")
        st.markdown("""
        - **Streaming Transcription**: Word-by-word live transcription
        - **Voice Activity Detection**: Auto-start/stop on speech
        - **Audio Quality Enhancement**: Noise reduction and normalization
        - **Multi-language Support**: Support for Welsh and other languages
        - **Integration with EHR**: Direct integration with hospital systems
        - **Offline Mode**: Local processing for sensitive environments
        """)
    
    # Demo section
    st.header("🎬 How It Works")
    
    with st.expander("📖 Step-by-Step Guide", expanded=True):
        st.markdown("""
        ### 1. 🎙️ **Record Audio**
        - Click "Record your clinical notes" audio input
        - Grant microphone permissions when prompted
        - Speak your clinical notes clearly
        - Click stop when finished
        
        ### 2. 🔄 **Process & Transcribe**
        - Click "Transcribe & Process Audio"
        - System transcribes speech using OpenAI Whisper
        - AI extracts structured clinical data
        - NHS forms are auto-generated
        
        ### 3. 📥 **Download Forms**
        - Review extracted data and generated forms
        - Download individual PDFs or form bundles
        - Forms are NHS-compliant and ready for submission
        
        ### 4. ✅ **Quality Assurance**
        - Check confidence scores for data extraction
        - Review suggested improvements
        - Verify all critical information is captured
        """)


def realtime_audio_main_page():
    """Main real-time audio page with all features"""
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.title("🎙️ Real-time Clinical Note Recording")
    st.markdown("*Record, transcribe, and process clinical notes in real-time*")
    
    # Show features overview
    show_realtime_features()
    
    # Main recording interface
    simple_realtime_audio_page()


# Export for main dashboard
def get_realtime_audio_page():
    """Return the real-time audio page function for main dashboard integration"""
    return simple_realtime_audio_page
