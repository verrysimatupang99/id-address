"""Data models for address parsing and geocoding results."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class AddressComponents:
    """Structured components of an Indonesian address."""
    
    # Street level
    street: Optional[str] = None
    street_type: Optional[str] = None  # Jl., Jalan, Gg., Gang, etc.
    street_name: Optional[str] = None
    house_number: Optional[str] = None
    building_name: Optional[str] = None
    
    # RT/RW (unique to Indonesia)
    rt: Optional[str] = None
    rw: Optional[str] = None
    
    # Administrative levels (smallest to largest)
    kelurahan: Optional[str] = None  # Village/sub-district
    kecamatan: Optional[str] = None  # District
    city: Optional[str] = None       # City/kabupaten
    province: Optional[str] = None
    
    # Postal
    postal_code: Optional[str] = None
    
    # Additional
    landmark: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AddressResult:
    """Complete result of address parsing and/or geocoding."""
    
    # Original input
    raw_input: str
    
    # Parsed components
    components: AddressComponents = field(default_factory=AddressComponents)
    
    # Geocoding
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float = 0.0  # 0.0 to 1.0
    
    # Metadata
    geocoding_source: Optional[str] = None  # "nominatim", "dataset", "fallback"
    matched_level: Optional[str] = None  # "exact", "street", "kelurahan", "kecamatan", "city"
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {
            "raw_input": self.raw_input,
            "components": self.components.to_dict(),
        }
        if self.latitude is not None:
            result["latitude"] = self.latitude
            result["longitude"] = self.longitude
            result["confidence"] = self.confidence
            result["geocoding_source"] = self.geocoding_source
        if self.matched_level:
            result["matched_level"] = self.matched_level
        return result
    
    @property
    def formatted(self) -> str:
        """Return formatted address string."""
        parts = []
        c = self.components
        
        if c.street:
            addr = c.street
            if c.house_number:
                addr += f" No. {c.house_number}"
            parts.append(addr)
        
        if c.rt or c.rw:
            rt_rw_parts = []
            if c.rt:
                rt_rw_parts.append(f"RT {c.rt}")
            if c.rw:
                rt_rw_parts.append(f"RW {c.rw}")
            parts.append("/".join(rt_rw_parts))
        
        if c.kelurahan:
            parts.append(c.kelurahan)
        if c.kecamatan:
            parts.append(c.kecamatan)
        if c.city:
            parts.append(c.city)
        if c.province:
            parts.append(c.province)
        if c.postal_code:
            parts.append(c.postal_code)
        
        return ", ".join(parts) if parts else self.raw_input
    
    def __str__(self) -> str:
        return self.formatted
    
    def __repr__(self) -> str:
        return f"AddressResult(formatted='{self.formatted}', confidence={self.confidence})"
