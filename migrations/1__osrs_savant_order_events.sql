CREATE TABLE IF NOT EXISTS osrs_savant_order_events (
    symbol LowCardinality(String) CODEC(ZSTD),
    trader_id Int32 CODEC(ZSTD),
    price Float64 CODEC(Delta, ZSTD),
    quantity Int32 CODEC(ZSTD),
    side LowCardinality(String) CODEC(ZSTD),
    entry_order_id Nullable(String) CODEC(ZSTD),
    time DateTime CODEC(DoubleDelta, ZSTD),
    order_id String CODEC(ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(time)
ORDER BY (order_id, time)
TTL time + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;