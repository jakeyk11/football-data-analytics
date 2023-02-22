# %% Create visualisation of player defensive contribution across a selection of games
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Whoscored match ids
#           Positions not to include
#           Date of run
#           Normalisation mode
#           Minimum play time
#
# Outputs:  Scatter plot of defensive contributions

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.transforms import Affine2D
from matplotlib.ticker import MultipleLocator
import mpl_toolkits.axisartist.floating_axes as floating_axes
from mpl_toolkits.axisartist.grid_finder import (FixedLocator, MaxNLocator, DictFormatter)
import matplotlib.patheffects as path_effects
from PIL import Image, ImageEnhance
import adjustText
import os
import sys
import bz2
import pickle
import numpy as np
from collections import Counter
import highlight_text as htext
import glob

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.pitch_zones as pz
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% User inputs

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Input run-date
run_date = '15/2/2023'

# Brighten logo
logo_brighten = False

# %% League logo

comp_logo = lab.get_competition_logo(league, year=year, logo_brighten=logo_brighten)     

# %% Get data

file_path = f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}"
files = os.listdir(file_path)

# Initialise storage dataframes
events_df = pd.DataFrame()
players_df = pd.DataFrame()

# Load data
for file in files:
    if file == 'event-types.pbz2':
        event_types = bz2.BZ2File(f"{file_path}/{file}", 'rb')
        event_types = pickle.load(event_types)
    elif file == 'formation-mapping.pbz2':
        formation_mapping = bz2.BZ2File(f"{file_path}/{file}", 'rb')
        formation_mapping = pickle.load(formation_mapping)
    elif '-eventdata-' in file:
        match_events = bz2.BZ2File(f"{file_path}/{file}", 'rb')
        match_events = pickle.load(match_events)
        events_df = pd.concat([events_df, match_events])
    elif '-playerdata-' in file:
        match_players = bz2.BZ2File(f"{file_path}/{file}", 'rb')
        match_players = pickle.load(match_players)
        players_df = pd.concat([players_df, match_players])
    else:
        pass

# %% Format data

all_matches = set(events_df['match_id'])

# Add cumulative minutes information
players_df = wde.minutes_played(players_df, events_df)

players_df['opposition'] = np.nan
idx = 0
for _,player in players_df.iterrows():
    teams = list(set(players_df[players_df['match_id']==player['match_id']]['team']))
    players_df.iloc[idx, len(players_df.axes[1])-1] = teams[0] if player['team'] == teams[1] else teams[1]
    idx +=1

# Isolate passes
passes_df = events_df[events_df['eventType']=='Pass']

# %% Get CB pass accuracy for each match

all_df_stats = pd.DataFrame()

for match in all_matches:
    
    match_passes = passes_df[passes_df['match_id']==match]
    match_suc_passes = match_passes[match_passes['outcomeType']=='Successful']

    match_players = players_df[players_df['match_id']==match]
    
    player_stats = wde.create_player_list(match_players, pass_extra=['opposition'])
    player_stats = wde.group_player_events(match_passes, player_stats, primary_event_name='passes')
    player_stats = wde.group_player_events(match_suc_passes, player_stats, primary_event_name='suc_passes')
        
    all_df_stats = pd.concat([all_df_stats, player_stats], axis=0)

all_df_stats['pass_acc'] = round(100*(all_df_stats['suc_passes']/all_df_stats['passes']),1)

# %%

opp_df_acc = all_df_stats.groupby(['opposition', 'position']).sum()
opp_df_acc['pass_acc'] = round(100*(opp_df_acc['suc_passes']/opp_df_acc['passes']),1)
