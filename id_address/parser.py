"""Indonesian address parser — converts raw address strings into structured components."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from id_address.models import AddressComponents, AddressResult
from id_address.administrative import AdministrativeDataset


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
RT_RW_PATTERN = re.compile(r'(?:RT|rt|Rt)\s*\.?\s*(\d{1,3})(?:\s*[/\-]\s*|\s+)(?:RW|rw|Rw)\s*\.?\s*(\d{1,3})', re.IGNORECASE)
POSTAL_CODE_PATTERN = re.compile(r'\b(\d{5})\b')
HOUSE_NUMBER_PATTERN = re.compile(r'\b(?:No\.?|Nomor|NO\.?)\s*\.?\s*([\d\w\-/]+)', re.IGNORECASE)
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
        self.dataset = AdministrativeDataset()
        self._loaded = True
    
    def load_dataset(self, dataset_path: Optional[str] = None) -> None:
        """
        Load administrative boundary dataset for better matching.
        
        Args:
            dataset_path: Path to CSV/JSON file with Indonesian administrative data.
                         If None, uses bundled minimal dataset.
        """
        self.dataset = AdministrativeDataset(dataset_path)
        self._loaded = True

    def _normalize_text(self, text: str) -> str:
        """Normalize unicode characters, strip HTML entities, and handle bad encodings."""
        if not text:
            return ""
        # NFKC normalizes things like ligatures
        text = unicodedata.normalize("NFKC", text)
        # Attempt to clean bad latin-1/utf-8 double encoding
        text = text.encode("utf-8", errors="ignore").decode("utf-8")
        return text.strip()
    
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
        
        # 0. Normalize the text (handle bad encoding)
        remaining = self._normalize_text(address)
        
        # 1. Extract postal code (5 digits)
        postal_match = POSTAL_CODE_PATTERN.search(remaining)
        if postal_match:
            components.postal_code = postal_match.group(1)
            remaining = remaining[:postal_match.start()] + remaining[postal_match.end():]
        
        # 2. Extract RT/RW
        rt_rw_match = RT_RW_PATTERN.search(remaining)
        if rt_rw_match:
            components.raw_rtrw = rt_rw_match.group(0).strip()
            components.rt = rt_rw_match.group(1).lstrip("0") or "0"
            components.rw = rt_rw_match.group(2).lstrip("0") or "0"
            remaining = remaining[:rt_rw_match.start()] + remaining[rt_rw_match.end():]
        
        # 3. Extract house number
        house_match = HOUSE_NUMBER_PATTERN.search(remaining)
        if house_match:
            components.house_number = house_match.group(1)
            # Don't remove from remaining — number might be part of address
        
        # 4. Parse comma-separated parts (common format)
        parts = [p.strip() for p in remaining.split(",") if p.strip()]
        
        # Try to identify street address (usually first part)
        if parts:
            first_part = parts[0].strip()
            
            # Extract explicit Kel/Kec/Ds from the first part if no commas separated them
            for kw in [" kecamatan ", " kec ", " kec. "]:
                idx = first_part.lower().find(kw)
                if idx != -1:
                    if not components.kecamatan:
                        components.kecamatan = first_part[idx + len(kw):].strip()
                    first_part = first_part[:idx].strip()
                    break
                    
            for kw in [" kelurahan ", " kel ", " kel. ", " desa ", " ds ", " ds. "]:
                idx = first_part.lower().find(kw)
                if idx != -1:
                    if not components.kelurahan:
                        components.kelurahan = first_part[idx + len(kw):].strip()
                    first_part = first_part[:idx].strip()
                    break
            
            street_match = STREET_PREFIX_PATTERN.match(first_part)
            if street_match:
                type_str = street_match.group(1)
                components.street_type = STREET_TYPES.get(type_str.lower(), type_str)
                rest_of_street = first_part[street_match.end():].strip()
                
                # Remove house number if present anywhere in the street string
                house_in_street = HOUSE_NUMBER_PATTERN.search(rest_of_street)
                if house_in_street:
                    if not components.house_number:
                        components.house_number = house_in_street.group(1)
                    rest_of_street = rest_of_street[:house_in_street.start()].strip()
                
                components.street_name = rest_of_street
                components.street = f"{components.street_type} {rest_of_street}".strip()
                parts = parts[1:]
            else:
                # If no street prefix, the whole first part might be the street/building
                house_in_street = HOUSE_NUMBER_PATTERN.search(first_part)
                if house_in_street:
                    if not components.house_number:
                        components.house_number = house_in_street.group(1)
                    first_part = first_part[:house_in_street.start()].strip()
                    
                if first_part and not components.street:
                    components.street = first_part
                parts = parts[1:]
                
                # If there are still leftovers from first_part (like City/Province separated by space), 
                # we should add them back to parts for the next step to process, but only if we had 0 commas originally.
                # Actually, our explicit Kel/Kec extraction modifies first_part, and we only assigned the remaining to components.street.
                # So if they typed "Jl Sudirman Kbyran Baru Jakarta Selatan"
                # first_part = "Jl Sudirman Kbyran Baru Jakarta Selatan"
                # components.street = "Jalan Sudirman Kbyran Baru Jakarta Selatan"
                # This means without commas, the whole string becomes the street.
                # We should extract the city and province from the end of the string.
        
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
                # Iterate through parts and look for explicit keywords first
                for p in parts:
                    p_lower = p.lower()
                    if p_lower.startswith("kota ") or p_lower.startswith("kabupaten ") or p_lower.startswith("kab "):
                        components.city = p
                    elif p_lower.startswith("kecamatan ") or p_lower.startswith("kec "):
                        components.kecamatan = p
                    elif p_lower.startswith("kelurahan ") or p_lower.startswith("kel "):
                        components.kelurahan = p
                    elif p_lower.startswith("provinsi ") or p_lower.startswith("prov "):
                        components.province = p
                
                # For any unassigned parts, fallback to index-based heuristics
                # Remove parts that were already explicitly assigned
                unassigned = [p for p in parts if p not in (components.city, components.kecamatan, components.kelurahan, components.province)]
                
                if unassigned:
                    if not components.city and len(unassigned) >= 2:
                        components.city = unassigned[-2].strip()
                        if not components.province:
                            components.province = unassigned[-1].strip()
                    elif not components.city and len(unassigned) == 1:
                        components.city = unassigned[-1].strip()
        else:
            # No commas were found, parts is empty. The entire remaining string is in components.street.
            # We need to extract the city/province from the end of the street string.
            if components.street:
                jakarta_match = re.search(r'\b(jakarta\s+(pusat|selatan|barat|timur|utara))\b', components.street, re.IGNORECASE)
                if jakarta_match:
                    components.city = f"Jakarta {jakarta_match.group(2).title()}"
                    components.street = components.street[:jakarta_match.start()].strip()
                    if not components.province:
                        components.province = "DKI Jakarta"
                
                # Check for explicit keywords at the end of the street string
                # We can do a reverse split to pull off City or Kecamatan if they aren't comma separated.
                # Example: "Jl. Jend. Sudirman No. 10 RT 01 RW 02 Kbyran Baru Jakarta Selatan"
                street_parts = components.street.split()
                if not components.city and len(street_parts) > 2:
                    # Let's see if the last two words match a city in our dataset list
                    last_two = f"{street_parts[-2]} {street_parts[-1]}"
                    if self._loaded and self.dataset._cities_list:
                        match_code, score, _ = self.dataset.match_city(last_two)
                        if match_code and score > 85:
                            components.city = last_two
                            components.street = " ".join(street_parts[:-2])
                            street_parts = components.street.split()

                if not components.kecamatan and len(street_parts) > 1:
                    # check last one or two words for kecamatan
                    for num_words in (2, 1):
                        if len(street_parts) >= num_words:
                            tail_words = " ".join(street_parts[-num_words:])
                            if self._loaded and self.dataset._kecamatans_list:
                                match_code, score, _ = self.dataset.match_kecamatan(tail_words)
                                if match_code and score > 85:
                                    components.kecamatan = tail_words
                                    components.street = " ".join(street_parts[:-num_words])
                                    street_parts = components.street.split()
                                    break
        
        # Cross-reference with Kemendagri dataset
        if self._loaded and self.dataset.data:
            self._enrich_from_dataset(components)
        
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
    
    def _enrich_from_dataset(self, components: AddressComponents) -> None:
        """Enrich and validate parsed components using the administrative dataset."""
        code = None
        # Start matching from smallest to largest to get the most specific code
        if components.kelurahan:
            match_code, score, is_fuzzy = self.dataset.match_kelurahan(components.kelurahan)
            if match_code:
                code = match_code
                if is_fuzzy:
                    components.parse_warnings.append(f"Fuzzy matched kelurahan '{components.kelurahan}' to score {score:.1f}")
        
        if not code and components.kecamatan:
            match_code, score, is_fuzzy = self.dataset.match_kecamatan(components.kecamatan)
            if match_code:
                code = match_code
                if is_fuzzy:
                    components.parse_warnings.append(f"Fuzzy matched kecamatan '{components.kecamatan}' to score {score:.1f}")
                    
        if not code and components.city:
            match_code, score, is_fuzzy = self.dataset.match_city(components.city)
            if match_code:
                code = match_code
                if is_fuzzy:
                    components.parse_warnings.append(f"Fuzzy matched city '{components.city}' to score {score:.1f}")
                    
        if code:
            components.administrative_code = code
            row = self.dataset.get_row_by_code(code)
            if row:
                # Standardize the names based on dataset
                if row.get("kelurahan") and (components.kelurahan or code == self.dataset.match_kelurahan(row.get("kelurahan", ""))[0]):
                    components.kelurahan = row.get("kelurahan")
                if row.get("kecamatan"):
                    components.kecamatan = row.get("kecamatan")
                if row.get("city"):
                    components.city = row.get("city")
                if row.get("province"):
                    components.province = row.get("province")
                if row.get("postal_code") and not components.postal_code:
                    components.postal_code = row.get("postal_code")

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
