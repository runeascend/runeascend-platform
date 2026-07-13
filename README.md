# Runespreader

A python runescape trading application

## Installing

### From PyPI

```
pip install runeascend-platform
```

### From Project

This project uses [uv](https://docs.astral.sh/uv/) for dependency
management and packaging.

```
# one-time: install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# create + populate the project venv at ./.venv
make create-dev
# or, directly:
uv sync --all-groups

# activate it
source .venv/bin/activate
```

Common tasks (`makefile`):

- `make format` / `make format-check` — black + isort via `uv run`
- `make dep-check` — deptry via `uv run`
- `make test` — pytest with coverage via `uv run`
- `make update-dev` — refresh the lockfile to the latest resolvable versions
- `make lock` — regenerate `uv.lock` after editing dependencies

## Running the applets

I recommend setting up systemd services (ideally [user services](https://wiki.archlinux.org/title/Systemd/User) - *make sure to enable linger!*) for all of the applications. Their services can be found in the service_templates directory

## Setting up clickhouse

Installing and configuring [clickhouse](https://clickhouse.com/docs/en/install#quick-install)

Migrations can be found in migrations/ and are managed by [clickhouse-migrations](https://github.com/zifter/clickhouse-migrations)

### Tables

#### OSRS API Data

- rs_buys
- rs_sells

#### Runespreaders Published Messages

 - osrs_hf_opp
 - osrs_mf_opp
 - osrs_mkt_data
 - osrs_sweeps

 #### Runevault/Runesavant Order Tracking
 
 - osrs_savant_cancel_events
 - osrs_savant_fill_events
 - osrs_savant_order_events
 - osrs_savant_orders


## Using grafana for visualization

I have a public instance that I can share with anyone interested, but feel free to point a grafana clickhouse datasource at your instance and then use the `grafana-dashboard.json` file to import. The discord bot in its excerpt for linking graphs assumes that you have the same public IP that is running the discord bot and the grafana server

## Setting up Redpanda

To install redpanda follow this [guide](https://docs.redpanda.com/current/deploy/deployment-option/self-hosted/manual/production/production-deployment/)

I recommend using redpanda console to interact with you environment, the instruction are included above

message schemas are updated in `schemas/` (except for osrs-ref-data)

### Keeping `advertised_kafka_api` in sync with the WAN IP

Redpanda's `advertised_kafka_api` in `/etc/redpanda/redpanda.yaml` must point at
the current public/WAN IP (this is what the discord bot's graph-linking assumes,
and what remote clients bootstrap to). On a residential/DHCP connection that IP
can change without warning; when it does, all producers and consumers silently
break because the broker keeps handing out a stale endpoint.

`service_templates/redpanda-update-advertised-ip.sh` plus its accompanying
`.service` / `.timer` units automate this. The timer fires 1 minute after boot
and then every 5 minutes; the script:

1. Resolves the current WAN IPv4 via a fallback chain of
   `api.ipify.org` → `ifconfig.me` → `icanhazip.com`.
2. Compares it to `advertised_kafka_api[0].address` in `redpanda.yaml`.
3. If different: backs up the config (`redpanda.yaml.bak.<timestamp>`),
   rewrites `advertised_kafka_api` and `advertised_rpc_api` via a YAML
   round-trip, validates the result, restarts `redpanda.service`, and rolls
   back on any restart failure.
4. If the IP is unchanged, it's a no-op.

Install:

```bash
sudo install -o root -g root -m 755 \
  service_templates/redpanda-update-advertised-ip.sh \
  /usr/local/sbin/redpanda-update-advertised-ip.sh

sudo install -o root -g root -m 644 \
  service_templates/redpanda-update-advertised-ip.service \
  /etc/systemd/system/redpanda-update-advertised-ip.service

sudo install -o root -g root -m 644 \
  service_templates/redpanda-update-advertised-ip.timer \
  /etc/systemd/system/redpanda-update-advertised-ip.timer

sudo systemctl daemon-reload
sudo systemctl enable --now redpanda-update-advertised-ip.timer
```

Verify with:

```bash
systemctl list-timers redpanda-update-advertised-ip.timer
journalctl -t redpanda-ip -n 20
```

```
osrs-fills: Successful execution {price, symbol_id, account_username, buy/sell, position_open_time, position_close_time}

```

