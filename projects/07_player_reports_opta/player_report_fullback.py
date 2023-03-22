# %% Create full back analysis report
#
# Inputs:   Player name, league and year to analyse
#           List of player names, leagues and years to compare to
#           League(s) to rank players within
#
# Outputs:  Player report

# To add

# Crosses and cutbacks
# Long ball percentage
# Actions after turnover

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
from scipy.spatial import ConvexHull
from scipy.interpolate import interp2d
from scipy.spatial import Delaunay
from shapely.geometry.polygon import Polygon

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
player_name = 'Dominic Thompson'
league = "EFLC"
year = '2022'

# Players, leagues and years to compare
comparison_players = [('Morgan Fox', 'EFLC', '2022'),
                      ('Max Lowe', 'EFLC', '2022')]

# %%
# Full league and criteria to compare against
comparison_league = ('EFLC', '2022')
comparison_pos = ['DL']
comparison_min_mins = 900

# Abbreviated league name for printing
comparison_league_abbrev = 'EFLC'
player_pos_abbrev = 'LB'
comparison_pos_abbrev = 'LB'

# %% Load analysis and comparison data

# Create list of data to load
data_to_load = [(player_name,league, year)] + comparison_players

# Set-up storage dataframe
all_data = pd.DataFrame()

#%% Get data from whoscored

for idx, data in enumerate(data_to_load):
    
    # Determine file path
    file_path = f"../../data_directory/whoscored_data/{data[2]}_{str(int(data[2].replace('20','', 1)) + 1)}/{data[1]}"
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
    team_id = players[(players['name']==dataset['player'])]['teamId'].tolist()[0]
    
    # Get player events
    match_ids = players[(players['name']==dataset['player']) & (players['mins_played']>0)]['match_id'].tolist()
    player_match_events = events[events['match_id'].isin(match_ids)]
    player_events = events[(events['match_id'].isin(match_ids)) & (events['playerId']==player_id)]

    # In play touches
    touches = player_events[player_events['isTouch'] == True]
    inplay_touches = touches[touches['satisfiedEventsTypes'].apply(lambda x: False if (5 in x or 31 in x or 34 in x or 212 in x) else True)]
    suc_touch_opp3 = inplay_touches[(inplay_touches['outcomeType']=='Successful') & (inplay_touches['x']>=100*(2/3))]
    suc_touch_box = inplay_touches[(inplay_touches['outcomeType']=='Successful') & (inplay_touches['x']>=83) & (inplay_touches['y']<=79) & (inplay_touches['y']>=21)]
    
    # Player progressive passes, passes into opposition third and box passes
    player_events['progressive_pass'] = player_events.apply(wce.progressive_pass, axis=1)
    player_events['box_pass'] = player_events.apply(wce.pass_into_box, axis=1)
    all_pass =  player_events[player_events['eventType']=='Pass']
    suc_pass = all_pass[all_pass['outcomeType']=='Successful']   
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
    
    # Crosses
    crosses = all_pass[all_pass['satisfiedEventsTypes'].apply(lambda x: True if (125 in x or 126 in x) else False)]
    suc_crosses = crosses[crosses['outcomeType']=='Successful']

    # Player defensive actions, convex hull and opposition actions in convex hull
    player_def_actions = wde.find_defensive_actions(player_events)     
    player_def_hull = wce.create_convex_hull(player_def_actions, name=dataset['player'], min_events=5, include_events='1std', pitch_area = 10000)
    player_def_hull = wce.passes_into_hull(player_def_hull.squeeze(), player_match_events[player_match_events['teamId'] != team_id], xt_info=True)

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
    
    playerinfo = wde.group_player_events(crosses, playerinfo, group_type='count', primary_event_name='crosses')
    playerinfo = wde.group_player_events(suc_crosses, playerinfo, group_type='count', primary_event_name='suc_crosses')

    playerinfo = wde.group_player_events(tackles, playerinfo, group_type='count', primary_event_name='tackles')
    playerinfo = wde.group_player_events(suc_tackles, playerinfo, group_type='count', primary_event_name='suc_tackles')

    playerinfo = wde.group_player_events(interceptions, playerinfo, group_type='count', primary_event_name='interceptions')

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
    
    # Retain plotted information
    if idx == 0:
        player_suc_passes = suc_pass
        player_suc_passes_ip = player_suc_passes[player_suc_passes['satisfiedEventsTypes'].apply(lambda x: False if (5 in x or 31 in x or 34 in x or 212 in x) else True)]
        player_inplay_touches = inplay_touches
        player_hull = player_def_hull
        player_suc_prog_passes = suc_prog_pass
        player_suc_prog_carries = suc_prog_carry
        player_balls_won = pd.concat([interceptions, suc_tackles], axis=0)

# %% Stats from analysis players

player_stats['suc_touch_opp3_90'] = round(90*(player_stats['suc_touch_opp3']/player_stats['mins_played']),2)    
player_stats['suc_touch_box_90'] = round(90*(player_stats['suc_touch_box']/player_stats['mins_played']),2)    
player_stats['suc_prog_pass_90'] = round(90*(player_stats['suc_prog_pass']/player_stats['mins_played']),2)    
player_stats['suc_pass_opp3_90'] = round(90*(player_stats['suc_pass_opp3']/player_stats['mins_played']),2)
player_stats['suc_pass_box_90'] = round(90*(player_stats['suc_pass_box']/player_stats['mins_played']),2)    
player_stats['xt_pass_90'] = round(90*(player_stats['xThreat_x']/player_stats['mins_played']),2)   
player_stats['suc_prog_carry_90'] = round(90*(player_stats['suc_prog_carry']/player_stats['mins_played']),2)    
player_stats['suc_carry_opp3_90'] = round(90*(player_stats['suc_carry_opp3']/player_stats['mins_played']),2)
player_stats['suc_carry_box_90'] = round(90*(player_stats['suc_carry_box']/player_stats['mins_played']),2)    
player_stats['xt_carry_90'] = round(90*(player_stats['xThreat_y']/player_stats['mins_played']),2)
player_stats['suc_prog_action_90'] = player_stats['suc_prog_pass_90'] + player_stats['suc_prog_carry_90']
player_stats['suc_action_opp3_90'] = player_stats['suc_pass_opp3_90'] + player_stats['suc_carry_opp3_90']
player_stats['suc_action_opp3'] = player_stats['suc_pass_opp3'] + player_stats['suc_carry_opp3']
player_stats['suc_action_box_90'] = player_stats['suc_pass_box_90'] + player_stats['suc_carry_box_90']
player_stats['xt_action_90'] = player_stats['xt_pass_90'] + player_stats['xt_carry_90']
player_stats['suc_cross_90'] = round(90*(player_stats['suc_crosses']/player_stats['mins_played']),2)
player_stats['cross_complete_pct'] = round(100*(player_stats['suc_crosses']/player_stats['crosses']),1)
player_stats['suc_tackles_90'] = round(90*(player_stats['suc_tackles']/player_stats['mins_played']),2)    
player_stats['dribble_prevented_pct'] = round(100*(player_stats['suc_tackles']/player_stats['tackles']),1)
player_stats['interceptions_90'] = round(90*(player_stats['interceptions']/player_stats['mins_played']),2)    
player_stats['aerials_won_90'] = round(90*(player_stats['aerials']/player_stats['mins_played']),2)
player_stats['aerial_win_pct'] = round(100*(player_stats['aerials_won']/player_stats['aerials']),1)
player_stats['recoveries_90'] = round(90*(player_stats['recoveries']/player_stats['mins_played']),2)

# %% Load league comparison data and analyse

file_path = f"../../data_directory/whoscored_data/{comparison_league[1]}_{str(int(comparison_league[1].replace('20','', 1)) + 1)}/{comparison_league[0]}"
files = os.listdir(file_path)

# Initialise storage dataframes
comp_events = pd.DataFrame()
comp_players = pd.DataFrame()

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
        comp_events = pd.concat([comp_events, match_events])
    elif '-playerdata-' in file:
        match_players = bz2.BZ2File(f"{file_path}/{file}", 'rb')
        match_players = pickle.load(match_players)
        comp_players = pd.concat([comp_players, match_players])
    else:
        pass

# Synthesise additional information
comp_events = wde.cumulative_match_mins(comp_events)
comp_events = wce.insert_ball_carries(comp_events)
comp_events = wce.get_xthreat(comp_events, interpolate = True)

# %% Produce player dataframe for comparison league

# In play touches
touches = comp_events[comp_events['isTouch'] == True]
inplay_touches = touches[touches['satisfiedEventsTypes'].apply(lambda x: False if (5 in x or 31 in x or 34 in x or 212 in x) else True)]
suc_touch_opp3 = inplay_touches[(inplay_touches['outcomeType']=='Successful') & (inplay_touches['x']>=100*(2/3))]
suc_touch_box = inplay_touches[(inplay_touches['outcomeType']=='Successful') & (inplay_touches['x']>=83) & (inplay_touches['y']<=79) & (inplay_touches['y']>=21)]
    
# Player progressive passes, passes into opposition third and box passes
comp_events['progressive_pass'] = comp_events.apply(wce.progressive_pass, axis=1)
comp_events['box_pass'] = comp_events.apply(wce.pass_into_box, axis=1)
all_pass =  comp_events[comp_events['eventType']=='Pass']
suc_pass = all_pass[all_pass['outcomeType']=='Successful']   
suc_prog_pass = comp_events[(comp_events['progressive_pass']==True)]    
suc_prog_pass_opph = comp_events[(player_events['progressive_pass']==True) & (comp_events['x']>=50)]
pass_opp3 = comp_events[(comp_events['eventType'] == 'Pass') & (comp_events['x']<100*(2/3)) & (comp_events['endX'] >=100*(2/3))]
suc_pass_opp3 = pass_opp3[pass_opp3['outcomeType'] == 'Successful']
suc_pass_box = comp_events[(comp_events['box_pass']==True)]    

# Player progressive carries, carries into opposition third and box carries
comp_events['progressive_carry'] = comp_events.apply(wce.progressive_carry, axis=1)
comp_events['box_carry'] = comp_events.apply(wce.carry_into_box, axis=1)
suc_carry = comp_events[(comp_events['eventType']=='Carry') & (comp_events['outcomeType']=='Successful')]   
suc_prog_carry = comp_events[(comp_events['progressive_carry']==True)]    
suc_prog_carry_opph = comp_events[(comp_events['progressive_carry']==True) & (comp_events['x']>=50)]
suc_carry_opp3 = comp_events[(comp_events['eventType'] == 'Carry') & (comp_events['x']<100*(2/3)) & (comp_events['endX'] >=100*(2/3))]
suc_carry_box = comp_events[(comp_events['box_carry']==True)]

# Crosses
crosses = all_pass[all_pass['satisfiedEventsTypes'].apply(lambda x: True if (125 in x or 126 in x) else False)]
suc_crosses = crosses[crosses['outcomeType']=='Successful']

# Player defensive actions, convex hull and opposition actions in convex hull
#player_def_actions = wde.find_defensive_actions(player_events)     
#player_def_hull = wce.create_convex_hull(player_def_actions, name=dataset['player'], min_events=5, include_events='1std', pitch_area = 10000)
#player_def_hull = wce.passes_into_hull(player_def_hull.squeeze(), player_match_events[player_match_events['teamId'] != team_id], xt_info=True)

# Player tackles
tackles = comp_events[comp_events['eventType'] == 'Tackle']
suc_tackles = tackles[tackles['outcomeType'] == 'Successful']

# Player interceptions
interceptions = comp_events[comp_events['eventType'] == 'Interception']

# Aerial challenges
aerials = comp_events[comp_events['eventType'] == 'Aerial']
aerials_won = aerials[aerials['outcomeType'] == 'Successful']

# Recoveries
recoveries = comp_events[comp_events['eventType'] == 'BallRecovery']

# Set-up info dataframe and add basic stats
comp_players = wde.minutes_played(comp_players, comp_events)
playerinfo = wde.create_player_list(comp_players)

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

playerinfo = wde.group_player_events(crosses, playerinfo, group_type='count', primary_event_name='crosses')
playerinfo = wde.group_player_events(suc_crosses, playerinfo, group_type='count', primary_event_name='suc_crosses')

playerinfo = wde.group_player_events(tackles, playerinfo, group_type='count', primary_event_name='tackles')
playerinfo = wde.group_player_events(suc_tackles, playerinfo, group_type='count', primary_event_name='suc_tackles')

playerinfo = wde.group_player_events(interceptions, playerinfo, group_type='count', primary_event_name='interceptions')

playerinfo = wde.group_player_events(aerials, playerinfo, group_type='count', primary_event_name='aerials')
playerinfo = wde.group_player_events(aerials_won, playerinfo, group_type='count', primary_event_name='aerials_won')

playerinfo = wde.group_player_events(recoveries, playerinfo, group_type='count', primary_event_name='recoveries')

# Remove players
playerinfo = playerinfo[(playerinfo['position'].isin(comparison_pos)) & (playerinfo['mins_played'] >= comparison_min_mins)]

# %% Stats from comparison league

playerinfo['suc_touch_opp3_90'] = round(90*(playerinfo['suc_touch_opp3']/playerinfo['mins_played']),2)    
playerinfo['suc_touch_box_90'] = round(90*(playerinfo['suc_touch_box']/playerinfo['mins_played']),2)    
playerinfo['suc_prog_pass_90'] = round(90*(playerinfo['suc_prog_pass']/playerinfo['mins_played']),2)    
playerinfo['suc_pass_opp3_90'] = round(90*(playerinfo['suc_pass_opp3']/playerinfo['mins_played']),2)
playerinfo['suc_pass_box_90'] = round(90*(playerinfo['suc_pass_box']/playerinfo['mins_played']),2)    
playerinfo['xt_pass_90'] = round(90*(playerinfo['xThreat_x']/playerinfo['mins_played']),2)   
playerinfo['suc_prog_carry_90'] = round(90*(playerinfo['suc_prog_carry']/playerinfo['mins_played']),2)    
playerinfo['suc_carry_opp3_90'] = round(90*(playerinfo['suc_carry_opp3']/playerinfo['mins_played']),2)
playerinfo['suc_carry_box_90'] = round(90*(playerinfo['suc_carry_box']/playerinfo['mins_played']),2)    
playerinfo['xt_carry_90'] = round(90*(playerinfo['xThreat_y']/playerinfo['mins_played']),2)
playerinfo['suc_prog_action_90'] = playerinfo['suc_prog_pass_90'] + playerinfo['suc_prog_carry_90']
playerinfo['suc_action_opp3'] = playerinfo['suc_pass_opp3'] + playerinfo['suc_carry_opp3']
playerinfo['suc_action_opp3_90'] = playerinfo['suc_pass_opp3_90'] + playerinfo['suc_carry_opp3_90']
playerinfo['suc_action_box_90'] = playerinfo['suc_pass_box_90'] + playerinfo['suc_carry_box_90']
playerinfo['xt_action_90'] = playerinfo['xt_pass_90'] + playerinfo['xt_carry_90']
playerinfo['suc_cross_90'] = round(90*(playerinfo['suc_crosses']/playerinfo['mins_played']),2)
playerinfo['cross_complete_pct'] = round(100*(playerinfo['suc_crosses']/playerinfo['crosses']),1)
playerinfo['suc_tackles_90'] = round(90*(playerinfo['suc_tackles']/playerinfo['mins_played']),2)    
playerinfo['dribble_prevented_pct'] = round(100*(playerinfo['suc_tackles']/playerinfo['tackles']),1)
playerinfo['interceptions_90'] = round(90*(playerinfo['interceptions']/playerinfo['mins_played']),2)    
playerinfo['aerials_won_90'] = round(90*(playerinfo['aerials']/playerinfo['mins_played']),2)
playerinfo['aerial_win_pct'] = round(100*(playerinfo['aerials_won']/playerinfo['aerials']),1)
playerinfo['recoveries_90'] = round(90*(playerinfo['recoveries']/playerinfo['mins_played']),2)

# %% Calculate player rankings

for idx, player_stat in player_stats.iterrows():
    
    ranking_df = pd.concat([playerinfo[playerinfo['name']!=player_stat['name']], player_stat.to_frame().T], axis = 0)
    
    for stat in ['suc_touch_box_90', 'suc_touch_opp3_90', 'suc_action_opp3_90', 'suc_prog_pass_90', 'suc_prog_carry_90', 'xt_pass_90', 'xt_carry_90', 'suc_tackles_90', 'dribble_prevented_pct', 'interceptions_90', 'aerials_won_90', 'aerial_win_pct', 'cross_complete_pct', 'recoveries_90', 'suc_prog_action_90', 'suc_action_box_90', 'suc_cross_90']:
        
        ascending = False
        rank_str = stat + '_rank'
        percentile_str = stat + '_percentile'
        ranking_df.sort_values(stat, ascending = ascending ,inplace = True)
        player_stats.loc[idx, rank_str] = ranking_df.index.get_loc(idx)+1
        player_stats.loc[idx, percentile_str] = int(100*((len(ranking_df) - ranking_df.index.get_loc(idx)) / len(ranking_df)))
    
    player_stats.loc[idx, 'comparison_pts'] = len(ranking_df)
    
    # Retain information for analysis player
    if idx == 0:
        comparison_df = ranking_df
        comparison_df['primary_player'] = comparison_df['name'].apply(lambda x: True if x==player_name else False)

# %% Create player report

## Set up figure, grid and text/colour effects
fig = plt.figure(constrained_layout=False, figsize = (12.44, 7))
fig.set_facecolor('#313332')
gs = fig.add_gridspec(2, 4, left=0.21, right=0.98, bottom = 0.1, top = 0.94, wspace=0.05, hspace=0.2, width_ratios=[1,1,1,2], height_ratios = [2,2])
pitch1 = fig.add_subplot(gs[0,0])
pitch2 = fig.add_subplot(gs[0,1])
pitch3 = fig.add_subplot(gs[0,2])
pitch4 = fig.add_subplot(gs[1,0])
pitch5 = fig.add_subplot(gs[1,1])
pitch6 = fig.add_subplot(gs[1,2])

# Create side panel
title_ax = fig.add_axes([0, 0, 0.2, 1])
title_ax.set_facecolor('#212126')
title_ax.axes.xaxis.set_visible(False)
title_ax.axes.yaxis.set_visible(False)
for spine in title_ax.spines.values():
    spine.set_visible(False)
    
# Define full pitch
full_pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='w', linewidth=1, stripe=False)
for pitch_ax in [pitch1, pitch2, pitch3, pitch4, pitch5, pitch6]:
    full_pitch.draw(ax=pitch_ax)

# Path effects
path_eff = [path_effects.Stroke(linewidth=1, foreground='#313332'), path_effects.Normal()]

# Manual implentation of colourmap
pass_cmap = cm.get_cmap('viridis')
pass_cmap = pass_cmap(np.linspace(0.35,1,256))

## Titles and logo

# Main titles
text_start_y = 0.78
fig.text(0.142, 0.905, "Player\nReport", fontsize=18, fontweight="bold", color='w', ha = "center", va = "center")
fig.text(0.1, text_start_y, player_name, fontsize=16, fontweight="bold", color='w', ha = "center")
fig.text(0.1, text_start_y-0.03, player_pos_abbrev + ", " + player_stats.loc[0, 'team'], fontsize=12, fontweight="regular", color='w', ha = "center")
fig.text(0.1, text_start_y-0.057, f"{player_stats.loc[0, 'league'].replace('_',' ')}, {player_stats.loc[0, 'year']}/{int(player_stats.loc[0, 'year'])+1}", fontsize=9, fontweight="regular", color='w', ha = "center")

# Logo
team_logo, team_colourmap = lab.get_team_badge_and_colour(player_stats.loc[0, 'team'], 'home')
logo_ax = fig.add_axes([-0.01, 0.84, 0.13, 0.13])
logo_ax.axis("off")
logo_ax.imshow(team_logo)

## Side panel stats

# Top level stats
stat_start_y = 0.65
fig.text(0.012, stat_start_y, "Matches played:", fontsize=11, fontweight="bold", color='w', va = "center")
fig.text(0.188, stat_start_y, int(player_stats.loc[0, 'matches']), fontsize=11, fontweight="regular", color='w', va = "center", ha = "right")

fig.text(0.012, stat_start_y-0.05, "Tackles:", fontsize=11, fontweight="bold", color='w', va = "center")
fig.text(0.188, stat_start_y-0.05, int(player_stats.loc[0, 'suc_tackles']), fontsize=11, fontweight="regular", color='w', va = "center", ha = "right")
bar1 = fig.add_axes([0.0125, stat_start_y-0.08, 0.183, 0.016])
bar1.barh(0.5, 100, height = 1, edgecolor = 'w', color = '#212126')
bar1.barh(0.5, player_stats.loc[0, 'suc_tackles_90_percentile'] , height = 1, edgecolor = None, color = 'w')
bar1.axis("off")
fig.text(0.188, stat_start_y-0.095, f"Rank: {int(player_stats.loc[0, 'suc_tackles_90_rank'])}/{int(player_stats.loc[0, 'comparison_pts'])}", fontsize=6, color='w', ha = "right", va = "center")

fig.text(0.012, stat_start_y-0.125, "Tackle Success:", fontsize=11, fontweight="bold", color='w', va = "center")
fig.text(0.188, stat_start_y-0.125, str(round(player_stats.loc[0, 'dribble_prevented_pct'], 2)) + "%", fontsize=11, fontweight="regular", color='w', va = "center", ha = "right")
bar2 = fig.add_axes([0.0125, stat_start_y-0.155, 0.183, 0.016])
bar2.barh(0.5, 100, height = 1, edgecolor = 'w', color = '#212126')
bar2.barh(0.5, player_stats.loc[0, 'dribble_prevented_pct_percentile'] , height = 1, edgecolor = None, color = 'w')
bar2.axis("off")
fig.text(0.188, stat_start_y-0.17, f"Rank: {int(player_stats.loc[0, 'dribble_prevented_pct_rank'])}/{int(player_stats.loc[0, 'comparison_pts'])}", fontsize=6, color='w', ha = "right", va = "center")

fig.text(0.012, stat_start_y-0.2, "Interceptions:", fontsize=11, fontweight="bold", color='w', va = "center")
fig.text(0.188, stat_start_y-0.2, int(player_stats.loc[0, 'interceptions']), fontsize=11, fontweight="regular", color='w', va = "center", ha = "right")
bar2 = fig.add_axes([0.0125, stat_start_y-0.23, 0.183, 0.016])
bar2.barh(0.5, 100, height = 1, edgecolor = 'w', color = '#212126')
bar2.barh(0.5, player_stats.loc[0, 'interceptions_90_percentile'] , height = 1, edgecolor = None, color = 'w')
bar2.axis("off")
fig.text(0.188, stat_start_y-0.245, f"Rank: {int(player_stats.loc[0, 'interceptions_90_rank'])}/{int(player_stats.loc[0, 'comparison_pts'])}", fontsize=6, color='w', ha = "right", va = "center")

fig.text(0.012, stat_start_y-0.275, "Recoveries:", fontsize=11, fontweight="bold", color='w', va = "center")
fig.text(0.188, stat_start_y-0.275, int(player_stats.loc[0, 'recoveries']), fontsize=11, fontweight="regular", color='w', va = "center", ha = "right")
bar2 = fig.add_axes([0.0125, stat_start_y-0.305, 0.183, 0.016])
bar2.barh(0.5, 100, height = 1, edgecolor = 'w', color = '#212126')
bar2.barh(0.5, player_stats.loc[0, 'recoveries_90_percentile'] , height = 1, edgecolor = None, color = 'w')
bar2.axis("off")
fig.text(0.188, stat_start_y-0.32, f"Rank: {int(player_stats.loc[0, 'recoveries_90_rank'])}/{int(player_stats.loc[0, 'comparison_pts'])}", fontsize=6, color='w', ha = "right", va = "center")

fig.text(0.012, stat_start_y-0.35, "Aerial Duels Won:", fontsize=11, fontweight="bold", color='w', va = "center")
fig.text(0.188, stat_start_y-0.35, str(round(player_stats.loc[0, 'aerial_win_pct'],1)) + "%", fontsize=11, fontweight="regular", color='w', va = "center", ha = "right")
bar2 = fig.add_axes([0.0125, stat_start_y-0.38, 0.183, 0.016])
bar2.barh(0.5, 100, height = 1, edgecolor = 'w', color = '#212126')
bar2.barh(0.5, player_stats.loc[0, 'aerial_win_pct_percentile'] , height = 1, edgecolor = None, color = 'w')
bar2.axis("off")
fig.text(0.188, stat_start_y-0.395, f"Rank: {int(player_stats.loc[0, 'aerial_win_pct_rank'])}/{int(player_stats.loc[0, 'comparison_pts'])}", fontsize=6, color='w', ha = "right", va = "center")

fig.text(0.012, stat_start_y-0.425, "Cross Completion:", fontsize=11, fontweight="bold", color='w', va = "center")
fig.text(0.188, stat_start_y-0.425, str(round(player_stats.loc[0, 'cross_complete_pct'],1)) + "%", fontsize=11, fontweight="regular", color='w', va = "center", ha = "right")
bar2 = fig.add_axes([0.0125, stat_start_y-0.455, 0.183, 0.016])
bar2.barh(0.5, 100, height = 1, edgecolor = 'w', color = '#212126')
bar2.barh(0.5, player_stats.loc[0, 'cross_complete_pct_percentile'] , height = 1, edgecolor = None, color = 'w')
bar2.axis("off")
fig.text(0.188, stat_start_y-0.47, f"Rank: {int(player_stats.loc[0, 'cross_complete_pct_rank'])}/{int(player_stats.loc[0, 'comparison_pts'])}", fontsize=6, color='w', ha = "right", va = "center")

fig.text(0.012, stat_start_y-0.5, "Final Third Touches:", fontsize=11, fontweight="bold", color='w', va = "center")
fig.text(0.188, stat_start_y-0.5, int(player_stats.loc[0, 'suc_touch_opp3']), fontsize=11, fontweight="regular", color='w', va = "center", ha = "right")
bar2 = fig.add_axes([0.0125, stat_start_y-0.53, 0.183, 0.016])
bar2.barh(0.5, 100, height = 1, edgecolor = 'w', color = '#212126')
bar2.barh(0.5, player_stats.loc[0, 'suc_touch_opp3_90_percentile'] , height = 1, edgecolor = None, color = 'w')
bar2.axis("off")
fig.text(0.188, stat_start_y-0.545, f"Rank: {int(player_stats.loc[0, 'suc_touch_opp3_90_rank'])}/{int(player_stats.loc[0, 'comparison_pts'])}", fontsize=6, color='w', ha = "right", va = "center")

fig.text(0.1, 0.08, f"Rank & percentile bars against {comparison_pos_abbrev}s\nplaying over {comparison_min_mins} minutes in {comparison_league[0]} during\nthe {comparison_league[1]}/{int(comparison_league[1])+1} season. If not specified,\nrankings are calculated on stat per 90.", fontsize=8, fontweight="regular", color='w', va = "top", ha = "center")

## Heatmap of player touches

# Title 
pitch1.set_title("Heatmap of All\n In-Play Touches", pad = -1, fontsize = 9, color = 'w', fontweight = "bold")

# Heatmap
full_pitch.kdeplot(player_inplay_touches['x'], player_inplay_touches['y'], fill=True, levels=80, shade_lowest=True, cmap='viridis', cut=8, alpha=1, antialiased=True, zorder=0, ax=pitch1)  
full_pitch.kdeplot(player_inplay_touches['x'], player_inplay_touches['y'], fill=True, levels=100, shade_lowest=True, cmap='viridis', cut=8, alpha=1, antialiased=True, zorder=0, ax=pitch1)  

# Touch scatter
for _,touch in player_inplay_touches.iterrows():
    if touch['outcomeType'] == 'Successful':
        c = 'w'
    else:
        c = 'r'
    full_pitch.scatter(touch['x'], touch['y'], color = c, marker='o', alpha = 0.5, s = 2, zorder=1, ax=pitch1)

# Add legend
legend_ax = fig.add_axes([0.22, 0.5, 0.1, 0.06])
legend_ax.axis("off")

legend_ax.scatter(0.04,0.8, s=30, color = 'w')
legend_ax.text(0.1,0.89, "Successful Touch", va = "top", color='w', fontsize = 7)
legend_ax.scatter(0.04,0.4, s=30, color = 'r')
legend_ax.text(0.1,0.49, "Unsuccessful Touch", va = "top", color='w', fontsize = 7)

legend_ax.set_xlim(0,1)
legend_ax.set_ylim(0,1)
    
## Convex hull plot

pitch2.set_title("Defensive Territory &\nKey Opposition Actions (xT)", pad = -1, fontsize = 9, color = 'w', fontweight = "bold")
# Player initials
if len(player_name.split(' ')) == 1:
    player_initials = player_name.split(' ')[0][0:2]
else:
    player_initials = player_name.split(' ')[0][0].upper() + player_name.split(' ')[1][0].upper()

# Convex hull
plot_hull = full_pitch.convexhull(player_hull['hull_reduced_x'], player_hull['hull_reduced_y'])
full_pitch.polygon(plot_hull, ax=pitch2, color='lightgrey', alpha=0.3, zorder=2)
full_pitch.polygon(plot_hull, ax=pitch2, edgecolor='lightgrey', alpha=0.7, lw=1.5, facecolor='none', zorder=3)
pitch2.scatter(player_hull['hull_centre'][1], player_hull['hull_centre'][0], marker ='H', color = 'grey', alpha = 0.8, s = 300, zorder = 4)
pitch2.scatter(player_hull['hull_centre'][1], player_hull['hull_centre'][0], marker ='H', edgecolor = 'lightgrey', facecolor = 'none', alpha = 1, lw = 2, s = 300, zorder = 4)
pitch2.text(player_hull['hull_centre'][1], player_hull['hull_centre'][0], player_initials, fontsize = 7, fontweight = 'bold', va = 'center', ha = 'center', color = 'w', zorder = 7, path_effects = path_eff)

# Passes into hull
for single_pass in player_hull['suc_pass_into_hull']:
    pass_xt = single_pass[2]
    if pass_xt < 0.02:
        line_colour = 'w'
        line_alpha = 0
        zorder = 1
    else:
        line_colour = pass_cmap[int(255*min(pass_xt/0.05, 1))]
        line_alpha = 0.2
        zorder = 6
    full_pitch.lines(single_pass[0][0], single_pass[0][1], single_pass[1][0], single_pass[1][1], lw = 2, comet=True, capstyle='round',
                alpha = line_alpha, color = line_colour, zorder=zorder, ax=pitch2)

# Turnovers by pitch region
pitch3.set_title("Ball Wins by Pitch\nRegion", pad = -1, fontsize = 9, color = 'w', fontweight = "bold")
bin_statistic_1 = full_pitch.bin_statistic(player_balls_won['x'], player_balls_won['y'],
                                    statistic='count', bins=(6, 5), normalize=True)
full_pitch.heatmap(bin_statistic_1, pitch3, cmap='cividis', edgecolor='w', lw=0.5, zorder=0, alpha=0.7)
labels = full_pitch.label_heatmap(bin_statistic_1, color='w', fontsize=8, fontweight = 'bold',
                             ax=pitch3, ha='center', va='center', str_format='{:.0%}', path_effects=path_eff)

# Progressive passes
pitch4.set_title("Progressive Passes (xT)", pad = -1, fontsize = 9, color = 'w', fontweight = "bold")
for _, single_pass in player_suc_prog_passes.iterrows():
    pass_xt = single_pass['xThreat']
    if pass_xt < 0.005:
        line_colour = 'w'
        line_alpha = 0.03
        zorder = 1
    else:
        line_colour = pass_cmap[int(255*min(pass_xt/0.05, 1))]
        line_alpha = 0.2
        zorder = 2
    full_pitch.lines(single_pass['x'], single_pass['y'], single_pass['endX'], single_pass['endY'], lw = 2, comet=True, capstyle='round',
                alpha = line_alpha, color = line_colour, zorder=zorder, ax=pitch4)

# Progressive carries
pitch5.set_title("Progressive Carries (xT)", pad = -1, fontsize = 9, color = 'w', fontweight = "bold")
for _, single_carry in player_suc_prog_carries.iterrows():
    pass_xt = single_carry['xThreat']
    if pass_xt < 0.005:
        line_colour = 'w'
        line_alpha = 0.03
        zorder = 1
    else:
        line_colour = pass_cmap[int(255*min(pass_xt/0.05, 1))]
        line_alpha = 0.2
        zorder = 2
    full_pitch.lines(single_carry['x'], single_carry['y'], single_carry['endX'], single_carry['endY'], lw = 2, comet=True, capstyle='round',
                alpha = line_alpha, color = line_colour, zorder=zorder, ax=pitch5)
 
# Threat by pitch region
player_suc_passes_ip['xThreat_gen'] = player_suc_passes_ip['xThreat'].apply(lambda x: x if x>0 else 0)
pitch6.set_title("In-Play Threat Creation by\nPitch Region", pad = -1, fontsize = 9, color = 'w', fontweight = "bold")

bin_statistic_2 = full_pitch.bin_statistic(player_suc_passes_ip['x'], player_suc_passes_ip['y'],
                                    statistic='sum', bins=(6, 5), normalize=True, values = player_suc_passes_ip['xThreat_gen'])
full_pitch.heatmap(bin_statistic_2, pitch6, cmap='cividis', edgecolor='w', lw=0.5, zorder=0, alpha=0.7)
labels = full_pitch.label_heatmap(bin_statistic_2, color='w', fontsize=8, fontweight = 'bold',
                             ax=pitch6, ha='center', va='center', str_format='{:.0%}', path_effects=path_eff)

# Add legends
legend_ax = fig.add_axes([0.22, 0.023, 0.18, 0.06])
legend_ax.axis("off")
plt.xlim([0, 8])
plt.ylim([0, 1])
hex_count = 6
path_eff = [path_effects.Stroke(linewidth=1.25, foreground='k'), path_effects.Normal()]

for idx in np.arange(0,hex_count):
    
    if idx%2 == 0:
        ypos = 0.36
    else:
        ypos= 0.64
    xpos = idx/1.05 + 2.5
    
    if idx == 0:
        xt = '<0.005'
        color = 'grey'
    elif idx == 1:
        xt = round(0.005 + (0.05-0.005) * ((idx-1)/(hex_count-2)),3)
        color = pass_cmap[int(255*(idx-1)/(hex_count-2))]
    else:
        xt = round(0.005 + (0.05-0.005) * ((idx-1)/(hex_count-2)),2)
        color = pass_cmap[int(255*(idx-1)/(hex_count-2))]
    
    legend_ax.scatter(xpos, ypos, marker='H', s=400, color=color, edgecolors=None)
    legend_ax.text(xpos+0.03, ypos-0.02, xt, color='w', fontsize = 8, ha = "center", va = "center", path_effects = path_eff)
    legend_ax.text(0, 0.5, "xThreat:", color='w', fontsize = 9, ha = "left", va = "center", fontweight="regular")
    
## Create table
tab_ax = fig.add_axes([0.68, 0.03, 0.3, 0.95])
tab_ax.axis("off")

# Table colourmap
table_cmap = cm.get_cmap('RdYlGn_r')

# List stats to include and names
stats_to_tabulate = ['suc_tackles_90', 'dribble_prevented_pct', 'interceptions_90', 'aerials_won_90', 'aerial_win_pct', 'recoveries_90',
                     'suc_touch_box_90', 'suc_prog_action_90', 'suc_action_opp3_90', 'suc_action_box_90', 'xt_pass_90', 'xt_carry_90',
                     'suc_cross_90', 'cross_complete_pct']
stat_names = ['Tackles / 90', 'Tackle Success %', 'Interceptions / 90', 'Aerial Duels Won / 90', 'Aerial Duel Success %', 'Recoveries / 90',
                     'Opp. Box Touches / 90', 'Progressive Actions / 90', 'Actions into Opp 3rd / 90', 'Actions into Opp box / 90',
                     'Pass xThreat / 90', 'Carry xThreat / 90', 'Crosses / 90', 'Cross Success %']

 # Determine row and columns count
num_rows = len(stats_to_tabulate)
num_cols = len(player_stats)

# Choose row and column start positions
header_start_height = 0.84
column_indent = 0.5

# Determine row and column dimensions
row_height = header_start_height / num_rows
col_width = column_indent / num_cols

# Add header shading
header_rect = patches.Rectangle((0, 1), 1, -(1-header_start_height), linewidth=1, color = '#212126')
tab_ax.add_patch(header_rect)

# Plot column lines and player names
tab_ax.plot([0,0],[0,1], 'w', alpha = 0.2, lw = 1)
for idx in np.arange(0, num_cols+1):
    xpos_colend = column_indent + (idx*col_width)
    tab_ax.plot([xpos_colend,xpos_colend],[0,1], 'w', alpha = 0.2, lw = 1)
    if idx != num_cols:
        xpos_txt = (column_indent+col_width/2) + (idx*col_width)
        plyr_name = player_stats.loc[idx, 'name'].split(' ')[0][0] + " " + player_stats.loc[idx, 'name'].split(' ')[1]
        plyr_year = str(int(player_stats.loc[idx, 'year'].replace('20','', 1))) + "/" + str(1+int(player_stats.loc[idx, 'year'].replace('20','', 1)))
        if len(plyr_name)>10:
            plyr_name = player_stats.loc[idx, 'name'].split(' ')[0][0] + " " + player_stats.loc[idx, 'name'].split(' ')[1][0:10] + "\n" + player_stats.loc[idx, 'name'].split(' ')[1][10:]                                                                                                                                                           
        tab_ax.text(xpos_txt, (1+header_start_height)/2, f"{plyr_name} {plyr_year}",
                    fontsize=8, va="center", ha="center", rotation=90, color = 'w', fontweight='bold')
        
# Plot row lines and stats
for idx in np.arange(0, num_rows+1):
    ypos_rowend = header_start_height - (idx*row_height)
    tab_ax.plot([0,1],[ypos_rowend,ypos_rowend], 'w', alpha = 0.2, lw = 1)
    if idx != num_rows:
        ypos_txt = (header_start_height-row_height/2) - (idx*row_height)
        tab_ax.text(0.02, ypos_txt, stat_names[idx], fontweight = 'bold', fontsize = 8, color = 'w', va = "center")
        
        for idx_2 in np.arange(0, num_cols):
            xpos_txt = (column_indent+0.01) + (idx_2*col_width)
            xpos_rnk = (column_indent + 3*col_width/4) + (idx_2*col_width)
            tab_ax.text(xpos_txt, ypos_txt, round(player_stats.loc[idx_2, stats_to_tabulate[idx]], 2), fontsize = 8, color = 'w', va = "center")
            tab_ax.scatter(xpos_rnk, ypos_txt, s = 3500*row_height, marker = 's', color = table_cmap(int(255 * (player_stats.loc[idx_2, stats_to_tabulate[idx] + "_rank"]/player_stats.loc[idx_2, 'comparison_pts']))))
            tab_ax.text(xpos_rnk, ypos_txt, int(player_stats.loc[idx_2, stats_to_tabulate[idx] + "_rank"]), fontsize = 8, fontweight = 'bold', va = 'center', ha = 'center', color = 'w', path_effects = path_eff)

tab_ax.set_xlim(0,1)
tab_ax.set_ylim(0,1)

fig.text(0.535, 0.08, f"Adjacent table compares the players to a set of relevant\n{comparison_pos_abbrev}s. Performance metrics are provided, with each player\nranked against {comparison_pos_abbrev}s with over {comparison_min_mins} minutes in {comparison_league[0]} during\nthe {comparison_league[1]}/{int(comparison_league[1])+1} season.", fontsize=8, fontweight="regular", color='w', va = "top", ha = "center")

fig.savefig(f"player_reports/{player_name}-{player_stats.loc[0, 'team']}-{player_stats.loc[0, 'league']}-{player_stats.loc[0, 'year']}-{player_stats.loc[0, 'position']}-report", dpi=600)