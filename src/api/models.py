"""
Pydantic models for API requests and responses.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MOTExtractionRequest(BaseModel):
    """Request model for MOT data extraction."""
    validate_with_dvla: bool = Field(default=True, description="Whether to validate with DVLA API")
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0, description="Minimum confidence threshold")


class ExtractedData(BaseModel):
    """Extracted MOT data."""
    registration: str = Field(description="Vehicle registration number")
    mot_expiry: str = Field(description="MOT expiry date (DD/MM/YYYY)")
    make: str = Field(description="Vehicle make")
    model: str = Field(description="Vehicle model")
    customer_name: str = Field(description="Customer name")
    customer_phone: str = Field(description="Customer phone number")
    customer_email: str = Field(description="Customer email address")


class ConfidenceScores(BaseModel):
    """Confidence scores for extracted fields."""
    registration: float = Field(ge=0.0, le=1.0)
    mot_expiry: float = Field(ge=0.0, le=1.0)
    make: float = Field(ge=0.0, le=1.0)
    model: float = Field(ge=0.0, le=1.0)
    customer_name: float = Field(ge=0.0, le=1.0)
    customer_phone: float = Field(ge=0.0, le=1.0)
    customer_email: float = Field(ge=0.0, le=1.0)


class DVLAVehicleInfo(BaseModel):
    """DVLA vehicle information."""
    registration_number: str
    make: str
    model: str
    colour: str
    fuel_type: str
    engine_capacity: Optional[int] = None
    date_of_first_registration: Optional[str] = None
    year_of_manufacture: Optional[int] = None
    co2_emissions: Optional[int] = None
    mot_status: Optional[str] = None
    mot_expiry_date: Optional[str] = None
    tax_status: Optional[str] = None
    tax_due_date: Optional[str] = None
    type_approval: Optional[str] = None
    wheelplan: Optional[str] = None
    revenue_weight: Optional[int] = None


class DVLAValidation(BaseModel):
    """DVLA validation result."""
    is_valid: bool
    vehicle_info: Optional[DVLAVehicleInfo] = None
    error_message: Optional[str] = None
    response_time: float
    api_status_code: Optional[int] = None


class MOTExtractionResponse(BaseModel):
    """Response model for MOT data extraction."""
    request_id: str = Field(description="Unique request identifier")
    success: bool = Field(description="Whether extraction was successful")
    processing_time: float = Field(description="Total processing time in seconds")
    extracted_data: Dict[str, str] = Field(description="Extracted MOT data")
    confidence_scores: Dict[str, float] = Field(description="Confidence scores for each field")
    software_detected: str = Field(description="Detected garage management software")
    models_used: List[str] = Field(description="Vision models used in extraction")
    agreement_level: float = Field(ge=0.0, le=1.0, description="Agreement level between models")
    validation_results: Dict[str, bool] = Field(description="Field validation results")
    dvla_validation: Optional[Dict[str, Any]] = Field(description="DVLA validation results")
    requires_manual_review: bool = Field(description="Whether manual review is required")
    error_message: Optional[str] = Field(description="Error message if extraction failed")


class ValidationResponse(BaseModel):
    """Response model for registration validation."""
    registration: str = Field(description="Registration number validated")
    is_valid: bool = Field(description="Whether registration is valid")
    dvla_info: Optional[Dict[str, Any]] = Field(description="DVLA vehicle information")
    error_message: Optional[str] = Field(description="Error message if validation failed")
    response_time: float = Field(description="DVLA API response time")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="System status")
    timestamp: float = Field(description="Current timestamp")
    version: str = Field(description="System version")
    models_available: int = Field(description="Number of available vision models")
    dvla_api_configured: bool = Field(description="Whether DVLA API is configured")


class ModelInfo(BaseModel):
    """Information about a vision model."""
    name: str = Field(description="Model name")
    provider: str = Field(description="Model provider")
    model_id: str = Field(description="Model identifier")
    capabilities: List[str] = Field(description="Model capabilities")
    max_image_size: str = Field(description="Maximum supported image size")
    supported_formats: List[str] = Field(description="Supported image formats")


class ModelsInfoResponse(BaseModel):
    """Response for models information."""
    available_models: int = Field(description="Number of available models")
    models: List[ModelInfo] = Field(description="Detailed model information")
    ensemble_strategy: str = Field(description="Ensemble voting strategy")
    model_weights: Dict[str, float] = Field(description="Model weights for ensemble")


class BatchExtractionRequest(BaseModel):
    """Request model for batch MOT data extraction."""
    validate_with_dvla: bool = Field(default=True, description="Whether to validate with DVLA API")
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_concurrent: int = Field(default=3, ge=1, le=10, description="Maximum concurrent processing")


class BatchExtractionResponse(BaseModel):
    """Response model for batch MOT data extraction."""
    batch_id: str = Field(description="Unique batch identifier")
    total_files: int = Field(description="Total number of files processed")
    successful_extractions: int = Field(description="Number of successful extractions")
    failed_extractions: int = Field(description="Number of failed extractions")
    total_processing_time: float = Field(description="Total processing time in seconds")
    results: List[MOTExtractionResponse] = Field(description="Individual extraction results")
    summary: Dict[str, Any] = Field(description="Batch processing summary")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(description="Additional error details")
    timestamp: float = Field(description="Error timestamp")
    request_id: Optional[str] = Field(description="Request ID if available")


class ConfigurationResponse(BaseModel):
    """System configuration response."""
    version: str = Field(description="System version")
    supported_formats: List[str] = Field(description="Supported image formats")
    max_file_size: int = Field(description="Maximum file size in bytes")
    max_image_dimensions: Dict[str, int] = Field(description="Maximum image dimensions")
    confidence_threshold: float = Field(description="Default confidence threshold")
    dvla_validation_enabled: bool = Field(description="Whether DVLA validation is enabled")
    ensemble_models: List[str] = Field(description="Available ensemble models")


# Example responses for documentation
class ExampleResponses:
    """Example responses for API documentation."""
    
    SUCCESSFUL_EXTRACTION = {
        "request_id": "123e4567-e89b-12d3-a456-426614174000",
        "success": True,
        "processing_time": 2.45,
        "extracted_data": {
            "registration": "AB12 CDE",
            "mot_expiry": "15/03/2025",
            "make": "FORD",
            "model": "FOCUS",
            "customer_name": "John Smith",
            "customer_phone": "07123456789",
            "customer_email": "john.smith@email.com"
        },
        "confidence_scores": {
            "registration": 0.98,
            "mot_expiry": 0.95,
            "make": 0.92,
            "model": 0.89,
            "customer_name": 0.87,
            "customer_phone": 0.91,
            "customer_email": 0.94
        },
        "software_detected": "garage_hive",
        "models_used": ["claude-3-5-sonnet", "gpt-4-vision-preview"],
        "agreement_level": 0.94,
        "validation_results": {
            "registration_format": True,
            "date_format": True,
            "dvla_match": True
        },
        "dvla_validation": {
            "is_valid": True,
            "vehicle_info": {
                "make": "FORD",
                "model": "FOCUS",
                "mot_expiry_date": "2025-03-15"
            }
        },
        "requires_manual_review": False,
        "error_message": None
    }
    
    FAILED_EXTRACTION = {
        "request_id": "123e4567-e89b-12d3-a456-426614174001",
        "success": False,
        "processing_time": 1.23,
        "extracted_data": {},
        "confidence_scores": {},
        "software_detected": "UNKNOWN",
        "models_used": [],
        "agreement_level": 0.0,
        "validation_results": {},
        "dvla_validation": None,
        "requires_manual_review": True,
        "error_message": "Unable to process image: insufficient text quality"
    }
