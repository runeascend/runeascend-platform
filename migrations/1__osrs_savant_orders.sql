CREATE TABLE IF NOT EXISTS osrs_savant_orders (
    symbol LowCardinality(String) CODEC(ZSTD),
    req_price Float64 CODEC(Delta, ZSTD),
    req_quantity Int32 CODEC(ZSTD),
    trader_id Int32 CODEC(ZSTD),
    side LowCardinality(String) CODEC(ZSTD),
    entry_order_id Nullable(String) CODEC(ZSTD),
    open_time DateTime CODEC(DoubleDelta, ZSTD),
    order_id String CODEC(ZSTD),
    fill_price Float64 CODEC(Delta, ZSTD),
    fill_quantity Int32 CODEC(ZSTD),
    order_status LowCardinality(String) CODEC(ZSTD),
    close_time Nullable(DateTime) CODEC(DoubleDelta, ZSTD),
    cancel_reason Nullable(String) CODEC(ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(open_time)
ORDER BY (order_id, open_time)