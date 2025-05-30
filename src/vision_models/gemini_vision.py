"""
Google Gemini Pro Vision implementation for MOT data extraction.
"""
import json
import time
import asyncio
from typing import Dict, Any
import google.generativeai as genai
from PIL import Image
from .base_vision_model import BaseVisionModel, ExtractionResult, ModelConfig, VisionModelError, VisionModelAPIError


class GeminiVisionModel(BaseVisionModel):
    """Google Gemini Pro Vision model for MOT data extraction."""
    
    EXTRACTION_PROMPT = """
Analyze this garage management software screenshot and extract MOT reminder data with high precision.

Extract the following information:
1. UK Vehicle Registration Number (formats: AB12 CDE, A123 BCD, ABC 123D, 1234 AB)
2. MOT Expiry Date (DD/MM/YYYY format preferred)
3. Vehicle Make
4. Vehicle Model
5. Customer Name
6. Customer Phone Number
7. Customer Email Address

CRITICAL REQUIREMENTS:
- UK registration numbers must follow specific patterns
- Dates should be in DD/MM/YYYY format
- If any field is unclear or missing, use "NOT_FOUND"
- Provide confidence score (0.0-1.0) for each field
- Examine the entire screenshot carefully

Return ONLY a valid JSON object with this structure:
{
    "registration": "extracted_registration_or_NOT_FOUND",
    "mot_expiry": "DD/MM/YYYY_or_NOT_FOUND",
    "make": "extracted_make_or_NOT_FOUND",
    "model": "extracted_model_or_NOT_FOUND",
    "customer_name": "extracted_name_or_NOT_FOUND",
    "customer_phone": "extracted_phone_or_NOT_FOUND",
    "customer_email": "extracted_email_or_NOT_FOUND",
    "confidence_scores": {
        "registration": 0.0,
        "mot_expiry": 0.0,
        "make": 0.0,
        "model": 0.0,
        "customer_name": 0.0,
        "customer_phone": 0.0,
        "customer_email": 0.0
    },
    "software_detected": "detected_software_name_or_UNKNOWN"
}

Do not include any text before or after the JSON object.
"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model_name)
    
    async def extract_mot_data(self, image_path: str) -> ExtractionResult:
        """
        Extract MOT data using Gemini Pro Vision.
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            ExtractionResult with extracted data and confidence scores
        """
        start_time = time.time()
        
        try:
            # Prepare image
            image = self._prepare_image(image_path)
            
            # Generate content with image and prompt
            response = await self._call_gemini_api(image)
            
            # Parse response
            parsed_data = self._parse_response(response.text)
            
            processing_time = time.time() - start_time
            
            return self._create_extraction_result(
                parsed_data,
                response.text,
                processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            raise VisionModelError(f"Gemini extraction failed: {str(e)}") from e
    
    def _prepare_image(self, image_path: str) -> Image.Image:
        """
        Prepare image for Gemini API.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            PIL Image object
        """
        try:
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            raise ValueError(f"Failed to prepare image: {str(e)}")
    
    async def _call_gemini_api(self, image: Image.Image) -> Any:
        """
        Call Gemini API with image and prompt.
        
        Args:
            image: PIL Image object
            
        Returns:
            Gemini API response
        """
        try:
            # Run the synchronous API call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content([self.EXTRACTION_PROMPT, image])
            )
            
            return response
            
        except Exception as e:
            raise VisionModelAPIError(f"Gemini API error: {str(e)}") from e
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Gemini's JSON response.
        
        Args:
            response: Raw response from Gemini
            
        Returns:
            Parsed data dictionary
        """
        try:
            # Clean the response - remove any text before/after JSON
            response = response.strip()
            
            # Find JSON object boundaries
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")
            
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Validate the response structure
            if not self._validate_extraction_result(data):
                raise ValueError("Invalid response structure from Gemini")
            
            return data
            
        except json.JSONDecodeError as e:
            raise VisionModelError(f"Failed to parse Gemini JSON response: {str(e)}") from e
        except Exception as e:
            raise VisionModelError(f"Failed to parse Gemini response: {str(e)}") from e
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Gemini model."""
        return {
            "name": "Gemini Pro Vision",
            "provider": "Google",
            "model_id": self.config.model_name,
            "capabilities": [
                "multimodal_understanding",
                "structured_extraction",
                "high_accuracy_ocr",
                "context_awareness"
            ],
            "max_image_size": "2048x2048",
            "supported_formats": ["JPEG", "PNG", "WebP", "GIF"]
        }
