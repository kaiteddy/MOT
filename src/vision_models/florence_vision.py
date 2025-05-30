"""
Microsoft Florence-2 implementation for MOT data extraction.
"""
import json
import time
import asyncio
from typing import Dict, Any
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image
from .base_vision_model import BaseVisionModel, ExtractionResult, ModelConfig, VisionModelError


class FlorenceVisionModel(BaseVisionModel):
    """Microsoft Florence-2 model for MOT data extraction."""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = None
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Florence-2 model and processor."""
        try:
            self.processor = AutoProcessor.from_pretrained(
                self.config.model_name, 
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name, 
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            
        except Exception as e:
            raise VisionModelError(f"Failed to initialize Florence-2 model: {str(e)}")
    
    async def extract_mot_data(self, image_path: str) -> ExtractionResult:
        """
        Extract MOT data using Florence-2.
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            ExtractionResult with extracted data and confidence scores
        """
        start_time = time.time()
        
        try:
            # Prepare image
            image = self._prepare_image(image_path)
            
            # Extract text using Florence-2
            extracted_text = await self._extract_text_with_florence(image)
            
            # Parse extracted text into structured data
            parsed_data = self._parse_extracted_text(extracted_text)
            
            processing_time = time.time() - start_time
            
            return self._create_extraction_result(
                parsed_data,
                extracted_text,
                processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            raise VisionModelError(f"Florence-2 extraction failed: {str(e)}") from e
    
    def _prepare_image(self, image_path: str) -> Image.Image:
        """
        Prepare image for Florence-2.
        
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
            
            return image
            
        except Exception as e:
            raise ValueError(f"Failed to prepare image: {str(e)}")
    
    async def _extract_text_with_florence(self, image: Image.Image) -> str:
        """
        Extract text using Florence-2 OCR capabilities.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        try:
            # Use Florence-2 for OCR task
            task_prompt = "<OCR>"
            
            # Run inference in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_florence_inference,
                image,
                task_prompt
            )
            
            return result
            
        except Exception as e:
            raise VisionModelError(f"Florence-2 text extraction failed: {str(e)}")
    
    def _run_florence_inference(self, image: Image.Image, task_prompt: str) -> str:
        """
        Run Florence-2 inference synchronously.
        
        Args:
            image: PIL Image object
            task_prompt: Task prompt for Florence-2
            
        Returns:
            Extracted text
        """
        try:
            # Prepare inputs
            inputs = self.processor(
                text=task_prompt, 
                images=image, 
                return_tensors="pt"
            ).to(self.device)
            
            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    input_ids=inputs["input_ids"],
                    pixel_values=inputs["pixel_values"],
                    max_new_tokens=1024,
                    num_beams=3,
                    do_sample=False
                )
            
            # Decode
            generated_text = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=False
            )[0]
            
            # Extract the actual OCR result
            parsed_answer = self.processor.post_process_generation(
                generated_text, 
                task=task_prompt, 
                image_size=(image.width, image.height)
            )
            
            return parsed_answer.get(task_prompt, "")
            
        except Exception as e:
            raise VisionModelError(f"Florence-2 inference failed: {str(e)}")
    
    def _parse_extracted_text(self, text: str) -> Dict[str, Any]:
        """
        Parse extracted text into structured MOT data.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Parsed data dictionary
        """
        import re
        
        # Initialize result structure
        result = {
            "registration": "NOT_FOUND",
            "mot_expiry": "NOT_FOUND",
            "make": "NOT_FOUND",
            "model": "NOT_FOUND",
            "customer_name": "NOT_FOUND",
            "customer_phone": "NOT_FOUND",
            "customer_email": "NOT_FOUND",
            "confidence_scores": {
                "registration": 0.0,
                "mot_expiry": 0.0,
                "make": 0.0,
                "model": 0.0,
                "customer_name": 0.0,
                "customer_phone": 0.0,
                "customer_email": 0.0
            },
            "software_detected": "UNKNOWN"
        }
        
        if not text:
            return result
        
        # UK Registration patterns
        reg_patterns = [
            r'\b[A-Z]{2}[0-9]{2}\s?[A-Z]{3}\b',  # Current format
            r'\b[A-Z][0-9]{1,3}\s?[A-Z]{3}\b',   # Prefix format
            r'\b[A-Z]{3}\s?[0-9]{1,3}[A-Z]\b',   # Suffix format
            r'\b[0-9]{1,4}\s?[A-Z]{1,3}\b'       # Dateless format
        ]
        
        # Search for registration
        for pattern in reg_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["registration"] = match.group().upper()
                result["confidence_scores"]["registration"] = 0.8
                break
        
        # Date patterns
        date_patterns = [
            r'\b\d{2}/\d{2}/\d{4}\b',
            r'\b\d{2}-\d{2}-\d{4}\b',
            r'\b\d{2}\.\d{2}\.\d{4}\b'
        ]
        
        # Search for MOT expiry date
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                result["mot_expiry"] = match.group()
                result["confidence_scores"]["mot_expiry"] = 0.7
                break
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            result["customer_email"] = email_match.group()
            result["confidence_scores"]["customer_email"] = 0.9
        
        # Phone pattern (UK)
        phone_patterns = [
            r'\b(?:0|\+44)[1-9]\d{8,9}\b',
            r'\b07\d{9}\b'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                result["customer_phone"] = match.group()
                result["confidence_scores"]["customer_phone"] = 0.8
                break
        
        # Vehicle make detection (common UK makes)
        makes = [
            "FORD", "VAUXHALL", "BMW", "AUDI", "MERCEDES", "VOLKSWAGEN",
            "TOYOTA", "HONDA", "NISSAN", "PEUGEOT", "RENAULT", "CITROEN",
            "HYUNDAI", "KIA", "MAZDA", "SUBARU", "VOLVO", "JAGUAR",
            "LAND ROVER", "MINI", "FIAT", "ALFA ROMEO", "SEAT", "SKODA"
        ]
        
        for make in makes:
            if make in text.upper():
                result["make"] = make
                result["confidence_scores"]["make"] = 0.7
                break
        
        # Software detection
        software_indicators = {
            "garage hive": "garage_hive",
            "autotrader": "autotrader_pro",
            "autowork": "autowork_online",
            "techman": "techman",
            "motasoft": "motasoft"
        }
        
        for indicator, software in software_indicators.items():
            if indicator in text.lower():
                result["software_detected"] = software
                break
        
        return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Florence-2 model."""
        return {
            "name": "Florence-2",
            "provider": "Microsoft",
            "model_id": self.config.model_name,
            "capabilities": [
                "ocr_extraction",
                "layout_understanding",
                "local_processing",
                "no_api_required"
            ],
            "max_image_size": "Variable",
            "supported_formats": ["JPEG", "PNG", "WebP", "BMP"],
            "device": self.device
        }
