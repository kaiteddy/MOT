"""
Tests for validation components.
"""
import pytest
from datetime import datetime, timedelta

from src.validation.uk_registration_validator import UKRegistrationValidator
from src.validation.date_validator import DateValidator


class TestUKRegistrationValidator:
    """Test UK registration validation."""
    
    def setup_method(self):
        self.validator = UKRegistrationValidator()
    
    def test_valid_current_format(self):
        """Test valid current format registrations."""
        valid_registrations = [
            "AB12 CDE", "AB12CDE", "ab12 cde", "ab12cde",
            "XY99 ZZZ", "AA01 AAA", "ZZ74 ZZZ"
        ]
        
        for reg in valid_registrations:
            result = self.validator.validate_registration(reg)
            assert result.is_valid, f"Registration {reg} should be valid"
            assert result.format_type == "current"
            assert result.confidence_score > 0.5
    
    def test_valid_prefix_format(self):
        """Test valid prefix format registrations."""
        valid_registrations = [
            "A123 BCD", "A1 BCD", "A999 ZZZ", "Z1 AAA"
        ]
        
        for reg in valid_registrations:
            result = self.validator.validate_registration(reg)
            assert result.is_valid, f"Registration {reg} should be valid"
            assert result.format_type == "prefix"
    
    def test_valid_suffix_format(self):
        """Test valid suffix format registrations."""
        valid_registrations = [
            "ABC 123D", "ABC 1D", "ZZZ 999Z", "AAA 1A"
        ]
        
        for reg in valid_registrations:
            result = self.validator.validate_registration(reg)
            assert result.is_valid, f"Registration {reg} should be valid"
            assert result.format_type == "suffix"
    
    def test_valid_dateless_format(self):
        """Test valid dateless format registrations."""
        valid_registrations = [
            "1234 AB", "123 A", "9999 ZZ", "1 A"
        ]
        
        for reg in valid_registrations:
            result = self.validator.validate_registration(reg)
            assert result.is_valid, f"Registration {reg} should be valid"
            assert result.format_type == "dateless"
    
    def test_invalid_registrations(self):
        """Test invalid registrations."""
        invalid_registrations = [
            "INVALID", "123", "AB", "AB12", "AB12 CD",
            "AB123 CDE", "1234 ABCD", "", "NOT_FOUND"
        ]
        
        for reg in invalid_registrations:
            result = self.validator.validate_registration(reg)
            assert not result.is_valid, f"Registration {reg} should be invalid"
    
    def test_age_identifier_validation(self):
        """Test age identifier validation for current format."""
        # Valid age identifiers
        valid_regs = ["AB21 CDE", "XY72 ZZZ", "AA01 BBB"]
        for reg in valid_regs:
            result = self.validator.validate_registration(reg)
            assert result.is_valid
            assert result.age_identifier is not None
            assert result.estimated_year is not None
        
        # Invalid age identifiers
        invalid_regs = ["AB00 CDE", "XY99 ZZZ"]  # 00 and 99 are not valid
        for reg in invalid_regs:
            result = self.validator.validate_registration(reg)
            # Should still be valid format but with lower confidence
            assert result.format_type == "current"
            assert len(result.validation_errors) > 0
    
    def test_future_year_validation(self):
        """Test validation of future year registrations."""
        current_year = datetime.now().year
        future_year = current_year + 2
        
        # This would be a future registration (if it exists)
        # The validator should flag this as suspicious
        future_reg = f"AB{str(future_year)[-2:]} CDE"
        result = self.validator.validate_registration(future_reg)
        
        # Might be valid format but should have validation errors
        if result.estimated_year and result.estimated_year > current_year + 1:
            assert len(result.validation_errors) > 0
    
    def test_normalization(self):
        """Test registration normalization."""
        test_cases = [
            ("AB12 CDE", "AB12CDE"),
            ("ab12 cde", "AB12CDE"),
            ("  AB12  CDE  ", "AB12CDE"),
            ("AB12CDE", "AB12CDE")
        ]
        
        for input_reg, expected in test_cases:
            result = self.validator.validate_registration(input_reg)
            assert result.normalized_registration == expected
    
    def test_get_registration_info(self):
        """Test getting detailed registration information."""
        reg = "AB21 CDE"
        info = self.validator.get_registration_info(reg)
        
        assert info['registration'] == "AB21CDE"
        assert info['is_valid']
        assert info['format_type'] == "current"
        assert 'format_description' in info
        assert 'format_example' in info
        assert 'age_identifier' in info
        assert 'estimated_year' in info


class TestDateValidator:
    """Test MOT date validation."""
    
    def setup_method(self):
        self.validator = DateValidator()
    
    def test_valid_date_formats(self):
        """Test various valid date formats."""
        valid_dates = [
            "15/03/2025", "01/12/2024", "31/01/2026",
            "15-03-2025", "01-12-2024", "31-01-2026",
            "15.03.2025", "01.12.2024", "31.01.2026",
            "2025-03-15", "2024-12-01", "2026-01-31",
            "15 Mar 2025", "1 Dec 2024", "31 Jan 2026",
            "15 March 2025", "1 December 2024", "31 January 2026"
        ]
        
        for date_str in valid_dates:
            result = self.validator.validate_date(date_str)
            assert result.is_valid, f"Date {date_str} should be valid"
            assert result.parsed_date is not None
            assert result.confidence_score > 0.5
    
    def test_invalid_date_formats(self):
        """Test invalid date formats."""
        invalid_dates = [
            "32/01/2025", "15/13/2025", "29/02/2023",  # Invalid dates
            "15/03/25", "2025", "March 2025",  # Incomplete dates
            "invalid", "", "NOT_FOUND"  # Non-dates
        ]
        
        for date_str in invalid_dates:
            result = self.validator.validate_date(date_str)
            assert not result.is_valid, f"Date {date_str} should be invalid"
    
    def test_date_reasonableness(self):
        """Test date reasonableness validation."""
        now = datetime.now()
        
        # Very old date (before MOT testing)
        old_date = "15/03/1950"
        result = self.validator.validate_date(old_date)
        assert not result.is_valid
        assert "before MOT testing began" in str(result.validation_errors)
        
        # Very future date
        future_year = now.year + 10
        future_date = f"15/03/{future_year}"
        result = self.validator.validate_date(future_date)
        assert not result.is_valid
        assert "unreasonably far in the future" in str(result.validation_errors)
    
    def test_expiry_calculation(self):
        """Test MOT expiry status calculation."""
        now = datetime.now()
        
        # Expired date
        expired_date = (now - timedelta(days=30)).strftime("%d/%m/%Y")
        result = self.validator.validate_date(expired_date)
        assert result.is_expired
        assert result.days_until_expiry is None
        
        # Future date
        future_date = (now + timedelta(days=60)).strftime("%d/%m/%Y")
        result = self.validator.validate_date(future_date)
        assert not result.is_expired
        assert result.days_until_expiry is not None
        assert result.days_until_expiry > 0
    
    def test_date_cleaning(self):
        """Test date string cleaning."""
        test_cases = [
            ("MOT: 15/03/2025", "15/03/2025"),
            ("Expires: 15/03/2025", "15/03/2025"),
            ("15/03/2025 MOT", "15/03/2025"),
            ("  15/03/2025  ", "15/03/2025")
        ]
        
        for input_date, expected_clean in test_cases:
            cleaned = self.validator._clean_date_string(input_date)
            # The cleaned string should contain the expected date
            assert expected_clean in cleaned or cleaned == expected_clean
    
    def test_ocr_corrections(self):
        """Test OCR error corrections."""
        # Test common OCR misreadings
        test_cases = [
            ("I5/O3/2O25", "15/03/2025"),  # I->1, O->0
            ("l5/o3/2o25", "15/03/2025"),  # l->1, o->0
            ("15/03/2O2S", "15/03/2025"),  # O->0, S->5
        ]
        
        for ocr_date, expected in test_cases:
            cleaned = self.validator._clean_date_string(ocr_date)
            # Should contain corrected characters
            assert "1" in cleaned and "0" in cleaned and "5" in cleaned
    
    def test_get_date_info(self):
        """Test getting comprehensive date information."""
        date_str = "15/03/2025"
        info = self.validator.get_date_info(date_str)
        
        assert info['original_string'] == date_str
        assert info['normalized_date'] == "15/03/2025"
        assert info['is_valid']
        assert 'parsed_date' in info
        assert 'formatted_date' in info
        assert 'status' in info
    
    def test_urgent_expiry_status(self):
        """Test urgent expiry status detection."""
        now = datetime.now()
        
        # Date expiring in 15 days (urgent)
        urgent_date = (now + timedelta(days=15)).strftime("%d/%m/%Y")
        info = self.validator.get_date_info(urgent_date)
        assert "URGENT" in info['status']
        
        # Date expiring in 45 days (soon)
        soon_date = (now + timedelta(days=45)).strftime("%d/%m/%Y")
        info = self.validator.get_date_info(soon_date)
        assert "SOON" in info['status']
        
        # Date expiring in 6 months (normal)
        normal_date = (now + timedelta(days=180)).strftime("%d/%m/%Y")
        info = self.validator.get_date_info(normal_date)
        assert "URGENT" not in info['status'] and "SOON" not in info['status']


if __name__ == "__main__":
    pytest.main([__file__])
