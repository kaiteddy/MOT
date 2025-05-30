"""
FastAPI application for MOT OCR system.
"""
import os
import time
import uuid
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .models import (
    MOTExtractionResponse, 
    MOTExtractionRequest,
    HealthCheckResponse,
    ValidationResponse
)
from ..pipeline.ensemble_pipeline import EnsemblePipeline
from ..dvla.api_client import DVLAAPIClient
from ..utils.file_handler import FileHandler
from ..utils.logger import setup_logger
from config.settings import settings

# Initialize logger
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MOT OCR System",
    description="High-accuracy MOT reminder data extraction using Vision-Language Models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
ensemble_pipeline = EnsemblePipeline()
dvla_client = DVLAAPIClient()
file_handler = FileHandler()


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting MOT OCR System")
    
    # Create necessary directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.results_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("MOT OCR System started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down MOT OCR System")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0",
        models_available=len(ensemble_pipeline.models),
        dvla_api_configured=bool(settings.dvla_api_key)
    )


@app.post("/extract-mot-data", response_model=MOTExtractionResponse)
async def extract_mot_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    validate_with_dvla: bool = True,
    confidence_threshold: float = 0.85
):
    """
    Extract MOT reminder data from garage management software screenshot.
    
    Args:
        file: Screenshot image file
        validate_with_dvla: Whether to validate with DVLA API
        confidence_threshold: Minimum confidence threshold for acceptance
        
    Returns:
        MOTExtractionResponse with extracted data and validation results
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"Processing MOT extraction request {request_id}")
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file_handler.is_valid_image_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {settings.allowed_extensions}"
            )
        
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Save uploaded file
        file_path = await file_handler.save_upload_file(file, request_id)
        
        try:
            # Process with ensemble pipeline
            ensemble_result = await ensemble_pipeline.process_screenshot(file_path)
            
            # DVLA validation if requested and registration found
            dvla_validation = None
            if (validate_with_dvla and 
                ensemble_result.final_extraction.registration != "NOT_FOUND"):
                
                dvla_validation = await dvla_client.validate_registration(
                    ensemble_result.final_extraction.registration
                )
            
            # Calculate final confidence score
            final_confidence = ensemble_result.final_extraction.confidence_scores
            avg_confidence = sum(final_confidence.values()) / len(final_confidence) if final_confidence else 0.0
            
            # Determine if manual review is required
            requires_manual_review = (
                ensemble_result.requires_manual_review or
                avg_confidence < confidence_threshold or
                (dvla_validation and not dvla_validation.is_valid)
            )
            
            processing_time = time.time() - start_time
            
            # Create response
            response = MOTExtractionResponse(
                request_id=request_id,
                success=True,
                processing_time=processing_time,
                extracted_data={
                    "registration": ensemble_result.final_extraction.registration,
                    "mot_expiry": ensemble_result.final_extraction.mot_expiry,
                    "make": ensemble_result.final_extraction.make,
                    "model": ensemble_result.final_extraction.model,
                    "customer_name": ensemble_result.final_extraction.customer_name,
                    "customer_phone": ensemble_result.final_extraction.customer_phone,
                    "customer_email": ensemble_result.final_extraction.customer_email,
                },
                confidence_scores=ensemble_result.final_extraction.confidence_scores,
                software_detected=ensemble_result.final_extraction.software_detected,
                models_used=ensemble_result.models_used,
                agreement_level=ensemble_result.agreement_level,
                validation_results=ensemble_result.validation_results,
                dvla_validation=dvla_validation.__dict__ if dvla_validation else None,
                requires_manual_review=requires_manual_review,
                error_message=None
            )
            
            # Schedule cleanup
            background_tasks.add_task(file_handler.cleanup_file, file_path)
            
            logger.info(f"Successfully processed request {request_id} in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            # Cleanup file on error
            background_tasks.add_task(file_handler.cleanup_file, file_path)
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing request {request_id}: {str(e)}")
        
        return MOTExtractionResponse(
            request_id=request_id,
            success=False,
            processing_time=processing_time,
            extracted_data={},
            confidence_scores={},
            software_detected="UNKNOWN",
            models_used=[],
            agreement_level=0.0,
            validation_results={},
            dvla_validation=None,
            requires_manual_review=True,
            error_message=str(e)
        )


@app.post("/validate-registration", response_model=ValidationResponse)
async def validate_registration(registration: str):
    """
    Validate a UK vehicle registration number.
    
    Args:
        registration: Vehicle registration number to validate
        
    Returns:
        ValidationResponse with validation results
    """
    try:
        # Validate with DVLA
        dvla_result = await dvla_client.validate_registration(registration)
        
        return ValidationResponse(
            registration=registration,
            is_valid=dvla_result.is_valid,
            dvla_info=dvla_result.vehicle_info.__dict__ if dvla_result.vehicle_info else None,
            error_message=dvla_result.error_message,
            response_time=dvla_result.response_time
        )
        
    except Exception as e:
        logger.error(f"Error validating registration {registration}: {str(e)}")
        return ValidationResponse(
            registration=registration,
            is_valid=False,
            dvla_info=None,
            error_message=str(e),
            response_time=0.0
        )


@app.get("/models/info")
async def get_models_info():
    """Get information about available vision models."""
    models_info = []
    
    for model in ensemble_pipeline.models:
        if hasattr(model, 'get_model_info'):
            models_info.append(model.get_model_info())
    
    return {
        "available_models": len(ensemble_pipeline.models),
        "models": models_info,
        "ensemble_strategy": settings.ensemble_voting_strategy,
        "model_weights": settings.model_weights
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower()
    )
