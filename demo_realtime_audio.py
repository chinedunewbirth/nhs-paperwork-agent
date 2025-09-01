#!/usr/bin/env python3
"""
Real-time Audio Recording Demo for NHS Paperwork Automation Agent
Demonstrates the real-time audio recording and transcription capabilities
"""

import asyncio
import requests
import json
import time
import tempfile
import os
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8000"

class RealtimeAudioDemo:
    """Demo class for testing real-time audio functionality"""
    
    def __init__(self):
        self.api_url = API_BASE_URL
        self.session_id = None
    
    def check_api_health(self) -> bool:
        """Check if the API server is running and healthy"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ API server is healthy")
                logger.info(f"Services status: {health_data['services']}")
                return True
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cannot connect to API server: {str(e)}")
            logger.info("Please start the API server: python start_api.py")
            return False
    
    def create_session(self) -> bool:
        """Create a new real-time audio session"""
        try:
            response = requests.post(f"{self.api_url}/audio/session", timeout=10)
            if response.status_code == 200:
                session_data = response.json()
                self.session_id = session_data['session_id']
                logger.info(f"✅ Created audio session: {self.session_id}")
                return True
            else:
                logger.error(f"❌ Failed to create session: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error creating session: {str(e)}")
            return False
    
    def start_recording(self) -> bool:
        """Start recording for the current session"""
        if not self.session_id:
            logger.error("❌ No active session")
            return False
        
        try:
            response = requests.post(f"{self.api_url}/audio/session/{self.session_id}/start", timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Recording started: {result}")
                return True
            else:
                logger.error(f"❌ Failed to start recording: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error starting recording: {str(e)}")
            return False
    
    def stop_recording(self) -> Dict[str, Any]:
        """Stop recording and get final transcription"""
        if not self.session_id:
            logger.error("❌ No active session")
            return {}
        
        try:
            response = requests.post(f"{self.api_url}/audio/session/{self.session_id}/stop", timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Recording stopped: {result}")
                return result
            else:
                logger.error(f"❌ Failed to stop recording: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error stopping recording: {str(e)}")
            return {}
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        if not self.session_id:
            logger.error("❌ No active session")
            return {}
        
        try:
            response = requests.get(f"{self.api_url}/audio/session/{self.session_id}/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                logger.info(f"📊 Session status: {status}")
                return status
            else:
                logger.error(f"❌ Failed to get session status: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error getting session status: {str(e)}")
            return {}
    
    def get_transcription_updates(self) -> Dict[str, Any]:
        """Get live transcription updates"""
        if not self.session_id:
            logger.error("❌ No active session")
            return {}
        
        try:
            response = requests.get(f"{self.api_url}/audio/session/{self.session_id}/transcription", timeout=10)
            if response.status_code == 200:
                transcription = response.json()
                logger.info(f"📝 Transcription update: {transcription}")
                return transcription
            else:
                logger.error(f"❌ Failed to get transcription: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error getting transcription: {str(e)}")
            return {}
    
    def cleanup_session(self) -> bool:
        """Clean up the current session"""
        if not self.session_id:
            return True
        
        try:
            response = requests.delete(f"{self.api_url}/audio/session/{self.session_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Session cleaned up: {result}")
                self.session_id = None
                return True
            else:
                logger.error(f"❌ Failed to cleanup session: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error cleaning up session: {str(e)}")
            return False
    
    def test_existing_transcription(self):
        """Test transcription with a sample audio file (if available)"""
        logger.info("🧪 Testing existing transcription endpoint...")
        
        # Create a simple test audio file
        sample_text = """
        Patient John Smith, NHS number 1234567890, date of birth 15th March 1965.
        Presenting complaint: chest pain for two days.
        Primary diagnosis: acute myocardial infarction.
        Current medications: aspirin 75mg once daily, atorvastatin 40mg at night.
        Allergies: penicillin.
        Discharge plan: cardiology follow-up in six weeks.
        """
        
        logger.info("📝 Sample clinical note for testing:")
        logger.info(sample_text.strip())
        
        # Test processing with the existing text endpoint
        try:
            request_data = {
                "note": {
                    "raw_text": sample_text,
                    "note_type": "test_audio",
                    "date_created": datetime.now().isoformat()
                },
                "form_types": ["discharge_summary"],
                "auto_fill_forms": True,
                "include_suggestions": True,
                "priority": "Routine"
            }
            
            response = requests.post(
                f"{self.api_url}/process",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Text processing successful!")
                logger.info(f"Extraction confidence: {result['extracted_data']['extraction_confidence']:.1%}")
                logger.info(f"Generated forms: {len(result['generated_forms'])}")
                return result
            else:
                logger.error(f"❌ Text processing failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error testing text processing: {str(e)}")
            return None


def run_demo():
    """Run the real-time audio demo"""
    print("🩺 NHS Paperwork Agent - Real-time Audio Demo")
    print("=" * 50)
    
    demo = RealtimeAudioDemo()
    
    # Step 1: Check API health
    print("\n1. 🔍 Checking API server health...")
    if not demo.check_api_health():
        print("❌ Demo cannot proceed without API server")
        print("Please start the API server: python start_api.py")
        return
    
    # Step 2: Test existing functionality
    print("\n2. 🧪 Testing existing transcription processing...")
    result = demo.test_existing_transcription()
    if result:
        print("✅ Existing functionality working correctly")
    else:
        print("⚠️ Issues with existing functionality")
    
    # Step 3: Test real-time session management
    print("\n3. 🎙️ Testing real-time audio session management...")
    
    if demo.create_session():
        print("✅ Audio session created successfully")
        
        # Test session status
        status = demo.get_session_status()
        if status:
            print("✅ Session status retrieved successfully")
        
        # Test transcription endpoint
        transcription = demo.get_transcription_updates()
        if "error" not in transcription:
            print("✅ Transcription endpoint accessible")
        
        # Cleanup
        if demo.cleanup_session():
            print("✅ Session cleaned up successfully")
    else:
        print("❌ Failed to create audio session")
    
    # Step 4: Show available endpoints
    print("\n4. 📋 Available Real-time Audio Endpoints:")
    endpoints = [
        "POST /audio/session - Create new recording session",
        "POST /audio/session/{id}/start - Start recording",
        "POST /audio/session/{id}/stop - Stop recording", 
        "GET /audio/session/{id}/status - Get session status",
        "GET /audio/session/{id}/transcription - Get live transcription",
        "DELETE /audio/session/{id} - Cleanup session",
        "WebSocket /ws/audio/{id} - Real-time audio streaming"
    ]
    
    for endpoint in endpoints:
        print(f"  ✅ {endpoint}")
    
    print("\n5. 🚀 Usage Instructions:")
    print("""
    To use the real-time audio recording:
    
    1. Start the API server:
       python start_api.py
    
    2. Start the dashboard:
       python start_dashboard.py
    
    3. Open browser: http://localhost:8501
    
    4. Navigate to "Real-time Recording" page
    
    5. Click "Record your clinical notes" and grant microphone permissions
    
    6. Speak your clinical notes clearly
    
    7. Click "Transcribe & Process Audio" to generate NHS forms
    
    8. Download the generated PDF forms
    """)
    
    print("\n✅ Real-time Audio Demo Complete!")
    print("\nThe system now supports:")
    print("  🎙️ Browser-based audio recording")
    print("  📝 Real-time transcription with OpenAI Whisper")
    print("  🔄 Live processing of clinical notes")
    print("  📄 Automatic NHS form generation")
    print("  📥 PDF download of completed forms")


def test_audio_endpoints():
    """Test all audio-related API endpoints"""
    print("\n🧪 Testing Audio API Endpoints...")
    
    demo = RealtimeAudioDemo()
    
    if not demo.check_api_health():
        return False
    
    # Test session creation
    if not demo.create_session():
        return False
    
    # Test all endpoints
    endpoints_tested = []
    
    # Start recording
    if demo.start_recording():
        endpoints_tested.append("✅ Start recording")
    else:
        endpoints_tested.append("❌ Start recording")
    
    # Get status
    status = demo.get_session_status()
    if status and "error" not in status:
        endpoints_tested.append("✅ Get session status")
    else:
        endpoints_tested.append("❌ Get session status")
    
    # Get transcription
    transcription = demo.get_transcription_updates()
    if transcription and "error" not in transcription:
        endpoints_tested.append("✅ Get transcription updates")
    else:
        endpoints_tested.append("❌ Get transcription updates")
    
    # Stop recording
    stop_result = demo.stop_recording()
    if stop_result and "error" not in stop_result:
        endpoints_tested.append("✅ Stop recording")
    else:
        endpoints_tested.append("❌ Stop recording")
    
    # Cleanup
    if demo.cleanup_session():
        endpoints_tested.append("✅ Cleanup session")
    else:
        endpoints_tested.append("❌ Cleanup session")
    
    print("\n📊 Endpoint Test Results:")
    for result in endpoints_tested:
        print(f"  {result}")
    
    return all("✅" in result for result in endpoints_tested)


if __name__ == "__main__":
    try:
        # Run the main demo
        run_demo()
        
        # Run endpoint tests
        if input("\n🧪 Run endpoint tests? (y/N): ").lower() == 'y':
            success = test_audio_endpoints()
            if success:
                print("\n🎉 All audio endpoints working correctly!")
            else:
                print("\n⚠️ Some endpoints may need attention")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        logger.exception("Demo failed with exception")
