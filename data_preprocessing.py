import json
import os
import time
from pathlib import Path

import pandas as pd

from cycling_session import OpenLappSession

import config

start_time = time.time()
mmps = [
    {'mmp': '5m', 'n': 2, },
    {'mmp': '6m', 'n': 2, },
    {'mmp': '10m', 'n': 2, },
    {'mmp': '12m', 'n': 2, },
    {'mmp': '15m', 'n': 2, },
    {'mmp': '20m', 'n': 2, },
    {'mmp': '30m', 'n': 2, },
    {'mmp': '40m', 'n': 1, },
    {'mmp': '45m', 'n': 1, },
]
cycling_data = []
for rider in os.listdir(config.data_dir):
    rider_path = config.data_dir / Path(rider)
    if os.path.isdir(rider_path):
        with open(config.dir_meta / '{}.json'.format(rider), 'r') as f:
            meta_data = json.load(f)
        for session_file in os.listdir(rider_path):
            if session_file.endswith(config.raw_data_format_ext):
                filename = rider_path / session_file
                print('Processing {}'.format(filename))
                try:
                    session = OpenLappSession(str(filename), meta_data, '20m')
                    session.add_features()
                    session.add_mmps(mmps, extra=session.lappparser.grades, extra_label='grades_mmp')
                    cycling_data.append(session.session_data)
                except:
                    pass

pd.DataFrame(cycling_data).to_csv(config.csv_file_name, index=False)

print("--- %s seconds ---" % (time.time() - start_time))
