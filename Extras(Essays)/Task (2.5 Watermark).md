# Task 2.5 - Watermark Semantics

The API watermark is the greatest successfully persisted updated_at value.
On the next run the pipeline requests only records with updated_at greater
than the saved watermark. The watermark is operational state, not source data.

## What could go wrong if the watermark is saved before the raw file is written?

If the watermark moves forward before the write finishes and something
fails midway, the pipeline assumes those records were already handled. The
next run only fetches anything newer than the advanced watermark so the
records from the failed run never get retrieved again. There is no error
thrown, just a quiet gap in the data that would be very easy to miss
unless someone was actively checking record counts. This is why the
watermark should only advance after the write is confirmed, not before.

## What could go wrong if the source allows multiple records with exactly the same timestamp?

The watermark filter uses strictly greater than the saved value. If
several records share the exact same timestamp as the current watermark,
any that were not included in the last successful run get permanently
skipped on every future run since they will never be strictly newer than
the watermark. The pipeline has no way to catch this because it only
tracks the watermark value and not how many records were sitting at that
exact timestamp. 

## One limitation and one production-grade mitigation

Limitation: If multiple records share the exact same updated_at value
as the watermark, any that were not part of the previous successful run
will be silently skipped on all future runs with no way to recover them
short of a full re-ingest.

## Mitigation: 
A production pipeline would persist not just the watermark
timestamp but also the set of event_ids ingested at that exact timestamp.
The next run would fetch records where updated_at is greater than or equal
to the watermark then filter out the already ingested event_ids. That way
new records at the boundary timestamp are not missed while previously
ingested ones are not duplicated.