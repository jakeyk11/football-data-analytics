# Scrape user-specified data from transfermarkt.com using custom football data module 

# %% Imports

import os
import sys

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.get_football_data as gfd

# %% User Inputs

# Input league country (England = GB, Spain = ES, Germany = L, Italy = IT, France = FR, Scotland = SC)
country_code = 'GB'

# Input league number (for example Premier League = 1, Championship = 2, League One = 3, etc.)
division_num = '1'

# Input year that season started
start_year = '2021'

# Choose whether to obtains stats from all competitions (False = League comp. only, True = All comps.)
all_comps = False

# Obtain and save data using custom function
player_info = gfd.get_transfermarkt_data(country_code, division_num, start_year, all_comps, save_to_file=True, folderpath=f"../../data_directory/transfermarkt_data/{start_year}_{str(int(start_year.replace('20','')) + 1)}")