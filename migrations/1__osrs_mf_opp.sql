
CREATE TABLE IF NOT EXISTS osrs_mf_opp (
    time DateTime CODEC(DoubleDelta, ZSTD),
    name LowCardinality(String) CODEC(ZSTD),
    id Int32 CODEC(ZSTD),
    low_time DateTime CODEC(DoubleDelta, ZSTD),
    low Int32 CODEC(ZSTD),
    high_time DateTime CODEC(DoubleDelta, ZSTD),
    high Int32 CODEC(ZSTD),
    mid_price Float64 CODEC(Delta, ZSTD),
    macd_signal_crossover UInt8 CODEC(ZSTD),
    macd_trigger Float64 CODEC(Delta, ZSTD),
    macd_signal Float64 CODEC(Delta, ZSTD),
    k_ewm Float64 CODEC(Delta, ZSTD),
    d_ewm Float64 CODEC(Delta, ZSTD),
    k_interval Int32 CODEC(ZSTD),
    d_interval Int32 CODEC(ZSTD),
    signal_interval Int32 CODEC(ZSTD),
    time_window Int32 CODEC(ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(time)
ORDER BY (id, time)