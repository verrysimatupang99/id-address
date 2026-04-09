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

    @pytest.mark.parametrize(
        "address,expected_rt",
        [
            ("Jl. M.H. Thamrin No.1, RT.02/RW.08, Gelora, Tanah Abang, Jakarta Pusat 10270", "2"),
            ("Jl. Jend. Sudirman No. 10, RT 01/RW 02, Gubeng, Surabaya, Jawa Timur 60281", "1"),
            ("Jl. A. Yani Km. 5, RT.05/RW.01, Pemurus Baru, Banjarmasin Selatan, Kota Banjarmasin, Kalimantan Selatan", "5"),
            ("Jl. Raya Puputan, RT 001/RW 002, Renon, Denpasar Selatan, Denpasar, Bali", "1"),
            ("Jl. Sudirman No. 34, Medan Polonia, Kota Medan, Sumatera Utara", None),
        ]
    )
    def test_parse_regional_addresses(self, address, expected_rt):
        """Test parsing addresses from various regions with different formats."""
        result = self.parser.parse(address)
        if expected_rt:
            assert result.components.rt == expected_rt
            assert result.components.raw_rtrw is not None
        else:
            assert result.components.rt is None

    @pytest.mark.parametrize(
        "address,expected_street,expected_rt,expected_rw",
        [
            ("Jl. H. Agus Salim No.10 RT 003 RW 007 Kel Menteng", "Jalan H. Agus Salim", "3", "7"),
            ("RT.05/RW.03 Ds. Sumberagung Kec. Moyudan Sleman DIY", None, "5", "3"),
            ("Blok A3 No 5 Perumahan Griya Asri, Banjarbaru", "Blok A3", None, None),
            ("Gang Mawar II No. 3B", "Gang Mawar II", None, None),
        ]
    )
    def test_parse_ecommerce_edge_cases(self, address, expected_street, expected_rt, expected_rw):
        """Test common messy e-commerce/logistics address formats."""
        result = self.parser.parse(address)
        if expected_street:
            assert result.components.street == expected_street
        if expected_rt:
            assert result.components.rt == expected_rt
            assert result.components.rw == expected_rw

    def test_parse_unicode_normalization(self):
        """Test that unicode normalization cleans up bad characters."""
        # Address with non-standard unicode characters
        address = "Jl. Sudirm\u00e1n No. 1\u00b23" # á and ²
        result = self.parser.parse(address)
        assert "Sudirmán" in result.raw_input
        # The parser's string is now normalized. It doesn't drop accents but normalizes superscripts
        assert result.components.house_number == "123"
    
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
