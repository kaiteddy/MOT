"""
Logging utilities for the MOT OCR system.
"""
import logging
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from config.settings import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru."""
    
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration using loguru.
    
    Args:
        name: Logger name (optional)
        
    Returns:
        Configured logger instance
    """
    # Remove default loguru handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Console handler with colored output
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File handler with rotation
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Configure specific loggers
    for logger_name in ["uvicorn", "uvicorn.access", "fastapi", "httpx"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
    
    # Return standard logger for compatibility
    return logging.getLogger(name or __name__)


def log_extraction_request(request_id: str, filename: str, file_size: int):
    """Log MOT extraction request details."""
    logger.info(
        f"MOT extraction request started",
        extra={
            "request_id": request_id,
            "filename": filename,
            "file_size": file_size,
            "event_type": "extraction_request"
        }
    )


def log_extraction_result(
    request_id: str, 
    success: bool, 
    processing_time: float,
    models_used: list,
    confidence_scores: dict,
    requires_manual_review: bool
):
    """Log MOT extraction result details."""
    avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
    
    logger.info(
        f"MOT extraction completed",
        extra={
            "request_id": request_id,
            "success": success,
            "processing_time": processing_time,
            "models_used": models_used,
            "avg_confidence": avg_confidence,
            "requires_manual_review": requires_manual_review,
            "event_type": "extraction_result"
        }
    )


def log_dvla_validation(request_id: str, registration: str, is_valid: bool, response_time: float):
    """Log DVLA validation details."""
    logger.info(
        f"DVLA validation completed",
        extra={
            "request_id": request_id,
            "registration": registration,
            "is_valid": is_valid,
            "response_time": response_time,
            "event_type": "dvla_validation"
        }
    )


def log_model_performance(model_name: str, processing_time: float, success: bool, confidence: float):
    """Log individual model performance."""
    logger.debug(
        f"Model performance",
        extra={
            "model_name": model_name,
            "processing_time": processing_time,
            "success": success,
            "confidence": confidence,
            "event_type": "model_performance"
        }
    )


def log_error(request_id: str, error_type: str, error_message: str, stack_trace: str = None):
    """Log error details."""
    logger.error(
        f"Error occurred: {error_type}",
        extra={
            "request_id": request_id,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "event_type": "error"
        }
    )


def log_system_metrics(
    active_requests: int,
    total_requests: int,
    success_rate: float,
    avg_processing_time: float
):
    """Log system performance metrics."""
    logger.info(
        f"System metrics",
        extra={
            "active_requests": active_requests,
            "total_requests": total_requests,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "event_type": "system_metrics"
        }
    )


class RequestLogger:
    """Context manager for request logging."""
    
    def __init__(self, request_id: str, operation: str):
        self.request_id = request_id
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = logger.bind(request_id=self.request_id).info(f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            logger.bind(request_id=self.request_id).info(f"Completed {self.operation}")
        else:
            logger.bind(request_id=self.request_id).error(
                f"Failed {self.operation}: {exc_val}"
            )


# Configure structured logging for different components
def get_component_logger(component: str) -> logging.Logger:
    """Get a logger for a specific component."""
    return logging.getLogger(f"mot_ocr.{component}")


# Pre-configured loggers for different components
extraction_logger = get_component_logger("extraction")
validation_logger = get_component_logger("validation")
api_logger = get_component_logger("api")
dvla_logger = get_component_logger("dvla")
ensemble_logger = get_component_logger("ensemble")
