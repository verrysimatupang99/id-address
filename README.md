# id-address

**Indonesian Address Parser & Geocoder** — parse messy Indonesian addresses into structured components and geocode them to coordinates.

[![PyPI version](https://badge.fury.io/py/id-address.svg)](https://badge.fury.io/py/id-address)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why?

Indonesian addresses are **chaos**. There's no standardized format, and addresses often mix:
- Street abbreviations (`Jl.`, `Jalan`, `Jln.`, `Gg.`, `Gang`, `Komp.`)
- RT/RW (unique neighborhood system: `RT 05/RW 08`)
- Administrative levels (Kelurahan → Kecamatan → Kota/Kabupaten → Provinsi)
- Landmarks (`Sebelah Indomaret`, `Depan Masjid`)
- Inconsistent postal codes

Google Maps API is expensive. Existing parsers don't handle Indonesian formats. This library fills that gap by providing a deterministic parser backed by **official Kemendagri dataset matching** and **fuzzy text matching**.

## Installation

```bash
pip install id-address
```

## Quick Start

```python
from id_address import AddressParser, Geocoder

parser = AddressParser()
result = parser.parse("Jl. M.H. Thamrin No.1, RT.02/RW.08, Gelora, Tanah Abang, Jakarta Pusat")

print(f"Street: {result.components.street}")
print(f"Kelurahan: {result.components.kelurahan}")
print(f"Kemendagri Code: {result.components.administrative_code}")
```

## Features

### ✅ Currently Supported
- **Dataset Integration**: Matches parsed components against official Kemendagri codes.
- **Fuzzy Matching**: Tolerates typos in Kelurahan/Kecamatan/City names via Levenshtein distance.
- **Robust Parsing**: Handles Street prefixes, RT/RW extraction, House numbers, Postal codes.
- **Unicode Normalization**: Automatically cleans messy encodings and HTML entities before parsing.
- **CLI Tool**: Process massive CSVs directly from the terminal via `id-address batch`.
- **Geocoding**: Abstract `BaseGeocoder` with a robust `NominatimGeocoder` implementation (includes exponential backoff).
- **Graceful Failure**: Tracks ambiguity inside `result.components.parse_warnings`.

### 🚧 Roadmap (v0.3 - v1.0)
- [ ] Enterprise Plugins (Pandas `id_address` accessor, FastAPI Pydantic validators)
- [ ] Multi-provider geocoding (Google Maps, Here)
- [ ] Support for POI/Landmark based addresses via Overpass API

## Usage Examples

### Command Line Interface (CLI)

Process thousands of addresses from a CSV file directly from your terminal:

```bash
# Parse a single address
id-address parse "Jl. Merdeka No 10, RT 03/RW 05, Menteng"

# Geocode a single address
id-address geocode "Jl. Ahmad Yani, Banjarmasin"

# Batch process a CSV file (must contain an 'address' column)
id-address batch input.csv -o cleaned_addresses.csv
```

### Custom Dataset / Kemendagri Data

By default, the library uses a bundled minimal sample dataset. To use the full Kemendagri dataset or your own custom administrative data, provide a JSON file formatted like so:

```json
[
  {
    "code": "31.71.01.1001",
    "province": "DKI Jakarta",
    "city": "Jakarta Pusat",
    "kecamatan": "Tanah Abang",
    "kelurahan": "Gelora",
    "postal_code": "10270"
  }
]
```

And load it into the parser:

```python
parser = AddressParser()
parser.load_dataset("path/to/your/custom_dataset.json")
```

### Parse a batch of addresses in Python

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
- **Kemendagri**: Official Indonesian administrative boundaries
- **BPS**: Indonesian statistics agency geographic data

## License

MIT License — see [LICENSE](LICENSE) file.

## Acknowledgments

Built because every Indonesian developer has suffered through parsing addresses like:
> "Jl. K.H. Hasyim Ashari No. 89, RT.07/RW.02, Duri Pulo, Kec. Gambir, Kota Jakarta Pusat, DKI Jakarta 10140 — SEBERANG INDOMARET"

No more. 🇮🇩