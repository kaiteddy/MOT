#!/usr/bin/env python3
"""
Test script for the MOT OCR System.
"""
import asyncio
import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.validation.uk_registration_validator import UKRegistrationValidator
from src.validation.date_validator import DateValidator
from src.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)


async def test_validation_components():
    """Test the validation components."""
    logger.info("Testing validation components...")
    
    # Test UK Registration Validator
    reg_validator = UKRegistrationValidator()
    
    test_registrations = [
        "AB12 CDE",  # Valid current format
        "A123 BCD",  # Valid prefix format
        "ABC 123D",  # Valid suffix format
        "1234 AB",   # Valid dateless format
        "INVALID",   # Invalid format
    ]
    
    logger.info("Testing UK Registration Validator:")
    for reg in test_registrations:
        result = reg_validator.validate_registration(reg)
        logger.info(f"  {reg}: Valid={result.is_valid}, Format={result.format_type}, Confidence={result.confidence_score:.2f}")
    
    # Test Date Validator
    date_validator = DateValidator()
    
    test_dates = [
        "15/03/2025",    # Valid DD/MM/YYYY
        "15-03-2025",    # Valid DD-MM-YYYY
        "2025-03-15",    # Valid YYYY-MM-DD
        "15 Mar 2025",   # Valid DD Mon YYYY
        "32/01/2025",    # Invalid date
        "INVALID",       # Invalid format
    ]
    
    logger.info("\nTesting Date Validator:")
    for date_str in test_dates:
        result = date_validator.validate_date(date_str)
        logger.info(f"  {date_str}: Valid={result.is_valid}, Parsed={result.normalized_date}, Confidence={result.confidence_score:.2f}")


async def test_api_availability():
    """Test if required APIs are available."""
    logger.info("Testing API availability...")
    
    import os
    
    # Check environment variables
    api_keys = {
        "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Google": os.getenv("GOOGLE_API_KEY"),
        "DVLA": os.getenv("DVLA_API_KEY"),
    }
    
    for service, key in api_keys.items():
        if key:
            logger.info(f"  ✓ {service} API key configured")
        else:
            logger.warning(f"  ✗ {service} API key missing")


async def test_ensemble_pipeline():
    """Test the ensemble pipeline initialization."""
    logger.info("Testing ensemble pipeline...")
    
    try:
        from src.pipeline.ensemble_pipeline import EnsemblePipeline
        
        pipeline = EnsemblePipeline()
        logger.info(f"  ✓ Ensemble pipeline initialized with {len(pipeline.models)} models")
        
        # List available models
        for model in pipeline.models:
            model_name = getattr(model, 'model_name', 'Unknown')
            logger.info(f"    - {model_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ✗ Ensemble pipeline failed: {str(e)}")
        return False


async def test_dvla_client():
    """Test DVLA client initialization."""
    logger.info("Testing DVLA client...")
    
    try:
        from src.dvla.api_client import DVLAAPIClient
        
        dvla_client = DVLAAPIClient()
        logger.info("  ✓ DVLA client initialized")
        
        # Test with a known invalid registration (should fail gracefully)
        result = await dvla_client.validate_registration("INVALID123")
        logger.info(f"  ✓ DVLA validation test completed (expected failure): {result.error_message}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ✗ DVLA client failed: {str(e)}")
        return False


def create_sample_test_data():
    """Create sample test data for demonstration."""
    logger.info("Creating sample test data...")
    
    sample_data = {
        "valid_registrations": [
            "AB12 CDE", "XY21 ZZZ", "AA01 BBB", "ZZ74 ABC"
        ],
        "valid_dates": [
            "15/03/2025", "01/12/2024", "31/01/2026", "15-06-2025"
        ],
        "sample_extraction": {
            "registration": "AB12 CDE",
            "mot_expiry": "15/03/2025",
            "make": "FORD",
            "model": "FOCUS",
            "customer_name": "John Smith",
            "customer_phone": "07123456789",
            "customer_email": "john.smith@email.com"
        }
    }
    
    # Save sample data
    import json
    sample_file = Path("sample_test_data.json")
    with open(sample_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    logger.info(f"  ✓ Sample test data saved to {sample_file}")


async def run_comprehensive_test():
    """Run comprehensive system test."""
    logger.info("=" * 60)
    logger.info("MOT OCR System - Comprehensive Test")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # Test validation components
    await test_validation_components()
    
    # Test API availability
    await test_api_availability()
    
    # Test ensemble pipeline
    pipeline_ok = await test_ensemble_pipeline()
    
    # Test DVLA client
    dvla_ok = await test_dvla_client()
    
    # Create sample data
    create_sample_test_data()
    
    # Summary
    total_time = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary:")
    logger.info(f"  Total test time: {total_time:.2f} seconds")
    logger.info(f"  Ensemble pipeline: {'✓ OK' if pipeline_ok else '✗ FAILED'}")
    logger.info(f"  DVLA client: {'✓ OK' if dvla_ok else '✗ FAILED'}")
    
    if pipeline_ok and dvla_ok:
        logger.info("  🎉 All core components are working!")
        logger.info("\nNext steps:")
        logger.info("  1. Start the API server: python run.py")
        logger.info("  2. Test with sample images")
        logger.info("  3. Check API documentation: docs/api_documentation.md")
    else:
        logger.warning("  ⚠️  Some components failed - check configuration")
        logger.info("\nTroubleshooting:")
        logger.info("  1. Verify API keys in .env file")
        logger.info("  2. Check internet connectivity")
        logger.info("  3. Review installation guide: INSTALLATION.md")


def main():
    """Main test function."""
    try:
        asyncio.run(run_comprehensive_test())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
