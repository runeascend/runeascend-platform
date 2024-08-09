# Runespreader

A python runescape market making library / app

## Installing

### From PyPI

```
pip install runespreader
```

### From Project

```
make create-dev
```

## Running the applets

I recommend setting up systemd services (ideally [user services](https://wiki.archlinux.org/title/Systemd/User) - *make sure to enable linger!*) for all of the apps like such:

OSRS Discord Bot:
```
[Unit]
Description= OSRS Bot
[Service]
User=<your_user_here>
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && discord_bot"
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target
```

Scraping script to populate clickhouse:
```
[Unit]
Description= OSRS GE Archiver
[Service]
User=<your_user_here>
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && archiver"
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target
```

TradeSeeker - The simple opportunity finder bot
```
[Unit]
Description= OSRS GE Market Maker
[Service]
User=charles
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && trade_seeker"
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target
```
Kafka Publisher - Distribute aggregated data to downstream consumers
```
[Unit]
Description= OSRS Publisher
[Service]
User=<your_user_here>
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && publisher"
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target 
```
Runewriter - Kafka Consumer that writes to clickhouse
```
[Unit]
Description= OSRS Kafka Consumer
[Service]
User=<your_user_here>
WorkingDirectory=/home/<your_user_here>/tmp # There is a directory emitted from faust while running so you need to specify a location
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && consumer worker -l info"
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target 
```


## Setting up clickhouse

Installing and configuring [clickhouse](https://clickhouse.com/docs/en/install#quick-install)

### Clickhouse table creation statements:

#### Raw Runescape Data

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

#### Runespreader Publisher Messages

```
CREATE TABLE osrs_hf_opp (
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
```
```
CREATE TABLE default.osrs_sweeps (
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
```
```
CREATE TABLE osrs_mkt_data (
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
```
```
CREATE TABLE osrs_mf_opp (
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
```

#### Runesavant Order Tracking

```
CREATE TABLE osrs_savant_order_events (
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
```

```
CREATE TABLE osrs_savant_fill_events (
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
```
```
CREATE TABLE osrs_savant_cancel_events (
    order_id String CODEC(ZSTD),
    time DateTime CODEC(DoubleDelta, ZSTD),
    reason String CODEC(ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(time)
ORDER BY (order_id, time)
TTL time + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;
```

```
CREATE TABLE osrs_savant_orders (
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
```

## Using grafana for visualization

I have a public instance that I can share with anyone interested, but feel free to point a grafana clickhouse datasource at your instance and then use the `grafana-dashboard.json` file to import. The discord bot in its excerpt for linking graphs assumes that you have the same public IP that is running the discord bot and the grafana server

## Setting up Redpanda

To install redpanda follow this [guide](https://docs.redpanda.com/current/deploy/deployment-option/self-hosted/manual/production/production-deployment/)

I recommend using redpanda console to interact with you environment, the instruction are included above

message schemas are updated in `schemas/` (except for osrs-ref-data)

```
osrs-fills: Successful execution {price, symbol_id, account_username, buy/sell, position_open_time, position_close_time}

```

