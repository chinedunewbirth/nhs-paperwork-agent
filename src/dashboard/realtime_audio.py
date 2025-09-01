"""
Real-time Audio Recording Component for Streamlit Dashboard
Provides UI for live audio recording and transcription
"""

import streamlit as st
import requests
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit.components.v1 as components

# Audio recording JavaScript component
AUDIO_RECORDER_JS = """
<!DOCTYPE html>
<html>
<head>
    <title>Real-time Audio Recorder</title>
    <style>
        .recorder-container {
            padding: 20px;
            border-radius: 10px;
            background: #f0f2f6;
            margin: 10px 0;
        }
        .controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }
        .btn-start {
            background: #00c851;
            color: white;
        }
        .btn-stop {
            background: #ff4444;
            color: white;
        }
        .btn-pause {
            background: #ffbb33;
            color: white;
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .btn:hover:not(:disabled) {
            opacity: 0.8;
        }
        .visualizer {
            width: 100%;
            height: 100px;
            background: #333;
            border-radius: 5px;
            margin: 10px 0;
        }
        .status {
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
        }
        .transcription {
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #007bff;
            min-height: 100px;
            max-height: 300px;
            overflow-y: auto;
        }
        .confidence-indicator {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            margin-left: 10px;
        }
        .confidence-high { background: #28a745; color: white; }
        .confidence-medium { background: #ffc107; color: black; }
        .confidence-low { background: #dc3545; color: white; }
    </style>
</head>
<body>
    <div class="recorder-container">
        <h3>🎙️ Real-time Audio Recording</h3>
        
        <div class="status" id="status">Ready to record</div>
        
        <canvas class="visualizer" id="visualizer"></canvas>
        
        <div class="controls">
            <button class="btn btn-start" id="startBtn" onclick="startRecording()">Start Recording</button>
            <button class="btn btn-pause" id="pauseBtn" onclick="pauseRecording()" disabled>Pause</button>
            <button class="btn btn-stop" id="stopBtn" onclick="stopRecording()" disabled>Stop Recording</button>
        </div>
        
        <div class="transcription" id="transcription">
            <em>Live transcription will appear here...</em>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;
        let isPaused = false;
        let sessionId = null;
        let websocket = null;
        let audioContext;
        let analyser;
        let microphone;
        let dataArray;
        let animationId;
        
        // Initialize audio visualization
        function initializeVisualization() {
            const canvas = document.getElementById('visualizer');
            const canvasContext = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            
            function draw() {
                if (!analyser) return;
                
                analyser.getByteFrequencyData(dataArray);
                
                canvasContext.fillStyle = '#333';
                canvasContext.fillRect(0, 0, canvas.width, canvas.height);
                
                const barWidth = canvas.width / dataArray.length;
                let x = 0;
                
                for (let i = 0; i < dataArray.length; i++) {
                    const barHeight = (dataArray[i] / 255) * canvas.height;
                    
                    const red = (i / dataArray.length) * 255;
                    const green = 255 - red;
                    canvasContext.fillStyle = `rgb(${red}, ${green}, 50)`;
                    
                    canvasContext.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                    x += barWidth;
                }
                
                animationId = requestAnimationFrame(draw);
            }
            
            draw();
        }
        
        async function createSession() {
            try {
                const response = await fetch('/audio/session', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await response.json();
                sessionId = data.session_id;
                console.log('Session created:', sessionId);
                return sessionId;
            } catch (error) {
                console.error('Error creating session:', error);
                updateStatus('Error creating session', 'error');
                return null;
            }
        }
        
        function connectWebSocket() {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/audio/${sessionId}`;
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = function(event) {
                console.log('WebSocket connected');
                updateStatus('Connected to server', 'success');
            };
            
            websocket.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            };
            
            websocket.onclose = function(event) {
                console.log('WebSocket disconnected');
                updateStatus('Disconnected from server', 'warning');
            };
            
            websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateStatus('Connection error', 'error');
            };
        }
        
        function handleWebSocketMessage(message) {
            switch (message.type) {
                case 'connection_established':
                    updateStatus('Ready to record', 'success');
                    break;
                    
                case 'recording_started':
                    updateStatus('🔴 Recording...', 'recording');
                    break;
                    
                case 'recording_stopped':
                    updateStatus('⏹️ Recording stopped', 'stopped');
                    if (message.result.final_transcription) {
                        displayTranscription(message.result.final_transcription, 1.0, true);
                    }
                    break;
                    
                case 'transcription_update':
                    if (message.data.new_segments) {
                        message.data.new_segments.forEach(segment => {
                            displayTranscription(segment.text, segment.confidence, false);
                        });
                    }
                    break;
                    
                case 'error':
                    updateStatus(`Error: ${message.message}`, 'error');
                    break;
            }
        }
        
        function updateStatus(message, type = 'info') {
            const statusElement = document.getElementById('status');
            statusElement.textContent = message;
            
            // Update status styling
            statusElement.className = 'status';
            if (type === 'error') statusElement.style.color = '#ff4444';
            else if (type === 'success') statusElement.style.color = '#00c851';
            else if (type === 'warning') statusElement.style.color = '#ffbb33';
            else if (type === 'recording') statusElement.style.color = '#ff4444';
            else statusElement.style.color = '#333';
        }
        
        function displayTranscription(text, confidence, isFinal = false) {
            const transcriptionElement = document.getElementById('transcription');
            
            // Create confidence indicator
            let confidenceClass = 'confidence-low';
            if (confidence > 0.8) confidenceClass = 'confidence-high';
            else if (confidence > 0.6) confidenceClass = 'confidence-medium';
            
            const timestamp = new Date().toLocaleTimeString();
            const confidencePercent = Math.round(confidence * 100);
            
            const segmentHtml = `
                <div style="margin-bottom: 10px; ${isFinal ? 'border-bottom: 2px solid #007bff; padding-bottom: 10px;' : ''}">
                    <span style="color: #666; font-size: 12px;">[${timestamp}]</span>
                    <span class="confidence-indicator ${confidenceClass}">${confidencePercent}%</span>
                    <br>
                    <span style="${isFinal ? 'font-weight: bold;' : ''}">${text}</span>
                </div>
            `;
            
            if (isFinal) {
                transcriptionElement.innerHTML = segmentHtml;
            } else {
                transcriptionElement.innerHTML += segmentHtml;
            }
            
            // Auto-scroll to bottom
            transcriptionElement.scrollTop = transcriptionElement.scrollHeight;
        }
        
        async function startRecording() {
            try {
                if (!sessionId) {
                    sessionId = await createSession();
                    if (!sessionId) return;
                }
                
                if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                    connectWebSocket();
                    // Wait for connection
                    await new Promise(resolve => {
                        const checkConnection = () => {
                            if (websocket.readyState === WebSocket.OPEN) {
                                resolve();
                            } else {
                                setTimeout(checkConnection, 100);
                            }
                        };
                        checkConnection();
                    });
                }
                
                // Request microphone access
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        sampleRate: 16000,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true
                    } 
                });
                
                // Set up audio context for visualization
                audioContext = new AudioContext();
                analyser = audioContext.createAnalyser();
                microphone = audioContext.createMediaStreamSource(stream);
                microphone.connect(analyser);
                
                analyser.fftSize = 256;
                const bufferLength = analyser.frequencyBinCount;
                dataArray = new Uint8Array(bufferLength);
                
                initializeVisualization();
                
                // Set up MediaRecorder for audio capture
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                
                mediaRecorder.ondataavailable = function(event) {
                    if (event.data.size > 0 && websocket && websocket.readyState === WebSocket.OPEN) {
                        // Send audio data via WebSocket
                        event.data.arrayBuffer().then(buffer => {
                            websocket.send(buffer);
                        });
                    }
                };
                
                // Start recording
                mediaRecorder.start(1000); // Capture in 1-second chunks
                isRecording = true;
                
                // Send start command via WebSocket
                websocket.send(JSON.stringify({action: 'start_recording'}));
                
                // Update UI
                document.getElementById('startBtn').disabled = true;
                document.getElementById('pauseBtn').disabled = false;
                document.getElementById('stopBtn').disabled = false;
                
                updateStatus('🔴 Recording started...', 'recording');
                
            } catch (error) {
                console.error('Error starting recording:', error);
                updateStatus('Error: Could not access microphone', 'error');
            }
        }
        
        function pauseRecording() {
            if (mediaRecorder && isRecording) {
                if (isPaused) {
                    mediaRecorder.resume();
                    isPaused = false;
                    document.getElementById('pauseBtn').textContent = 'Pause';
                    updateStatus('🔴 Recording resumed...', 'recording');
                } else {
                    mediaRecorder.pause();
                    isPaused = true;
                    document.getElementById('pauseBtn').textContent = 'Resume';
                    updateStatus('⏸️ Recording paused', 'warning');
                }
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                isPaused = false;
                
                // Stop audio visualization
                if (animationId) {
                    cancelAnimationFrame(animationId);
                }
                
                // Stop audio context
                if (audioContext) {
                    audioContext.close();
                }
                
                // Send stop command via WebSocket
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                    websocket.send(JSON.stringify({action: 'stop_recording'}));
                }
                
                // Update UI
                document.getElementById('startBtn').disabled = false;
                document.getElementById('pauseBtn').disabled = true;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('pauseBtn').textContent = 'Pause';
                
                updateStatus('⏹️ Recording stopped', 'stopped');
            }
        }
        
        // Initialize when page loads
        window.onload = function() {
            updateStatus('Ready to record', 'info');
        };
        
        // Cleanup when page unloads
        window.onbeforeunload = function() {
            if (isRecording) {
                stopRecording();
            }
            if (websocket) {
                websocket.close();
            }
        };
    </script>
</body>
</html>
"""


def realtime_audio_page():
    """Streamlit page for real-time audio recording and transcription"""
    st.header("🎙️ Real-time Audio Recording & Transcription")
    
    st.markdown("""
    Record audio in real-time and see live transcription of your clinical notes.
    The system will automatically transcribe speech as you speak and can be used
    to generate NHS forms directly from your voice.
    """)
    
    # Check API server connection
    api_url = st.session_state.get('api_url', 'http://localhost:8000')
    
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code != 200:
            st.error("⚠️ API server is not responding. Please make sure it's running.")
            return
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to API server. Please start the backend service.")
        st.code("python start_api.py")
        return
    
    # Initialize session state
    if 'recording_session_id' not in st.session_state:
        st.session_state.recording_session_id = None
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'transcription_history' not in st.session_state:
        st.session_state.transcription_history = []
    
    # Configuration section
    with st.expander("⚙️ Recording Configuration", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            chunk_duration = st.slider(
                "Transcription interval (seconds)",
                min_value=1.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                help="How often to transcribe audio chunks"
            )
            
            auto_process = st.checkbox(
                "Auto-process transcription",
                value=True,
                help="Automatically extract data from transcription"
            )
        
        with col2:
            voice_threshold = st.slider(
                "Voice detection sensitivity",
                min_value=0.01,
                max_value=0.1,
                value=0.03,
                step=0.01,
                help="Sensitivity for voice activity detection"
            )
            
            form_types = st.multiselect(
                "Forms to generate",
                ["discharge_summary", "referral", "risk_assessment"],
                default=["discharge_summary"],
                help="NHS forms to auto-generate from transcription"
            )
    
    # Main recording interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Embed the JavaScript audio recorder
        components.html(AUDIO_RECORDER_JS, height=500, scrolling=False)
    
    with col2:
        st.subheader("📊 Session Information")
        
        # Session management
        if st.button("🔄 Create New Session", type="secondary"):
            try:
                response = requests.post(f"{api_url}/audio/session", timeout=10)
                if response.status_code == 200:
                    session_data = response.json()
                    st.session_state.recording_session_id = session_data['session_id']
                    st.success("✅ New session created!")
                    st.rerun()
                else:
                    st.error("Failed to create session")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Display current session info
        if st.session_state.recording_session_id:
            st.text(f"Session ID: {st.session_state.recording_session_id[:8]}...")
            
            # Get session status
            if st.button("📊 Refresh Status"):
                try:
                    response = requests.get(
                        f"{api_url}/audio/session/{st.session_state.recording_session_id}/status",
                        timeout=10
                    )
                    if response.status_code == 200:
                        status_data = response.json()
                        
                        st.metric("Recording Duration", f"{status_data.get('recording_duration', 0):.1f}s")
                        st.metric("Segments Transcribed", status_data.get('segment_count', 0))
                        st.metric("Buffer Level", f"{status_data.get('buffer_level', 0):.1%}")
                        
                        # Display current transcription
                        current_transcription = status_data.get('full_transcription', '')
                        if current_transcription:
                            st.text_area(
                                "Current Transcription",
                                value=current_transcription,
                                height=200,
                                disabled=True
                            )
                except Exception as e:
                    st.error(f"Error getting status: {str(e)}")
        
        # Recording tips
        with st.expander("💡 Recording Tips", expanded=True):
            st.markdown("""
            **For best results:**
            - Speak clearly and at normal pace
            - Avoid background noise
            - Use medical terminology consistently
            - Include patient identifiers
            - Mention diagnoses and medications clearly
            
            **The system will:**
            - ✅ Transcribe speech in real-time
            - ✅ Extract structured data automatically
            - ✅ Generate NHS forms
            - ✅ Show confidence scores
            """)
    
    # Live transcription display
    st.header("📝 Live Transcription")
    
    # Polling for transcription updates (fallback if WebSocket not working)
    if st.session_state.recording_session_id:
        transcription_placeholder = st.empty()
        
        # Auto-refresh transcription
        if st.button("🔄 Get Latest Transcription"):
            try:
                response = requests.get(
                    f"{api_url}/audio/session/{st.session_state.recording_session_id}/transcription",
                    timeout=10
                )
                if response.status_code == 200:
                    transcription_data = response.json()
                    full_text = transcription_data.get('full_transcription', '')
                    
                    if full_text:
                        transcription_placeholder.text_area(
                            "Transcribed Text",
                            value=full_text,
                            height=200,
                            help="Copy this text to process with NHS forms"
                        )
                        
                        # Option to process transcription
                        if st.button("🔄 Process Transcription for NHS Forms", type="primary"):
                            process_transcription_for_forms(full_text, form_types)
                    else:
                        transcription_placeholder.info("No transcription available yet.")
            except Exception as e:
                st.error(f"Error getting transcription: {str(e)}")
    
    # Session cleanup
    if st.session_state.recording_session_id:
        if st.button("🗑️ End Session", type="secondary"):
            try:
                response = requests.delete(
                    f"{api_url}/audio/session/{st.session_state.recording_session_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    st.session_state.recording_session_id = None
                    st.session_state.is_recording = False
                    st.success("✅ Session ended and cleaned up")
                    st.rerun()
            except Exception as e:
                st.error(f"Error ending session: {str(e)}")


def process_transcription_for_forms(transcription_text: str, form_types: list):
    """Process transcribed text to generate NHS forms"""
    
    if not transcription_text.strip():
        st.warning("No transcription text to process")
        return
    
    try:
        with st.spinner("Processing transcription for NHS forms..."):
            # Prepare request data
            request_data = {
                "note": {
                    "raw_text": transcription_text,
                    "note_type": "transcribed_audio",
                    "date_created": datetime.now().isoformat()
                },
                "form_types": form_types,
                "auto_fill_forms": True,
                "include_suggestions": True,
                "priority": "Routine"
            }
            
            # Make API request
            api_url = st.session_state.get('api_url', 'http://localhost:8000')
            response = requests.post(
                f"{api_url}/process",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                display_transcription_processing_results(result)
            else:
                st.error(f"Processing failed: {response.text}")
                
    except Exception as e:
        st.error(f"Error processing transcription: {str(e)}")


def display_transcription_processing_results(result: Dict[str, Any]):
    """Display results from processing transcribed audio"""
    
    st.success(f"✅ Transcription processed in {result['processing_time']:.1f}s")
    
    # Show warnings and errors
    if result.get('warnings'):
        for warning in result['warnings']:
            st.warning(f"⚠️ {warning}")
    
    if result.get('errors'):
        for error in result['errors']:
            st.error(f"❌ {error}")
    
    # Extracted data
    st.header("📊 Extracted Data from Voice Recording")
    
    extracted_data = result['extracted_data']
    confidence = extracted_data.get('extraction_confidence', 0)
    
    # Confidence indicator
    conf_color = "green" if confidence > 0.8 else "orange" if confidence > 0.5 else "red"
    st.markdown(f"**Extraction Confidence:** :{conf_color}[{confidence:.1%}]")
    
    # Display extracted information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Patient Information")
        patient_data = extracted_data['patient']
        for field, value in patient_data.items():
            if value:
                st.text(f"{field.replace('_', ' ').title()}: {value}")
    
    with col2:
        st.subheader("🏥 Clinical Information")
        clinical_data = extracted_data['clinical']
        
        # Key clinical fields
        key_fields = ['primary_diagnosis', 'presenting_complaint', 'examination_findings']
        for field in key_fields:
            value = clinical_data.get(field)
            if value:
                st.text(f"{field.replace('_', ' ').title()}: {value}")
        
        # Display lists
        for field, values in clinical_data.items():
            if isinstance(values, list) and values:
                st.text(f"{field.replace('_', ' ').title()}: {'; '.join(str(v) for v in values)}")
    
    # Generated forms
    generated_forms = result.get('generated_forms', [])
    if generated_forms:
        st.header("📄 Generated NHS Forms from Voice Recording")
        
        for i, form in enumerate(generated_forms):
            with st.expander(f"Form {i+1}: {form['form_type'].title()}", expanded=True):
                st.json(form['filled_data'])
                
                # PDF download button
                if st.button(
                    f"📥 Download {form['form_type'].title()} PDF",
                    key=f"voice_download_{i}",
                    help="Download this form as PDF"
                ):
                    download_form_pdf_from_voice(form['form_type'], extracted_data)


def download_form_pdf_from_voice(form_type: str, extracted_data: Dict[str, Any]):
    """Download PDF for form generated from voice transcription"""
    
    try:
        with st.spinner(f"Generating {form_type.title()} PDF from voice recording..."):
            api_url = st.session_state.get('api_url', 'http://localhost:8000')
            
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
                # Provide download
                st.download_button(
                    label=f"📥 Download {form_type.title()} PDF",
                    data=response.content,
                    file_name=f"voice_{form_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key=f"voice_pdf_download_{form_type}_{datetime.now().timestamp()}"
                )
                st.success(f"✅ {form_type.title()} PDF generated from voice recording!")
            else:
                st.error(f"Failed to generate PDF: {response.text}")
                
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")


def display_audio_level_meter():
    """Display a simple audio level meter using Streamlit"""
    
    # Placeholder for audio level visualization
    level_placeholder = st.empty()
    
    # This would be updated in real-time from the audio stream
    # For now, we'll show a static meter
    level_placeholder.progress(0.0)
    
    return level_placeholder


# Real-time transcription status component
def show_transcription_status():
    """Show real-time transcription status"""
    
    status_container = st.container()
    
    with status_container:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Recording Status", "Ready", "")
        
        with col2:
            st.metric("Transcription Confidence", "0%", "")
        
        with col3:
            st.metric("Words Transcribed", "0", "")
    
    return status_container


# Main function to add to dashboard
def add_realtime_audio_to_dashboard():
    """Add real-time audio functionality to the main dashboard"""
    
    # This function would be called from the main dashboard app.py
    # to integrate the real-time audio page
    
    return {
        "page_name": "Real-time Recording",
        "page_function": realtime_audio_page,
        "icon": "🎙️"
    }
