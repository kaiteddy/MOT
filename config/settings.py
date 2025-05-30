"""
Configuration settings for the next-generation MOT OCR system using Vision-Language Models.
"""
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings for VLM-based MOT extraction."""

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_debug: bool = Field(default=False, env="API_DEBUG")

    # Vision-Language Model API Keys
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")

    # DVLA API Configuration
    dvla_api_key: str = Field(default="", env="DVLA_API_KEY")
    dvla_api_url: str = Field(
        default="https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles",
        env="DVLA_API_URL"
    )
    dvla_timeout: int = Field(default=30, env="DVLA_TIMEOUT")

    # Vision Model Configuration
    primary_vision_model: str = Field(default="claude-3-5-sonnet", env="PRIMARY_VISION_MODEL")
    secondary_vision_models: List[str] = Field(
        default=["gpt-4-vision-preview", "gemini-pro-vision", "florence-2"],
        env="SECONDARY_VISION_MODELS"
    )

    # Claude Configuration
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", env="CLAUDE_MODEL")
    claude_max_tokens: int = Field(default=4096, env="CLAUDE_MAX_TOKENS")
    claude_temperature: float = Field(default=0.1, env="CLAUDE_TEMPERATURE")

    # OpenAI Configuration
    openai_model: str = Field(default="gpt-4-vision-preview", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4096, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")

    # Google Gemini Configuration
    gemini_model: str = Field(default="gemini-pro-vision", env="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.1, env="GEMINI_TEMPERATURE")

    # Florence-2 Configuration
    florence_model: str = Field(default="microsoft/Florence-2-large", env="FLORENCE_MODEL")
    florence_device: str = Field(default="cuda", env="FLORENCE_DEVICE")

    # Ensemble Configuration
    ensemble_voting_strategy: str = Field(default="weighted", env="ENSEMBLE_VOTING_STRATEGY")
    minimum_model_agreement: int = Field(default=2, env="MINIMUM_MODEL_AGREEMENT")
    confidence_threshold: float = Field(default=0.85, env="CONFIDENCE_THRESHOLD")

    # Model Weights for Ensemble Voting
    model_weights: dict = Field(
        default={
            "claude-3-5-sonnet": 0.35,
            "gpt-4-vision-preview": 0.25,
            "gemini-pro-vision": 0.20,
            "florence-2": 0.20
        },
        env="MODEL_WEIGHTS"
    )

    # Image Preprocessing Configuration
    image_max_width: int = Field(default=2048, env="IMAGE_MAX_WIDTH")
    image_max_height: int = Field(default=2048, env="IMAGE_MAX_HEIGHT")
    image_quality_threshold: float = Field(default=0.5, env="IMAGE_QUALITY_THRESHOLD")

    # Validation Configuration
    min_confidence_score: float = Field(default=0.8, env="MIN_CONFIDENCE_SCORE")
    require_dvla_validation: bool = Field(default=True, env="REQUIRE_DVLA_VALIDATION")
    max_validation_retries: int = Field(default=3, env="MAX_VALIDATION_RETRIES")

    # UK Registration Patterns
    uk_registration_patterns: List[str] = Field(
        default=[
            r"^[A-Z]{2}[0-9]{2}\s?[A-Z]{3}$",  # Current format: AB12 CDE
            r"^[A-Z][0-9]{1,3}\s?[A-Z]{3}$",   # Prefix format: A123 BCD
            r"^[A-Z]{3}\s?[0-9]{1,3}[A-Z]$",   # Suffix format: ABC 123D
            r"^[0-9]{1,4}\s?[A-Z]{1,3}$",      # Dateless format: 1234 AB
        ],
        env="UK_REGISTRATION_PATTERNS"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/mot_ocr.log", env="LOG_FILE")
    log_rotation: str = Field(default="1 day", env="LOG_ROTATION")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")

    # File Storage Configuration
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    results_dir: str = Field(default="results", env="RESULTS_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"],
        env="ALLOWED_EXTENSIONS"
    )

    # Performance Configuration
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


# UK MOT Date Validation Patterns
MOT_DATE_PATTERNS = [
    r"\d{2}/\d{2}/\d{4}",  # DD/MM/YYYY
    r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
    r"\d{2}\.\d{2}\.\d{4}",  # DD.MM.YYYY
    r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
]

# Common garage management software field mappings
FIELD_MAPPINGS = {
    "registration": ["reg", "registration", "reg_no", "vehicle_reg", "number_plate"],
    "mot_expiry": ["mot", "mot_expiry", "mot_due", "mot_expires", "test_due"],
    "make": ["make", "manufacturer", "brand"],
    "model": ["model", "variant"],
    "customer_name": ["customer", "owner", "name", "client"],
    "customer_phone": ["phone", "telephone", "mobile", "contact"],
    "customer_email": ["email", "e-mail", "email_address"],
}

# Confidence scoring weights
CONFIDENCE_WEIGHTS = {
    "ocr_confidence": 0.4,
    "format_validation": 0.3,
    "dvla_validation": 0.3,
}
