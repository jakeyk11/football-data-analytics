## Script to download and save fbref data

# %% Imports

import ScraperFC as sfc
import traceback
import pandas as pd

# %% User inputs

# Select competition from following list 
'''['Copa Libertadores', 'Champions League', 'Europa League', 'Europa Conference League',
    'World Cup', 'Copa America', 'Euros', 'Big 5 combined', 'EPL', 'Ligue 1', 'Bundesliga',
    'Serie A', 'La Liga', 'MLS', 'Brazilian Serie A', 'Eredivisie', 'Liga MX', 'Primeira Liga',
    'EFL Championship', 'Women Champions League', 'Womens World Cup', 'Womens Euros', 'NWSL',
    'A-League Women', 'WSL', 'D1 Feminine', 'Womens Bundesliga', 'Womens Serie A', 'Liga F',
    'NWSL Challenge Cup', 'NWSL Fall Series'] '''

COMPETITION = 'EPL'

# Select calender year in which the competition finishes
COMPETITION_END_YEAR = 2023

# Select whether to store player data, team data or vs team data, using one of the following case-insensitive options
'''['player_only', 'team_only', 'vs_team_only', 'all'] '''

STORAGE_MODE = 'all'

# Point at directory to store data (relative to directory of this script)
DIRECTORY = f"../../data_directory/fbref_data/{str(COMPETITION_END_YEAR-1)}_{str(COMPETITION_END_YEAR).replace('20','',1)}/{COMPETITION}/"

# %% Scrape data

# Initialise scraper
scraper = sfc.FBRef()

# Get data
try:
    fbref_dict = scraper.scrape_all_stats(year=COMPETITION_END_YEAR, league=COMPETITION)
except:
    traceback.print_exc()
finally:
    scraper.close()

# %% Format scraped data

playerinfo_df = pd.DataFrame()
teaminfo_for_df = pd.DataFrame()
teaminfo_against_df = pd.DataFrame()

# Iterate over statistic type
for statistic_group in list(fbref_dict.keys()):
    
    # Team stats for
    temp_team_stat_for_df = fbref_dict[statistic_group][0].copy()
    new_col_names = []
    for col_name in temp_team_stat_for_df.columns:
        col_name_1 = '' if 'Unnamed' in col_name[0] else col_name[0]
        col_name_2 = col_name[1] if 'Unnamed' in col_name[0] else ' ' + col_name[1]
        new_col_names.append(col_name_1 + col_name_2)
    temp_team_stat_for_df.columns = new_col_names
    teaminfo_for_df = pd.concat([teaminfo_for_df, temp_team_stat_for_df], axis=1)
    teaminfo_for_df = teaminfo_for_df.loc[:,~teaminfo_for_df.columns.duplicated()]
    
    # Team stats against
    temp_team_stat_against_df = fbref_dict[statistic_group][1].copy()
    new_col_names = []
    for col_name in temp_team_stat_against_df.columns:
        col_name_1 = '' if 'Unnamed' in col_name[0] else col_name[0]
        col_name_2 = col_name[1] if 'Unnamed' in col_name[0] else ' ' + col_name[1]
        new_col_names.append(col_name_1 + col_name_2)
    temp_team_stat_against_df.columns = new_col_names
    teaminfo_against_df = pd.concat([teaminfo_against_df, temp_team_stat_against_df], axis=1)
    teaminfo_against_df = teaminfo_against_df.loc[:,~teaminfo_against_df.columns.duplicated()]

    # Player stats
    temp_player_stat_df = fbref_dict[statistic_group][2].copy()
    new_col_names = []
    for col_name in temp_player_stat_df.columns:
        col_name_1 = '' if 'Unnamed' in col_name[0] else col_name[0]
        col_name_2 = col_name[1] if 'Unnamed' in col_name[0] else ' ' + col_name[1]
        new_col_names.append(col_name_1 + col_name_2)
    temp_player_stat_df.columns = new_col_names
    playerinfo_df = pd.concat([playerinfo_df, temp_player_stat_df], axis=1)
    playerinfo_df = playerinfo_df.loc[:,~playerinfo_df.columns.duplicated()]

# %% Save scraped data

file_extension_name = COMPETITION.lower() + ' ' + str(COMPETITION_END_YEAR)

if STORAGE_MODE.lower().replace('_',' ') == 'player only':
    playerinfo_df.to_json(DIRECTORY + file_extension_name + ' player data.json')

elif STORAGE_MODE.lower().replace('_',' ') == 'team only':
    teaminfo_for_df.to_json(DIRECTORY + file_extension_name + ' team data.json')
    
elif STORAGE_MODE.lower().replace('_',' ') == 'vs team only':
    teaminfo_against_df.to_json(DIRECTORY + file_extension_name + ' vs team data.json')
    
else:
    playerinfo_df.to_json(DIRECTORY + file_extension_name + ' player data.json')
    teaminfo_for_df.to_json(DIRECTORY + file_extension_name + ' team data.json')
    teaminfo_against_df.to_json(DIRECTORY + file_extension_name + ' vs team data.json')