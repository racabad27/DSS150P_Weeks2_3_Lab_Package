"""Week 3 starter: rerunnable ingestion to a raw area.
Students implement file ingestion + paginated REST API ingestion + watermark + duplicate prevention.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, uuid, csv
import requests

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; RAW=ROOT/'raw'; STATE=ROOT/'state'
API_URL='http://127.0.0.1:8000/api/events'

def utc_now(): return datetime.now(timezone.utc).isoformat()

def sha256_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def load_watermark():
    p=STATE/'api_watermark.json'
    if not p.exists(): return None
    return json.loads(p.read_text())['updated_at']

def save_watermark(value):
    STATE.mkdir(exist_ok=True)
    tmp=STATE/'api_watermark.tmp'
    tmp.write_text(json.dumps({'updated_at':value},indent=2))
    tmp.replace(STATE/'api_watermark.json')

def ingest_files():
    files = ['customers.csv', 'orders.json', 'products.parquet']
    dest  = RAW/'files'
    dest.mkdir(exist_ok=True)

    manifest_path = dest/'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    for file_name in files:
        src       = DATA/file_name
        file_hash = sha256_file(src)

        if any(entry['sha256'] == file_hash for entry in manifest.values()):
            print(f'  SKIP {file_name} — hash already in manifest')
            continue

        shutil.copy2(src, dest/file_name)
        manifest[file_name] = {
            'source_file' : file_name,
            'ingested_at' : utc_now(),
            'sha256'      : file_hash,
            'bytes'       : src.stat().st_size,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f'  OK   {file_name} — {src.stat().st_size:,} bytes — {file_hash[:12]}...')

def fetch_api_page(page, per_page=20, updated_after=None):
    params={'page':page,'per_page':per_page}
    if updated_after: params['updated_after']=updated_after
    r=requests.get(API_URL,params=params,timeout=30); r.raise_for_status(); return r.json()

def ingest_api():
    started_at       = utc_now()
    watermark_before = load_watermark()

    try:
        # 1) read watermark
        print(f'  watermark before: {watermark_before}')

        # 2) follow pagination until has_more is False
        all_records = []
        page = 1
        while True:
            data = fetch_api_page(page, updated_after=watermark_before)
            for record in data['items']:
                # 3) attach ingestion metadata
                record['_ingested_at'] = started_at
                record['_source']      = API_URL
                all_records.append(record)
            print(f'  fetched page {page} ({len(data["items"])} records)')
            if not data['has_more']:
                break
            page = data['next_page']

        print(f'  total records fetched: {len(all_records)}')

        # 4) deduplicate by event_id keeping greatest updated_at
        seen = {}
        for record in all_records:
            eid = record['event_id']
            if eid not in seen or record['updated_at'] > seen[eid]['updated_at']:
                seen[eid] = record
        deduped            = list(seen.values())
        duplicates_removed = len(all_records) - len(deduped)
        print(f'  duplicates removed: {duplicates_removed}')

        # 5) write raw/api/events.jsonl atomically
        dest = RAW/'api'
        dest.mkdir(exist_ok=True)
        tmp  = dest/'events.tmp'
        with open(tmp, 'w') as f:
            for record in deduped:
                f.write(json.dumps(record) + '\n')
        tmp.replace(dest/'events.jsonl')
        print(f'  written {len(deduped)} records to raw/api/events.jsonl')

        # 6) update watermark only after successful write
        watermark_after = max(r['updated_at'] for r in deduped)
        save_watermark(watermark_after)
        print(f'  watermark after: {watermark_after}')

    except requests.exceptions.RequestException as e:
        print(f'  ERROR fetching API: {e}')
        raise

if __name__=='__main__':
    RAW.mkdir(exist_ok=True); STATE.mkdir(exist_ok=True)
    ingest_files(); ingest_api()