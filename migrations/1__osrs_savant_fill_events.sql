CREATE TABLE IF NOT EXISTS osrs_savant_fill_events (
    symbol LowCardinality(String) CODEC(ZSTD),
    price Float64 CODEC(Delta, ZSTD),
    quantity Int32 CODEC(ZSTD),
    time DateTime CODEC(DoubleDelta, ZSTD),
    order_id String CODEC(ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(time)
ORDER BY (order_id, time)
TTL time + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;