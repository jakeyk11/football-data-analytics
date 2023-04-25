# Import user-specified data from Sky league-tables using custom football data module 

#%% Imports

import os
import sys
import numpy as np

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.get_football_data as gfd

# %% User inputs

# Input league identifier and starting year of season
league = "EFLC"
start_year = '2021'

# Set up folder path
folder_path = f"../../data_directory/leaguetable_data/{start_year}_{str(int(start_year.replace('20','', 1)) + 1)}"

# %% Get data

league_table = gfd.get_league_table(league, start_year, folderpath=folder_path)





