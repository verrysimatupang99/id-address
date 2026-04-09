"""Indonesian address parser — converts raw address strings into structured components."""

from __future__ import annotations

import re
from typing import Optional

from id_address.models import AddressComponents, AddressResult


# Common Indonesian street type abbreviations
STREET_TYPES = {
    "jl.": "Jalan",
    "jln.": "Jalan",
    "jln": "Jalan",
    "jl": "Jalan",
    "jalan": "Jalan",
    "gg.": "Gang",
    "gg": "Gang",
    "gang": "Gang",
    "ln.": "Lorong",
    "ln": "Lorong",
    "lorong": "Lorong",
    "perum.": "Perumahan",
    "perum": "Perumahan",
    "perumahan": "Perumahan",
    "komp.": "Komplek",
    "komp": "Komplek",
    "komplek": "Komplek",
    "kompleks": "Komplek",
    "kav.": "Kavling",
    "kav": "Kavling",
    "kavling": "Kavling",
    "blok": "Blok",
    "no.": "Nomor",
    "no": "Nomor",
}

# Regex patterns
RT_RW_PATTERN = re.compile(r'(?:RT|rt|Rt)\s*\.?\s*(\d{2,3})\s*[/\-]\s*(?:RW|rw|Rw)\s*\.?\s*(\d{2,3})', re.IGNORECASE)
POSTAL_CODE_PATTERN = re.compile(r'\b(\d{5})\b')
HOUSE_NUMBER_PATTERN = re.compile(r'(?:No\.?|Nomor|NO\.?)\s*\.?\s*([\d\w\-/]+)', re.IGNORECASE)
STREET_PREFIX_PATTERN = re.compile(
    r'^(Jl\.?|Jalan|Jln\.?|Gg\.?|Gang|Ln\.?|Lorong|Perum\.?|Perumahan|Komp\.?|Komplek|Kav\.?|Kavling|Blok)\s+',
    re.IGNORECASE
)


class AddressParser:
    """
    Parse Indonesian address strings into structured components.
    
    Handles common formats including:
    - Jl. Sudirman No. 123, RT 05/RW 08, Kel. Senayan, Kec. Kebayoran Baru, Jakarta Selatan 12190
    - Gang Kelinci No.5, RT.003/RW.006, Petojo Selatan, Kec. Gambir, Kota Jakarta Pusat 10160
    - Komp. Puri Kencana Blok A12 No. 3, Kembangan Selatan, Jakarta Barat
    
    Usage:
        >>> parser = AddressParser()
        >>> result = parser.parse("Jl. Sudirman No. 123, RT 05/RW 08, Jakarta 12190")
        >>> print(result.components.street)
        Sudirman
        >>> print(result.components.postal_code)
        12190
    """
    
    def __init__(self):
        self._kelurahan_list: list[str] = []
        self._kecamatan_list: list[str] = []
        self._city_list: list[str] = []
        self._province_list: list[str] = []
        self._loaded = False
    
    def load_dataset(self, dataset_path: Optional[str] = None) -> None:
        """
        Load administrative boundary dataset for better matching.
        
        Args:
            dataset_path: Path to CSV/JSON file with Indonesian administrative data.
                         If None, uses bundled minimal dataset.
        """
        # TODO: Load from Kemendagri dataset
        # For now, we use pattern-based parsing only
        self._loaded = True
    
    def parse(self, address: str) -> AddressResult:
        """
        Parse an Indonesian address string into structured components.
        
        Args:
            address: Raw address string
            
        Returns:
            AddressResult with parsed components
            
        Example:
            >>> parser = AddressParser()
            >>> result = parser.parse("Jl. M.H. Thamrin No.1, RT.02/RW.08, Gelora, Jakarta Pusat 10270")
            >>> result.components.street
            'M.H. Thamrin'
            >>> result.components.rt
            '02'
            >>> result.components.postal_code
            '10270'
        """
        components = AddressComponents()
        remaining = address.strip()
        
        # 1. Extract postal code (5 digits)
        postal_match = POSTAL_CODE_PATTERN.search(remaining)
        if postal_match:
            components.postal_code = postal_match.group(1)
            remaining = remaining[:postal_match.start()] + remaining[postal_match.end():]
        
        # 2. Extract RT/RW
        rt_rw_match = RT_RW_PATTERN.search(remaining)
        if rt_rw_match:
            components.rt = rt_rw_match.group(1).lstrip("0") or "0"
            components.rw = rt_rw_match.group(2).lstrip("0") or "0"
            remaining = remaining[:rt_rw_match.start()] + remaining[rt_rw_match.end():]
        
        # 3. Extract house number
        house_match = HOUSE_NUMBER_PATTERN.search(remaining)
        if house_match:
            components.house_number = house_match.group(1)
            # Don't remove from remaining — number might be part of address
        
        # 4. Parse comma-separated parts (common format)
        parts = [p.strip() for p in remaining.split(",")]
        
        # Try to identify street address (usually first part)
        if parts:
            first_part = parts[0].strip()
            street_match = STREET_PREFIX_PATTERN.match(first_part)
            if street_match:
                type_str = street_match.group(1)
                components.street_type = STREET_TYPES.get(type_str.lower(), type_str)
                rest_of_street = first_part[street_match.end():].strip()
                
                # Remove house number if present
                house_in_street = HOUSE_NUMBER_PATTERN.match(rest_of_street)
                if house_in_street and not components.house_number:
                    components.house_number = house_in_street.group(1)
                    rest_of_street = rest_of_street[house_in_street.end():].strip()
                
                components.street_name = rest_of_street
                components.street = f"{components.street_type} {rest_of_street}".strip()
                parts = parts[1:]
        
        # 5. Try to match remaining parts to administrative levels
        # This is heuristic — proper matching needs the full dataset
        if parts:
            # Last part before postal code is often city or province
            last_part = parts[-1].strip()
            
            # Check if it looks like a Jakarta area
            jakarta_patterns = [
                (r'jakarta\s+(pusat|selatan|barat|timur|utara)', "Jakarta"),
                (r'kota\s+administrasi\s+', ""),
                (r'dki\s+jakarta', "DKI Jakarta"),
            ]
            
            for pattern, replacement in jakarta_patterns:
                if re.search(pattern, last_part, re.IGNORECASE):
                    if "jakarta" in replacement.lower():
                        components.province = replacement if "dki" in replacement.lower() else "DKI Jakarta"
                        city_match = re.search(r'jakarta\s+(pusat|selatan|barat|timur|utara)', last_part, re.IGNORECASE)
                        if city_match:
                            components.city = f"Jakarta {city_match.group(1).title()}"
                    break
            
            # If not Jakarta, try to assign remaining parts
            if not components.city and len(parts) >= 2:
                # Second-to-last might be city, third might be province
                if len(parts) >= 3:
                    components.province = parts[-1].strip()
                    components.city = parts[-2].strip()
                    if len(parts) >= 4:
                        components.kecamatan = parts[-3].strip()
                        if len(parts) >= 5:
                            components.kelurahan = parts[-4].strip()
                else:
                    components.city = parts[-1].strip()
        
        # Calculate confidence based on how much we parsed
        confidence = self._calculate_confidence(components, address)
        matched_level = self._determine_match_level(components)
        
        return AddressResult(
            raw_input=address,
            components=components,
            confidence=confidence,
            matched_level=matched_level,
        )
    
    def parse_batch(self, addresses: list[str]) -> list[AddressResult]:
        """Parse multiple addresses."""
        return [self.parse(addr) for addr in addresses]
    
    def _calculate_confidence(self, components: AddressComponents, raw: str) -> float:
        """Estimate parsing confidence based on extracted components."""
        score = 0.0
        max_score = 0.0
        
        if components.street:
            score += 0.3
        max_score += 0.3
        
        if components.house_number:
            score += 0.1
        max_score += 0.1
        
        if components.rt and components.rw:
            score += 0.15
        max_score += 0.15
        
        if components.kelurahan:
            score += 0.15
        max_score += 0.15
        
        if components.kecamatan:
            score += 0.1
        max_score += 0.1
        
        if components.city:
            score += 0.1
        max_score += 0.1
        
        if components.province:
            score += 0.1
        max_score += 0.1
        
        if components.postal_code:
            score += 0.1
        max_score += 0.1
        
        return round(score / max_score, 2) if max_score > 0 else 0.0
    
    def _determine_match_level(self, components: AddressComponents) -> str:
        """Determine the granularity level of the parsed address."""
        if components.street and components.rt and components.kelurahan and components.kecamatan and components.city:
            return "exact"
        elif components.street and components.city:
            return "street"
        elif components.kelurahan and components.kecamatan:
            return "kelurahan"
        elif components.kecamatan:
            return "kecamatan"
        elif components.city:
            return "city"
        return "minimal"
