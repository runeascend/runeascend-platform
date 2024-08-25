import os

from clickhouse_driver import Client

from runeascend.common.config import get_config


def get_clickhouse_client():
    config = get_config()
    if host := os.getenv("CLICKHOUSE_HOST"):
        if password := os.getenv("CLICKHOUSE_PASSWORD"):
            if port := os.getenv("CLICKHOUSE_PORT"):
                return Client(host=host, password=password, port=port)
            return Client(host=host, password=password)
        if port := os.getenv("CLICKHOUSE_PORT"):
            return Client(host=host, port=port)
        return Client(host=host)
    else:
        if password := config.get("CH_PASSWORD"):
            return Client(host="localhost", password=password)
        return Client(host="localhost", password=config.get("CH_PASSWORD"))
