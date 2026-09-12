# Task 2.4 - Ingestion Design
sources:
  - source: "CSV/JSON/Parquet"
    method: "File copy"
    raw_destination: "raw/files/"
    duplicate_key: "File SHA-256"
    incremental_state: "N/A"
    key takeaways: 
      Each file is copied as-is into raw/files/ and a SHA-256 hash is
      recorded in the manifest. On rerun if the hash matches an existing
      entry the file is skipped and no duplicate is written.

  - source: "REST API"
    method: "Paginated GET"
    raw_destination: "raw/api/events.jsonl"
    duplicate_key: "event_id"
    incremental_state: "max(updated_at)"
    key takeaways: 
      Pages are requested in a loop until has_more is false. Records are
      deduplicated by event_id keeping the greatest updated_at and the
      watermark only advances after a confirmed successful write.

  - source: "PostgreSQL"
    method: "Inspection only in this lab"
    raw_destination: "N/A"
    duplicate_key: "ticket_id"
    incremental_state: 
      No extraction performed in this lab. updated_at is present on the
      table which makes a watermark strategy viable. CDC via PostgreSQL
      logical replication is the more reliable production option but is
      out of scope here.