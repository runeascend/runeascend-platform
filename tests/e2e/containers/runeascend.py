

from testcontainers.core.generic import DockerContainer
from testcontainers.core.image import DockerImage
from testcontainers.core.waiting_utils import wait_container_is_ready
from testcontainers.core.network import Network



def get_container(env_dict: dict, command: list, network: Network) -> DockerContainer:
    image = DockerImage(tag="runeascend:e2e", path=".") 
    container = DockerContainer(image=str(image))
    for key, value in env_dict.items():
        container = container.with_env(key, value)
    container = container.with_name("runeascend-e2e")
    container = container.with_command(command)
    container = container.with_network(network)
    container = container.start()
    wait_container_is_ready(container)
    return container
    
