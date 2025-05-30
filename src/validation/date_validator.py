"""
MOT date validation and parsing.
"""
import re
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class DateValidationResult:
    """Result of date validation."""
    is_valid: bool
    parsed_date: Optional[datetime]
    normalized_date: str
    confidence_score: float
    validation_errors: List[str]
    is_expired: bool
    days_until_expiry: Optional[int]


class DateValidator:
    """Validator for MOT expiry dates."""
    
    # Date patterns in order of preference
    DATE_PATTERNS = [
        {
            'pattern': r'(\d{2})/(\d{2})/(\d{4})',
            'format': '%d/%m/%Y',
            'description': 'DD/MM/YYYY'
        },
        {
            'pattern': r'(\d{2})-(\d{2})-(\d{4})',
            'format': '%d-%m-%Y',
            'description': 'DD-MM-YYYY'
        },
        {
            'pattern': r'(\d{2})\.(\d{2})\.(\d{4})',
            'format': '%d.%m.%Y',
            'description': 'DD.MM.YYYY'
        },
        {
            'pattern': r'(\d{4})-(\d{2})-(\d{2})',
            'format': '%Y-%m-%d',
            'description': 'YYYY-MM-DD'
        },
        {
            'pattern': r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',
            'format': '%d %b %Y',
            'description': 'DD Mon YYYY'
        },
        {
            'pattern': r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            'format': '%d %B %Y',
            'description': 'DD Month YYYY'
        }
    ]
    
    # Common OCR misreadings
    OCR_CORRECTIONS = {
        'O': '0', 'o': '0', 'I': '1', 'l': '1', 'S': '5', 's': '5',
        'G': '6', 'B': '8', 'Z': '2', 'z': '2'
    }
    
    def validate_date(self, date_string: str) -> DateValidationResult:
        """
        Validate and parse a MOT expiry date.
        
        Args:
            date_string: The date string to validate
            
        Returns:
            DateValidationResult with validation details
        """
        if not date_string or date_string.strip() == "NOT_FOUND":
            return DateValidationResult(
                is_valid=False,
                parsed_date=None,
                normalized_date="",
                confidence_score=0.0,
                validation_errors=["Date is empty or not found"],
                is_expired=False,
                days_until_expiry=None
            )
        
        # Clean and normalize the date string
        cleaned_date = self._clean_date_string(date_string)
        validation_errors = []
        
        # Try to parse with different patterns
        parsed_date, pattern_used, confidence = self._parse_date(cleaned_date)
        
        if not parsed_date:
            validation_errors.append("Could not parse date format")
            return DateValidationResult(
                is_valid=False,
                parsed_date=None,
                normalized_date=cleaned_date,
                confidence_score=0.0,
                validation_errors=validation_errors,
                is_expired=False,
                days_until_expiry=None
            )
        
        # Validate date reasonableness
        confidence = self._validate_date_reasonableness(parsed_date, confidence, validation_errors)
        
        # Calculate expiry status
        is_expired, days_until_expiry = self._calculate_expiry_status(parsed_date)
        
        # Format normalized date
        normalized_date = parsed_date.strftime('%d/%m/%Y')
        
        is_valid = len(validation_errors) == 0 and confidence >= 0.5
        
        return DateValidationResult(
            is_valid=is_valid,
            parsed_date=parsed_date,
            normalized_date=normalized_date,
            confidence_score=max(0.0, confidence),
            validation_errors=validation_errors,
            is_expired=is_expired,
            days_until_expiry=days_until_expiry
        )
    
    def _clean_date_string(self, date_string: str) -> str:
        """
        Clean and normalize date string for parsing.
        
        Args:
            date_string: Raw date string
            
        Returns:
            Cleaned date string
        """
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', date_string.strip())
        
        # Apply OCR corrections
        for wrong, correct in self.OCR_CORRECTIONS.items():
            cleaned = cleaned.replace(wrong, correct)
        
        # Remove common prefixes/suffixes
        cleaned = re.sub(r'^(MOT|Expires?|Due|Until):\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*(MOT|Expiry|Due)$', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def _parse_date(self, date_string: str) -> Tuple[Optional[datetime], Optional[str], float]:
        """
        Try to parse date using various patterns.
        
        Args:
            date_string: Cleaned date string
            
        Returns:
            Tuple of (parsed_date, pattern_used, confidence_score)
        """
        for pattern_info in self.DATE_PATTERNS:
            try:
                match = re.search(pattern_info['pattern'], date_string, re.IGNORECASE)
                if match:
                    # Try to parse the date
                    if pattern_info['format'] in ['%d %b %Y', '%d %B %Y']:
                        # Handle month name patterns
                        parsed_date = datetime.strptime(match.group(0), pattern_info['format'])
                    else:
                        # Handle numeric patterns
                        parsed_date = datetime.strptime(match.group(0), pattern_info['format'])
                    
                    # Calculate confidence based on pattern quality
                    confidence = self._calculate_pattern_confidence(pattern_info, match.group(0))
                    
                    return parsed_date, pattern_info['description'], confidence
                    
            except ValueError:
                # Invalid date (e.g., 32/13/2024)
                continue
        
        return None, None, 0.0
    
    def _calculate_pattern_confidence(self, pattern_info: dict, matched_string: str) -> float:
        """
        Calculate confidence score based on pattern type and quality.
        
        Args:
            pattern_info: Pattern information dictionary
            matched_string: The matched date string
            
        Returns:
            Confidence score (0.0-1.0)
        """
        base_confidence = 0.8
        
        # Prefer DD/MM/YYYY format (most common in UK)
        if pattern_info['description'] == 'DD/MM/YYYY':
            base_confidence = 1.0
        elif pattern_info['description'] in ['DD-MM-YYYY', 'DD.MM.YYYY']:
            base_confidence = 0.9
        elif pattern_info['description'] == 'YYYY-MM-DD':
            base_confidence = 0.7  # Less common in UK
        
        # Check for suspicious patterns
        if re.search(r'[0-9]{2}/[0-9]{2}/[0-9]{2}$', matched_string):
            base_confidence -= 0.2  # Two-digit year is suspicious
        
        return base_confidence
    
    def _validate_date_reasonableness(
        self, 
        parsed_date: datetime, 
        base_confidence: float, 
        validation_errors: List[str]
    ) -> float:
        """
        Validate that the date is reasonable for MOT expiry.
        
        Args:
            parsed_date: Parsed datetime object
            base_confidence: Base confidence score
            validation_errors: List to append validation errors to
            
        Returns:
            Adjusted confidence score
        """
        now = datetime.now()
        confidence = base_confidence
        
        # Check if date is too far in the past
        if parsed_date < now - timedelta(days=365 * 2):  # More than 2 years ago
            validation_errors.append("Date is more than 2 years in the past")
            confidence -= 0.3
        
        # Check if date is too far in the future
        if parsed_date > now + timedelta(days=365 * 2):  # More than 2 years in future
            validation_errors.append("Date is more than 2 years in the future")
            confidence -= 0.4
        
        # Check for impossible dates
        if parsed_date.year < 1960:  # MOT testing started in 1960
            validation_errors.append("Date is before MOT testing began")
            confidence -= 0.5
        
        if parsed_date.year > now.year + 5:  # More than 5 years in future
            validation_errors.append("Date is unreasonably far in the future")
            confidence -= 0.5
        
        return max(0.0, confidence)
    
    def _calculate_expiry_status(self, parsed_date: datetime) -> Tuple[bool, Optional[int]]:
        """
        Calculate whether the MOT has expired and days until expiry.
        
        Args:
            parsed_date: Parsed MOT expiry date
            
        Returns:
            Tuple of (is_expired, days_until_expiry)
        """
        now = datetime.now()
        
        # Calculate days difference
        days_diff = (parsed_date - now).days
        
        is_expired = days_diff < 0
        days_until_expiry = days_diff if not is_expired else None
        
        return is_expired, days_until_expiry
    
    def get_date_info(self, date_string: str) -> dict:
        """
        Get comprehensive information about a date string.
        
        Args:
            date_string: Date string to analyze
            
        Returns:
            Dictionary with date information
        """
        validation_result = self.validate_date(date_string)
        
        info = {
            'original_string': date_string,
            'normalized_date': validation_result.normalized_date,
            'is_valid': validation_result.is_valid,
            'confidence_score': validation_result.confidence_score,
            'validation_errors': validation_result.validation_errors,
            'is_expired': validation_result.is_expired
        }
        
        if validation_result.parsed_date:
            info['parsed_date'] = validation_result.parsed_date.isoformat()
            info['formatted_date'] = validation_result.parsed_date.strftime('%d %B %Y')
            info['days_until_expiry'] = validation_result.days_until_expiry
            
            # Add expiry status description
            if validation_result.is_expired:
                days_overdue = abs(validation_result.days_until_expiry or 0)
                info['status'] = f"Expired {days_overdue} days ago"
            elif validation_result.days_until_expiry is not None:
                if validation_result.days_until_expiry <= 30:
                    info['status'] = f"Expires in {validation_result.days_until_expiry} days (URGENT)"
                elif validation_result.days_until_expiry <= 60:
                    info['status'] = f"Expires in {validation_result.days_until_expiry} days (SOON)"
                else:
                    info['status'] = f"Expires in {validation_result.days_until_expiry} days"
        
        return info
