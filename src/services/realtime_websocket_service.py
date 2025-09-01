"""
Real-time audio transcription service using WebSockets
Handles streaming audio data and provides live transcription
"""

import asyncio
import json
import logging
import tempfile
import os
from typing import Dict, Any, Optional
from datetime import datetime
import base64

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class RealtimeAudioTranscriber:
    """Handles real-time audio transcription via WebSocket connections"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.audio_buffer = bytearray()
        self.chunk_size = 4096  # Audio chunk size
        self.min_audio_length = 2.0  # Minimum seconds of audio before transcription
        self.session_id = None
        
        if OPENAI_AVAILABLE and self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        
    async def handle_websocket_connection(self, websocket, path):
        """Handle incoming WebSocket connections for real-time audio"""
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"New real-time audio session started: {self.session_id}")
        
        try:
            await websocket.send(json.dumps({
                "type": "connection_established",
                "session_id": self.session_id,
                "message": "Real-time audio transcription ready"
            }))
            
            async for message in websocket:
                await self.process_websocket_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed for session {self.session_id}")
        except Exception as e:
            logger.error(f"WebSocket error in session {self.session_id}: {str(e)}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Error processing audio: {str(e)}"
            }))
    
    async def process_websocket_message(self, websocket, message):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "audio_chunk":
                await self.handle_audio_chunk(websocket, data)
            elif message_type == "start_recording":
                await self.start_recording_session(websocket)
            elif message_type == "stop_recording":
                await self.stop_recording_session(websocket)
            elif message_type == "get_transcription":
                await self.get_current_transcription(websocket)
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON message format"
            }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Processing error: {str(e)}"
            }))
    
    async def handle_audio_chunk(self, websocket, data):
        """Process incoming audio chunk"""
        try:
            # Decode base64 audio data
            audio_data = base64.b64decode(data["audio_data"])
            self.audio_buffer.extend(audio_data)
            
            # Check if we have enough audio data for transcription
            estimated_duration = len(self.audio_buffer) / (16000 * 2)  # Assuming 16kHz, 16-bit
            
            if estimated_duration >= self.min_audio_length:
                # Transcribe the accumulated audio
                transcription = await self.transcribe_audio_buffer()
                
                if transcription:
                    await websocket.send(json.dumps({
                        "type": "transcription_update",
                        "transcription": transcription,
                        "timestamp": datetime.now().isoformat(),
                        "audio_duration": estimated_duration
                    }))
                
                # Clear buffer after transcription
                self.audio_buffer.clear()
            
            # Send acknowledgment
            await websocket.send(json.dumps({
                "type": "chunk_received",
                "buffer_size": len(self.audio_buffer),
                "estimated_duration": estimated_duration
            }))
            
        except Exception as e:
            logger.error(f"Error handling audio chunk: {str(e)}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Error processing audio chunk: {str(e)}"
            }))
    
    async def transcribe_audio_buffer(self) -> Optional[str]:
        """Transcribe the current audio buffer"""
        if not self.client or not self.audio_buffer:
            return None
        
        try:
            # Create temporary WAV file from buffer
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write WAV header (basic 16kHz, 16-bit mono)
                sample_rate = 16000
                bits_per_sample = 16
                channels = 1
                
                # WAV header
                temp_file.write(b'RIFF')
                temp_file.write((len(self.audio_buffer) + 36).to_bytes(4, 'little'))
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
                temp_file.write(len(self.audio_buffer).to_bytes(4, 'little'))
                temp_file.write(self.audio_buffer)
                
                temp_path = temp_file.name
            
            # Transcribe using OpenAI Whisper
            with open(temp_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return transcript.strip() if transcript else None
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return None
    
    async def start_recording_session(self, websocket):
        """Start a new recording session"""
        self.audio_buffer.clear()
        await websocket.send(json.dumps({
            "type": "recording_started",
            "session_id": self.session_id,
            "message": "Recording session started"
        }))
    
    async def stop_recording_session(self, websocket):
        """Stop the current recording session"""
        # Final transcription of any remaining audio
        if self.audio_buffer:
            final_transcription = await self.transcribe_audio_buffer()
            if final_transcription:
                await websocket.send(json.dumps({
                    "type": "final_transcription",
                    "transcription": final_transcription,
                    "timestamp": datetime.now().isoformat()
                }))
        
        self.audio_buffer.clear()
        await websocket.send(json.dumps({
            "type": "recording_stopped",
            "session_id": self.session_id,
            "message": "Recording session ended"
        }))
    
    async def get_current_transcription(self, websocket):
        """Get current transcription without clearing buffer"""
        if self.audio_buffer:
            transcription = await self.transcribe_audio_buffer()
            if transcription:
                await websocket.send(json.dumps({
                    "type": "current_transcription",
                    "transcription": transcription,
                    "timestamp": datetime.now().isoformat(),
                    "is_partial": True
                }))
        else:
            await websocket.send(json.dumps({
                "type": "current_transcription",
                "transcription": "",
                "message": "No audio data available"
            }))


class RealtimeAudioManager:
    """Manager for real-time audio sessions"""
    
    def __init__(self):
        self.active_sessions = {}
        self.transcriber = RealtimeAudioTranscriber()
    
    def create_session(self) -> str:
        """Create a new real-time audio session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.active_sessions[session_id] = {
            "created": datetime.now(),
            "transcriber": RealtimeAudioTranscriber(),
            "accumulated_transcription": ""
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.active_sessions.get(session_id)
    
    def close_session(self, session_id: str):
        """Close and clean up session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_sessions)


# Global manager instance
realtime_manager = RealtimeAudioManager()


def get_realtime_audio_manager() -> RealtimeAudioManager:
    """Get the global real-time audio manager"""
    return realtime_manager


# Simple fallback functions for when WebSockets aren't available
def get_fallback_transcription_status():
    """Fallback status when WebSockets aren't available"""
    return {
        "status": "websockets_unavailable",
        "message": "Real-time transcription requires websockets library",
        "fallback_available": True
    }


def process_audio_chunk_fallback(audio_data: bytes) -> Dict[str, Any]:
    """Fallback processing for audio chunks"""
    return {
        "status": "processed_fallback",
        "message": "Audio chunk received but real-time processing unavailable",
        "chunk_size": len(audio_data)
    }
