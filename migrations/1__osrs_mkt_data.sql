CREATE TABLE IF NOT EXISTS osrs_mkt_data (
    high Int32 CODEC(ZSTD),
    low Int32 CODEC(ZSTD),
    name LowCardinality(String) CODEC(ZSTD),
    time DateTime CODEC(DoubleDelta, ZSTD),
    id Int32 CODEC(ZSTD),
    avg_high_price Int32 CODEC(ZSTD),
    avg_low_price Int32 CODEC(ZSTD),
    high_price_volume Int32 CODEC(ZSTD),
    low_price_volume Int32 CODEC(ZSTD),
    high_time DateTime CODEC(DoubleDelta, ZSTD),
    low_time DateTime CODEC(DoubleDelta, ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(time)
ORDER BY (id, time)