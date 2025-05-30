"""
Abstract base class for Vision-Language Models used in MOT data extraction.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import base64
from PIL import Image
import io


@dataclass
class ExtractionResult:
    """Result from vision model extraction."""
    registration: str
    mot_expiry: str
    make: str
    model: str
    customer_name: str
    customer_phone: str
    customer_email: str
    confidence_scores: Dict[str, float]
    software_detected: str
    raw_response: str
    processing_time: float
    model_name: str


@dataclass
class ModelConfig:
    """Configuration for vision models."""
    api_key: str
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 60


class BaseVisionModel(ABC):
    """Abstract base class for vision-language models."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model_name = config.model_name
        
    @abstractmethod
    async def extract_mot_data(self, image_path: str) -> ExtractionResult:
        """
        Extract MOT data from garage management software screenshot.
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            ExtractionResult with extracted data and confidence scores
        """
        pass
    
    @abstractmethod
    def _prepare_image(self, image_path: str) -> str:
        """
        Prepare image for the specific model's requirements.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Prepared image data (base64, URL, etc.)
        """
        pass
    
    @abstractmethod
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the model's response into structured data.
        
        Args:
            response: Raw response from the model
            
        Returns:
            Parsed data dictionary
        """
        pass
    
    def _encode_image_base64(self, image_path: str, max_size: tuple = (2048, 2048)) -> str:
        """
        Encode image to base64 with optional resizing.
        
        Args:
            image_path: Path to the image
            max_size: Maximum dimensions (width, height)
            
        Returns:
            Base64 encoded image string
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=95)
                img_bytes = buffer.getvalue()
                
                return base64.b64encode(img_bytes).decode('utf-8')
                
        except Exception as e:
            raise ValueError(f"Failed to encode image: {str(e)}")
    
    def _validate_extraction_result(self, data: Dict[str, Any]) -> bool:
        """
        Validate that extraction result has required fields.
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'registration', 'mot_expiry', 'make', 'model',
            'customer_name', 'customer_phone', 'customer_email',
            'confidence_scores'
        ]
        
        for field in required_fields:
            if field not in data:
                return False
                
        # Validate confidence_scores structure
        if not isinstance(data['confidence_scores'], dict):
            return False
            
        confidence_fields = [
            'registration', 'mot_expiry', 'make', 'model',
            'customer_name', 'customer_phone', 'customer_email'
        ]
        
        for field in confidence_fields:
            if field not in data['confidence_scores']:
                return False
            if not isinstance(data['confidence_scores'][field], (int, float)):
                return False
            if not 0 <= data['confidence_scores'][field] <= 1:
                return False
                
        return True
    
    def _create_extraction_result(
        self, 
        data: Dict[str, Any], 
        raw_response: str, 
        processing_time: float
    ) -> ExtractionResult:
        """
        Create ExtractionResult from parsed data.
        
        Args:
            data: Parsed extraction data
            raw_response: Raw model response
            processing_time: Time taken for processing
            
        Returns:
            ExtractionResult object
        """
        return ExtractionResult(
            registration=data.get('registration', 'NOT_FOUND'),
            mot_expiry=data.get('mot_expiry', 'NOT_FOUND'),
            make=data.get('make', 'NOT_FOUND'),
            model=data.get('model', 'NOT_FOUND'),
            customer_name=data.get('customer_name', 'NOT_FOUND'),
            customer_phone=data.get('customer_phone', 'NOT_FOUND'),
            customer_email=data.get('customer_email', 'NOT_FOUND'),
            confidence_scores=data.get('confidence_scores', {}),
            software_detected=data.get('software_detected', 'UNKNOWN'),
            raw_response=raw_response,
            processing_time=processing_time,
            model_name=self.model_name
        )


class VisionModelError(Exception):
    """Custom exception for vision model errors."""
    pass


class VisionModelTimeoutError(VisionModelError):
    """Exception for model timeout errors."""
    pass


class VisionModelAPIError(VisionModelError):
    """Exception for API-related errors."""
    pass
