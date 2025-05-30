# MOT OCR System API Documentation

## Overview

The MOT OCR System provides a REST API for extracting MOT reminder data from garage management software screenshots using state-of-the-art Vision-Language Models.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required for API access. In production, implement appropriate authentication mechanisms.

## Endpoints

### Health Check

**GET** `/health`

Check the system health and status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1703123456.789,
  "version": "1.0.0",
  "models_available": 2,
  "dvla_api_configured": true
}
```

### Extract MOT Data

**POST** `/extract-mot-data`

Extract MOT reminder data from a garage management software screenshot.

**Parameters:**
- `file` (required): Image file (multipart/form-data)
- `validate_with_dvla` (optional): Boolean, default `true`
- `confidence_threshold` (optional): Float 0.0-1.0, default `0.85`

**Request Example:**
```bash
curl -X POST "http://localhost:8000/extract-mot-data" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@screenshot.png" \
  -F "validate_with_dvla=true" \
  -F "confidence_threshold=0.85"
```

**Response:**
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "success": true,
  "processing_time": 2.45,
  "extracted_data": {
    "registration": "AB12 CDE",
    "mot_expiry": "15/03/2025",
    "make": "FORD",
    "model": "FOCUS",
    "customer_name": "John Smith",
    "customer_phone": "07123456789",
    "customer_email": "john.smith@email.com"
  },
  "confidence_scores": {
    "registration": 0.98,
    "mot_expiry": 0.95,
    "make": 0.92,
    "model": 0.89,
    "customer_name": 0.87,
    "customer_phone": 0.91,
    "customer_email": 0.94
  },
  "software_detected": "garage_hive",
  "models_used": ["claude-3-5-sonnet", "gpt-4-vision-preview"],
  "agreement_level": 0.94,
  "validation_results": {
    "registration_format": true,
    "date_format": true,
    "dvla_match": true
  },
  "dvla_validation": {
    "is_valid": true,
    "vehicle_info": {
      "make": "FORD",
      "model": "FOCUS",
      "mot_expiry_date": "2025-03-15"
    },
    "response_time": 0.45
  },
  "requires_manual_review": false,
  "error_message": null
}
```

### Validate Registration

**POST** `/validate-registration`

Validate a UK vehicle registration number against the DVLA database.

**Request Body:**
```json
{
  "registration": "AB12 CDE"
}
```

**Response:**
```json
{
  "registration": "AB12 CDE",
  "is_valid": true,
  "dvla_info": {
    "registration_number": "AB12CDE",
    "make": "FORD",
    "model": "FOCUS",
    "colour": "BLUE",
    "fuel_type": "PETROL",
    "mot_expiry_date": "2025-03-15",
    "tax_status": "Taxed",
    "year_of_manufacture": 2012
  },
  "error_message": null,
  "response_time": 0.45
}
```

### Get Models Information

**GET** `/models/info`

Get information about available vision models and ensemble configuration.

**Response:**
```json
{
  "available_models": 2,
  "models": [
    {
      "name": "Claude 3.5 Sonnet Vision",
      "provider": "Anthropic",
      "model_id": "claude-3-5-sonnet-20241022",
      "capabilities": [
        "high_accuracy_ocr",
        "context_understanding",
        "structured_extraction",
        "confidence_scoring"
      ],
      "max_image_size": "2048x2048",
      "supported_formats": ["JPEG", "PNG", "WebP", "GIF"]
    },
    {
      "name": "GPT-4 Vision Preview",
      "provider": "OpenAI",
      "model_id": "gpt-4-vision-preview",
      "capabilities": [
        "vision_understanding",
        "structured_extraction",
        "high_detail_analysis",
        "context_awareness"
      ],
      "max_image_size": "2048x2048",
      "supported_formats": ["JPEG", "PNG", "WebP", "GIF"]
    }
  ],
  "ensemble_strategy": "weighted",
  "model_weights": {
    "claude-3-5-sonnet": 0.35,
    "gpt-4-vision-preview": 0.25,
    "gemini-pro-vision": 0.20,
    "florence-2": 0.20
  }
}
```

## Error Responses

All endpoints return appropriate HTTP status codes and error messages:

**400 Bad Request:**
```json
{
  "detail": "Invalid file type. Allowed: ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']"
}
```

**500 Internal Server Error:**
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174001",
  "success": false,
  "processing_time": 1.23,
  "extracted_data": {},
  "confidence_scores": {},
  "software_detected": "UNKNOWN",
  "models_used": [],
  "agreement_level": 0.0,
  "validation_results": {},
  "dvla_validation": null,
  "requires_manual_review": true,
  "error_message": "Unable to process image: insufficient text quality"
}
```

## Rate Limiting

The system supports a maximum of 5 concurrent requests by default. Additional requests will be queued.

## File Requirements

### Supported Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)
- WebP (.webp)

### File Size Limits
- Maximum file size: 10MB
- Maximum image dimensions: 2048x2048 pixels

### Image Quality Guidelines
- Minimum resolution: 800x600 pixels recommended
- Clear, unblurred text
- Good contrast between text and background
- Avoid excessive compression artifacts

## Confidence Scores

The system provides confidence scores (0.0-1.0) for each extracted field:

- **0.9-1.0**: Very high confidence, likely accurate
- **0.8-0.9**: High confidence, probably accurate
- **0.7-0.8**: Medium confidence, may need review
- **0.6-0.7**: Low confidence, likely needs review
- **0.0-0.6**: Very low confidence, manual review required

## Manual Review Flags

The system automatically flags extractions for manual review when:

- Average confidence score < 0.85
- DVLA validation fails
- Models disagree significantly
- Suspicious patterns detected
- Critical fields missing

## Supported Garage Software

The system can detect and extract data from:

- AutoTrader Pro
- Garage Hive
- Autowork Online
- TechMan
- Motasoft
- Generic garage management interfaces

## Integration Examples

### Python SDK Example

```python
import requests

def extract_mot_data(image_path):
    url = "http://localhost:8000/extract-mot-data"
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'validate_with_dvla': True,
            'confidence_threshold': 0.85
        }
        
        response = requests.post(url, files=files, data=data)
        return response.json()

# Usage
result = extract_mot_data("screenshot.png")
print(f"Registration: {result['extracted_data']['registration']}")
print(f"MOT Expiry: {result['extracted_data']['mot_expiry']}")
```

### JavaScript Example

```javascript
async function extractMOTData(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('validate_with_dvla', 'true');
    formData.append('confidence_threshold', '0.85');
    
    const response = await fetch('http://localhost:8000/extract-mot-data', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// Usage
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];
const result = await extractMOTData(file);
console.log('Extracted data:', result.extracted_data);
```

## Performance Metrics

Typical performance characteristics:

- **Processing Time**: 2-5 seconds per image
- **Accuracy**: 99%+ for clear screenshots
- **Throughput**: 5 concurrent requests
- **DVLA Validation**: <1 second response time

## Troubleshooting

### Common Issues

1. **Low Confidence Scores**
   - Ensure image quality is high
   - Check for proper lighting and contrast
   - Verify text is clearly visible

2. **DVLA Validation Failures**
   - Check DVLA API key configuration
   - Verify registration format is correct
   - Ensure vehicle exists in DVLA database

3. **Model Timeouts**
   - Reduce image size if very large
   - Check API key limits
   - Verify network connectivity

### Debug Mode

Enable debug mode by setting `API_DEBUG=true` in environment variables for detailed logging.
