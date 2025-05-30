#!/usr/bin/env python3
"""
Startup script for the MOT OCR System.
"""
import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import settings
from src.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)


def check_environment():
    """Check if environment is properly configured."""
    required_vars = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY", 
        "DVLA_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work properly. Please check your .env file.")
        return False
    
    return True


def create_directories():
    """Create necessary directories."""
    directories = [
        settings.upload_dir,
        settings.results_dir,
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


async def health_check():
    """Perform basic health checks."""
    logger.info("Performing health checks...")
    
    try:
        # Check if we can import all required modules
        from src.vision_models.claude_vision import ClaudeVisionModel
        from src.vision_models.gpt4_vision import GPT4VisionModel
        from src.pipeline.ensemble_pipeline import EnsemblePipeline
        from src.dvla.api_client import DVLAAPIClient
        
        logger.info("✓ All modules imported successfully")
        
        # Test ensemble pipeline initialization
        pipeline = EnsemblePipeline()
        logger.info(f"✓ Ensemble pipeline initialized with {len(pipeline.models)} models")
        
        # Test DVLA client
        dvla_client = DVLAAPIClient()
        logger.info("✓ DVLA client initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Health check failed: {str(e)}")
        return False


def main():
    """Main startup function."""
    logger.info("Starting MOT OCR System...")
    
    # Check environment
    env_ok = check_environment()
    if not env_ok:
        logger.warning("Environment check failed - continuing with limited functionality")
    
    # Create directories
    create_directories()
    
    # Run health checks
    health_ok = asyncio.run(health_check())
    if not health_ok:
        logger.error("Health checks failed - exiting")
        sys.exit(1)
    
    logger.info("All checks passed - starting server...")
    
    # Start the server
    try:
        uvicorn.run(
            "src.api.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.api_debug,
            log_level=settings.log_level.lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
