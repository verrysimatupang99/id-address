# Google Colab Snippets for id-address

This file contains clean code blocks that you can directly copy and paste into Google Colab cells.

### Cell 1: Installation
```python
!pip install id-address==0.1.0a1
```

### Cell 2: Test Parser and Geocoder
```python
from id_address import AddressParser, Geocoder
import json

print("Memuat Dataset Kemendagri & Model...")
parser = AddressParser()
geocoder = Geocoder()

alamat_kotor = "Jl. Jend. Sudirman No. 10 RT 01 RW 02 Kbyran Baru Jakarta Selatan 12190"
print(f"\nAlamat Input: '{alamat_kotor}'")

print("\n--- HASIL PARSING ---")
parsed_result = parser.parse(alamat_kotor)

print(f"Jalan           : {parsed_result.components.street}")
print(f"Nomor Rumah     : {parsed_result.components.house_number}")
print(f"RT / RW         : {parsed_result.components.rt} / {parsed_result.components.rw}")
print(f"Kecamatan       : {parsed_result.components.kecamatan}")
print(f"Kota            : {parsed_result.components.city}")
print(f"Kode Pos        : {parsed_result.components.postal_code}")
print(f"Kode Kemendagri : {parsed_result.components.administrative_code}")

if parsed_result.components.parse_warnings:
    print(f"\nPeringatan Parser:")
    for warning in parsed_result.components.parse_warnings:
        print(f"- {warning}")

print("\n--- HASIL GEOCODING ---")
geocoded_result = geocoder.geocode(parsed_result)
print(f"Latitude    : {geocoded_result.latitude}")
print(f"Longitude   : {geocoded_result.longitude}")
print(f"Confidence  : {geocoded_result.confidence}")
print(f"Sumber API  : {geocoded_result.geocoding_source}")
```

### Cell 3: Test Pandas Batch Processing
```python
import pandas as pd
from id_address import AddressParser

df = pd.DataFrame({
    'id': [1, 2, 3, 4],
    'alamat_raw': [
        "Jl. H. Agus Salim No.10 RT 003 RW 007 Kel Menteng",
        "RT.05/RW.03 Ds. Sumberagung Kec. Moyudan Sleman DIY",
        "Blok A3 No 5 Perumahan Griya Asri, Banjarbaru",
        "Jl. Transmigrasi Gg. Mahakam, Ds. Baroqah, Simpang Empat, Tanah Bumbu"
    ]
})

parser = AddressParser()

def parse_to_dict(alamat):
    result = parser.parse(alamat)
    return {
        'jalan': result.components.street,
        'rt_rw': f"{result.components.rt}/{result.components.rw}",
        'kecamatan': result.components.kecamatan,
        'kota': result.components.city
    }

parsed_df = df['alamat_raw'].apply(parse_to_dict).apply(pd.Series)
df_bersih = pd.concat([df, parsed_df], axis=1)

display(df_bersih)
```