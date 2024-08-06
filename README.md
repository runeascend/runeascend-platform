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
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && python3 /home/<your_user_here>/runescape/runespreader/bot.py"
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target
```

Scraping script to populate clickhouse:
```
[Unit]
Description= OSRS GE Ripper
[Service]
User=<your_user_here>
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && python3 /home/<your_user_here>/runescape/runespreader/clickhouse.py"
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target
```

Spreadfinder - The simple opportunity finder bot
```
[Unit]
Description= OSRS GE Market Maker
[Service]
User=charles
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && python3 /home/<your_user_here>/runescape/runespreader/spreadfinder.py"
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
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && python3 /home/<your_user_here>/runescape/runespreader/publisher.py"
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
ExecStart= /bin/bash -c "source /home/<your_user_here>/.venvs/runespreader/bin/activate && python3 /home/<your_user_here>/runescape/runespreader/consumer.py worker -l info"
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target 
```


## Setting up clickhouse

Installing and configuring [clickhouse](https://clickhouse.com/docs/en/install#quick-install)

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
    _time DateTime DEFAULT now() CODEC(DoubleDelta, ZSTD)
) ENGINE = MergeTree()
PARTITION BY toDate(_time)
ORDER BY (id, _time)
TTL _time + INTERVAL 7 DAY;
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
    _time DateTime DEFAULT now() CODEC(DoubleDelta, ZSTD(1))
)
ENGINE = MergeTree
PARTITION BY toDate(_time)
ORDER BY (_time, id)
TTL _time + toIntervalDay(7)
SETTINGS index_granularity = 8192;
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

