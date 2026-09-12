"""Starter validation checks for raw outputs."""
from pathlib import Path
from datetime import datetime
import json

ROOT=Path(__file__).resolve().parents[1]

def _parseable(value):
    try:
        datetime.fromisoformat(value)
        return True
    except Exception:
        return False

def main():
    passed = 0
    failed = 0

    def check(label, condition, detail=''):
        nonlocal passed, failed
        if condition:
            print(f'  PASS  {label}')
            passed += 1
        else:
            print(f'  FAIL  {label}{"  -- " + detail if detail else ""}')
            failed += 1

    print('--- file ingestion checks ---')
    for filename in ['customers.csv', 'orders.json', 'products.parquet']:
        check(
            f'raw/files/{filename} exists',
            (ROOT/'raw'/'files'/filename).exists()
        )

    check(
        'manifest.json exists',
        (ROOT/'raw'/'files'/'manifest.json').exists()
    )

    if (ROOT/'raw'/'files'/'manifest.json').exists():
        manifest = json.loads((ROOT/'raw'/'files'/'manifest.json').read_text())
        check(
            'manifest has entry for all 3 source files',
            all(f in manifest for f in ['customers.csv','orders.json','products.parquet'])
        )
        for filename in ['customers.csv', 'orders.json', 'products.parquet']:
            if filename in manifest:
                check(
                    f'{filename} manifest entry has required fields',
                    all(k in manifest[filename] for k in ['source_file','ingested_at','sha256','bytes'])
                )

    print('--- API ingestion checks ---')
    events_path = ROOT/'raw'/'api'/'events.jsonl'
    check('raw/api/events.jsonl exists', events_path.exists())

    if events_path.exists():
        records = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]

        event_ids = [r['event_id'] for r in records]
        check(
            'event_ids are unique after deduplication',
            len(event_ids) == len(set(event_ids)),
            f'{len(event_ids) - len(set(event_ids))} duplicates found'
        )
        check(
            '_ingested_at present on every record',
            all('_ingested_at' in r for r in records)
        )
        check(
            '_source present on every record',
            all('_source' in r for r in records)
        )
        check(
            'updated_at parseable on every record',
            all(_parseable(r['updated_at']) for r in records)
        )

    print('--- watermark checks ---')
    watermark_path = ROOT/'state'/'api_watermark.json'
    check('state/api_watermark.json exists', watermark_path.exists())

    if watermark_path.exists() and events_path.exists():
        watermark = json.loads(watermark_path.read_text())['updated_at']
        actual_max = max(r['updated_at'] for r in records)
        check(
            'watermark equals max updated_at in raw output',
            watermark == actual_max,
            f'watermark={watermark} max={actual_max}'
        )

    print(f'--- {passed} passed  {failed} failed ---')
    if failed > 0:
        raise SystemExit(1)

if __name__=='__main__': main()