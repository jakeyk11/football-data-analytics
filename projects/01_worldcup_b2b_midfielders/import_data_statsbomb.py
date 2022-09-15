# Import user-specified data from Statsbomb using custom football data module 

#%% Imports

import os
import sys

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.get_football_data as gfd

#%% User inputs

# Input competition name (Statsbomb convention)
competition = 'FIFA World Cup'

# Input competition startyear
year = '2018'

# Obtain and save data using custom function
events, lineups = gfd.get_statsbomb_data(competition, year, save_to_file=True, folderpath=f"../../data_directory/statsbomb_data/{int(year)-1}_{str(int(year.replace('20','')))}/{competition}")

