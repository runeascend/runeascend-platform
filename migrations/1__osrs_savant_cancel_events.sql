CREATE TABLE IF NOT EXISTS osrs_savant_cancel_events (
    order_id String CODEC(ZSTD),
    time DateTime CODEC(DoubleDelta, ZSTD),
    reason String CODEC(ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(time)
ORDER BY (order_id, time)
TTL time + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;