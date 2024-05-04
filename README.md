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