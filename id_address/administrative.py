"""Administrative dataset loader and matcher for Kemendagri data."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Optional, Dict, Any, List, Tuple

from thefuzz import process, fuzz


class AdministrativeDataset:
    """Loads and provides exact/fuzzy matching against the Kemendagri dataset."""
    
    def __init__(self, data_path: Optional[str] = None):
        self.data: List[Dict[str, str]] = []
        
        # In-memory indices for exact matching O(1)
        self._prov_index: Dict[str, str] = {}
        self._city_index: Dict[str, str] = {}
        self._kecamatan_index: Dict[str, str] = {}
        self._kelurahan_index: Dict[str, str] = {}
        
        # Pre-extracted lists for fuzzy matching
        self._cities_list: List[str] = []
        self._kecamatans_list: List[str] = []
        self._kelurahans_list: List[str] = []
        
        if data_path:
            self.load_data(data_path)
        else:
            # Fallback to bundled sample data if no path provided
            default_path = os.path.join(os.path.dirname(__file__), "data", "kemendagri_sample.json")
            if os.path.exists(default_path):
                self.load_data(default_path)

    def load_data(self, path: str) -> None:
        """Load JSON data and build indices."""
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
            
        for row in self.data:
            code = row.get("code", "")
            if not code:
                continue
                
            prov = row.get("province", "")
            city = row.get("city", "")
            kec = row.get("kecamatan", "")
            kel = row.get("kelurahan", "")
            
            # Exact indices map lowercase name to code
            if prov:
                self._prov_index[prov.lower()] = code
            if city:
                self._city_index[city.lower()] = code
                # Also index without 'Kota' or 'Kabupaten' prefixes
                clean_city = city.lower().replace("kota ", "").replace("kabupaten ", "").replace("kab. ", "")
                if clean_city:
                    self._city_index[clean_city] = code
            if kec:
                self._kecamatan_index[kec.lower()] = code
            if kel:
                self._kelurahan_index[kel.lower()] = code
        
        self._cities_list = list(self._city_index.keys())
        self._kecamatans_list = list(self._kecamatan_index.keys())
        self._kelurahans_list = list(self._kelurahan_index.keys())

    def get_row_by_code(self, code: str) -> Optional[Dict[str, str]]:
        """Retrieve full data row by Kemendagri code."""
        for row in self.data:
            if row.get("code") == code:
                return row
        return None

    def match_kelurahan(self, text: str) -> Tuple[Optional[str], float, bool]:
        """Match kelurahan. Returns (Kemendagri_code, score, is_fuzzy)."""
        text = text.lower().strip()
        if not text:
            return None, 0.0, False
            
        if text in self._kelurahan_index:
            return self._kelurahan_index[text], 100.0, False
            
        code, score = self._fuzzy_match_kelurahan(text)
        if code and score >= 85:
            return code, score, True
        return None, 0.0, False
        
    def match_kecamatan(self, text: str) -> Tuple[Optional[str], float, bool]:
        """Match kecamatan. Returns (Kemendagri_code, score, is_fuzzy)."""
        text = text.lower().strip()
        if not text:
            return None, 0.0, False
            
        if text in self._kecamatan_index:
            return self._kecamatan_index[text], 100.0, False
            
        code, score = self._fuzzy_match_kecamatan(text)
        if code and score >= 85:
            return code, score, True
        return None, 0.0, False
        
    def match_city(self, text: str) -> Tuple[Optional[str], float, bool]:
        """Match city. Returns (Kemendagri_code, score, is_fuzzy)."""
        text = text.lower().strip()
        if not text:
            return None, 0.0, False
            
        # Try exact with standard text
        if text in self._city_index:
            return self._city_index[text], 100.0, False
            
        # Try stripping prefixes
        clean_text = text.replace("kota ", "").replace("kabupaten ", "").replace("kab. ", "")
        if clean_text in self._city_index:
            return self._city_index[clean_text], 100.0, False
            
        code, score = self._fuzzy_match_city(clean_text)
        if code and score >= 90:
            return code, score, True
        return None, 0.0, False

    def match_province(self, text: str) -> Tuple[Optional[str], float, bool]:
        """Match province."""
        text = text.lower().strip()
        if not text:
            return None, 0.0, False
            
        if text in self._prov_index:
            return self._prov_index[text], 100.0, False
        return None, 0.0, False

    # The fuzzy matchers are wrapped in LRU Cache to avoid repetitive fuzzing in batches
    @lru_cache(maxsize=1024)
    def _fuzzy_match_kelurahan(self, text: str) -> Tuple[Optional[str], float]:
        if not self._kelurahans_list:
            return None, 0.0
        match = process.extractOne(text, self._kelurahans_list, scorer=fuzz.ratio)
        if match:
            best_match_str, score = match[:2]
            return self._kelurahan_index[best_match_str], float(score)
        return None, 0.0

    @lru_cache(maxsize=1024)
    def _fuzzy_match_kecamatan(self, text: str) -> Tuple[Optional[str], float]:
        if not self._kecamatans_list:
            return None, 0.0
        match = process.extractOne(text, self._kecamatans_list, scorer=fuzz.ratio)
        if match:
            best_match_str, score = match[:2]
            return self._kecamatan_index[best_match_str], float(score)
        return None, 0.0

    @lru_cache(maxsize=1024)
    def _fuzzy_match_city(self, text: str) -> Tuple[Optional[str], float]:
        if not self._cities_list:
            return None, 0.0
        match = process.extractOne(text, self._cities_list, scorer=fuzz.ratio)
        if match:
            best_match_str, score = match[:2]
            return self._city_index[best_match_str], float(score)
        return None, 0.0
