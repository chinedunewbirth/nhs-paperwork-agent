"""
Real-time Audio Recording and Transcription Service
Handles real-time audio capture, streaming, and live transcription for NHS paperwork automation
"""

import asyncio
import json
import logging
import tempfile
import os
import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import uuid
import threading
from queue import Queue
import io

from openai import OpenAI
try:
    import numpy as np
    import soundfile as sf
    import librosa
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    print("Audio processing libraries not available. Using basic functionality only.")

logger = logging.getLogger(__name__)


class AudioBuffer:
    """Ring buffer for audio data with configurable size"""
    
    def __init__(self, sample_rate: int = 16000, buffer_duration: float = 30.0):
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_duration)
        if AUDIO_LIBS_AVAILABLE:
            self.buffer = np.zeros(self.buffer_size, dtype=np.float32)
        else:
            self.buffer = [0.0] * self.buffer_size
        self.write_index = 0
        self.is_full = False
        
    def write(self, audio_data):
        """Write audio data to the ring buffer"""
        data_length = len(audio_data)
        
        if data_length >= self.buffer_size:
            # If data is larger than buffer, keep only the last buffer_size samples
            self.buffer = audio_data[-self.buffer_size:].copy()
            self.write_index = 0
            self.is_full = True
        else:
            # Normal case: append data to buffer
            end_index = self.write_index + data_length
            
            if end_index <= self.buffer_size:
                # Data fits without wrapping
                self.buffer[self.write_index:end_index] = audio_data
                self.write_index = end_index % self.buffer_size
            else:
                # Data wraps around
                first_chunk_size = self.buffer_size - self.write_index
                self.buffer[self.write_index:] = audio_data[:first_chunk_size]
                self.buffer[:data_length - first_chunk_size] = audio_data[first_chunk_size:]
                self.write_index = data_length - first_chunk_size
                self.is_full = True
    
    def read_last_seconds(self, duration: float):
        """Read the last N seconds of audio from the buffer"""
        samples = int(self.sample_rate * duration)
        samples = min(samples, self.buffer_size)
        
        if not self.is_full and self.write_index < samples:
            # Not enough data yet
            return self.buffer[:self.write_index].copy()
        
        if self.write_index >= samples:
            # Data is contiguous
            return self.buffer[self.write_index - samples:self.write_index].copy()
        else:
            # Data wraps around
            first_part = self.buffer[self.buffer_size - (samples - self.write_index):]
            second_part = self.buffer[:self.write_index]
            return np.concatenate([first_part, second_part])


class RealtimeAudioService:
    """Service for real-time audio recording and transcription"""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.transcription_model = "whisper-1"
        
        # Audio configuration
        self.sample_rate = 16000
        self.chunk_duration = 3.0  # Transcribe every 3 seconds
        self.buffer_duration = 30.0  # Keep 30 seconds of audio
        
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new real-time audio session"""
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "is_recording": False,
            "audio_buffer": AudioBuffer(self.sample_rate, self.buffer_duration),
            "transcription_queue": Queue(),
            "full_transcription": "",
            "transcription_segments": [],
            "last_transcription_time": 0,
            "callback": None
        }
        
        logger.info(f"Created audio session: {session_id}")
        return session_id
    
    def start_recording(self, session_id: str) -> bool:
        """Start recording for a session"""
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return False
            
        session = self.sessions[session_id]
        session["is_recording"] = True
        session["recording_start_time"] = time.time()
        
        logger.info(f"Started recording for session: {session_id}")
        return True
    
    def stop_recording(self, session_id: str) -> bool:
        """Stop recording for a session"""
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return False
            
        session = self.sessions[session_id]
        session["is_recording"] = False
        
        # Process any remaining audio
        self._process_final_audio_chunk(session_id)
        
        logger.info(f"Stopped recording for session: {session_id}")
        return True
    
    def process_audio_chunk(self, session_id: str, audio_data: bytes) -> Dict[str, Any]:
        """Process an incoming audio chunk"""
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return {"error": "Session not found"}
            
        session = self.sessions[session_id]
        
        if not session["is_recording"]:
            return {"error": "Session not recording"}
        
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # Add to buffer
            session["audio_buffer"].write(audio_array)
            
            # Check if it's time for transcription
            current_time = time.time()
            if current_time - session["last_transcription_time"] >= self.chunk_duration:
                self._transcribe_audio_chunk(session_id)
                session["last_transcription_time"] = current_time
            
            return {
                "status": "success",
                "buffer_level": self._get_buffer_level(session_id),
                "timestamp": current_time
            }
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {str(e)}")
            return {"error": str(e)}
    
    def _transcribe_audio_chunk(self, session_id: str):
        """Transcribe the latest audio chunk"""
        session = self.sessions[session_id]
        
        try:
            # Get last few seconds of audio
            audio_data = session["audio_buffer"].read_last_seconds(self.chunk_duration)
            
            if len(audio_data) < self.sample_rate * 0.5:  # Less than 0.5 seconds
                return  # Not enough audio to transcribe
            
            # Create temporary file for whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, self.sample_rate)
                temp_path = temp_file.name
            
            # Transcribe with Whisper
            with open(temp_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.transcription_model,
                    file=audio_file,
                    response_format="verbose_json",
                    language="en"
                )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Process transcription result
            if transcript.text.strip():
                segment = {
                    "text": transcript.text.strip(),
                    "timestamp": datetime.now().isoformat(),
                    "confidence": getattr(transcript, 'confidence', 0.9),
                    "duration": len(audio_data) / self.sample_rate
                }
                
                session["transcription_segments"].append(segment)
                session["full_transcription"] += " " + transcript.text.strip()
                
                # Add to queue for real-time updates
                session["transcription_queue"].put(segment)
                
                logger.info(f"Transcribed chunk for session {session_id}: {transcript.text[:50]}...")
                
        except Exception as e:
            logger.error(f"Error transcribing audio chunk: {str(e)}")
    
    def _process_final_audio_chunk(self, session_id: str):
        """Process any remaining audio when recording stops"""
        session = self.sessions[session_id]
        
        try:
            # Get all remaining audio
            audio_data = session["audio_buffer"].read_last_seconds(self.buffer_duration)
            
            if len(audio_data) < self.sample_rate * 0.5:
                return
            
            # Create temporary file for whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, self.sample_rate)
                temp_path = temp_file.name
            
            # Final transcription
            with open(temp_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.transcription_model,
                    file=audio_file,
                    response_format="text"
                )
            
            # Clean up
            os.unlink(temp_path)
            
            # Update final transcription
            if transcript.strip():
                session["final_transcription"] = transcript.strip()
                logger.info(f"Final transcription completed for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error in final transcription: {str(e)}")
    
    def get_live_transcription(self, session_id: str) -> Dict[str, Any]:
        """Get the latest transcription updates"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        # Get new segments from queue
        new_segments = []
        while not session["transcription_queue"].empty():
            try:
                segment = session["transcription_queue"].get_nowait()
                new_segments.append(segment)
            except:
                break
        
        return {
            "session_id": session_id,
            "is_recording": session["is_recording"],
            "new_segments": new_segments,
            "full_transcription": session["full_transcription"].strip(),
            "segment_count": len(session["transcription_segments"]),
            "buffer_level": self._get_buffer_level(session_id)
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "is_recording": session["is_recording"],
            "created_at": session["created_at"].isoformat(),
            "full_transcription": session["full_transcription"].strip(),
            "segment_count": len(session["transcription_segments"]),
            "recording_duration": self._get_recording_duration(session_id),
            "buffer_level": self._get_buffer_level(session_id)
        }
    
    def get_final_transcription(self, session_id: str) -> Optional[str]:
        """Get the complete transcription for a session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Return final transcription if available, otherwise return accumulated transcription
        return session.get("final_transcription", session["full_transcription"].strip())
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up a session and free resources"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up session: {session_id}")
            return True
        return False
    
    def _get_buffer_level(self, session_id: str) -> float:
        """Get current buffer fill level (0.0 to 1.0)"""
        if session_id not in self.sessions:
            return 0.0
        
        session = self.sessions[session_id]
        buffer = session["audio_buffer"]
        
        if buffer.is_full:
            return 1.0
        else:
            return buffer.write_index / buffer.buffer_size
    
    def _get_recording_duration(self, session_id: str) -> float:
        """Get recording duration in seconds"""
        if session_id not in self.sessions:
            return 0.0
        
        session = self.sessions[session_id]
        start_time = session.get("recording_start_time")
        
        if start_time and session["is_recording"]:
            return time.time() - start_time
        elif start_time:
            return session.get("recording_end_time", time.time()) - start_time
        else:
            return 0.0


class AudioStreamProcessor:
    """Processes audio streams with voice activity detection"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.frame_duration = 0.02  # 20ms frames
        self.frame_size = int(sample_rate * self.frame_duration)
        
        # Voice activity detection parameters
        self.vad_threshold = 0.01  # RMS threshold for voice detection
        self.silence_timeout = 2.0  # Seconds of silence before auto-processing
        
    def detect_voice_activity(self, audio_data: np.ndarray) -> bool:
        """Simple voice activity detection based on RMS energy"""
        if len(audio_data) == 0:
            return False
        
        rms = np.sqrt(np.mean(audio_data ** 2))
        return rms > self.vad_threshold
    
    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Preprocess audio for better transcription quality"""
        # Normalize audio
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data)) * 0.95
        
        # Apply simple noise reduction (basic high-pass filter)
        if len(audio_data) > 100:
            audio_data = librosa.effects.preemphasis(audio_data)
        
        return audio_data


class RealtimeTranscriptionManager:
    """Manages multiple real-time transcription sessions"""
    
    def __init__(self, openai_api_key: str):
        self.audio_service = RealtimeAudioService(openai_api_key)
        self.processor = AudioStreamProcessor()
        self.active_sessions = set()
        
    async def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new transcription session"""
        session_id = self.audio_service.create_session()
        self.active_sessions.add(session_id)
        
        logger.info(f"Created transcription session {session_id} for user {user_id}")
        return session_id
    
    async def start_recording(self, session_id: str) -> Dict[str, Any]:
        """Start recording for a session"""
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
        """Stop recording for a session"""
        success = self.audio_service.stop_recording(session_id)
        
        if success:
            # Get final transcription
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
    
    async def process_audio_data(self, session_id: str, audio_bytes: bytes) -> Dict[str, Any]:
        """Process incoming audio data"""
        try:
            # Convert bytes to numpy array (assuming float32 PCM)
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            
            # Preprocess audio
            processed_audio = self.processor.preprocess_audio(audio_array)
            
            # Convert back to bytes
            processed_bytes = processed_audio.tobytes()
            
            # Process through audio service
            result = self.audio_service.process_audio_chunk(session_id, processed_bytes)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio data: {str(e)}")
            return {"error": str(e)}
    
    async def get_transcription_updates(self, session_id: str) -> Dict[str, Any]:
        """Get live transcription updates"""
        return self.audio_service.get_live_transcription(session_id)
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session information"""
        return self.audio_service.get_session_status(session_id)
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up a session"""
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
        
        return self.audio_service.cleanup_session(session_id)
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.active_sessions)


# Global instance for the application
_transcription_manager: Optional[RealtimeTranscriptionManager] = None


def get_transcription_manager(openai_api_key: str) -> RealtimeTranscriptionManager:
    """Get or create the global transcription manager"""
    global _transcription_manager
    
    if _transcription_manager is None:
        _transcription_manager = RealtimeTranscriptionManager(openai_api_key)
    
    return _transcription_manager


def cleanup_all_sessions():
    """Clean up all active sessions"""
    global _transcription_manager
    
    if _transcription_manager:
        for session_id in _transcription_manager.get_active_sessions():
            _transcription_manager.cleanup_session(session_id)
        
        logger.info("Cleaned up all transcription sessions")
