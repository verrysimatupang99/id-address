"""Command-line interface for id-address."""

import click
import json
import csv
import sys
from id_address.parser import AddressParser
from id_address.geocoder import NominatimGeocoder

@click.group()
def main():
    """id-address: Parse and geocode Indonesian addresses."""
    pass

@main.command()
@click.argument('address')
def parse(address):
    """Parse a single Indonesian address."""
    parser = AddressParser()
    result = parser.parse(address)
    click.echo(json.dumps(result.to_dict(), indent=2))

@main.command()
@click.argument('address')
def geocode(address):
    """Parse and geocode a single Indonesian address."""
    parser = AddressParser()
    geocoder = NominatimGeocoder()
    result = parser.parse(address)
    geocoded = geocoder.geocode(result)
    click.echo(json.dumps(geocoded.to_dict(), indent=2))

@main.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), required=True, help="Output CSV file path.")
def batch(input_file, output):
    """Batch parse and geocode addresses from a CSV file. Expects an 'address' column."""
    parser = AddressParser()
    geocoder = NominatimGeocoder()
    
    with open(input_file, 'r', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        if not reader.fieldnames or 'address' not in reader.fieldnames:
            click.echo("Error: Input CSV must contain an 'address' column.", err=True)
            sys.exit(1)
        
        rows = list(reader)
        
    results = []
    with click.progressbar(rows, label='Processing addresses') as bar:
        for row in bar:
            parsed = parser.parse(row['address'])
            geocoded = geocoder.geocode(parsed)
            flat_dict = geocoded.to_dict()
            components = flat_dict.pop('components', {})
            for k, v in components.items():
                flat_dict[f"comp_{k}"] = v
            results.append(flat_dict)
            
    if not results:
        click.echo("No results to write.")
        return

    with open(output, 'w', encoding='utf-8', newline='') as fout:
        # Collect all possible keys for the CSV header
        fieldnames = set()
        for r in results:
            fieldnames.update(r.keys())
        writer = csv.DictWriter(fout, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(results)
        
    click.echo(f"Successfully processed {len(results)} addresses to {output}.")

if __name__ == '__main__':
    main()
