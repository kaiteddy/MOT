#!/usr/bin/env python3
"""
Comprehensive API test script for all Vision-Language Models.
Tests Claude, GPT-4V, Gemini, and Florence-2 integrations.
"""
import asyncio
import sys
import os
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.vision_models.base_vision_model import ModelConfig
from src.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)


async def test_claude_api():
    """Test Claude 3.5 Sonnet Vision API."""
    logger.info("Testing Claude 3.5 Sonnet Vision API...")
    
    try:
        from src.vision_models.claude_vision import ClaudeVisionModel
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("❌ ANTHROPIC_API_KEY not found - skipping Claude test")
            return False
        
        config = ModelConfig(
            api_key=api_key,
            model_name="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.1
        )
        
        model = ClaudeVisionModel(config)
        logger.info("✅ Claude model initialized successfully")
        
        # Test model info
        info = model.get_model_info()
        logger.info(f"   Model: {info['name']} by {info['provider']}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Claude import failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Claude test failed: {str(e)}")
        return False


async def test_gpt4v_api():
    """Test GPT-4 Vision API."""
    logger.info("Testing GPT-4 Vision API...")
    
    try:
        from src.vision_models.gpt4_vision import GPT4VisionModel
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("❌ OPENAI_API_KEY not found - skipping GPT-4V test")
            return False
        
        config = ModelConfig(
            api_key=api_key,
            model_name="gpt-4-vision-preview",
            max_tokens=1000,
            temperature=0.1
        )
        
        model = GPT4VisionModel(config)
        logger.info("✅ GPT-4V model initialized successfully")
        
        # Test model info
        info = model.get_model_info()
        logger.info(f"   Model: {info['name']} by {info['provider']}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ GPT-4V import failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ GPT-4V test failed: {str(e)}")
        return False


async def test_gemini_api():
    """Test Gemini Pro Vision API."""
    logger.info("Testing Gemini Pro Vision API...")
    
    try:
        from src.vision_models.gemini_vision import GeminiVisionModel
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("❌ GOOGLE_API_KEY not found - skipping Gemini test")
            return False
        
        config = ModelConfig(
            api_key=api_key,
            model_name="gemini-pro-vision",
            temperature=0.1
        )
        
        model = GeminiVisionModel(config)
        logger.info("✅ Gemini model initialized successfully")
        
        # Test model info
        info = model.get_model_info()
        logger.info(f"   Model: {info['name']} by {info['provider']}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Gemini import failed: {str(e)}")
        logger.info("   Install with: pip install google-generativeai")
        return False
    except Exception as e:
        logger.error(f"❌ Gemini test failed: {str(e)}")
        return False


async def test_florence_api():
    """Test Florence-2 model."""
    logger.info("Testing Florence-2 model...")
    
    try:
        from src.vision_models.florence_vision import FlorenceVisionModel
        
        config = ModelConfig(
            api_key="",  # Not needed for local model
            model_name="microsoft/Florence-2-large"
        )
        
        model = FlorenceVisionModel(config)
        logger.info("✅ Florence-2 model initialized successfully")
        
        # Test model info
        info = model.get_model_info()
        logger.info(f"   Model: {info['name']} by {info['provider']}")
        logger.info(f"   Device: {info['device']}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Florence-2 import failed: {str(e)}")
        logger.info("   Install with: pip install transformers torch")
        return False
    except Exception as e:
        logger.error(f"❌ Florence-2 test failed: {str(e)}")
        logger.info("   Note: Florence-2 requires significant memory and may fail on limited systems")
        return False


async def test_dvla_api():
    """Test DVLA API integration."""
    logger.info("Testing DVLA API integration...")
    
    try:
        from src.dvla.api_client import DVLAAPIClient
        
        api_key = os.getenv("DVLA_API_KEY")
        if not api_key:
            logger.warning("❌ DVLA_API_KEY not found - skipping DVLA test")
            return False
        
        client = DVLAAPIClient()
        logger.info("✅ DVLA client initialized successfully")
        
        # Test with a known invalid registration (should fail gracefully)
        result = await client.validate_registration("INVALID123")
        if not result.is_valid:
            logger.info("✅ DVLA validation working (expected failure for invalid registration)")
            return True
        else:
            logger.warning("⚠️  DVLA validation returned unexpected result")
            return False
        
    except ImportError as e:
        logger.error(f"❌ DVLA import failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ DVLA test failed: {str(e)}")
        return False


async def test_ensemble_pipeline():
    """Test the ensemble pipeline with all available models."""
    logger.info("Testing Ensemble Pipeline...")
    
    try:
        from src.pipeline.ensemble_pipeline import EnsemblePipeline
        
        pipeline = EnsemblePipeline()
        logger.info(f"✅ Ensemble pipeline initialized with {len(pipeline.models)} models")
        
        # List available models
        for model in pipeline.models:
            model_name = getattr(model, 'model_name', model.__class__.__name__)
            logger.info(f"   • {model_name}")
        
        return len(pipeline.models) > 0
        
    except ImportError as e:
        logger.error(f"❌ Ensemble pipeline import failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Ensemble pipeline test failed: {str(e)}")
        return False


def check_environment_variables():
    """Check if required environment variables are set."""
    logger.info("Checking environment variables...")
    
    required_vars = {
        "ANTHROPIC_API_KEY": "Claude 3.5 Sonnet",
        "OPENAI_API_KEY": "GPT-4 Vision",
        "GOOGLE_API_KEY": "Gemini Pro Vision",
        "DVLA_API_KEY": "DVLA Vehicle Enquiry"
    }
    
    found_vars = 0
    for var, description in required_vars.items():
        if os.getenv(var):
            logger.info(f"✅ {var} configured for {description}")
            found_vars += 1
        else:
            logger.warning(f"❌ {var} missing for {description}")
    
    logger.info(f"Environment check: {found_vars}/{len(required_vars)} API keys configured")
    return found_vars


async def run_comprehensive_api_test():
    """Run comprehensive test of all APIs."""
    logger.info("=" * 60)
    logger.info("MOT OCR System - Comprehensive API Test")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # Check environment variables
    env_count = check_environment_variables()
    
    # Test individual APIs
    tests = [
        ("Claude 3.5 Sonnet", test_claude_api()),
        ("GPT-4 Vision", test_gpt4v_api()),
        ("Gemini Pro Vision", test_gemini_api()),
        ("Florence-2", test_florence_api()),
        ("DVLA API", test_dvla_api()),
        ("Ensemble Pipeline", test_ensemble_pipeline())
    ]
    
    results = {}
    for name, test_coro in tests:
        try:
            results[name] = await test_coro
        except Exception as e:
            logger.error(f"❌ {name} test crashed: {str(e)}")
            results[name] = False
    
    # Summary
    total_time = time.time() - start_time
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    logger.info("\n" + "=" * 60)
    logger.info("API TEST SUMMARY")
    logger.info("=" * 60)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {name}")
    
    logger.info(f"\nResults: {passed_tests}/{total_tests} tests passed")
    logger.info(f"Environment: {env_count}/4 API keys configured")
    logger.info(f"Total test time: {total_time:.2f} seconds")
    
    if passed_tests >= 2:  # At least 2 models working
        logger.info("\n🎉 SYSTEM READY!")
        logger.info("You have enough working models to run the MOT OCR system.")
        logger.info("\nNext steps:")
        logger.info("1. Configure missing API keys if needed")
        logger.info("2. Start the server: python run.py")
        logger.info("3. Test with a screenshot: curl -X POST http://localhost:8000/extract-mot-data -F 'file=@image.png'")
    else:
        logger.warning("\n⚠️  INSUFFICIENT MODELS")
        logger.warning("You need at least 2 working models for reliable ensemble processing.")
        logger.info("\nTroubleshooting:")
        logger.info("1. Check API keys in .env file")
        logger.info("2. Install missing dependencies: pip install -r requirements.txt")
        logger.info("3. Check internet connectivity")
    
    return passed_tests >= 2


def main():
    """Main test function."""
    try:
        success = asyncio.run(run_comprehensive_api_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
