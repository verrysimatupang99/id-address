"""Geocoder for Indonesian addresses using Nominatim (OpenStreetMap) and local datasets."""

from __future__ import annotations

import time
import logging
from typing import Optional
from urllib.parse import quote
from abc import ABC, abstractmethod

import requests

from id_address.models import AddressResult
from id_address.parser import AddressParser

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {
    "User-Agent": "id-address/0.1.0 (https://github.com/verrysimatupang99/id-address)",
}


class BaseGeocoder(ABC):
    """Abstract base class for geocoding providers."""
    
    @abstractmethod
    def geocode(self, address_result: AddressResult) -> AddressResult:
        """Geocode an AddressResult in-place."""
        pass
        
    @abstractmethod
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[AddressResult]:
        """Reverse geocode coordinates to an AddressResult."""
        pass
        
    def geocode_batch(self, results: list[AddressResult], delay: float = 1.0) -> list[AddressResult]:
        """Geocode multiple addresses with rate limiting."""
        for i, result in enumerate(results):
            self.geocode(result)
            if i < len(results) - 1:
                time.sleep(delay)
        return results


class NominatimGeocoder(BaseGeocoder):
    """
    Geocode Indonesian addresses to coordinates.
    
    Uses Nominatim (OpenStreetMap) as primary source with fallback logic
    for partial matches when full address geocoding fails.
    
    Usage:
        >>> from id_address import AddressParser, NominatimGeocoder
        >>> parser = AddressParser()
        >>> geocoder = NominatimGeocoder()
        >>> result = parser.parse("Jl. Sudirman, Jakarta Pusat")
        >>> geocoder.geocode(result)
        >>> print(result.latitude)
        -6.2088
    """
    
    def __init__(self, nominatim_url: str = NOMINATIM_URL, timeout: float = 5.0):
        """
        Initialize geocoder.
        
        Args:
            nominatim_url: Nominatim API endpoint
            timeout: Request timeout in seconds
        """
        self.nominatim_url = nominatim_url
        self.timeout = timeout
        self._parser = AddressParser()
    
    def geocode(self, address_result: AddressResult) -> AddressResult:
        """
        Geocode a parsed address result in-place.
        
        Tries multiple strategies:
        1. Full address string via Nominatim
        2. Constructed address from components
        3. Fallback to city/province level
        
        Args:
            address_result: Result from AddressParser.parse()
            
        Returns:
            Same AddressResult with latitude/longitude populated
        """
        # Strategy 1: Try full raw address
        if address_result.raw_input:
            coords = self._query_nominatim(address_result.raw_input)
            if coords:
                address_result.latitude = float(coords["lat"])
                address_result.longitude = float(coords["lon"])
                address_result.confidence = max(address_result.confidence, float(coords.get("importance", 0.5)))
                address_result.geocoding_source = "nominatim"
                return address_result
        
        # Strategy 2: Construct address from components
        constructed = self._construct_address(address_result.components)
        if constructed:
            coords = self._query_nominatim(constructed)
            if coords:
                address_result.latitude = float(coords["lat"])
                address_result.longitude = float(coords["lon"])
                address_result.confidence = max(address_result.confidence, float(coords.get("importance", 0.4)))
                address_result.geocoding_source = "nominatim"
                return address_result
        
        # Strategy 3: Try city + province only
        if address_result.components.city:
            city_query = address_result.components.city
            if address_result.components.province:
                city_query += f", {address_result.components.province}"
            coords = self._query_nominatim(city_query)
            if coords:
                address_result.latitude = float(coords["lat"])
                address_result.longitude = float(coords["lon"])
                address_result.confidence = 0.3
                address_result.geocoding_source = "nominatim"
                address_result.matched_level = "city"
                return address_result
        
        logger.warning(f"Could not geocode address: {address_result.raw_input}")
        return address_result
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[AddressResult]:
        """
        Reverse geocode coordinates to address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            AddressResult with parsed address components, or None
        """
        url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&addressdetails=1"
        
        try:
            response = requests.get(url, headers=NOMINATIM_HEADERS, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logger.warning(f"Reverse geocoding error: {data['error']}")
                return None
            
            address = data.get("address", {})
            result = AddressResult(
                raw_input=f"{latitude}, {longitude}",
                confidence=float(data.get("importance", 0.5)),
                geocoding_source="nominatim",
            )
            
            # Map Nominatim response to our components
            comp = result.components
            comp.road = address.get("road")
            comp.house_number = address.get("house_number")
            comp.suburb = address.get("suburb")
            comp.kelurahan = address.get("neighbourhood") or address.get("suburb")
            comp.kecamatan = address.get("city_district") or address.get("county")
            comp.city = address.get("city") or address.get("town") or address.get("municipality")
            comp.province = address.get("state")
            comp.postal_code = address.get("postcode")
            
            result.latitude = latitude
            result.longitude = longitude
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Reverse geocoding failed: {e}")
            return None
    
    def _query_nominatim(self, query: str) -> Optional[dict]:
        """Query Nominatim with an address string."""
        params = {
            "q": f"{query}, Indonesia",
            "format": "json",
            "limit": 1,
            "countrycodes": "id",  # Indonesia only
        }
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.nominatim_url,
                    params=params,
                    headers=NOMINATIM_HEADERS,
                    timeout=self.timeout,
                )
                
                if response.status_code == 429:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited by Nominatim (429). Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                    
                response.raise_for_status()
                results = response.json()
                
                if results:
                    return results[0]
                return None
                
            except requests.RequestException as e:
                logger.warning(f"Nominatim query failed for '{query}': {e}")
                return None
                
        return None
    
    def _construct_address(self, components) -> str:
        """Construct address string from components for geocoding."""
        parts = []
        
        if components.street:
            addr = components.street
            if components.house_number:
                addr += f" No. {components.house_number}"
            parts.append(addr)
        
        if components.kelurahan:
            parts.append(components.kelurahan)
        if components.kecamatan:
            parts.append(components.kecamatan)
        if components.city:
            parts.append(components.city)
        if components.province and "jakarta" not in components.province.lower():
            parts.append(components.province)
        
        return ", ".join(parts) if parts else ""
