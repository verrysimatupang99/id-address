# id-address

**Indonesian Address Parser & Geocoder** — parse messy Indonesian addresses into structured components and geocode them to coordinates.

[![PyPI version](https://badge.fury.io/py/id-address.svg)](https://badge.fury.io/py/id-address)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Why?

Indonesian addresses are **chaos**. There's no standardized format, and addresses often mix:
- Street abbreviations (`Jl.`, `Jalan`, `Jln.`, `Gg.`, `Gang`)
- RT/RW (unique neighborhood system: `RT 05/RW 08`)
- Administrative levels (Kelurahan → Kecamatan → Kota/Kabupaten → Provinsi)
- Landmarks (`Sebelah Indomaret`, `Depan Masjid`)
- Inconsistent postal codes

Google Maps API is expensive. Existing parsers don't handle Indonesian formats. This library fills that gap.

## Installation

```bash
pip install id-address
```

## Quick Start

```python
from id_address import AddressParser, Geocoder

# Parse an address
parser = AddressParser()
result = parser.parse("Jl. M.H. Thamrin No.1, RT.02/RW.08, Gelora, Tanah Abang, Jakarta Pusat 10270")

print(result.components.street)        # "Jalan M.H. Thamrin"
print(result.components.house_number)  # "1"
print(result.components.rt)            # "02"
print(result.components.rw)            # "08"
print(result.components.kelurahan)     # "Gelora"
print(result.components.kecamatan)     # "Tanah Abang"
print(result.components.city)          # "Jakarta Pusat"
print(result.components.province)      # "DKI Jakarta"
print(result.components.postal_code)   # "10270"

# Geocode it
geocoder = Geocoder()
geocoder.geocode(result)
print(result.latitude)   # -6.1944
print(result.longitude)  # 106.8229
print(result.confidence) # 0.85
```

## Features

### ✅ Currently Supported
- **Street parsing**: Jl., Jalan, Gg., Gang, Lorong, Komplek, Kavling, Blok
- **RT/RW extraction**: `RT 05/RW 08`, `RT.003/RW.006`, etc.
- **House numbers**: `No. 123`, `Nomor 5`, etc.
- **Postal codes**: 5-digit Indonesian postal code detection
- **Administrative levels**: Kelurahan, Kecamatan, City, Province (heuristic)
- **Jakarta special cases**: Handles Jakarta Pusat/Selatan/Barat/Timur/Utara
- **Geocoding**: Nominatim (OpenStreetMap) integration with rate limiting
- **Reverse geocoding**: Coordinates → address
- **Batch processing**: Parse/geocode multiple addresses
- **Confidence scoring**: 0.0–1.0 estimate of parse quality

### 🚧 Roadmap
- [ ] Full Kemendagri dataset (80K+ desa/kelurahan)
- [ ] Fuzzy matching for typos
- [ ] React component for address input
- [ ] CLI tool for bulk parsing
- [ ] Support for landmarks & POI-based addresses
- [ ] Integration with local geocoding providers

## Usage Examples

### Parse a batch of addresses

```python
addresses = [
    "Jl. Sudirman No. 45, Jakarta Pusat 10220",
    "Gg. Kelinci No.3, Petojo Selatan, Gambir, Jakarta Pusat 10160",
    "Komp. Puri Kencana Blok A12, Kembangan, Jakarta Barat 11610",
]

parser = AddressParser()
results = parser.parse_batch(addresses)

for r in results:
    print(f"{r.formatted} (confidence: {r.confidence})")
```

### Reverse geocoding

```python
from id_address import Geocoder

geocoder = Geocoder()
result = geocoder.reverse_geocode(-6.2088, 106.8229)

if result:
    print(result.formatted)
    # Output: Jalan M.H. Thamrin, Gelora, Tanah Abang, Jakarta Pusat, DKI Jakarta
```

### Geocode with rate limiting

```python
geocoder = Geocoder()
results = geocoder.geocode_batch(parsed_results, delay=1.0)  # 1 sec between requests
```

## API Reference

### `AddressParser`

| Method | Description |
|--------|-------------|
| `parse(address: str) -> AddressResult` | Parse single address |
| `parse_batch(addresses: list[str]) -> list[AddressResult]` | Parse multiple addresses |
| `load_dataset(path: str)` | Load administrative dataset (optional) |

### `Geocoder`

| Method | Description |
|--------|-------------|
| `geocode(result: AddressResult) -> AddressResult` | Geocode parsed address in-place |
| `geocode_batch(results: list[AddressResult], delay: float) -> list[AddressResult]` | Batch geocode with rate limiting |
| `reverse_geocode(lat: float, lon: float) -> Optional[AddressResult]` | Reverse geocoding |

### `AddressResult`

| Property | Type | Description |
|----------|------|-------------|
| `raw_input` | `str` | Original address string |
| `components` | `AddressComponents` | Parsed components |
| `latitude` | `float \| None` | Latitude coordinate |
| `longitude` | `float \| None` | Longitude coordinate |
| `confidence` | `float` | Confidence score (0.0–1.0) |
| `formatted` | `str` | Formatted address string |
| `to_dict()` | `dict` | Dictionary representation |

## Project Structure

```
id-address/
├── id_address/
│   ├── __init__.py
│   ├── models.py        # Data models
│   ├── parser.py        # Address parser
│   ├── geocoder.py      # Geocoding logic
│   └── data/            # Administrative datasets (future)
├── tests/
│   └── test_parser.py
├── pyproject.toml
└── README.md
```

## Development

### Setup

```bash
git clone https://github.com/verrysimatupang99/id-address.git
cd id-address
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Lint & format

```bash
ruff check id_address/
black id_address/
```

## Data Sources

- **Nominatim/OpenStreetMap**: Free geocoding (requires attribution)
- **Kemendagri** (future): Official Indonesian administrative boundaries (80K+ villages)
- **BPS** (future): Indonesian statistics agency geographic data

## License

MIT License — see [LICENSE](LICENSE) file.

## Contributing

Contributions welcome! Areas we need help:

1. **Dataset collection**: Kemendagri administrative boundary data
2. **Better parsing**: Handle more address formats & edge cases
3. **Fuzzy matching**: Improve matching for typos & abbreviations
4. **Documentation**: Examples, tutorials, API docs
5. **Tests**: More test cases for different address formats

Please open an issue or PR on GitHub.

## Acknowledgments

Built because every Indonesian developer has suffered through parsing addresses like:
> "Jl. K.H. Hasyim Ashari No. 89, RT.07/RW.02, Duri Pulo, Kec. Gambir, Kota Jakarta Pusat, DKI Jakarta 10140 — SEBERANG INDOMARET"

No more. 🇮🇩
