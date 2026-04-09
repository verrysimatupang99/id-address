# id-address — Agent Development Guide

This file provides context for AI agents (Qwen Code, Claude, etc.) working on this project.

## Project Overview

**id-address** is an Indonesian address parser and geocoder library. It converts messy, unstructured Indonesian address strings into structured components (street, RT/RW, kelurahan, kecamatan, city, province, postal code) and geocodes them to coordinates.

### Key Characteristics
- **Python 3.10+** library, MIT licensed
- **Single responsibility**: Parse Indonesian addresses → structured data + coordinates
- **No heavy dependencies**: Only `requests` and `thefuzz`
- **Target audience**: Indonesian developers building logistics, e-commerce, ride-hailing, property, or HRIS applications

## Architecture

```
id_address/
├── models.py       # Pure dataclasses — no external dependencies
├── parser.py       # Regex-based address parsing (stateless, deterministic)
├── geocoder.py     # Nominatim/OpenStreetMap HTTP client (stateful, rate-limited)
└── __init__.py     # Public API: AddressParser, Geocoder, AddressResult
```

### Design Principles

1. **Fail gracefully** — Never raise exceptions on bad input. Return low-confidence results instead.
2. **Deterministic parsing** — Same input always produces same output (no randomization).
3. **Extensible** — Plugin architecture planned for custom parsers and geocoding providers.
4. **Test-first** — All new features must have tests before merging.

## Code Conventions

### Style
- **Line length**: 100 characters (see `pyproject.toml` `[tool.ruff]`)
- **Type hints**: Mandatory on all public functions and methods
- **Docstrings**: Google-style for all public classes and functions
- **Formatting**: `black` for code, `ruff` for linting

### Naming
- **Classes**: `PascalCase` (`AddressParser`, `AddressResult`)
- **Functions/Methods**: `snake_case` (`parse`, `geocode_batch`)
- **Constants**: `UPPER_SNAKE_CASE` (`STREET_TYPES`, `RT_RW_PATTERN`)
- **Private/Internal**: Leading underscore (`_calculate_confidence`)

### Imports
```python
# Standard library
from __future__ import annotations
import re
from typing import Optional

# Third-party
import requests

# First-party
from id_address.models import AddressResult
```

## Testing

### Location
All tests in `tests/` directory, named `test_<module>.py`.

### Running Tests
```bash
# From project root
source venv/bin/activate
pytest tests/ -v

# With coverage
pytest tests/ --cov=id_address --cov-report=term-missing
```

### Test Conventions
- Use `pytest` fixtures for setup (`setup_method` or `@pytest.fixture`)
- Test both happy path AND edge cases (empty input, malformed addresses, unicode)
- Mock HTTP calls in geocoder tests (use `responses` or `unittest.mock`)
- Test confidence scores are always 0.0–1.0

## Common Tasks

### Adding a New Parser Feature
1. Add regex pattern to `parser.py` constants section
2. Add extraction logic to `AddressParser.parse()` method
3. Update `_calculate_confidence()` to weight the new component
4. Add tests in `tests/test_parser.py`
5. Update README.md examples

### Adding a New Geocoding Provider
1. Create new provider class in `geocoder.py` or separate file
2. Implement `geocode(address_result) -> AddressResult` interface
3. Add to `Geocoder.__init__()` as optional provider
4. Add tests with mocked HTTP responses
5. Document in README

### Adding a New Administrative Level
1. Update `AddressComponents` dataclass in `models.py`
2. Update parser logic in `parser.py`
3. Update `_determine_match_level()` if needed
4. Add tests for addresses containing that level
5. Update dataset loader (when Kemendagri dataset is integrated)

## Known Limitations (as of v0.1.0)

1. **No dataset integration** — Administrative matching is heuristic only (no Kemendagri data yet)
2. **Jakarta bias** — Parser works best for Jakarta addresses; other cities need improvement
3. **No landmark support** — "Sebelah Indomaret", "Depan Masjid" etc. not parsed
4. **No fuzzy matching** — Typos in addresses cause parse failures
5. **Single geocoding source** — Only Nominatim; no fallback providers
6. **No caching** — Repeated geocoding hits Nominatim API every time

## Dependencies

### Required
- `requests>=2.28` — HTTP client for geocoding
- `thefuzz>=0.19` — Fuzzy string matching (declared but not yet used)

### Development
- `pytest>=7.0` — Testing framework
- `pytest-cov>=4.0` — Coverage reporting
- `black>=23.0` — Code formatter
- `ruff>=0.1.0` — Linter
- `mypy>=1.0` — Static type checking (declared but not yet configured)

## External Services

### Nominatim / OpenStreetMap
- **URL**: `https://nominatim.openstreetmap.org/search`
- **Rate limit**: 1 request/second (enforced by `Geocoder.geocode_batch()`)
- **Attribution required**: Must credit OpenStreetMap in production
- **No API key needed** — Free and open
- **User-Agent**: Must be set (currently `id-address/0.1.0`)

### Future Data Sources
- **Kemendagri** — Official Indonesian administrative boundaries (80K+ villages)
- **BPS** — Indonesian statistics agency geographic data
- **POS Indonesia** — Postal code database

## Git Workflow

- **Branch naming**: `feature/<name>`, `fix/<name>`, `docs/<name>`
- **Commit messages**: Conventional Commits style (`feat:`, `fix:`, `docs:`, `test:`)
- **Squash merges** for feature branches (keep history clean)
- **No force-push** to `master`

## Publishing Checklist

Before publishing to PyPI:
- [ ] All tests pass (`pytest`)
- [ ] No linting errors (`ruff check id_address/`)
- [ ] Code formatted (`black id_address/`)
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] README.md examples work with published version
- [ ] Build succeeds (`python -m build`)
- [ ] Test install in fresh venv (`pip install dist/*.whl`)
