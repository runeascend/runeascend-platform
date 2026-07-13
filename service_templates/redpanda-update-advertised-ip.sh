#!/usr/bin/env bash
# Detect the current WAN IP and, if it differs from the address advertised by
# Redpanda's Kafka/RPC listeners, rewrite /etc/redpanda/redpanda.yaml and
# restart the broker.
#
# Intended to run periodically (see redpanda-update-advertised-ip.timer).
# Must run as root (writes /etc/redpanda and restarts redpanda.service).
set -euo pipefail

CONFIG="${REDPANDA_CONFIG:-/etc/redpanda/redpanda.yaml}"
SERVICE="${REDPANDA_SERVICE:-redpanda.service}"
LOG_TAG="redpanda-ip"

IP_SERVICES=(
  "https://api.ipify.org"
  "https://ifconfig.me/ip"
  "https://icanhazip.com"
  "https://ipv4.icanhazip.com"
)

log() { logger -t "$LOG_TAG" -- "$*"; echo "$*"; }

get_public_ip() {
  local url ip
  for url in "${IP_SERVICES[@]}"; do
    if ip=$(curl -4 -fsS --max-time 5 "$url" 2>/dev/null | tr -d '[:space:]'); then
      if [[ "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        echo "$ip"
        return 0
      fi
    fi
  done
  return 1
}

if ! new_ip=$(get_public_ip); then
  log "ERROR: unable to determine WAN IP from any provider"
  exit 1
fi

current_ip=$(python3 - "$CONFIG" <<'PYEOF'
import sys, yaml
with open(sys.argv[1]) as f:
    doc = yaml.safe_load(f)
entries = doc.get("redpanda", {}).get("advertised_kafka_api", [])
print(entries[0]["address"] if entries else "")
PYEOF
)

if [[ "$new_ip" == "$current_ip" ]]; then
  log "advertised IP unchanged ($current_ip); nothing to do"
  exit 0
fi

log "advertised IP change detected: ${current_ip:-<none>} -> ${new_ip}"

backup="${CONFIG}.bak.$(date +%Y%m%d%H%M%S)"
cp -p "$CONFIG" "$backup"
log "backed up config to $backup"

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

python3 - "$CONFIG" "$new_ip" > "$tmp" <<'PYEOF'
import sys, yaml
path, new_ip = sys.argv[1], sys.argv[2]
with open(path) as f:
    doc = yaml.safe_load(f)
rp = doc.setdefault("redpanda", {})
for entry in rp.get("advertised_kafka_api", []) or []:
    entry["address"] = new_ip
rpc = rp.get("advertised_rpc_api")
if isinstance(rpc, dict):
    rpc["address"] = new_ip
yaml.safe_dump(doc, sys.stdout, default_flow_style=False, sort_keys=False)
PYEOF

# sanity: file is non-empty and still valid YAML with expected key
if ! python3 -c "import yaml,sys; d=yaml.safe_load(open('$tmp')); assert d['redpanda']['advertised_kafka_api'][0]['address']=='$new_ip'"; then
  log "ERROR: rewritten config failed validation; leaving original in place"
  exit 1
fi

install -o root -g root -m 644 "$tmp" "$CONFIG"
log "wrote new config with advertised IP $new_ip; restarting $SERVICE"

if systemctl restart "$SERVICE"; then
  log "$SERVICE restarted successfully"
else
  rc=$?
  log "ERROR: failed to restart $SERVICE (exit $rc); rolling back config"
  install -o root -g root -m 644 "$backup" "$CONFIG"
  systemctl restart "$SERVICE" || log "ERROR: rollback restart also failed"
  exit $rc
fi
