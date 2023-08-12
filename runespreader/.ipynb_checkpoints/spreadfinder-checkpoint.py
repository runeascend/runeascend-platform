from runespreader.main import Runespreader
import pandas as pd
from clickhouse_driver import Client
import os
import time
import yaml
import pandas as pd
config = yaml.load(open('/home/charles/.config/runespreader'), Loader=yaml.Loader)

while True:
    r = Runespreader()
    client = Client(host='localhost', password=config.get("CH_PASSWORD"))
    data = r.get_latest_data_for_all_symbols