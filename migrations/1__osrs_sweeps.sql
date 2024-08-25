CREATE TABLE IF NOT EXISTS osrs_sweeps (
    symbol LowCardinality(String),
    id LowCardinality(String),
    limit UInt32 CODEC(Delta(4), ZSTD(1)),
    percent_sweep Float32 CODEC(Delta(4), ZSTD(1)),
    last_sell Float64 CODEC(Delta(8), ZSTD(1)),
    last_sell_time DateTime CODEC(DoubleDelta, ZSTD(1)),
    last_buy Float64 CODEC(Delta(8), ZSTD(1)),
    last_buy_time DateTime CODEC(DoubleDelta, ZSTD(1)),
    second_to_last_sell Float64 CODEC(Delta(8), ZSTD(1)),
    second_to_last_sell_time DateTime CODEC(DoubleDelta, ZSTD(1)),
    second_to_last_buy Float64 CODEC(Delta(8), ZSTD(1)),
    second_to_last_buy_time DateTime CODEC(DoubleDelta, ZSTD(1)),
    time DateTime DEFAULT now() CODEC(DoubleDelta, ZSTD(1))
)
ENGINE = MergeTree
PARTITION BY toDate(time)
ORDER BY (time, id)
TTL time + toIntervalDay(7)
SETTINGS index_granularity = 8192;