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

## Using grafana for visualization

I have a public instance that I can share with anyone interested, but feel free to point a grafana clickhouse datasource at your instance and then use the `grafana-dashboard.json` file to import. The discord bot in its excerpt for linking graphs assumes that you have the same public IP that is running the discord bot and the grafana server

## Setting up kafka

To install kafka follow this [guide](https://geekflare.com/apache-kafka-setup-guide/)

I recommend using kowl to easily interact with your environment:
`docker run --network=host -p 8080:8080 -e KAFKA_BROKERS=localhost:9092 quay.io/cloudhut/kowl:master`

There are four topics currently available / in development:

```
osrs-fills: Successful execution {price, symbol_id, account_username, buy/sell, position_open_time, position_close_time}

osrs-hf-opp: Juicy spread available
  key: id (9143)
  value:
    {
      "symbol":"Adamant bolts"
      "id":"9143"
      "profit_per_item":0.8800000000000008
      "limit":11000
      "m15_low":10.733333333333333
      "m15_high":12.9
      "m30_low":11.793103448275861
      "m30_high":13
      "h1_low":11.464285714285714
      "h1_high":13.03448275862069
      "last_sell":11
      "last_sell_time":"2024-06-16T03:52:24"
      "last_buy":12
      "last_buy_time":"2024-06-16T03:50:10"
    }

osrs-mkt-data: Raw latest API calls every 15s
  key: id(29486)
  value:
  {
    "high":50000
    "highTime":1718508189
    "low":33000
    "lowTime":1718507726
    "name":"Cursed amulet of magic"
    "id":29486
   }

osrs-ref-data: auxilary info to support trading
  key: day in unix epoch secs
  value:
     limits
     mappings
     high_volume_symbols

osrs-sweeps: Large negative price moves
  key: id(1941)
  value: {
    "symbol":"Swamp paste"
    "id":"1941"
    "limit":13000
    "percent_sweep":14.285714285714285
    "last_sell":6
    "last_sell_time":"2024-06-16T17:38:17"
    "last_buy":12
    "last_buy_time":"2024-06-16T17:37:43"
    "second_to_last_sell":7
    "second_to_last_sell_time":"2024-06-16T17:36:24"
    "second_to_last_buy":12
    "second_to_last_buy_time":"2024-06-16T17:37:43"
  }
```

