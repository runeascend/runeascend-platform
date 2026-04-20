from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from textwrap import dedent
from io import BytesIO
import tarfile
import time

class CustomRedpandaContainer(DockerContainer): 
    TC_START_SCRIPT = "/tc-start.sh"
    def __init__(
        self,
        image: str = "docker.redpanda.com/redpandadata/redpanda:v24.2.1",
        name = "redpanda-e2e",
        **kwargs,
    ) -> None:
        kwargs["entrypoint"] = "sh"
        super().__init__(image, **kwargs)
        self.name = name
        self.redpanda_port_internal = 9094
        self.redpanda_port = 9092
        self.with_exposed_ports(self.redpanda_port, self.redpanda_port_internal)

    def get_bootstrap_server_internal(self) -> str:
        port = self.redpanda_port_internal 
        return f"{self.name}:{port}"
    
    def get_bootstrap_server_external(self) -> str:
        port = self.get_exposed_port(self.redpanda_port)
        host = self.get_container_host_ip()
        return f"{host}:{port}"

    def tc_start(self) -> None:
        port = self.get_exposed_port(self.redpanda_port)
        host = self.get_container_host_ip()
        name = self.name
        data = (
            dedent(
                f"""
                #!/bin/bash
                /usr/bin/rpk redpanda start --smp 1 --memory 1G \
                --kafka-addr PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092,INSIDE://0.0.0.0:9094  \
                --advertise-kafka-addr PLAINTEXT://127.0.0.1:29092,OUTSIDE://{host}:{port},INSIDE://{name}:9094
                """
            )
            .strip()
            .encode("utf-8")
        )

        self.create_file(data, CustomRedpandaContainer.TC_START_SCRIPT)

    def start(self, timeout=10) -> "CustomRedpandaContainer":
        script = CustomRedpandaContainer.TC_START_SCRIPT
        command = f'-c "while [ ! -f {script} ]; do sleep 0.1; done; sh {script}"'
        self.with_command(command)
        super().start()
        self.tc_start()
        wait_for_logs(self, r".*Started Kafka API server.*", timeout=timeout)
        return self

    def create_file(self, content: bytes, path: str) -> None:
        with BytesIO() as archive, tarfile.TarFile(fileobj=archive, mode="w") as tar:
            tarinfo = tarfile.TarInfo(name=path)
            tarinfo.size = len(content)
            tarinfo.mtime = time.time()
            tar.addfile(tarinfo, BytesIO(content))
            archive.seek(0)
            self.get_wrapped_container().put_archive("/", archive)