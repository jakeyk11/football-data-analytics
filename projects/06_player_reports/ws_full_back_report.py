# %% Create full back analysis report
#
# Inputs:   Player name, league and year to analyse
#           List of player names, leagues and years to compare to
#           League(s) to rank players within
#
# Outputs:  Player report

# To add

# Tackles per 100 opp passes --
# Interceptions per 100 opp passes -- 
# Dribble past %
# Aerials  -- 
# Passes and carries into box 
# Progressive passes and carries
# xT allowed into territory
# Successful dribbles
# Deep progressions
# Opposition half progressions
# Turnovers / Recoveries
# Touches in opposition third -- 

# %% Imports and parameters

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import matplotlib.patheffects as path_effects
from mplsoccer.pitch import VerticalPitch
import seaborn as sns
import mplsoccer.pitch
import os
import sys
import bz2
import pickle

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.pitch_zones as pz
import analysis_tools.logos_and_badges as lab

# %% Inputs

# Player, league and year to analyse
player_name = 'Gideon Mensah'
league = "Ligue_1"
year = '2022'

# Players, leagues and years to compare
comparison_players = [('Abdul Rahman Baba', 'EFLC', '2022'),
                      ('Quentin Bernard', 'Ligue_1', '2022')]

# %%
# Full league and criteria to compare against
comparison_league = ('League One', '2021')
comparison_pos = 'Winger'
comparison_min_mins = 900

# Abbreviated league name for printing
comparison_league_abbrev = 'L1'

# %% Load analysis and comparison data

# Create list of data to load
data_to_load = [(player_name,league, year)] + comparison_players

# Set-up storage dataframe
all_data = pd.DataFrame()

#%% Get data from whoscored

for idx, data in enumerate(data_to_load):
    
    # Determine file path
    file_path = f"../../data_directory/whoscored_data/{data[2]}_{str(int(data[2].replace('20','')) + 1)}/{data[1]}"
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
        
    # Synthesise additional information
    events_df = wde.cumulative_match_mins(events_df)
    events_df = wce.insert_ball_carries(events_df)
    events_df = wce.get_xthreat(events_df, interpolate = True)
    
    # Store information
    all_data.loc[idx, 'player'] = data[0]
    all_data.loc[idx, 'league'] = data[1]
    all_data.loc[idx, 'year'] = data[2]
    all_data.loc[idx, 'events'] = [pd.DataFrame(events_df)]
    all_data.loc[idx, 'players'] = [pd.DataFrame(players_df)]

    # Reset storage dataframes
    del events_df
    del players_df

# %%
    
player_stats = all_data.loc[:,['player', 'league', 'year']]
player_stats = pd.DataFrame()

for idx, dataset in all_data.iterrows():
   
    # Protect against dataframe/list bug
    if type(dataset['players']) == list:
        players = dataset['players'][0]
    else:
        players = dataset['players']
        
    if type(dataset['events']) == list:
        events = dataset['events'][0]
    else:
        events = dataset['events']
    
    # Set up player info dataframe and get player id
    players = wde.minutes_played(players, events)
    playerinfo = wde.create_player_list(players)
    player_id = playerinfo[playerinfo['name']==dataset['player']].index.values[0]
    
    # Get player events
    match_ids = players[(players['name']==dataset['player']) & (players['mins_played']>0)]['match_id'].tolist()
    player_match_events = events[events['match_id'].isin(match_ids)]
    player_events = events[(events['match_id'].isin(match_ids)) & (events['playerId']==player_id)]

    # Player touches
    touches = player_events[player_events['isTouch'] == True]
    suc_touch_opp3 = touches[(touches['outcomeType']=='Successful') & (touches['x']>=100*(2/3))]
    suc_touch_box = touches[(touches['outcomeType']=='Successful') & (touches['x']>=83) & (touches['y']<=79) & (touches['y']>=21)]
    
    # Player progressive passes, passes into opposition third and box passes
    player_events['progressive_pass'] = player_events.apply(wce.progressive_pass, axis=1)
    player_events['box_pass'] = player_events.apply(wce.pass_into_box, axis=1)
    suc_pass = player_events[(player_events['eventType']=='Pass') & (player_events['outcomeType']=='Successful')]   
    suc_prog_pass = player_events[(player_events['progressive_pass']==True)]    
    suc_prog_pass_opph = player_events[(player_events['progressive_pass']==True) & (player_events['x']>=50)]
    pass_opp3 = player_events[(player_events['eventType'] == 'Pass') & (player_events['x']<100*(2/3)) & (player_events['endX'] >=100*(2/3))]
    suc_pass_opp3 = pass_opp3[pass_opp3['outcomeType'] == 'Successful']
    suc_pass_box = player_events[(player_events['box_pass']==True)]    
    
    # Player progressive carries, carries into opposition third and box carries
    player_events['progressive_carry'] = player_events.apply(wce.progressive_carry, axis=1)
    player_events['box_carry'] = player_events.apply(wce.carry_into_box, axis=1)
    suc_carry = player_events[(player_events['eventType']=='Carry') & (player_events['outcomeType']=='Successful')]   
    suc_prog_carry = player_events[(player_events['progressive_carry']==True)]    
    suc_prog_carry_opph = player_events[(player_events['progressive_carry']==True) & (player_events['x']>=50)]
    suc_carry_opp3 = player_events[(player_events['eventType'] == 'Carry') & (player_events['x']<100*(2/3)) & (player_events['endX'] >=100*(2/3))]
    suc_carry_box = player_events[(player_events['box_carry']==True)]       
    
    # Player tackles
    tackles = player_events[player_events['eventType'] == 'Tackle']
    suc_tackles = tackles[tackles['outcomeType'] == 'Successful']
    
    # Player interceptions
    interceptions = player_events[player_events['eventType'] == 'Interception']
    
    # Aerial challenges
    aerials = player_events[player_events['eventType'] == 'Aerial']
    aerials_won = aerials[aerials['outcomeType'] == 'Successful']
    
    # Recoveries
    recoveries = player_events[player_events['eventType'] == 'BallRecovery']
    
    # Add basic stats to info dataframe
    playerinfo = wde.group_player_events(touches, playerinfo, group_type='count', primary_event_name='touches')
    playerinfo = wde.group_player_events(suc_touch_opp3, playerinfo, group_type='count', primary_event_name='suc_touch_opp3')
    playerinfo = wde.group_player_events(suc_touch_box, playerinfo, group_type='count', primary_event_name='suc_touch_box')
    
    playerinfo = wde.group_player_events(suc_prog_pass, playerinfo, group_type='count', primary_event_name='suc_prog_pass')
    playerinfo = wde.group_player_events(suc_prog_pass_opph, playerinfo, group_type='count', primary_event_name='suc_prog_pass_opph')
    playerinfo = wde.group_player_events(pass_opp3, playerinfo, group_type='count', primary_event_name='pass_opp3')
    playerinfo = wde.group_player_events(suc_pass_opp3, playerinfo, group_type='count', primary_event_name='suc_pass_opp3')
    playerinfo = wde.group_player_events(suc_pass_box, playerinfo, group_type='count', primary_event_name='suc_pass_box')
    playerinfo = wde.group_player_events(suc_pass, playerinfo, group_type='sum', event_types=['xThreat'])
    
    playerinfo = wde.group_player_events(suc_prog_carry, playerinfo, group_type='count', primary_event_name='suc_prog_carry')
    playerinfo = wde.group_player_events(suc_prog_carry_opph, playerinfo, group_type='count', primary_event_name='suc_prog_carry_opph')
    playerinfo = wde.group_player_events(suc_carry_opp3, playerinfo, group_type='count', primary_event_name='suc_carry_opp3')
    playerinfo = wde.group_player_events(suc_carry_box, playerinfo, group_type='count', primary_event_name='suc_carry_box')
    playerinfo = wde.group_player_events(suc_carry, playerinfo, group_type='sum', event_types=['xThreat'])

    playerinfo = wde.group_player_events(tackles, playerinfo, group_type='count', primary_event_name='tackles')
    playerinfo = wde.group_player_events(suc_tackles, playerinfo, group_type='count', primary_event_name='suc_tackles')

    playerinfo = wde.group_player_events(interceptions, playerinfo, group_type='count', primary_event_name='inteceptions')

    playerinfo = wde.group_player_events(aerials, playerinfo, group_type='count', primary_event_name='aerials')
    playerinfo = wde.group_player_events(aerials_won, playerinfo, group_type='count', primary_event_name='aerials_won')

    playerinfo = wde.group_player_events(recoveries, playerinfo, group_type='count', primary_event_name='recoveries')

    # Filter out comparison/analysis players only
    playerinfo = playerinfo[playerinfo['name'] == dataset['player']]
    playerinfo['id'] = idx
    playerinfo.set_index('id', inplace=True)
    
    # Concatenate all stats
    player_stats = pd.concat([player_stats, playerinfo], axis = 0)
    
    # Add extra info
    player_stats.loc[idx, 'league'] = dataset['league']
    player_stats.loc[idx, 'year'] = dataset['year']
    player_stats.loc[idx, 'matches'] = len(players[(players['name']==dataset['player']) & (players['mins_played']>0)])
  

#%% 
