# 🎙️ Real-time Audio Recording & Transcription

## Overview

The NHS Paperwork Automation Agent now includes comprehensive real-time audio recording and transcription capabilities, allowing healthcare professionals to dictate clinical notes and automatically generate NHS forms.

## 🚀 Key Features

### ✅ **Real-time Audio Capture**
- Browser-based microphone access
- Live audio visualization with frequency spectrum
- Start/Stop/Pause recording controls
- Audio quality optimization for medical speech

### ✅ **Live Transcription**
- OpenAI Whisper integration for medical terminology
- Real-time speech-to-text processing
- Confidence scoring for transcription quality
- Support for multiple audio formats

### ✅ **Streaming Processing**
- WebSocket-based real-time communication
- Audio chunk processing (3-second intervals)
- Live transcription updates in browser
- Session management for multiple users

### ✅ **NHS Form Auto-generation**
- Direct conversion from speech to NHS forms
- Support for Discharge Summaries, Referrals, Risk Assessments
- Structured data extraction from voice recordings
- PDF generation from spoken clinical notes

## 🏗️ Technical Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Browser       │    │   FastAPI        │    │   OpenAI        │
│   Audio Capture │◄──►│   WebSocket      │◄──►│   Whisper API   │
│   + JavaScript  │    │   + REST API     │    │   Transcription │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Audio Buffer   │    │   NLP Extraction│
│   Dashboard     │    │   Ring Buffer    │    │   GPT-4 Analysis│
│   Real-time UI  │    │   Session Mgmt   │    │   Form Generator│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 New File Structure

```
src/
├── services/
│   ├── realtime_audio_service.py     # Core real-time audio processing
│   └── nlp_extraction.py             # Enhanced with audio support
├── dashboard/
│   ├── realtime_audio.py             # Full WebSocket implementation
│   ├── simple_realtime_audio.py      # Simplified browser-based recording
│   └── app.py                        # Updated main dashboard
└── api/
    └── main.py                       # WebSocket + REST endpoints

demo_realtime_audio.py                # Demo script for testing
REALTIME_AUDIO_README.md              # This documentation
```

## 🎯 Usage Instructions

### 1. **Start the System**

```bash
# Terminal 1: Start API Server
python start_api.py

# Terminal 2: Start Dashboard  
python start_dashboard.py

# Open browser
http://localhost:8501
```

### 2. **Navigate to Real-time Recording**

- Go to the "Real-time Recording" page in the dashboard
- Ensure microphone permissions are granted
- Check system status (API connection)

### 3. **Record Clinical Notes**

```
Example spoken input:
"Patient John Smith, NHS number 1234567890, 
date of birth 15th March 1965. Presenting 
complaint chest pain for two days. Primary 
diagnosis acute myocardial infarction. Current 
medications aspirin 75mg once daily, 
atorvastatin 40mg at night. Allergies penicillin. 
Discharge plan cardiology follow-up in six weeks."
```

### 4. **Process & Generate Forms**

- Audio is automatically transcribed using OpenAI Whisper
- Clinical data is extracted using GPT-4
- NHS forms are auto-generated
- PDFs are available for immediate download

## 🔧 Configuration Options

### **Recording Settings**
- **Transcription Interval**: 2-10 seconds (default: 5s)
- **Audio Quality**: Standard 16kHz or High 44kHz
- **Auto-extract**: Automatic data extraction from transcription
- **Form Types**: Select which NHS forms to generate

### **Audio Processing**
- **Sample Rate**: 16kHz optimized for speech
- **Channels**: Mono for better transcription
- **Echo Cancellation**: Enabled for clean recording
- **Noise Suppression**: Automatic background noise reduction

## 📊 API Endpoints

### **Session Management**
```http
POST   /audio/session                    # Create new session
GET    /audio/session/{id}/status        # Get session info  
DELETE /audio/session/{id}               # Cleanup session
```

### **Recording Control**
```http
POST   /audio/session/{id}/start         # Start recording
POST   /audio/session/{id}/stop          # Stop recording
GET    /audio/session/{id}/transcription # Get live transcription
```

### **Real-time Streaming**
```http
WebSocket /ws/audio/{id}                 # Live audio streaming
```

## 🎙️ WebSocket Protocol

### **Client to Server Messages**

```javascript
// Start recording
{
  "action": "start_recording"
}

// Stop recording  
{
  "action": "stop_recording"
}

// Audio data (binary)
ArrayBuffer // Raw audio data
```

### **Server to Client Messages**

```javascript
// Connection established
{
  "type": "connection_established",
  "session_id": "uuid",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Transcription update
{
  "type": "transcription_update", 
  "data": {
    "new_segments": [
      {
        "text": "Patient John Smith...",
        "timestamp": "2024-01-01T00:00:00Z",
        "confidence": 0.95
      }
    ],
    "full_transcription": "Complete text so far..."
  }
}

// Recording status
{
  "type": "recording_started|recording_stopped",
  "result": {...}
}
```

## 🧪 Testing

### **Run Demo Script**
```bash
python demo_realtime_audio.py
```

This will:
- ✅ Test API server health
- ✅ Verify existing transcription functionality  
- ✅ Test real-time session management
- ✅ Validate all audio endpoints
- ✅ Show usage instructions

### **Manual Testing**
1. Start both API server and dashboard
2. Navigate to "Real-time Recording" page
3. Click "Record your clinical notes"
4. Grant microphone permissions
5. Speak sample clinical notes
6. Verify transcription appears
7. Check generated NHS forms

## 🔒 Security & Privacy

### **Data Handling**
- Audio data is processed in memory only
- No permanent storage of audio recordings
- Transcriptions can be automatically deleted
- Session-based isolation for multi-user environments

### **Privacy Controls**
- Configurable data retention (default: session-only)
- Optional audio data encryption in transit
- Audit logging for all transcription activities
- NHS Data Security Standards compliance

## 🚀 Performance Optimization

### **Audio Processing**
- Ring buffer for efficient memory usage (30-second window)
- Voice Activity Detection to reduce unnecessary processing
- Audio preprocessing for improved transcription quality
- Configurable chunk sizes for optimal latency

### **Transcription Efficiency**
- Batch processing of audio chunks
- Concurrent transcription of multiple sessions
- Intelligent silence detection
- Error recovery and retry mechanisms

## 🔧 Troubleshooting

### **Common Issues**

**"Cannot access microphone"**
- Ensure browser microphone permissions are granted
- Check that no other applications are using the microphone
- Try refreshing the page and granting permissions again

**"WebSocket connection failed"**
- Verify API server is running on correct port (8000)
- Check firewall settings for WebSocket connections
- Ensure CORS is properly configured

**"Transcription not appearing"**
- Verify OpenAI API key is set in environment
- Check API server logs for transcription errors
- Ensure audio is being captured (check visualizer)

**"Poor transcription quality"**
- Speak more clearly and at moderate pace
- Reduce background noise
- Use medical terminology consistently
- Check microphone quality and positioning

### **Debug Mode**

Enable debug logging:
```bash
export DEBUG=True
python start_api.py
```

Check logs in:
- API server console output
- Browser developer console (F12)
- Streamlit dashboard logs

## 📈 Future Enhancements

### **Planned Features**
- **Continuous Transcription**: Word-by-word live updates
- **Speaker Identification**: Multi-speaker clinical encounters
- **Language Support**: Welsh, Scottish Gaelic, other NHS languages
- **Offline Mode**: Local Whisper model deployment
- **Integration**: Direct EHR system integration
- **Mobile Support**: Smartphone app for field recording

### **Advanced Audio**
- **Noise Cancellation**: Advanced audio filtering
- **Audio Enhancement**: Real-time audio quality improvement
- **Voice Commands**: Voice-controlled form navigation
- **Dictation Shortcuts**: Medical abbreviation expansion

## 🏥 Clinical Use Cases

### **Primary Applications**
1. **Ward Rounds**: Dictate patient observations and treatment plans
2. **Discharge Planning**: Record discharge summaries verbally
3. **Referral Letters**: Voice-to-form generation for referrals
4. **Risk Assessments**: Spoken risk evaluation documentation
5. **Consultation Notes**: Real-time consultation documentation

### **Workflow Integration**
- **Pre-consultation**: Set up recording session
- **During consultation**: Record clinical observations
- **Post-consultation**: Review and finalize forms
- **Documentation**: Generate and submit NHS-compliant PDFs

## 📞 Support

### **For Issues**
- Check the troubleshooting section above
- Review API server logs
- Test with demo script: `python demo_realtime_audio.py`

### **For Enhancements**
- Submit feature requests via project issues
- Review planned enhancements roadmap
- Contact development team for enterprise features

---

## ✅ Quick Start Checklist

- [ ] API server running (`python start_api.py`)
- [ ] Dashboard running (`python start_dashboard.py`)
- [ ] OpenAI API key configured
- [ ] Browser microphone permissions granted
- [ ] "Real-time Recording" page accessible
- [ ] Test recording working with audio visualization
- [ ] Transcription producing results
- [ ] NHS forms generating correctly
- [ ] PDF downloads working

**🎉 Congratulations! Your NHS Paperwork Agent now supports real-time audio recording and transcription!**

---

*Built with ❤️ for NHS healthcare professionals*
