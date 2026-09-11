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
    print (f'Missing value counts by column: {sum(1 for row in csv.reader(open(path)) if any(field == "" for field in row))}')
    print(f'Duplicate rows: {sum(1 for i, row in enumerate(csv.reader(open(path))) if row in list(csv.reader(open(path)))[:i])}')
    print(f'Testing for customer_id_uniqueness: {len(set(row[0] for row in csv.reader(open(path)))) == sum(1 for row in csv.reader(open(path))) - 1}')
    print (f'Inferred types: {[(field, type(field)) for field in next(csv.reader(open(path))) if field]}')
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
    pass

def profile_parquet(path):
    # TODO: use pandas.read_parquet; report rows/columns/dtypes/nulls and file size
    # Requires pyarrow from requirements.txt
    pass
    df = pd.read_parquet(path)
    print(f'Profiling Parquet file: {path} (Size: {path.stat().st_size} bytes)')
    print(f'Rows: {len(df)}')
    print(f'Columns: {list(df.columns)}')
    print(f'Data types: {df.dtypes.to_dict()}')
    print(f'Nulls: {df.isnull().sum().to_dict()}')
    pass

if __name__=='__main__':
    profile_csv(DATA_DIR/'customers.csv')
    profile_json(DATA_DIR/'orders.json')
    profile_parquet(DATA_DIR/'products.parquet')
