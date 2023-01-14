# Import user-specified data from WhoScored using custom football data module 

#%% Imports

import os
import sys
import numpy as np

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.get_football_data as gfd

# %% User inputs

# Input first and last match id to obtain data from
match_id_start = 1650638
match_id_end = 1650718

# Input year folder
year = '2022'

# Input league folder
league = 'La_Liga'

# %% Set-up file path and match ids
match_ids = np.arange(match_id_start, match_id_end+1)
folderpath = f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','',1)) + 1)}/{league}"

# %% Get data
for match_id in match_ids:
    match_id = str(match_id)
    
    # Obtain and save data using custom function
    events, players, mappings = gfd.get_whoscored_data(match_id, get_mappings=True, save_to_file=True, folderpath=folderpath)