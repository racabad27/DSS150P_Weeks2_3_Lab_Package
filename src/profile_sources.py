"""Week 2 starter: profile CSV, JSON, Parquet, API payload, and PostgreSQL table.
Complete the TODOs. Do not hard-code expected counts.
"""
from pathlib import Path
import json, csv
DATA_DIR=Path(__file__).resolve().parents[1]/'data'

def profile_csv(path):
    # TODO: row count, columns, missing counts, duplicate rows, duplicate customer_id, inferred types
    print (f'  Profiling CSV file: {path} (Size: {path.stat().st_size} bytes)')
    print (f'  Row count: {sum(1 for row in open(path)) - 1}')  # Excludes the headers
    print (f'  Columns: {len(next(csv.reader(open(path))))}')
    print (f'  Missing value counts by column: {sum(1 for row in csv.reader(open(path)) if any(field == "" for field in row))}')
    print(f'   Duplicate rows: {sum(1 for i, row in enumerate(csv.reader(open(path))) if row in list(csv.reader(open(path)))[:i])}')
    print(f' Testing for customer_id_uniqueness: {len(set(row[0] for row in csv.reader(open(path)))) == sum(1 for row in csv.reader(open(path))) - 1}')
    print (f'  Inferred types: {[(field, type(field)) for field in next(csv.reader(open(path))) if field]}')
    pass

def profile_json(path):
    # TODO: record count, keys, nested fields, date/time fields, numeric fields, nulls
    pass

def profile_parquet(path):
    # TODO: use pandas.read_parquet; report rows/columns/dtypes/nulls and file size
    # Requires pyarrow from requirements.txt
    pass

if __name__=='__main__':
    profile_csv(DATA_DIR/'customers.csv')
    profile_json(DATA_DIR/'orders.json')
    profile_parquet(DATA_DIR/'products.parquet')
