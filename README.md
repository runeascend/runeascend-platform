Clickhouse table creation statements:

```
CREATE TABLE default.rs_buys
(
    `high` UInt64 COMMENT 'Buy price',
    `highTime` DateTime COMMENT 'Buy time',
    `name` String COMMENT 'Friendly Name',
    `id` UInt64 COMMENT 'Not friendly Name'
)
ENGINE = ReplacingMergeTree 
ORDER BY (id, highTime)
PRIMARY KEY (id, highTime)
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
ENGINE = ReplacingMergeTree 
ORDER BY (id, lowTime)
PRIMARY KEY (id, lowTime)
SETTINGS index_granularity = 8192
```