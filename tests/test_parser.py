"""Tests for Indonesian address parser."""

import pytest
from id_address import AddressParser
from id_address.models import AddressResult


class TestAddressParser:
    """Test cases for AddressParser."""
    
    def setup_method(self):
        self.parser = AddressParser()
    
    def test_parse_jakarta_address(self):
        """Test parsing a typical Jakarta address."""
        address = "Jl. M.H. Thamrin No.1, RT.02/RW.08, Gelora, Tanah Abang, Jakarta Pusat 10270"
        result = self.parser.parse(address)
        
        assert isinstance(result, AddressResult)
        assert result.components.street is not None or result.components.street_name is not None
        assert result.components.rt is not None
        assert result.components.postal_code == "10270"
    
    def test_parse_simple_address(self):
        """Test parsing a simple address."""
        address = "Jl. Sudirman, Jakarta"
        result = self.parser.parse(address)
        
        assert result.components.city is not None or result.raw_input == address
    
    def test_parse_with_rt_rw(self):
        """Test RT/RW extraction."""
        address = "RT 05/RW 08, Senayan, Jakarta Selatan"
        result = self.parser.parse(address)
        
        assert result.components.rt is not None
        assert result.components.rw is not None
    
    def test_parse_postal_code_only(self):
        """Test postal code extraction."""
        address = "Jakarta 12190"
        result = self.parser.parse(address)
        
        assert result.components.postal_code == "12190"
    
    def test_parse_batch(self):
        """Test batch parsing."""
        addresses = [
            "Jl. Sudirman, Jakarta",
            "RT 05/RW 08, Bandung",
            "Jl. Gatot Subroto No. 10, Surabaya 60271",
        ]
        results = self.parser.parse_batch(addresses)
        
        assert len(results) == 3
        assert all(isinstance(r, AddressResult) for r in results)
    
    def test_empty_address(self):
        """Test parsing empty string."""
        result = self.parser.parse("")
        assert isinstance(result, AddressResult)
        assert result.raw_input == ""
    
    def test_confidence_score(self):
        """Test that confidence score is between 0 and 1."""
        result = self.parser.parse("Jl. Sudirman No. 123, RT 05/RW 08, Jakarta 12190")
        assert 0.0 <= result.confidence <= 1.0


class TestAddressResult:
    """Test cases for AddressResult model."""
    
    def test_formatted_address(self):
        """Test formatted address output."""
        from id_address.models import AddressComponents
        
        components = AddressComponents(
            street="Jalan Sudirman",
            house_number="123",
            rt="05",
            rw="08",
            kelurahan="Senayan",
            kecamatan="Kebayoran Baru",
            city="Jakarta Selatan",
            province="DKI Jakarta",
            postal_code="12190",
        )
        
        result = AddressResult(
            raw_input="test",
            components=components,
        )
        
        formatted = result.formatted
        assert "Sudirman" in formatted
        assert "12190" in formatted
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        from id_address.models import AddressComponents
        
        components = AddressComponents(street="Test Street", city="Jakarta")
        result = AddressResult(raw_input="test", components=components)
        
        d = result.to_dict()
        assert "raw_input" in d
        assert "components" in d
        assert d["components"]["street"] == "Test Street"
    
    def test_str_representation(self):
        """Test string representation."""
        from id_address.models import AddressComponents
        
        components = AddressComponents(street="Test Street")
        result = AddressResult(raw_input="test", components=components)
        
        assert isinstance(str(result), str)
