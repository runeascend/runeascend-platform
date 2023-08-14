Clickhouse table creation statements:

```
CREATE TABLE default.rs_buys
(
    `high` UInt64 COMMENT 'Buy price',
    `highTime` DateTime COMMENT 'Buy time',
    `name` String COMMENT 'Friendly Name',
    `id` UInt64 COMMENT 'Not friendly Name'
)
ENGINE = MergeTree
ORDER BY (highTime, id)
SETTINGS index_granularity = 8192 
```

```
CREATE TABLE default.rs_sells
(
    `low` UInt64 COMMENT 'Sell price',
    `lowTime` DateTime COMMENT 'Sell time',
    `name` String COMMENT 'Friendly Name',
    `id` UInt64 COMMENT 'Not friendly Name'
)
ENGINE = MergeTree
ORDER BY (lowTime, id)
SETTINGS index_granularity = 8192
```

```
CREATE TABLE default.rs_live_prices
(
    `high` UInt64 COMMENT 'Buy price',
    `highTime` DateTime COMMENT 'Buy time',
    `low` UInt64 COMMENT 'Sell price',
    `lowTime` DateTime COMMENT 'Sell time',
    `name` String COMMENT 'Friendly Name',
    `id` UInt64 COMMENT 'Not friendly Name'
)
ENGINE = MergeTree
ORDER BY (highTime, lowTime, id)
SETTINGS index_granularity = 8192
```