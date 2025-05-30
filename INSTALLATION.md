# MOT OCR System - Installation Guide

## Overview

This guide will help you set up the MOT OCR System, a high-accuracy text extraction system for garage management software screenshots using state-of-the-art Vision-Language Models.

## System Requirements

### Hardware Requirements
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **GPU**: Optional but recommended for faster processing

### Software Requirements
- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Internet Connection**: Required for API calls to vision models and DVLA

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MOTCHECK
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit the .env file with your API keys
nano .env  # or use your preferred editor
```

### 5. Configure API Keys

Edit the `.env` file and add your API keys:

```env
# Vision-Language Model API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# DVLA API Configuration
DVLA_API_KEY=your_dvla_api_key_here
```

## API Key Setup

### Anthropic Claude API

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

**Pricing**: Pay-per-use, approximately $0.01-0.03 per image

### OpenAI GPT-4 Vision API

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

**Pricing**: Pay-per-use, approximately $0.01-0.02 per image

### Google Gemini API

1. Visit [Google AI Studio](https://makersuite.google.com/)
2. Create an account or sign in
3. Generate an API key
4. Copy the key to your `.env` file

**Pricing**: Free tier available, then pay-per-use

### DVLA API

1. Visit [DVLA Developer Portal](https://developer-portal.driver-vehicle-licensing.api.gov.uk/)
2. Register for an account
3. Subscribe to the Vehicle Enquiry Service
4. Generate an API key
5. Copy the key to your `.env` file

**Pricing**: Free for limited use, paid tiers available

## Installation Verification

### 1. Run Health Check

```bash
python run.py
```

This will:
- Check environment variables
- Create necessary directories
- Verify all modules can be imported
- Initialize the ensemble pipeline
- Start the API server

### 2. Test API Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test models info endpoint
curl http://localhost:8000/models/info
```

### 3. Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Configuration Options

### Environment Variables

Key configuration options in `.env`:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Model Selection
PRIMARY_VISION_MODEL=claude-3-5-sonnet
SECONDARY_VISION_MODELS=["gpt-4-vision-preview", "gemini-pro-vision"]

# Performance Settings
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=300
MODEL_TIMEOUT=60

# Image Processing
IMAGE_MAX_WIDTH=2048
IMAGE_MAX_HEIGHT=2048
MAX_FILE_SIZE=10485760

# Validation
MIN_CONFIDENCE_SCORE=0.9
REQUIRE_DVLA_VALIDATION=true
```

### Model Weights

Adjust ensemble model weights in `config/settings.py`:

```python
model_weights = {
    "claude-3-5-sonnet": 0.35,      # Highest weight - best accuracy
    "gpt-4-vision-preview": 0.25,   # Good backup model
    "gemini-pro-vision": 0.20,      # Additional validation
    "florence-2": 0.20              # Local model option
}
```

## Docker Installation (Alternative)

### 1. Build Docker Image

```bash
# Build the image
docker build -t mot-ocr-system .

# Or use docker-compose
docker-compose build
```

### 2. Run with Docker

```bash
# Run with environment file
docker run --env-file .env -p 8000:8000 mot-ocr-system

# Or use docker-compose
docker-compose up
```

### 3. Docker Environment

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mot-ocr:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
      - ./results:/app/results
      - ./logs:/app/logs
    restart: unless-stopped
```

## Production Deployment

### 1. Security Considerations

```bash
# Set secure environment variables
export ANTHROPIC_API_KEY="your-secure-key"
export OPENAI_API_KEY="your-secure-key"
export DVLA_API_KEY="your-secure-key"

# Use HTTPS in production
export API_HOST="0.0.0.0"
export API_PORT="443"
```

### 2. Performance Optimization

```env
# Production settings
API_DEBUG=false
LOG_LEVEL=WARNING
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=120

# Enable caching
ENABLE_RESULT_CACHING=true
CACHE_TTL=3600
```

### 3. Monitoring Setup

```bash
# Install monitoring dependencies
pip install prometheus-client grafana-api

# Configure logging
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/mot-ocr/app.log
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 2. API Key Issues

```bash
# Verify API keys are set
python -c "import os; print('ANTHROPIC_API_KEY:', bool(os.getenv('ANTHROPIC_API_KEY')))"

# Test API connectivity
curl -H "x-api-key: YOUR_ANTHROPIC_KEY" https://api.anthropic.com/v1/messages
```

#### 3. Memory Issues

```bash
# Reduce image size limits
export IMAGE_MAX_WIDTH=1024
export IMAGE_MAX_HEIGHT=1024

# Reduce concurrent requests
export MAX_CONCURRENT_REQUESTS=2
```

#### 4. DVLA API Issues

```bash
# Test DVLA connectivity
curl -X POST "https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles" \
  -H "x-api-key: YOUR_DVLA_KEY" \
  -H "Content-Type: application/json" \
  -d '{"registrationNumber": "AB12CDE"}'
```

### Debug Mode

Enable debug mode for detailed logging:

```env
API_DEBUG=true
LOG_LEVEL=DEBUG
```

### Performance Monitoring

Monitor system performance:

```bash
# Check system resources
htop

# Monitor API logs
tail -f logs/mot_ocr.log

# Check API metrics
curl http://localhost:8000/health
```

## Updating the System

### 1. Update Code

```bash
git pull origin main
```

### 2. Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### 3. Restart Service

```bash
# Stop current service
pkill -f "python run.py"

# Start updated service
python run.py
```

## Support

For issues and support:

1. Check the troubleshooting section above
2. Review logs in `logs/mot_ocr.log`
3. Run tests to verify functionality
4. Check API documentation in `docs/api_documentation.md`

## Next Steps

After installation:

1. Test with sample garage software screenshots
2. Adjust confidence thresholds based on your accuracy requirements
3. Configure monitoring and alerting for production use
4. Set up automated backups for results and logs
5. Consider implementing authentication for production deployment
