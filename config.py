import os
from pathlib import Path

session_settings = {
    'tempo_coef': 0.9,
    'burst_length_min': 5,
    'burst_pause': 1,
    'mmp_delay': '2m'
}
grade_min = 0


data_dir = Path(os.getcwd())/Path('data/Sport5/')
dir_meta = Path(os.getcwd())/Path('data/metadata')
raw_data_format_ext = '.tcx'
csv_file_name = data_dir/'cycling_data.csv'