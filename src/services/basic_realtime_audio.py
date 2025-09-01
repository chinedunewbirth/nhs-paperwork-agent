"""
Basic Real-time Audio Service for NHS Paperwork Automation Agent
Simplified version using only standard libraries and OpenAI
"""

import json
import logging
import tempfile
import os
import time
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from queue import Queue
import asyncio

from openai import OpenAI

logger = logging.getLogger(__name__)


class BasicAudioSession:
    """Basic audio session management without complex buffering"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.is_recording = False
        self.recording_start_time = None
        self.recording_end_time = None
        self.transcription_segments = []
        self.full_transcription = ""
        self.transcription_queue = Queue()
        self.audio_buffer = bytearray()
        self.last_transcription_time = None
    
    def start_recording(self):
        """Start recording session"""
        self.is_recording = True
        self.recording_start_time = time.time()
        logger.info(f"Started recording for session: {self.session_id}")
    
    def stop_recording(self):
        """Stop recording session"""
        self.is_recording = False
        self.recording_end_time = time.time()
        logger.info(f"Stopped recording for session: {self.session_id}")
    
    def add_transcription_segment(self, text: str, confidence: float = 0.9):
        """Add a transcription segment"""
        segment = {
            "text": text.strip(),
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "session_id": self.session_id
        }
        
        self.transcription_segments.append(segment)
        self.full_transcription += " " + text.strip()
        self.transcription_queue.put(segment)
        self.last_transcription_time = time.time()
        
        logger.info(f"Added transcription segment: {text[:50]}...")
    
    def add_audio_data(self, audio_data: bytes):
        """Add audio data to buffer"""
        self.audio_buffer.extend(audio_data)
    
    def get_audio_buffer_size(self) -> int:
        """Get current audio buffer size"""
        return len(self.audio_buffer)
    
    def clear_audio_buffer(self):
        """Clear the audio buffer"""
        self.audio_buffer.clear()
    
    def get_recording_duration(self) -> float:
        """Get total recording duration"""
        if not self.recording_start_time:
            return 0.0
        
        end_time = self.recording_end_time or time.time()
        return end_time - self.recording_start_time
    
    def get_status(self) -> Dict[str, Any]:
        """Get session status"""
        return {
            "session_id": self.session_id,
            "is_recording": self.is_recording,
            "created_at": self.created_at.isoformat(),
            "recording_duration": self.get_recording_duration(),
            "segment_count": len(self.transcription_segments),
            "full_transcription": self.full_transcription.strip(),
            "audio_buffer_size": len(self.audio_buffer),
            "last_transcription": self.last_transcription_time
        }


class BasicRealtimeAudioService:
    """Basic real-time audio service with OpenAI Whisper integration"""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.sessions: Dict[str, BasicAudioSession] = {}
        self.transcription_model = "whisper-1"
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new audio session"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = BasicAudioSession(session_id)
        logger.info(f"Created basic audio session: {session_id}")
        return session_id
    
    def start_recording(self, session_id: str) -> bool:
        """Start recording for a session"""
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return False
        
        self.sessions[session_id].start_recording()
        return True
    
    def stop_recording(self, session_id: str) -> bool:
        """Stop recording for a session"""
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return False
        
        self.sessions[session_id].stop_recording()
        return True
    
    async def process_audio_data(self, session_id: str, audio_data: bytes) -> Dict[str, Any]:
        """Process streaming audio data"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        # Add audio data to buffer
        session.add_audio_data(audio_data)
        
        # Estimate if we have enough audio for transcription (rough estimate)
        buffer_size = session.get_audio_buffer_size()
        estimated_duration = buffer_size / (16000 * 2)  # Assuming 16kHz, 16-bit
        
        # Transcribe if we have enough audio (every 3 seconds or so)
        if estimated_duration >= 3.0:
            try:
                # Create temporary WAV file from buffer
                temp_path = await self._create_temp_wav_from_buffer(session.audio_buffer)
                
                if temp_path:
                    # Transcribe the audio
                    transcription_result = self.transcribe_audio_file(session_id, temp_path)
                    
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    
                    # Clear buffer after transcription
                    session.clear_audio_buffer()
                    
                    return {
                        "status": "processed",
                        "transcription_result": transcription_result,
                        "buffer_cleared": True
                    }
            
            except Exception as e:
                logger.error(f"Error processing audio data: {str(e)}")
                return {"error": f"Processing failed: {str(e)}"}
        
        return {
            "status": "buffering",
            "buffer_size": buffer_size,
            "estimated_duration": estimated_duration
        }
    
    async def _create_temp_wav_from_buffer(self, audio_buffer: bytearray) -> Optional[str]:
        """Create a temporary WAV file from audio buffer"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write basic WAV header (16kHz, 16-bit, mono)
                sample_rate = 16000
                bits_per_sample = 16
                channels = 1
                
                # WAV header
                temp_file.write(b'RIFF')
                temp_file.write((len(audio_buffer) + 36).to_bytes(4, 'little'))
                temp_file.write(b'WAVE')
                temp_file.write(b'fmt ')
                temp_file.write((16).to_bytes(4, 'little'))
                temp_file.write((1).to_bytes(2, 'little'))  # PCM
                temp_file.write(channels.to_bytes(2, 'little'))
                temp_file.write(sample_rate.to_bytes(4, 'little'))
                temp_file.write((sample_rate * channels * bits_per_sample // 8).to_bytes(4, 'little'))
                temp_file.write((channels * bits_per_sample // 8).to_bytes(2, 'little'))
                temp_file.write(bits_per_sample.to_bytes(2, 'little'))
                temp_file.write(b'data')
                temp_file.write(len(audio_buffer).to_bytes(4, 'little'))
                temp_file.write(audio_buffer)
                
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Error creating temp WAV file: {str(e)}")
            return None
    
    def transcribe_audio_file(self, session_id: str, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe an audio file and add to session"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        try:
            # Transcribe with Whisper
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.transcription_model,
                    file=audio_file,
                    response_format="verbose_json",
                    language="en"
                )
            
            # Add transcription to session
            if transcript.text.strip():
                confidence = getattr(transcript, 'confidence', 0.9)
                session.add_transcription_segment(transcript.text.strip(), confidence)
                
                return {
                    "status": "success",
                    "text": transcript.text.strip(),
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"status": "no_speech", "message": "No speech detected in audio"}
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return {"error": str(e)}
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        return self.sessions[session_id].get_status()
    
    def get_live_transcription(self, session_id: str) -> Dict[str, Any]:
        """Get live transcription updates"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        # Get new segments from queue
        new_segments = []
        while not session.transcription_queue.empty():
            try:
                segment = session.transcription_queue.get_nowait()
                new_segments.append(segment)
            except:
                break
        
        return {
            "session_id": session_id,
            "is_recording": session.is_recording,
            "new_segments": new_segments,
            "full_transcription": session.full_transcription.strip(),
            "segment_count": len(session.transcription_segments)
        }
    
    def get_final_transcription(self, session_id: str) -> Optional[str]:
        """Get final transcription for session"""
        if session_id not in self.sessions:
            return None
        
        return self.sessions[session_id].full_transcription.strip()
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up basic audio session: {session_id}")
            return True
        return False


class BasicRealtimeTranscriptionManager:
    """Basic manager for real-time transcription sessions"""
    
    def __init__(self, openai_api_key: str):
        self.audio_service = BasicRealtimeAudioService(openai_api_key)
        self.active_sessions = set()
    
    async def create_session(self, user_id: Optional[str] = None) -> str:
        """Create new transcription session"""
        session_id = self.audio_service.create_session()
        self.active_sessions.add(session_id)
        
        logger.info(f"Created basic transcription session {session_id}")
        return session_id
    
    async def start_recording(self, session_id: str) -> Dict[str, Any]:
        """Start recording"""
        success = self.audio_service.start_recording(session_id)
        
        if success:
            return {
                "status": "recording_started",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Failed to start recording"
            }
    
    async def stop_recording(self, session_id: str) -> Dict[str, Any]:
        """Stop recording"""
        success = self.audio_service.stop_recording(session_id)
        
        if success:
            final_transcription = self.audio_service.get_final_transcription(session_id)
            
            return {
                "status": "recording_stopped",
                "session_id": session_id,
                "final_transcription": final_transcription,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Failed to stop recording"
            }
    
    async def process_audio_data(self, session_id: str, audio_data: bytes) -> Dict[str, Any]:
        """Process streaming audio data"""
        return await self.audio_service.process_audio_data(session_id, audio_data)
    
    async def transcribe_uploaded_audio(self, session_id: str, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe uploaded audio file"""
        return self.audio_service.transcribe_audio_file(session_id, audio_file_path)
    
    async def get_transcription_updates(self, session_id: str) -> Dict[str, Any]:
        """Get transcription updates"""
        return self.audio_service.get_live_transcription(session_id)
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session information"""
        return self.audio_service.get_session_status(session_id)
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up session"""
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
        
        return self.audio_service.cleanup_session(session_id)
    
    def get_active_sessions(self) -> List[str]:
        """Get active session IDs"""
        return list(self.active_sessions)


# Global instance
_basic_transcription_manager: Optional[BasicRealtimeTranscriptionManager] = None


def get_basic_transcription_manager(openai_api_key: str) -> BasicRealtimeTranscriptionManager:
    """Get or create basic transcription manager"""
    global _basic_transcription_manager
    
    if _basic_transcription_manager is None:
        _basic_transcription_manager = BasicRealtimeTranscriptionManager(openai_api_key)
    
    return _basic_transcription_manager


def cleanup_all_basic_sessions():
    """Clean up all basic sessions"""
    global _basic_transcription_manager
    
    if _basic_transcription_manager:
        for session_id in _basic_transcription_manager.get_active_sessions():
            _basic_transcription_manager.cleanup_session(session_id)
        
        logger.info("Cleaned up all basic transcription sessions")
