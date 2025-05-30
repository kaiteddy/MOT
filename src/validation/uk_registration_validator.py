"""
UK vehicle registration number validation.
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegistrationValidationResult:
    """Result of registration validation."""
    is_valid: bool
    format_type: str
    confidence_score: float
    normalized_registration: str
    validation_errors: List[str]
    age_identifier: Optional[str] = None
    estimated_year: Optional[int] = None


class UKRegistrationValidator:
    """Validator for UK vehicle registration numbers."""
    
    # UK registration patterns with their descriptions
    REGISTRATION_PATTERNS = {
        'current': {
            'pattern': r'^[A-Z]{2}[0-9]{2}\s?[A-Z]{3}$',
            'description': 'Current format (2001-present): AB12 CDE',
            'example': 'AB12 CDE'
        },
        'prefix': {
            'pattern': r'^[A-Z][0-9]{1,3}\s?[A-Z]{3}$',
            'description': 'Prefix format (1983-2001): A123 BCD',
            'example': 'A123 BCD'
        },
        'suffix': {
            'pattern': r'^[A-Z]{3}\s?[0-9]{1,3}[A-Z]$',
            'description': 'Suffix format (1963-1983): ABC 123D',
            'example': 'ABC 123D'
        },
        'dateless': {
            'pattern': r'^[0-9]{1,4}\s?[A-Z]{1,3}$',
            'description': 'Dateless format (pre-1963): 1234 AB',
            'example': '1234 AB'
        },
        'northern_ireland': {
            'pattern': r'^[A-Z]{1,3}\s?[0-9]{1,4}$',
            'description': 'Northern Ireland format: ABC 1234',
            'example': 'ABC 1234'
        }
    }
    
    # DVLA area codes for validation
    DVLA_AREA_CODES = {
        'A': ['Peterborough'], 'B': ['Birmingham'], 'C': ['Cymru (Wales)'],
        'D': ['Deeside'], 'E': ['Dudley'], 'F': ['Forest & Fens'],
        'G': ['Garden of England'], 'H': ['Hampshire & Dorset'],
        'K': ['Luton'], 'L': ['London'], 'M': ['Manchester'],
        'N': ['Newcastle'], 'O': ['Oxford'], 'P': ['Preston'],
        'R': ['Reading'], 'S': ['Scotland'], 'V': ['Severn Valley'],
        'W': ['West of England'], 'Y': ['Yorkshire']
    }
    
    # Age identifiers for current format (2001-present)
    AGE_IDENTIFIERS = {
        '01': 2001, '51': 2001, '02': 2002, '52': 2002,
        '03': 2003, '53': 2003, '04': 2004, '54': 2004,
        '05': 2005, '55': 2005, '06': 2006, '56': 2006,
        '07': 2007, '57': 2007, '08': 2008, '58': 2008,
        '09': 2009, '59': 2009, '10': 2010, '60': 2010,
        '11': 2011, '61': 2011, '12': 2012, '62': 2012,
        '13': 2013, '63': 2013, '14': 2014, '64': 2014,
        '15': 2015, '65': 2015, '16': 2016, '66': 2016,
        '17': 2017, '67': 2017, '18': 2018, '68': 2018,
        '19': 2019, '69': 2019, '20': 2020, '70': 2020,
        '21': 2021, '71': 2021, '22': 2022, '72': 2022,
        '23': 2023, '73': 2023, '24': 2024, '74': 2024,
    }
    
    def validate_registration(self, registration: str) -> RegistrationValidationResult:
        """
        Validate a UK vehicle registration number.
        
        Args:
            registration: The registration number to validate
            
        Returns:
            RegistrationValidationResult with validation details
        """
        if not registration or registration.strip() == "NOT_FOUND":
            return RegistrationValidationResult(
                is_valid=False,
                format_type="unknown",
                confidence_score=0.0,
                normalized_registration="",
                validation_errors=["Registration is empty or not found"]
            )
        
        # Normalize the registration
        normalized_reg = self._normalize_registration(registration)
        validation_errors = []
        
        # Check against all patterns
        format_type, pattern_match = self._identify_format(normalized_reg)
        
        if not pattern_match:
            validation_errors.append("Does not match any known UK registration format")
            return RegistrationValidationResult(
                is_valid=False,
                format_type="unknown",
                confidence_score=0.0,
                normalized_registration=normalized_reg,
                validation_errors=validation_errors
            )
        
        # Additional validation based on format
        confidence_score = 1.0
        age_identifier = None
        estimated_year = None
        
        if format_type == 'current':
            # Validate current format specifics
            area_code = normalized_reg[:2]
            age_code = normalized_reg[2:4]
            
            # Check area code
            if area_code[0] not in self.DVLA_AREA_CODES:
                validation_errors.append(f"Invalid area code: {area_code[0]}")
                confidence_score -= 0.2
            
            # Check age identifier
            if age_code in self.AGE_IDENTIFIERS:
                age_identifier = age_code
                estimated_year = self.AGE_IDENTIFIERS[age_code]
            else:
                validation_errors.append(f"Invalid age identifier: {age_code}")
                confidence_score -= 0.3
            
            # Check for future dates
            current_year = datetime.now().year
            if estimated_year and estimated_year > current_year + 1:
                validation_errors.append(f"Registration appears to be from future year: {estimated_year}")
                confidence_score -= 0.4
        
        # Check for common OCR errors
        confidence_score = self._adjust_for_ocr_errors(normalized_reg, confidence_score)
        
        is_valid = len(validation_errors) == 0 and confidence_score >= 0.5
        
        return RegistrationValidationResult(
            is_valid=is_valid,
            format_type=format_type,
            confidence_score=max(0.0, confidence_score),
            normalized_registration=normalized_reg,
            validation_errors=validation_errors,
            age_identifier=age_identifier,
            estimated_year=estimated_year
        )
    
    def _normalize_registration(self, registration: str) -> str:
        """
        Normalize registration number for validation.
        
        Args:
            registration: Raw registration string
            
        Returns:
            Normalized registration string
        """
        # Remove spaces, convert to uppercase
        normalized = re.sub(r'\s+', '', registration.upper())
        
        # Remove common OCR artifacts
        normalized = normalized.replace('O', '0').replace('I', '1').replace('S', '5')
        
        return normalized
    
    def _identify_format(self, registration: str) -> Tuple[str, bool]:
        """
        Identify the format of the registration number.
        
        Args:
            registration: Normalized registration string
            
        Returns:
            Tuple of (format_type, is_match)
        """
        for format_type, pattern_info in self.REGISTRATION_PATTERNS.items():
            if re.match(pattern_info['pattern'], registration):
                return format_type, True
        
        return "unknown", False
    
    def _adjust_for_ocr_errors(self, registration: str, base_confidence: float) -> float:
        """
        Adjust confidence score based on potential OCR errors.
        
        Args:
            registration: Normalized registration
            base_confidence: Base confidence score
            
        Returns:
            Adjusted confidence score
        """
        # Check for suspicious character combinations that might be OCR errors
        suspicious_patterns = [
            r'[0-9][A-Z][0-9]',  # Number-letter-number (unusual)
            r'[A-Z][0-9][A-Z][0-9][A-Z]',  # Alternating pattern
            r'[IL1|][IL1|]',  # Multiple ambiguous characters
            r'[O0][O0]',  # Multiple O/0 characters
        ]
        
        confidence_adjustment = 0.0
        for pattern in suspicious_patterns:
            if re.search(pattern, registration):
                confidence_adjustment -= 0.1
        
        return max(0.0, base_confidence + confidence_adjustment)
    
    def get_registration_info(self, registration: str) -> Dict[str, any]:
        """
        Get detailed information about a registration number.
        
        Args:
            registration: Registration number to analyze
            
        Returns:
            Dictionary with registration information
        """
        validation_result = self.validate_registration(registration)
        
        info = {
            'registration': validation_result.normalized_registration,
            'is_valid': validation_result.is_valid,
            'format_type': validation_result.format_type,
            'confidence_score': validation_result.confidence_score,
            'validation_errors': validation_result.validation_errors
        }
        
        if validation_result.format_type in self.REGISTRATION_PATTERNS:
            pattern_info = self.REGISTRATION_PATTERNS[validation_result.format_type]
            info['format_description'] = pattern_info['description']
            info['format_example'] = pattern_info['example']
        
        if validation_result.age_identifier:
            info['age_identifier'] = validation_result.age_identifier
            info['estimated_year'] = validation_result.estimated_year
        
        return info
