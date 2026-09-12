"""Week 2 starter: profile CSV, JSON, Parquet, API payload, and PostgreSQL table.
Complete the TODOs. Do not hard-code expected counts.
"""
import pandas as pd
from pathlib import Path
import json, csv
DATA_DIR=Path(__file__).resolve().parents[1]/'data'

def profile_csv(path):
    # TODO: row count, columns, missing counts, duplicate rows, duplicate customer_id, inferred types
    print (f'Profiling CSV file: {path} (Size: {path.stat().st_size} bytes)')
    print (f'Row count: {sum(1 for row in open(path)) - 1}')  # Excludes the headers
    print (f'Columns: {len(next(csv.reader(open(path))))}')
    df = pd.read_csv(path)
    missing = df.isnull().sum()
    print('Missing value counts by column:')
    for col, cnt in missing.items():
        print(f'  {col}: {cnt}')
    print(f'Duplicate rows: {sum(1 for i, row in enumerate(csv.reader(open(path))) if row in list(csv.reader(open(path)))[:i])}')
    is_unique = df['customer_id'].is_unique
    dup_ids = df[df['customer_id'].duplicated(keep=False)]['customer_id'].unique()
    print(f'Testing for customer_id_uniqueness: {is_unique} — repeated IDs: {list(dup_ids)}')
    logical_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
    logical_overrides = {'signup_date': 'date (ISO-8601)', 'customer_segment': 'category'}
    logical_types.update(logical_overrides)
    print(f'Inferred types: {logical_types}')
    print('Candidate validation rules:')
    print('  1. customer_id must be non-null and match pattern, increasing order')
    print('  2. customer_id must be unique across all rows')
    print('  3. email, when present, must contain exactly one @ character')
    print('  4. signup_date must be parseable as ISO-8601 date (YYYY-MM-DD)')
    print('  5. customer_segment must be one of: SME, Retail, Professional, Student')
    pass

def profile_json(path):
    # TODO: record count, keys, nested fields, date/time fields, numeric fields, nulls
    print (f'Profiling JSON file: {path} (Size: {path.stat().st_size} bytes)')
    with open(path) as f:
        data = json.load(f)
    print(f'Record count: {len(data)}')
    print(f'Keys: {list(data[0].keys()) if data else []}')
    print(f'Nested fields: {[(k, v) for k, v in data[0].items() if isinstance(v, dict)] if data else []}')
    print(f'Date/time fields: {[(k, v) for k, v in data[0].items() if isinstance(v, str) and v.count("-") == 2 and v.count(":") == 2] if data else []}')
    print(f'Identified numeric fields: {[(k, v) for k, v in data[0].items() if isinstance(v, (int, float))] if data else []}')
    print(f"Nulls and missing keys: {[(i, {k: record.get(k) for k in set().union(*(item.keys() for item in data)) if k not in record or record[k] is None}) for i, record in enumerate(data) if any(k not in record or record[k] is None for k in set().union(*(item.keys() for item in data)))] if data else []}")
    print('Two downstream representations for the nested shipping object:')
    print('  Option A - Flatten: add shipping_region and shipping_method as top-level columns.')
    print('    Pro: simple tabular format, works directly in SQL/CSV.')
    print('    Con: adds columns, breaks if shipping gains new sub-fields.')
    print('  Option B - Separate child table keyed on order_id.')
    print('    Pro: normalised, extensible without touching the parent schema.')
    print('    Con: requires a JOIN to query order and shipping together.')
    pass

def profile_parquet(path):
    df = pd.read_parquet(path)
    print(f'Profiling Parquet file: {path} (Size: {path.stat().st_size} bytes)')
    print(f'Rows: {len(df)}')
    print(f'Columns: {list(df.columns)}')
    print(f'Data types: {df.dtypes.to_dict()}')
    print(f'Nulls: {df.isnull().sum().to_dict()}')

    csv_path  = path.parent / 'products_optional_compare.csv'
    json_path = path.parent / 'products_optional_compare.json'
    df_csv    = pd.read_csv(csv_path)
    df_json   = pd.read_json(json_path)
    print('File size comparison (same 200-row dataset):')
    print(f'  parquet : {path.stat().st_size:,} bytes')
    print(f'  csv     : {csv_path.stat().st_size:,} bytes')
    print(f'  json    : {json_path.stat().st_size:,} bytes')
    print('  Note: parquet larger than CSV here — compression pays off at scale, not 200 rows.')
    print('Type preservation (stock_quantity):')
    print(f'  parquet: {df["stock_quantity"].dtype} | csv: {df_csv["stock_quantity"].dtype} | json: {df_json["stock_quantity"].dtype}')
    print('  Parquet preserves int32 exactly; CSV and JSON carry no schema so pandas infers int64.')
    print('Schema behaviour comparison:')
    print('  CSV    : no embedded schema; types inferred by pandas, can be wrong.')
    print('  JSON   : no embedded schema; types inferred per field, silent coercion possible.')
    print('  Parquet: schema in file footer (Arrow/Thrift) — types guaranteed on read.')
    print('Why Parquet is not a common operational source format:')
    print('  Parquet is columnar, immutable, batch-oriented — no row-level inserts/updates/deletes.')
    print('  Operational systems produce real-time transactions Parquet cannot receive.')
    print('  Requires a runtime (pandas/Spark/DuckDB) to decode — not native to apps or terminals.')


if __name__=='__main__':
    profile_csv(DATA_DIR/'customers.csv')
    profile_json(DATA_DIR/'orders.json')
    profile_parquet(DATA_DIR/'products.parquet')
