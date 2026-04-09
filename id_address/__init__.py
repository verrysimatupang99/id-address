"""
Indonesian Address Parser & Geocoder
=====================================

Parse Indonesian addresses into structured components and geocode them to coordinates.

Usage:
    >>> from id_address import AddressParser
    >>> parser = AddressParser()
    >>> result = parser.parse("Jl. M.H. Thamrin No.1, RT.02/RW.08, Gelora, Tanah Abang, Jakarta Pusat 10270")
    >>> print(result.province)
    DKI Jakarta
"""

__version__ = "0.1.0"
__author__ = "Verry Simatupang"
__license__ = "MIT"

from id_address.parser import AddressParser
from id_address.geocoder import Geocoder
from id_address.models import AddressResult

__all__ = ["AddressParser", "Geocoder", "AddressResult"]
