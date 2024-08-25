CREATE TABLE IF NOT EXISTS osrs_hf_opp (
    symbol LowCardinality(String),
    id LowCardinality(String),
    profit_per_item Float64 CODEC(Delta, ZSTD),
    limit UInt32 CODEC(Delta, ZSTD),
    m15_low Float64 CODEC(Delta, ZSTD),
    m15_high Float64 CODEC(Delta, ZSTD),
    m30_low Float64 CODEC(Delta, ZSTD),
    m30_high Float64 CODEC(Delta, ZSTD),
    h1_low Float64 CODEC(Delta, ZSTD),
    h1_high Float64 CODEC(Delta, ZSTD),
    last_sell Float64 CODEC(Delta, ZSTD),
    last_sell_time DateTime CODEC(DoubleDelta, ZSTD),
    last_buy Float64 CODEC(Delta, ZSTD),
    last_buy_time DateTime CODEC(DoubleDelta, ZSTD),
    time DateTime DEFAULT now() CODEC(DoubleDelta, ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(time)
ORDER BY (id, time)
TTL time + INTERVAL 7 DAY;