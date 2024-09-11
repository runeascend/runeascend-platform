import os
import time
import json
import pytest
from testcontainers.clickhouse import ClickHouseContainer
from tests.e2e.containers.redpanda import CustomRedpandaContainer
from pathlib import Path
from tests.e2e.containers.runeascend import get_container
from runeascend.common.config import get_config
from runeascend.runespreader.publisher import hf_opp_publisher
from clickhouse_migrations.clickhouse_cluster import ClickhouseCluster
from testcontainers.core.network import Network
import clickhouse_driver
config = get_config()


def test_hf_opp():
    # Publish a message to the topic
    network = Network()
    network = network.create()
    with ClickHouseContainer().with_name("clickhouse-e2e").with_network(network) as clickhouse, CustomRedpandaContainer().with_name("redpanda-e2e").with_network(network) as redpanda:

        # Clickhouse setup
        clickhouse_client = clickhouse_driver.Client.from_url(clickhouse.get_connection_url())
        clickhouse_cluster = ClickhouseCluster(db_url=clickhouse.get_connection_url())
        clickhouse_cluster.migrate(migration_path=Path("migrations"), db_name=None)
        ch_host = clickhouse.get_container_host_ip()
        ch_port = clickhouse.get_exposed_port(9000)
        # Redpanada setup
        rp_broker_external = f"127.0.0.1:{redpanda.get_exposed_port(9094)}"
        # Setip env Vars
        os.environ["KAFKA_BROKER"] = rp_broker_external
        os.environ["CLICKHOUSE_HOST"] = ch_host
        os.environ["CLICKHOUSE_PORT"] = str(ch_port)
        
        # Start runevault consumer
        container = get_container(
            env_dict={"KAFKA_BROKER": f"redpanda-e2e:9094", "CLICKHOUSE_HOST": "clickhouse-e2e", "CLICKHOUSE_PORT": "9000"},
            #command=["tail", "-f", "/dev/null"],
            command=["poetry", "run", "consumer", "worker", "--without-web", "-l", "info"],
            network=network,
        )
        publisher = hf_opp_publisher(config=config)
        publisher.publish(
            key=1993,
            message={
                "time": "2024-08-10T18:33:57.478344",
                "symbol": "Jug of wine",
                "id": "1993",
                "profit_per_item": 1.9500000000000002,
                "limit": 6000,
                "m15_low": 3,
                "m15_high": 4,
                "m30_low": 3.090909090909091,
                "m30_high": 3.923076923076923,
                "h1_low": 3.161290322580645,
                "h1_high": 3.75,
                "last_sell": 3,
                "last_sell_time": "2024-08-10T18:31:27",
                "last_buy": 5,
                "last_buy_time": "2024-08-10T18:33:00",
            },
        )
    

        # Check the consumer has processed the message
        result = clickhouse_client.execute("SELECT * FROM osrs_hf_opp")
        assert len(result) == 1
        assert result[0]["time"] == "2024-08-10T18:33:57.478344"
        assert result[0]["symbol"] == "Jug of wine"
        assert result[0]["id"] == "1993"
        assert result[0]["profit_per_item"] == 1.9500000000000002
        assert result[0]["limit"] == 6000
        assert result[0]["m15_low"] == 3
        assert result[0]["m15_high"] == 4
        assert result[0]["m30_low"] == 3.090909090909091
        assert result[0]["m30_high"] == 3.923076923076923
        assert result[0]["h1_low"] == 3.161290322580645
        assert result[0]["h1_high"] == 3.75
        assert result[0]["last_sell"] == 3
        assert result[0]["last_sell_time"] == "2024-08-10T18:31:27"
        assert result[0]["last_buy"] == 5
        assert result[0]["last_buy_time"] == "2024-08-10T18:33:00"
        container.stop()

        
