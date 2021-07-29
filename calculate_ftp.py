import json
import os

from pathlib import Path
import numpy as np
from yatcxparser import TcxParser

dir = Path(os.getcwd())/Path('data/Sport5/')
dir_meta = Path(os.getcwd())/Path('data/metadata')
raw_data_format_ext = '.tcx'
ftp_interval = 20*60
n_threads = 10


def process_cyclist_ftp(path):
    all_sessions = os.listdir(path)
    n_total = len(all_sessions)
    n = 0
    ftp_values = {}
    for session in all_sessions:
        print('Processing file {} out of {}'.format(n,n_total), end='\r')
        if session.endswith(raw_data_format_ext):
            lappparser = TcxParser(str(path/session))
        if lappparser.has_powers:
            year = lappparser.date.year
            ftp = max(lappparser.mean_power_interval(ftp_interval))
            if ftp == np.nan:
                ftp = lappparser.mean_power
            if ((year not in ftp_values) or (year in ftp_values and ftp_values[year] < ftp)) and not np.isnan(ftp):
                ftp_values[year] = round(ftp)

        n += 1
    return ftp_values


for rider in os.listdir(dir):
    rider_path = dir/Path(rider)
    if os.path.isdir(rider_path):
        rider_data = {'name':rider}
        results = process_cyclist_ftp(rider_path)
        rider_data['ftps'] = results
        with open(dir_meta/'{}.json'.format(rider), 'w') as f:
            json.dump(rider_data, f)