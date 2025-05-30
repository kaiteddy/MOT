"""
DVLA Vehicle Enquiry Service API client for registration validation.
"""
import asyncio
import httpx
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from config.settings import settings


@dataclass
class DVLAVehicleInfo:
    """DVLA vehicle information."""
    registration_number: str
    make: str
    model: str
    colour: str
    fuel_type: str
    engine_capacity: Optional[int]
    date_of_first_registration: Optional[datetime]
    year_of_manufacture: Optional[int]
    co2_emissions: Optional[int]
    mot_status: Optional[str]
    mot_expiry_date: Optional[datetime]
    tax_status: Optional[str]
    tax_due_date: Optional[datetime]
    type_approval: Optional[str]
    wheelplan: Optional[str]
    revenue_weight: Optional[int]


@dataclass
class DVLAValidationResult:
    """Result of DVLA validation."""
    is_valid: bool
    vehicle_info: Optional[DVLAVehicleInfo]
    error_message: Optional[str]
    response_time: float
    api_status_code: Optional[int]


class DVLAAPIClient:
    """Client for DVLA Vehicle Enquiry Service API."""
    
    def __init__(self):
        self.api_key = settings.dvla_api_key
        self.api_url = settings.dvla_api_url
        self.timeout = settings.dvla_timeout
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.warning("DVLA API key not configured - validation will be skipped")
    
    async def validate_registration(self, registration: str) -> DVLAValidationResult:
        """
        Validate registration number against DVLA database.
        
        Args:
            registration: Vehicle registration number
            
        Returns:
            DVLAValidationResult with vehicle information or error
        """
        if not self.api_key:
            return DVLAValidationResult(
                is_valid=False,
                vehicle_info=None,
                error_message="DVLA API key not configured",
                response_time=0.0,
                api_status_code=None
            )
        
        if not registration or registration.strip() == "NOT_FOUND":
            return DVLAValidationResult(
                is_valid=False,
                vehicle_info=None,
                error_message="Invalid registration number",
                response_time=0.0,
                api_status_code=None
            )
        
        # Normalize registration for API call
        normalized_reg = self._normalize_registration(registration)
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await self._make_api_request(client, normalized_reg)
                
                response_time = asyncio.get_event_loop().time() - start_time
                
                if response.status_code == 200:
                    vehicle_data = response.json()
                    vehicle_info = self._parse_vehicle_data(vehicle_data, normalized_reg)
                    
                    return DVLAValidationResult(
                        is_valid=True,
                        vehicle_info=vehicle_info,
                        error_message=None,
                        response_time=response_time,
                        api_status_code=response.status_code
                    )
                
                elif response.status_code == 404:
                    return DVLAValidationResult(
                        is_valid=False,
                        vehicle_info=None,
                        error_message="Vehicle not found in DVLA database",
                        response_time=response_time,
                        api_status_code=response.status_code
                    )
                
                else:
                    error_msg = f"DVLA API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        if 'message' in error_data:
                            error_msg += f" - {error_data['message']}"
                    except:
                        pass
                    
                    return DVLAValidationResult(
                        is_valid=False,
                        vehicle_info=None,
                        error_message=error_msg,
                        response_time=response_time,
                        api_status_code=response.status_code
                    )
        
        except httpx.TimeoutException:
            response_time = asyncio.get_event_loop().time() - start_time
            return DVLAValidationResult(
                is_valid=False,
                vehicle_info=None,
                error_message="DVLA API request timeout",
                response_time=response_time,
                api_status_code=None
            )
        
        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"DVLA API error for registration {normalized_reg}: {str(e)}")
            return DVLAValidationResult(
                is_valid=False,
                vehicle_info=None,
                error_message=f"DVLA API error: {str(e)}",
                response_time=response_time,
                api_status_code=None
            )
    
    async def _make_api_request(self, client: httpx.AsyncClient, registration: str) -> httpx.Response:
        """
        Make the actual API request to DVLA.
        
        Args:
            client: HTTP client
            registration: Normalized registration number
            
        Returns:
            HTTP response
        """
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'registrationNumber': registration
        }
        
        response = await client.post(
            self.api_url,
            json=payload,
            headers=headers
        )
        
        return response
    
    def _normalize_registration(self, registration: str) -> str:
        """
        Normalize registration for DVLA API.
        
        Args:
            registration: Raw registration string
            
        Returns:
            Normalized registration string
        """
        # Remove spaces and convert to uppercase
        normalized = registration.replace(' ', '').upper()
        
        # Remove any non-alphanumeric characters
        normalized = ''.join(c for c in normalized if c.isalnum())
        
        return normalized
    
    def _parse_vehicle_data(self, data: Dict[str, Any], registration: str) -> DVLAVehicleInfo:
        """
        Parse DVLA API response into DVLAVehicleInfo object.
        
        Args:
            data: Raw API response data
            registration: Registration number
            
        Returns:
            DVLAVehicleInfo object
        """
        # Parse dates
        date_of_first_registration = None
        if data.get('dateOfFirstRegistration'):
            try:
                date_of_first_registration = datetime.strptime(
                    data['dateOfFirstRegistration'], '%Y-%m-%d'
                )
            except ValueError:
                pass
        
        mot_expiry_date = None
        if data.get('motExpiryDate'):
            try:
                mot_expiry_date = datetime.strptime(
                    data['motExpiryDate'], '%Y-%m-%d'
                )
            except ValueError:
                pass
        
        tax_due_date = None
        if data.get('taxDueDate'):
            try:
                tax_due_date = datetime.strptime(
                    data['taxDueDate'], '%Y-%m-%d'
                )
            except ValueError:
                pass
        
        return DVLAVehicleInfo(
            registration_number=registration,
            make=data.get('make', ''),
            model=data.get('model', ''),
            colour=data.get('colour', ''),
            fuel_type=data.get('fuelType', ''),
            engine_capacity=data.get('engineCapacity'),
            date_of_first_registration=date_of_first_registration,
            year_of_manufacture=data.get('yearOfManufacture'),
            co2_emissions=data.get('co2Emissions'),
            mot_status=data.get('motStatus'),
            mot_expiry_date=mot_expiry_date,
            tax_status=data.get('taxStatus'),
            tax_due_date=tax_due_date,
            type_approval=data.get('typeApproval'),
            wheelplan=data.get('wheelplan'),
            revenue_weight=data.get('revenueWeight')
        )
    
    def compare_extracted_data(
        self, 
        extracted_data: Dict[str, str], 
        dvla_info: DVLAVehicleInfo
    ) -> Dict[str, bool]:
        """
        Compare extracted data with DVLA information.
        
        Args:
            extracted_data: Data extracted from screenshot
            dvla_info: DVLA vehicle information
            
        Returns:
            Dictionary of field comparisons
        """
        comparisons = {}
        
        # Compare registration (should match exactly)
        extracted_reg = self._normalize_registration(extracted_data.get('registration', ''))
        dvla_reg = self._normalize_registration(dvla_info.registration_number)
        comparisons['registration'] = extracted_reg == dvla_reg
        
        # Compare make (case-insensitive, partial match allowed)
        extracted_make = extracted_data.get('make', '').upper()
        dvla_make = dvla_info.make.upper()
        if extracted_make and dvla_make:
            comparisons['make'] = (
                extracted_make in dvla_make or 
                dvla_make in extracted_make or
                extracted_make == dvla_make
            )
        else:
            comparisons['make'] = False
        
        # Compare model (case-insensitive, partial match allowed)
        extracted_model = extracted_data.get('model', '').upper()
        dvla_model = dvla_info.model.upper()
        if extracted_model and dvla_model:
            comparisons['model'] = (
                extracted_model in dvla_model or 
                dvla_model in extracted_model or
                extracted_model == dvla_model
            )
        else:
            comparisons['model'] = False
        
        # Compare MOT expiry date
        extracted_mot = extracted_data.get('mot_expiry', '')
        if extracted_mot and dvla_info.mot_expiry_date:
            try:
                extracted_date = datetime.strptime(extracted_mot, '%d/%m/%Y')
                comparisons['mot_expiry'] = extracted_date.date() == dvla_info.mot_expiry_date.date()
            except ValueError:
                comparisons['mot_expiry'] = False
        else:
            comparisons['mot_expiry'] = False
        
        return comparisons
