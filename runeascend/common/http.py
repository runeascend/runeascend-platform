import requests
from urllib3.util import Retry


def get_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1)
    session.mount(
        "https://", requests.adapters.HTTPAdapter(max_retries=retries)
    )
    return session
