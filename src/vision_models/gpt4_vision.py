"""
GPT-4 Vision implementation for MOT data extraction.
"""
import json
import time
import asyncio
from typing import Dict, Any
import openai
from .base_vision_model import BaseVisionModel, ExtractionResult, ModelConfig, VisionModelError, VisionModelAPIError


class GPT4VisionModel(BaseVisionModel):
    """GPT-4 Vision model for MOT data extraction."""
    
    EXTRACTION_PROMPT = """
Extract MOT reminder data from this garage management software screenshot with maximum precision.

Required information to extract:
1. UK Vehicle Registration Number (formats: AB12 CDE, A123 BCD, ABC 123D, 1234 AB)
2. MOT Expiry Date (DD/MM/YYYY format)
3. Vehicle Make
4. Vehicle Model
5. Customer Name
6. Customer Phone Number  
7. Customer Email Address

Instructions:
- Examine the entire screenshot carefully for relevant data
- UK registration numbers have specific patterns - validate format
- Use "NOT_FOUND" for any unclear or missing fields
- Provide confidence scores (0.0-1.0) based on text clarity
- Identify the garage software if possible

Return ONLY valid JSON in this exact format:
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
    "software_detected": "detected_software_or_UNKNOWN"
}
"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(api_key=config.api_key)
    
    async def extract_mot_data(self, image_path: str) -> ExtractionResult:
        """
        Extract MOT data using GPT-4 Vision.
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            ExtractionResult with extracted data and confidence scores
        """
        start_time = time.time()
        
        try:
            # Prepare image
            image_data = self._prepare_image(image_path)
            
            # Call GPT-4 Vision API
            response = await self._call_gpt4v_api(image_data)
            
            # Parse response
            parsed_data = self._parse_response(response.choices[0].message.content)
            
            processing_time = time.time() - start_time
            
            return self._create_extraction_result(
                parsed_data,
                response.choices[0].message.content,
                processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            raise VisionModelError(f"GPT-4V extraction failed: {str(e)}") from e
    
    def _prepare_image(self, image_path: str) -> str:
        """
        Prepare image for GPT-4V API (base64 encoding).
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string with data URL prefix
        """
        base64_image = self._encode_image_base64(image_path, max_size=(2048, 2048))
        return f"data:image/jpeg;base64,{base64_image}"
    
    async def _call_gpt4v_api(self, image_data: str) -> Any:
        """
        Call GPT-4 Vision API with image and prompt.
        
        Args:
            image_data: Base64 encoded image with data URL prefix
            
        Returns:
            OpenAI API response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.EXTRACTION_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response
            
        except openai.APIError as e:
            raise VisionModelAPIError(f"GPT-4V API error: {str(e)}") from e
        except Exception as e:
            raise VisionModelError(f"Unexpected error calling GPT-4V API: {str(e)}") from e
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse GPT-4V's JSON response.
        
        Args:
            response: Raw response from GPT-4V
            
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
                raise ValueError("Invalid response structure from GPT-4V")
            
            return data
            
        except json.JSONDecodeError as e:
            raise VisionModelError(f"Failed to parse GPT-4V JSON response: {str(e)}") from e
        except Exception as e:
            raise VisionModelError(f"Failed to parse GPT-4V response: {str(e)}") from e
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the GPT-4V model."""
        return {
            "name": "GPT-4 Vision Preview",
            "provider": "OpenAI",
            "model_id": self.config.model_name,
            "capabilities": [
                "vision_understanding",
                "structured_extraction",
                "high_detail_analysis",
                "context_awareness"
            ],
            "max_image_size": "2048x2048",
            "supported_formats": ["JPEG", "PNG", "WebP", "GIF"]
        }
