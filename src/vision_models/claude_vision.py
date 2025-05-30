"""
Claude 3.5 Sonnet Vision implementation for MOT data extraction.
"""
import json
import time
import asyncio
from typing import Dict, Any
import anthropic
from .base_vision_model import BaseVisionModel, ExtractionResult, ModelConfig, VisionModelError, VisionModelAPIError


class ClaudeVisionModel(BaseVisionModel):
    """Claude 3.5 Sonnet Vision model for MOT data extraction."""
    
    EXTRACTION_PROMPT = """
You are an expert at extracting MOT reminder data from garage management software screenshots with extreme precision.

Analyze this screenshot and extract the following information:

1. Vehicle Registration Number (UK format: AB12 CDE, A123 BCD, etc.)
2. MOT Expiry Date (DD/MM/YYYY format)
3. Vehicle Make
4. Vehicle Model  
5. Customer Name
6. Customer Phone Number
7. Customer Email Address

CRITICAL REQUIREMENTS:
- UK registration numbers follow specific patterns (AB12 CDE, A123 BCD, ABC 123D, 1234 AB)
- Dates must be in DD/MM/YYYY format
- If any field is unclear, missing, or you're not confident, use "NOT_FOUND"
- Provide confidence score (0.0-1.0) for each field based on clarity and certainty
- Try to identify the garage management software being used

IMPORTANT: Look carefully at the entire screenshot. Data might be in tables, forms, or scattered across the interface.

Return ONLY a valid JSON object with this exact structure:
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
        self.client = anthropic.Anthropic(api_key=config.api_key)
    
    async def extract_mot_data(self, image_path: str) -> ExtractionResult:
        """
        Extract MOT data using Claude 3.5 Sonnet Vision.
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            ExtractionResult with extracted data and confidence scores
        """
        start_time = time.time()
        
        try:
            # Prepare image
            image_data = self._prepare_image(image_path)
            
            # Create message with image
            message = await self._call_claude_api(image_data)
            
            # Parse response
            parsed_data = self._parse_response(message.content[0].text)
            
            processing_time = time.time() - start_time
            
            return self._create_extraction_result(
                parsed_data, 
                message.content[0].text, 
                processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            raise VisionModelError(f"Claude extraction failed: {str(e)}") from e
    
    def _prepare_image(self, image_path: str) -> str:
        """
        Prepare image for Claude API (base64 encoding).
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        return self._encode_image_base64(image_path, max_size=(2048, 2048))
    
    async def _call_claude_api(self, image_data: str) -> Any:
        """
        Call Claude API with image and prompt.
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            Claude API response
        """
        try:
            # Run the synchronous API call in a thread pool
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.config.model_name,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_data
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": self.EXTRACTION_PROMPT
                                }
                            ]
                        }
                    ]
                )
            )
            return message
            
        except anthropic.APIError as e:
            raise VisionModelAPIError(f"Claude API error: {str(e)}") from e
        except Exception as e:
            raise VisionModelError(f"Unexpected error calling Claude API: {str(e)}") from e
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Claude's JSON response.
        
        Args:
            response: Raw response from Claude
            
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
                raise ValueError("Invalid response structure from Claude")
            
            return data
            
        except json.JSONDecodeError as e:
            raise VisionModelError(f"Failed to parse Claude JSON response: {str(e)}") from e
        except Exception as e:
            raise VisionModelError(f"Failed to parse Claude response: {str(e)}") from e
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Claude model."""
        return {
            "name": "Claude 3.5 Sonnet Vision",
            "provider": "Anthropic",
            "model_id": self.config.model_name,
            "capabilities": [
                "high_accuracy_ocr",
                "context_understanding", 
                "structured_extraction",
                "confidence_scoring"
            ],
            "max_image_size": "2048x2048",
            "supported_formats": ["JPEG", "PNG", "WebP", "GIF"]
        }
