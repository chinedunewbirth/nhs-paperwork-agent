"""
FastAPI Backend for NHS Paperwork Automation Agent
Main application with REST API endpoints
"""

import os
import uuid
import logging
import json
from typing import List, Optional
from datetime import datetime
import tempfile

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from ..models.schemas import (
    ClinicalNote, 
    ProcessingRequest, 
    ProcessingResponse,
    ExtractedData,
    FormTypeEnum,
    FilledForm
)
from ..services.nlp_extraction import NLPExtractionService
from ..services.form_templates import FormTemplateService
from ..services.form_filler import FormFillerService
from ..services.enhanced_pdf_generator import EnhancedPDFGenerator
from ..services.basic_realtime_audio import get_basic_transcription_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
nlp_service: Optional[NLPExtractionService] = None
form_template_service: Optional[FormTemplateService] = None
form_filler_service: Optional[FormFillerService] = None
pdf_generator_service: Optional[EnhancedPDFGenerator] = None
realtime_transcription_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global nlp_service, form_template_service, form_filler_service, pdf_generator_service, realtime_transcription_manager
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
    
    # Initialize services
    nlp_service = NLPExtractionService(openai_api_key) if openai_api_key else None
    form_template_service = FormTemplateService()
    form_filler_service = FormFillerService()
    pdf_generator_service = EnhancedPDFGenerator()
    realtime_transcription_manager = get_basic_transcription_manager(openai_api_key) if openai_api_key else None
    
    logger.info("NHS Paperwork Agent services initialized")
    yield
    
    # Cleanup on shutdown
    if realtime_transcription_manager:
        for session_id in realtime_transcription_manager.get_active_sessions():
            await realtime_transcription_manager.cleanup_session(session_id)
    logger.info("NHS Paperwork Agent services shutting down")


# Create FastAPI app
app = FastAPI(
    title="NHS Paperwork Automation Agent",
    description="AI-powered automation for NHS clinical forms and documentation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_nlp_service() -> NLPExtractionService:
    """Dependency to get NLP service"""
    if nlp_service is None:
        raise HTTPException(status_code=500, detail="NLP service not initialized")
    return nlp_service


def get_form_services() -> tuple:
    """Dependency to get form services"""
    if form_template_service is None or form_filler_service is None:
        raise HTTPException(status_code=500, detail="Form services not initialized")
    return form_template_service, form_filler_service


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "NHS Paperwork Automation Agent API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "nlp": nlp_service is not None,
            "form_templates": form_template_service is not None,
            "form_filler": form_filler_service is not None,
            "pdf_generator": pdf_generator_service is not None
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/extract", response_model=ExtractedData)
async def extract_clinical_data(
    note: ClinicalNote,
    nlp_svc: NLPExtractionService = Depends(get_nlp_service)
):
    """
    Extract structured clinical data from a clinical note
    """
    try:
        extracted_data = nlp_svc.extract_clinical_data(note)
        return extracted_data
    except Exception as e:
        logger.error(f"Error in extract endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/process", response_model=ProcessingResponse)
async def process_clinical_note(
    request: ProcessingRequest,
    nlp_svc: NLPExtractionService = Depends(get_nlp_service),
    form_services: tuple = Depends(get_form_services)
):
    """
    Complete processing pipeline: extract data and generate forms
    """
    start_time = datetime.now()
    request_id = str(uuid.uuid4())
    
    try:
        form_template_svc, form_filler_svc = form_services
        
        # Extract clinical data
        extracted_data = nlp_svc.extract_clinical_data(request.note)
        
        generated_forms = []
        errors = []
        warnings = []
        
        # Generate requested forms
        if request.auto_fill_forms:
            for form_type in request.form_types:
                try:
                    template = form_template_svc.get_template(form_type)
                    if template:
                        filled_form = form_filler_svc.fill_form(template, extracted_data)
                        generated_forms.append(filled_form)
                    else:
                        warnings.append(f"Template not found for form type: {form_type}")
                except Exception as e:
                    errors.append(f"Error generating {form_type} form: {str(e)}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessingResponse(
            request_id=request_id,
            extracted_data=extracted_data,
            generated_forms=generated_forms,
            processing_time=processing_time,
            status="completed" if not errors else "completed_with_errors",
            errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error in process endpoint: {str(e)}")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessingResponse(
            request_id=request_id,
            extracted_data=ExtractedData(
                patient={},
                clinical={},
                extraction_confidence=0.0
            ),
            generated_forms=[],
            processing_time=processing_time,
            status="failed",
            errors=[str(e)]
        )


@app.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    nlp_svc: NLPExtractionService = Depends(get_nlp_service)
):
    """
    Transcribe audio file to text using OpenAI Whisper
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Transcribe audio
        transcribed_text = await nlp_svc.process_audio_note(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return {
            "transcribed_text": transcribed_text,
            "filename": audio_file.filename,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in transcribe endpoint: {str(e)}")
        # Clean up on error
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.get("/templates")
async def get_form_templates(
    form_services: tuple = Depends(get_form_services)
):
    """
    Get all available form templates
    """
    try:
        form_template_svc, _ = form_services
        templates = form_template_svc.get_all_templates()
        
        return {
            "templates": {
                form_type.value: {
                    "form_id": template.form_id,
                    "form_name": template.form_name,
                    "form_type": template.form_type,
                    "field_count": len(template.fields)
                }
                for form_type, template in templates.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in templates endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@app.get("/templates/{form_type}")
async def get_form_template(
    form_type: FormTypeEnum,
    form_services: tuple = Depends(get_form_services)
):
    """
    Get a specific form template with field definitions
    """
    try:
        form_template_svc, _ = form_services
        template = form_template_svc.get_template(form_type)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found for form type: {form_type}")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {form_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@app.post("/forms/fill")
async def fill_specific_form(
    form_type: FormTypeEnum,
    extracted_data: ExtractedData,
    form_services: tuple = Depends(get_form_services)
):
    """
    Fill a specific form with extracted data
    """
    try:
        form_template_svc, form_filler_svc = form_services
        
        template = form_template_svc.get_template(form_type)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found for form type: {form_type}")
        
        filled_form = form_filler_svc.fill_form(template, extracted_data)
        return filled_form
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filling form {form_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fill form: {str(e)}")


@app.post("/forms/pdf")
async def generate_single_form_pdf_json(
    request_data: dict,
    form_services: tuple = Depends(get_form_services)
):
    """
    Generate a PDF for a single filled form - JSON body version
    """
    try:
        form_template_svc, form_filler_svc = form_services
        
        if pdf_generator_service is None:
            raise HTTPException(status_code=500, detail="PDF generator service not initialized")
        
        # Extract parameters from request body
        form_type_str = request_data.get("form_type")
        if not form_type_str:
            raise HTTPException(status_code=400, detail="form_type is required")
        
        # Convert string to FormTypeEnum
        try:
            form_type = FormTypeEnum(form_type_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid form_type: {form_type_str}")
        
        extracted_data_dict = request_data.get("extracted_data")
        if not extracted_data_dict:
            raise HTTPException(status_code=400, detail="extracted_data is required")
        
        # Convert dict to ExtractedData model
        try:
            extracted_data = ExtractedData(**extracted_data_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid extracted_data format: {str(e)}")
        
        include_signature_placeholder = request_data.get("include_signature_placeholder", True)
        
        # Get and fill the template
        template = form_template_svc.get_template(form_type)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found for form type: {form_type}")
        
        filled_form = form_filler_svc.fill_form(template, extracted_data)
        
        # Generate PDF
        pdf_path = pdf_generator_service.generate_single_form_pdf(
            filled_form, 
            include_signature_placeholder=include_signature_placeholder
        )
        
        # Return the PDF file
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{form_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            headers={"Content-Disposition": f"attachment; filename={form_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@app.post("/forms/pdf/{form_type}")
async def generate_single_form_pdf(
    form_type: FormTypeEnum,
    extracted_data: ExtractedData,
    include_signature_placeholder: bool = True,
    form_services: tuple = Depends(get_form_services)
):
    """
    Generate a PDF for a single filled form
    """
    try:
        form_template_svc, form_filler_svc = form_services
        
        if pdf_generator_service is None:
            raise HTTPException(status_code=500, detail="PDF generator service not initialized")
        
        # Get and fill the template
        template = form_template_svc.get_template(form_type)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found for form type: {form_type}")
        
        filled_form = form_filler_svc.fill_form(template, extracted_data)
        
        # Generate PDF
        pdf_path = pdf_generator_service.generate_single_form_pdf(
            filled_form, 
            include_signature_placeholder=include_signature_placeholder
        )
        
        # Return the PDF file
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{form_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            headers={"Content-Disposition": f"attachment; filename={form_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF for form {form_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@app.post("/forms/pdf/bundle")
async def generate_forms_bundle_pdf(
    request_data: dict,
    form_services: tuple = Depends(get_form_services)
):
    """
    Generate a single PDF containing multiple filled forms
    """
    try:
        form_template_svc, form_filler_svc = form_services
        
        if pdf_generator_service is None:
            raise HTTPException(status_code=500, detail="PDF generator service not initialized")
        
        # Extract parameters from request body
        form_types_str = request_data.get("form_types", [])
        if not form_types_str:
            raise HTTPException(status_code=400, detail="form_types is required")
        
        # Convert strings to FormTypeEnum
        try:
            form_types = [FormTypeEnum(ft) for ft in form_types_str]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid form_type in list: {str(e)}")
        
        extracted_data_dict = request_data.get("extracted_data")
        if not extracted_data_dict:
            raise HTTPException(status_code=400, detail="extracted_data is required")
        
        # Convert dict to ExtractedData model
        try:
            extracted_data = ExtractedData(**extracted_data_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid extracted_data format: {str(e)}")
        
        include_signature_placeholder = request_data.get("include_signature_placeholder", True)
        bundle_name = request_data.get("bundle_name")
        
        # Fill all requested forms
        filled_forms = []
        errors = []
        
        for form_type in form_types:
            try:
                template = form_template_svc.get_template(form_type)
                if template:
                    filled_form = form_filler_svc.fill_form(template, extracted_data)
                    filled_forms.append(filled_form)
                else:
                    errors.append(f"Template not found for form type: {form_type}")
            except Exception as e:
                errors.append(f"Error filling {form_type} form: {str(e)}")
        
        if not filled_forms:
            raise HTTPException(status_code=400, detail="No forms could be generated")
        
        # Generate bundle PDF
        bundle_name = bundle_name or f"NHS_Forms_Bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        pdf_path = pdf_generator_service.generate_forms_bundle(
            filled_forms,
            bundle_name=bundle_name,
            include_signature_placeholder=include_signature_placeholder
        )
        
        # Return the PDF file
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{bundle_name}.pdf",
            headers={"Content-Disposition": f"attachment; filename={bundle_name}.pdf"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF bundle: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF bundle: {str(e)}")


@app.post("/forms/pdf/from-note")
async def generate_pdf_from_note(
    note: ClinicalNote,
    form_types: List[FormTypeEnum],
    include_signature_placeholder: bool = True,
    bundle_name: Optional[str] = None,
    nlp_svc: NLPExtractionService = Depends(get_nlp_service),
    form_services: tuple = Depends(get_form_services)
):
    """
    Complete pipeline: Extract data from note and generate PDF forms
    """
    try:
        form_template_svc, form_filler_svc = form_services
        
        if pdf_generator_service is None:
            raise HTTPException(status_code=500, detail="PDF generator service not initialized")
        
        # Extract clinical data from note
        extracted_data = nlp_svc.extract_clinical_data(note)
        
        # Fill all requested forms
        filled_forms = []
        errors = []
        
        for form_type in form_types:
            try:
                template = form_template_svc.get_template(form_type)
                if template:
                    filled_form = form_filler_svc.fill_form(template, extracted_data)
                    filled_forms.append(filled_form)
                else:
                    errors.append(f"Template not found for form type: {form_type}")
            except Exception as e:
                errors.append(f"Error filling {form_type} form: {str(e)}")
        
        if not filled_forms:
            raise HTTPException(status_code=400, detail="No forms could be generated")
        
        # Generate PDF (single form or bundle)
        if len(filled_forms) == 1:
            pdf_path = pdf_generator_service.generate_single_form_pdf(
                filled_forms[0],
                include_signature_placeholder=include_signature_placeholder
            )
            filename = f"{filled_forms[0].form_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            bundle_name = bundle_name or f"NHS_Forms_Bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            pdf_path = pdf_generator_service.generate_forms_bundle(
                filled_forms,
                bundle_name=bundle_name,
                include_signature_placeholder=include_signature_placeholder
            )
            filename = f"{bundle_name}.pdf"
        
        # Return the PDF file
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF from note: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


# Real-time Audio Endpoints

@app.post("/audio/session")
async def create_audio_session():
    """Create a new real-time audio recording session"""
    if realtime_transcription_manager is None:
        raise HTTPException(status_code=500, detail="Real-time transcription service not available")
    
    try:
        session_id = await realtime_transcription_manager.create_session()
        return {
            "session_id": session_id,
            "status": "session_created",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating audio session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.post("/audio/session/{session_id}/start")
async def start_recording(session_id: str):
    """Start recording for a session"""
    if realtime_transcription_manager is None:
        raise HTTPException(status_code=500, detail="Real-time transcription service not available")
    
    try:
        result = await realtime_transcription_manager.start_recording(session_id)
        return result
    except Exception as e:
        logger.error(f"Error starting recording: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")


@app.post("/audio/session/{session_id}/stop")
async def stop_recording(session_id: str):
    """Stop recording for a session"""
    if realtime_transcription_manager is None:
        raise HTTPException(status_code=500, detail="Real-time transcription service not available")
    
    try:
        result = await realtime_transcription_manager.stop_recording(session_id)
        return result
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop recording: {str(e)}")


@app.get("/audio/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session status and transcription"""
    if realtime_transcription_manager is None:
        raise HTTPException(status_code=500, detail="Real-time transcription service not available")
    
    try:
        result = await realtime_transcription_manager.get_session_info(session_id)
        return result
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")


@app.get("/audio/session/{session_id}/transcription")
async def get_transcription_updates(session_id: str):
    """Get live transcription updates"""
    if realtime_transcription_manager is None:
        raise HTTPException(status_code=500, detail="Real-time transcription service not available")
    
    try:
        result = await realtime_transcription_manager.get_transcription_updates(session_id)
        return result
    except Exception as e:
        logger.error(f"Error getting transcription updates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get transcription: {str(e)}")


@app.delete("/audio/session/{session_id}")
async def cleanup_audio_session(session_id: str):
    """Clean up an audio session"""
    if realtime_transcription_manager is None:
        raise HTTPException(status_code=500, detail="Real-time transcription service not available")
    
    try:
        success = await realtime_transcription_manager.cleanup_session(session_id)
        return {
            "session_id": session_id,
            "status": "cleaned_up" if success else "not_found",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning up session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup session: {str(e)}")


# WebSocket endpoint for real-time audio streaming
@app.websocket("/ws/audio/{session_id}")
async def websocket_audio_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio streaming and transcription"""
    await websocket.accept()
    
    if realtime_transcription_manager is None:
        await websocket.send_json({
            "type": "error",
            "message": "Real-time transcription service not available"
        })
        await websocket.close()
        return
    
    try:
        logger.info(f"WebSocket connection established for session: {session_id}")
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                # Receive audio data or control messages
                message = await websocket.receive()
                
                if "bytes" in message:
                    # Process binary audio data
                    audio_bytes = message["bytes"]
                    result = await realtime_transcription_manager.process_audio_data(session_id, audio_bytes)
                    
                    # Send processing result
                    await websocket.send_json({
                        "type": "audio_processed",
                        "result": result
                    })
                    
                    # Check for new transcription updates
                    transcription_update = await realtime_transcription_manager.get_transcription_updates(session_id)
                    if transcription_update.get("new_segments"):
                        await websocket.send_json({
                            "type": "transcription_update",
                            "data": transcription_update
                        })
                
                elif "text" in message:
                    # Handle JSON control messages
                    try:
                        control_data = json.loads(message["text"])
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid JSON in control message"
                        })
                        continue
                    
                    action = control_data.get("action") or control_data.get("type")
                    
                    if action == "start_recording":
                        result = await realtime_transcription_manager.start_recording(session_id)
                        await websocket.send_json({
                            "type": "recording_started",
                            "result": result
                        })
                    
                    elif action == "stop_recording":
                        result = await realtime_transcription_manager.stop_recording(session_id)
                        await websocket.send_json({
                            "type": "recording_stopped",
                            "result": result
                        })
                    
                    elif action == "get_status":
                        status = await realtime_transcription_manager.get_session_info(session_id)
                        await websocket.send_json({
                            "type": "session_status",
                            "data": status
                        })
                    
                    elif action == "audio_chunk":
                        # Handle base64 encoded audio chunks
                        audio_data = control_data.get("audio_data")
                        if audio_data:
                            try:
                                import base64
                                decoded_audio = base64.b64decode(audio_data)
                                result = await realtime_transcription_manager.process_audio_data(session_id, decoded_audio)
                                
                                await websocket.send_json({
                                    "type": "audio_processed",
                                    "result": result
                                })
                                
                                # Check for transcription updates
                                transcription_update = await realtime_transcription_manager.get_transcription_updates(session_id)
                                if transcription_update.get("new_segments"):
                                    await websocket.send_json({
                                        "type": "transcription_update",
                                        "data": transcription_update
                                    })
                            except Exception as e:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"Error processing audio chunk: {str(e)}"
                                })
                    
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Unknown action: {action}"
                        })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session: {session_id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message handling: {str(e)}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except:
                    # Connection might be closed
                    break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        # Clean up session when WebSocket closes
        if realtime_transcription_manager:
            try:
                await realtime_transcription_manager.cleanup_session(session_id)
                logger.info(f"Cleaned up session: {session_id}")
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
