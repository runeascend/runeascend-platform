from runespreader.main import Runespreader
import time
while True:
    r = Runespreader()
    print(r.get_latest_data_for_id(449))
    time.sleep(1)