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

def append_run_log(run_id, started_at, finished_at, status, source,
                   records_read, records_written, duplicates_removed,
                   watermark_before, watermark_after, error_message):
    log_path = RAW/'pipeline_run_log.csv'
    write_header = not log_path.exists()
    with open(log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                'run_id','started_at','finished_at','status','source',
                'records_read','records_written','duplicates_removed',
                'watermark_before','watermark_after','error_message'
            ])
        writer.writerow([
            run_id, started_at, finished_at, status, source,
            records_read, records_written, duplicates_removed,
            watermark_before, watermark_after, error_message
        ])

def ingest_files():
    files = ['customers.csv', 'orders.json', 'products.parquet']
    dest  = RAW/'files'
    dest.mkdir(exist_ok=True)

    manifest_path = dest/'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    for file_name in files:
        run_id     = str(uuid.uuid4())
        started_at = utc_now()
        src        = DATA/file_name
        file_hash  = sha256_file(src)

        if any(entry['sha256'] == file_hash for entry in manifest.values()):
            print(f'  SKIP {file_name} — hash already in manifest')
            append_run_log(run_id, started_at, utc_now(), 'skipped', file_name,
                           0, 0, 0, None, None, 'duplicate hash')
            continue

        shutil.copy2(src, dest/file_name)
        manifest[file_name] = {
            'source_file' : file_name,
            'ingested_at' : started_at,
            'sha256'      : file_hash,
            'bytes'       : src.stat().st_size,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f'  OK   {file_name} — {src.stat().st_size:,} bytes — {file_hash[:12]}...')
        append_run_log(run_id, started_at, utc_now(), 'success', file_name,
                       1, 1, 0, None, None, '')

def fetch_api_page(page, per_page=20, updated_after=None):
    params={'page':page,'per_page':per_page}
    if updated_after: params['updated_after']=updated_after
    r=requests.get(API_URL,params=params,timeout=30); r.raise_for_status(); return r.json()

def ingest_api():
    run_id           = str(uuid.uuid4())
    started_at       = utc_now()
    watermark_before = load_watermark()

    try:
        print(f'  watermark before: {watermark_before}')

        all_records = []
        page = 1
        while True:
            data = fetch_api_page(page, updated_after=watermark_before)
            for record in data['items']:
                record['_ingested_at'] = started_at
                record['_source']      = API_URL
                all_records.append(record)
            print(f'  fetched page {page} ({len(data["items"])} records)')
            if not data['has_more']:
                break
            page = data['next_page']

        print(f'  total records fetched: {len(all_records)}')

        seen = {}
        for record in all_records:
            eid = record['event_id']
            if eid not in seen or record['updated_at'] > seen[eid]['updated_at']:
                seen[eid] = record
        deduped            = list(seen.values())
        duplicates_removed = len(all_records) - len(deduped)
        print(f'  duplicates removed: {duplicates_removed}')

        if not deduped:
            print('  no new records since last watermark')
            append_run_log(run_id, started_at, utc_now(), 'success', 'api_events',
                           0, 0, 0, watermark_before, watermark_before, '')
            return

        dest = RAW/'api'
        dest.mkdir(exist_ok=True)
        tmp  = dest/'events.tmp'
        with open(tmp, 'w') as f:
            for record in deduped:
                f.write(json.dumps(record) + '\n')
        tmp.replace(dest/'events.jsonl')
        print(f'  written {len(deduped)} records to raw/api/events.jsonl')

        watermark_after = max(r['updated_at'] for r in deduped)
        save_watermark(watermark_after)
        print(f'  watermark after: {watermark_after}')

        append_run_log(run_id, started_at, utc_now(), 'success', 'api_events',
                       len(all_records), len(deduped), duplicates_removed,
                       watermark_before, watermark_after, '')

    except requests.exceptions.RequestException as e:
        print(f'  ERROR fetching API: {e}')
        append_run_log(run_id, started_at, utc_now(), 'failed', 'api_events',
                       0, 0, 0, watermark_before, watermark_before, str(e))
        raise

if __name__=='__main__':
    RAW.mkdir(exist_ok=True); STATE.mkdir(exist_ok=True)
    ingest_files(); ingest_api()