# id-address — Roadmap & Development Process

## Vision

Menjadi **de-facto standard library** untuk parsing dan geocoding alamat Indonesia di ekosistem open-source.

---

## Phase 1: Foundation (v0.1.x) — ✅ DONE

**Status: Completed — April 2026**

### Goals
- [x] Project scaffold dengan struktur yang jelas
- [x] Core address parser (regex-based)
- [x] Basic geocoding via Nominatim
- [x] Data models (AddressResult, AddressComponents)
- [x] Confidence scoring system
- [x] Batch processing support
- [x] 10 test cases passing
- [x] MIT License
- [x] README dengan dokumentasi awal

### What Works
```python
parser = AddressParser()
result = parser.parse("Jl. Sudirman No. 123, RT 05/RW 08, Jakarta 12190")
# ✅ Parses street, house number, RT/RW, postal code, city

geocoder = Geocoder()
geocoder.geocode(result)
# ✅ Returns lat/lon from Nominatim
```

### Known Gaps
- Administrative matching masih heuristic (belum ada dataset Kemendagri)
- Parser bias Jakarta
- Tidak handle landmark ("Sebelah Indomaret")
- Tidak ada fuzzy matching

---

## Phase 2: Dataset Integration (v0.2.x) — 🎯 NEXT

**Target: Mei–Juni 2026 (6–8 minggu)**

### Goals
1. **Kemendagri Dataset Collection**
   - Scrape/download data administrasi 80K+ desa/kelurahan
   - Struktur: Provinsi → Kota/Kabupaten → Kecamatan → Kelurahan/Desa → Kode Pos
   - Simpan sebagai JSON/SQLite untuk query cepat

2. **Smart Administrative Matching**
   - Setelah parse RT/RW dan street, match kelurahan/kecamatan dari dataset
   - Fuzzy matching untuk typo (`"Kbyoran Baru"` → `"Kebayoran Baru"`)
   - Disambiguation: "Sudirman" bisa ada di 5 kota berbeda

3. **Improved Parser Coverage**
   - Handle landmark-based addresses: `"Depan Masjid Al-Ikhlas, Jl. Fatmawati"`
   - Handle perumahan/komplek: `"Komp. Puri Kencana Blok A12 No. 3"`
   - Handle alamat pedesaan (tanpa jalan): `"Desa Sukamaju, Kec. Cisarua, Bogor"`

4. **Caching Layer**
   - Cache geocoding results (SQLite atau in-memory dict)
   - Hindari hit Nominatim berulang kali untuk alamat sama
   - TTL-based invalidation (default: 30 hari)

5. **CLI Tool (MVP)**
   ```bash
   $ id-address parse "Jl. Sudirman, Jakarta"
   $ id-address geocode "Jl. Sudirman, Jakarta" --output json
   $ id-address bulk addresses.csv --output geocoded.csv
   ```

### Deliverables
- [ ] `id_address/data/kemendagri_2026.json` (dataset)
- [ ] `id_address/dataset.py` (dataset loader & matcher)
- [ ] Fuzzy matching untuk kelurahan/kecamatan
- [ ] Landmark detection (basic)
- [ ] Geocoding cache (SQLite)
- [ ] CLI entry point (`id-address`)
- [ ] 30+ test cases
- [ ] Coverage > 80%

### Success Metrics
- Parse accuracy > 85% (diukur dari test set 500 alamat random)
- Geocoding success rate > 70%
- Response time < 100ms untuk parse tanpa geocoding

---

## Phase 3: Polish & Community (v0.3.x)

**Target: Juli–September 2026**

### Goals
1. **React Component (Frontend)**
   ```jsx
   import { AddressInput } from '@id-address/react'
   
   <AddressInput
     onChange={(result) => console.log(result)}
     placeholder="Masukkan alamat..."
   />
   ```
   - Autocomplete saat user mengetik
   - Dropdown saran kelurahan/kecamatan
   - Validasi postal code otomatis

2. **Provider Plugin System**
   ```python
   from id_address import Geocoder
   from id_address.providers import GoogleGeocoder, MapboxGeocoder
   
   geocoder = Geocoder(providers=[
       NominatimGeocoder(),  # default, free
       GoogleGeocoder(api_key="..."),  # fallback, berbayar
   ])
   ```

3. **Better Documentation**
   - API reference lengkap (Sphinx atau MkDocs)
   - Tutorial: "Building a delivery app with id-address"
   - Tutorial: "Bulk geocoding 10,000 addresses"
   - Migration guide dari library lain

4. **CI/CD Pipeline**
   - GitHub Actions: test on push (Python 3.10, 3.11, 3.12)
   - Auto-publish ke PyPI on tag
   - Code coverage badge
   - Linting check di PR

5. **Performance Optimization**
   - Async support (`async def parse()`, `async def geocode()`)
   - Parallel batch geocoding (asyncio.gather)
   - Memory profiling untuk dataset besar

### Deliverables
- [ ] `@id-address/react` package (NPM)
- [ ] Plugin system untuk geocoding providers
- [ ] MkDocs documentation site
- [ ] GitHub Actions CI/CD
- [ ] Async API
- [ ] 50+ test cases
- [ ] Coverage > 90%

### Success Metrics
- 100+ GitHub stars
- 2+ external contributors
- Dipakai di 1-2 startup/project open-source

---

## Phase 4: Scale & Ecosystem (v1.0.0)

**Target: Q4 2026 – Q1 2027**

### Goals
1. **Production-Ready Stability**
   - Semantic versioning 1.0 (API stabil, no breaking changes tanpa major version)
   - Backward compatibility guarantee
   - Changelog yang jelas untuk setiap release

2. **Advanced Features**
   - **Address validation**: "Apakah alamat ini valid/exists?"
   - **Address normalization**: Standardize format untuk database consistency
   - **Distance calculation**: Hitung jarak antara 2 alamat
   - **Administrative hierarchy**: `get_children(kecamatan)` → list kelurahan

3. **Integration Ecosystem**
   - Plugin untuk **FastAPI** (auto-validate address di endpoint)
   - Plugin untuk **SQLAlchemy** (Address type untuk ORM)
   - Plugin untuk **Pandas** (vectorized parsing untuk DataFrame)
   - Wrapper untuk **Gojek/Grab delivery API**

4. **Community & Marketing**
   - Blog post di HackerNews, r/Indonesia, r/algotrading
   - Submit ke **Awesome Python** list
   - Submit ke **Awesome Indonesia** list
   - Talk di meetup/komunitas developer Indonesia

5. **Monetization (Opsional)**
   - Hosted API service (berbayar untuk volume tinggi)
   - Premium dataset (updated quarterly)
   - Consulting untuk enterprise integration

### Deliverables
- [ ] v1.0.0 stable release
- [ ] FastAPI, SQLAlchemy, Pandas plugins
- [ ] Hosted API (opsional)
- [ ] 500+ GitHub stars
- [ ] Featured di Awesome lists
- [ ] Dipakai di production oleh 3-5 perusahaan

### Success Metrics
- Parse accuracy > 95%
- Geocoding success rate > 85%
- 10+ external contributors
- 1K+ PyPI downloads/bulan

---

## Long-Term Vision (2027+)

### Geographic Expansion
- **Malaysia**: Address parser untuk format Malaysia (similar administrative structure)
- **Philippines**: Address parser untuk format Filipina
- **Southeast Asia**: Unified address standardization library

### AI-Enhanced Parsing
- Fine-tune small LLM (atau gunakan API) untuk parse alamat yang sangat ambigu
- Train pada dataset 1M+ alamat real dari users (anonymized)
- Confidence score berbasis model prediction, bukan heuristic

### Government Partnership
- Kolaborasi dengan **Kemendagri** untuk digitalisasi data administrasi
- Kolaborasi dengan **POS Indonesia** untuk postal code database
- Kontribusi balik ke **OpenStreetMap** Indonesia

---

## Development Process

### Workflow

```
Issue/Feature Request
    ↓
Discuss (GitHub Issues)
    ↓
Branch: feature/<name>
    ↓
Implement + Tests
    ↓
PR → Review (self-review atau community)
    ↓
Merge to master
    ↓
Release (tag + PyPI publish)
```

### Release Cadence

| Version | Frequency | Scope |
|---------|-----------|-------|
| **Patch** (0.1.1, 0.1.2) | Setiap ada bugfix | Fix only, no new features |
| **Minor** (0.2.0, 0.3.0) | 4–8 minggu | New features, backward compatible |
| **Major** (1.0.0, 2.0.0) | 6–12 bulan | Breaking changes, stability guarantee |

### Quality Gates

| Gate | Tool | Threshold |
|------|------|-----------|
| Tests | pytest | 100% pass rate |
| Coverage | pytest-cov | > 80% (v0.2), > 90% (v0.3+) |
| Linting | ruff | 0 errors, 0 warnings |
| Formatting | black | Auto-formatted |
| Type checking | mypy | 0 errors (target v0.3) |

### Decision-Making

- **Solo maintainer** (v0.1–v0.3): Verry Simatupang mengambil semua keputusan teknis
- **Community-driven** (v1.0+): RFC process untuk perubahan besar, vote dari contributors aktif
- **BDFL** (Beyond v1.0): Verry sebagai BDFL (Benevolent Dictator For Life) dengan tim core maintainers

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Nominatim rate limiting | High | Medium | Caching, multiple providers, respect ToS |
| Dataset tidak tersedia | Medium | High | Scrape Kemendagri, crowdsource dari users |
| Low community adoption | Medium | High | Marketing, blog posts, HN submission |
| Competing library muncul | Low | Medium | First-mover advantage, community building |
| Burnout (solo maintainer) | Medium | High | Recruit co-maintainers early, dokumentasi bagus |
| Legal/privacy issues (address data) | Low | High | Anonymize data, comply with UU PDP |

---

## Milestones Tracker

| Milestone | Target Date | Status | Notes |
|-----------|-------------|--------|-------|
| ✅ Initial scaffold | April 10, 2026 | ✅ DONE | Parser + geocoder + tests |
| 🎯 Kemendagri dataset | Mei 2026 | ⏳ Pending | Scrape/download data |
| 🎯 Fuzzy matching | Juni 2026 | ⏳ Pending | Integrate thefuzz |
| 🎯 CLI tool | Juni 2026 | ⏳ Pending | Click/typer-based CLI |
| 🎯 v0.2.0 release | Juli 2026 | ⏳ Pending | Dataset + CLI + caching |
| 🎯 React component | Agustus 2026 | ⏳ Pending | @id-address/react |
| 🎯 100 GitHub stars | September 2026 | ⏳ Pending | Marketing push |
| 🎯 v0.3.0 release | Oktober 2026 | ⏳ Pending | Plugins + async + docs |
| 🎯 v1.0.0 release | Q1 2027 | ⏳ Pending | Production stable |

---

## Resources & References

### Data Sources
- **Kemendagri**: https://www.kemendagri.go.id/ (data wilayah administrasi)
- **BPS**: https://www.bps.go.id/ (statistik & geografis)
- **POS Indonesia**: https://www.posindonesia.co.id/ (kode pos)
- **OpenStreetMap**: https://www.openstreetmap.org/ (geocoding via Nominatim)
- **Nominatim API**: https://nominatim.org/release-docs/latest/api/Overview/

### Similar Projects (Inspiration)
- **libaddressinput** (Google): https://github.com/google/libaddressinput
- **postal** (OpenCage): https://github.com/openvenues/libpostal
- **pyap**: https://github.com/vladimirdotpy/pyap (address parsing untuk US/UK)
- **panduan-kode-pos**: https://github.com/nickohappy7/kode-pos (kode pos Indonesia)

### Indonesian Admin Boundaries
- **GitHub: indonesia-geo**: https://github.com/ans-4175/indonesia-geo
- **GitHub: wilayah-administratif**: Various repos dengan data GeoJSON
- **Kemendagri Permendagri No. 72 Tahun 2019**: Tentang Kode dan Data Wilayah Administrasi Pemerintahan

---

## Changelog

### v0.1.0 — April 10, 2026
- 🎉 Initial release
- ✅ AddressParser dengan regex-based parsing
- ✅ Geocoder dengan Nominatim integration
- ✅ AddressResult & AddressComponents models
- ✅ Confidence scoring
- ✅ Batch processing
- ✅ 10 test cases

---

_This roadmap is a living document. Updated as the project evolves._
_Last updated: April 10, 2026_
