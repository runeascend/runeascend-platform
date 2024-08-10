import os

import yaml


def get_config():
    return yaml.load(
        open(f"{os.path.expanduser('~')}/.config/runespreader"),
        Loader=yaml.Loader,
    )
