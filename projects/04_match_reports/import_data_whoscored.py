# Import user-specified data from WhoScored using custom football data module 

#%% Imports

import os
import sys

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.get_football_data as gfd

# %% User inputs

# Input WhoScored match id
match_id = '1640709'

# Obtain and save data using custom function
events, players, mappings = gfd.get_whoscored_data(match_id, get_mappings=False, save_to_file=True, folderpath='../../data_directory/whoscored_data')