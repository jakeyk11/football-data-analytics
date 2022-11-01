# %% Create visualisation of top players by defensive actions across a selection of games
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Whoscored match ids
#           Positions not to include
#           Date of run
#           Normalisation mode
#           Minimum play time
#
# Outputs:  Top 12 players by defensive actions

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
from mplsoccer.pitch import VerticalPitch, Pitch
import os
import sys
import bz2
import pickle
import numpy as np
from collections import Counter
import highlight_text as htext
import glob

# %% Function definitions


def protected_divide(n, d):
    return n / d if d else 0

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.pitch_zones as pz
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% User inputs

# Input WhoScored range of match id
match_id_start = 1650559
match_id_end = 1650638
match_ids = np.arange(match_id_start, match_id_end+1)

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'La_Liga'

# Select position to exclude
pos_exclude=[]

# Position formatting on title
pos_input = ''

# Input run-date
run_date = '23/09/2022'

# Normalisation (None, '_90', '_100opp_pass')
norm_mode = '_100opp_pass'
#norm_mode = '_90'

# Min minutes played
min_mins = 270

# %% League logo

comp_logo = lab.get_competition_logo(league) 
    
# %% Read in data

# Opta data
events_df = pd.DataFrame()
players_df = pd.DataFrame()
for match_id in match_ids:
    match_event_path = f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}/match-eventdata-{match_id}-*.pbz2"
    match_players_path = f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}/match-playerdata-{match_id}-*.pbz2"
    try:
        match_events = bz2.BZ2File(glob.glob(match_event_path)[0], 'rb')
        match_events = pickle.load(match_events)
    except:
        match_events = pd.DataFrame()
    try:
        match_players = bz2.BZ2File(glob.glob(match_players_path)[0], 'rb')
        match_players = pickle.load(match_players)
    except:
        match_players = pd.DataFrame()
    try:
        events_df = pd.concat([events_df, match_events])
        players_df = pd.concat([players_df, match_players])
    except IndexError:
        events_df = match_events
        players_df = match_players

event_types = bz2.BZ2File(f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}/event-types.pbz2", 'rb')
event_types = pickle.load(event_types)

# %% Pre-process data

# Add pass recipient
events_df = wde.get_recipient(events_df)

# Add cumulative minutes information
players_df = wde.minutes_played(players_df, events_df)

# Calculate longest consistent xi
players_df = wde.longest_xi(players_df)

# Calculate pass events that each player faces per game
players_df = wde.events_while_playing(events_df, players_df, event_name = 'Pass', event_team = 'opposition')

# Calculate opposition half pass events that each player faces per game
players_df['oppthird_opp_pass'] = wde.events_while_playing(events_df[events_df['x']<= 34], players_df, event_name = 'Pass', event_team = 'opposition')['opp_pass']

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df, additional_cols = ['opp_pass', 'oppthird_opp_pass'])

#%% Aggregation

# Aggregate all defensive actions
all_def_actions = wde.find_defensive_actions(events_df)
playerinfo_df = wde.group_player_events(all_def_actions, playerinfo_df, primary_event_name='def_actions')

# Aggregate defensive actions in opp half
oppthird_def_actions = all_def_actions[all_def_actions['x']>67]
playerinfo_df = wde.group_player_events(oppthird_def_actions, playerinfo_df, primary_event_name='oppthird_def_actions')

# Defensive actions per 100 opp passes and per 90 mins
playerinfo_df['def_actions_100opp_pass'] = round(100*playerinfo_df['def_actions']/playerinfo_df['opp_pass'],2)
playerinfo_df['def_actions_90'] = round(90*playerinfo_df['def_actions']/playerinfo_df['mins_played'],2)
playerinfo_df['oppthird_def_actions_100opp_pass'] = round(100*playerinfo_df['oppthird_def_actions']/playerinfo_df['oppthird_opp_pass'],2)
playerinfo_df['oppthird_def_actions_90'] = round(90*playerinfo_df['oppthird_def_actions']/playerinfo_df['mins_played'],2)

# %% Player removal
 
playerinfo_reduced_df = playerinfo_df[(playerinfo_df['position'].isin(pos_exclude) == False) & (playerinfo_df['mins_played']>=min_mins)]

# %% Ordering based on normalisation

if norm_mode == None:
    sorted_df = playerinfo_reduced_df.sort_values(['oppthird_def_actions', 'oppthird_def_actions_100opp_pass'], ascending=[False, False])
elif norm_mode == '_90':
    sorted_df = playerinfo_reduced_df.sort_values(['oppthird_def_actions_90', 'oppthird_def_actions_100opp_pass'], ascending=[False, False])
elif norm_mode == '_100opp_pass':
    sorted_df = playerinfo_reduced_df.sort_values(['oppthird_def_actions_100opp_pass', 'oppthird_def_actions_90'], ascending=[False, False])

# %% Text formatting 

if norm_mode == None:
    title_addition = ''
elif norm_mode == '_90':
    title_addition = 'per 90mins'
elif norm_mode == '_100opp_pass':
    title_addition = 'per 100 opposition passes in that third'
    
if len(pos_exclude)==0:
    title_pos_str = 'players'
    file_pos_str = ''
else:
    title_pos_str = pos_input
    file_pos_str = '-' + pos_input

# %% Create viz of top progressive passers

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.75, space=0.12, axis=False)
fig.set_size_inches(14, 10)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Plot successful prog passes as arrows, using for loop to iterate through each player and each pass
idx = 0

for player_id, name in sorted_df.head(12).iterrows():
    player_def_actions = all_def_actions[all_def_actions['playerId'] == player_id]
    player_opp_third_def_actions = oppthird_def_actions[oppthird_def_actions['playerId'] == player_id]
    
    ax['pitch'][idx].set_title(f"  {idx + 1}: {name['name']}", loc = "left", color='w', fontsize = 10)

    pitch.kdeplot(player_def_actions['x'], player_def_actions['y'], ax=ax['pitch'][idx], fill=True, levels=80, shade_lowest=True, cmap='viridis', cut=8, alpha=0.6, antialiased=True, zorder=0)  
    pitch.kdeplot(player_def_actions['x'], player_def_actions['y'], ax=ax['pitch'][idx], fill=True, levels=100, shade_lowest=True, cmap='viridis', cut=8, alpha=0.6, antialiased=True, zorder=0)  

    ax['pitch'][idx].fill([0, 67, 67, 0], [0, 0, 100, 100], 'grey', alpha = 0.7, zorder=0)
    ax['pitch'][idx].plot([67, 67], [0, 99], 'w', ls = 'dashed', zorder=0)

    pitch.scatter(player_def_actions['x'], player_def_actions['y'], color = 'k', alpha = 0.2, s = 12, zorder=1, ax=ax['pitch'][idx])
    pitch.scatter(player_opp_third_def_actions['x'], player_opp_third_def_actions['y'], color = 'w', alpha = 0.6, s = 12, zorder=1, ax=ax['pitch'][idx])

    ax['pitch'][idx].text(0, -8, "Opp. 3rd Actions:", fontsize=8, fontweight='bold', color='w', zorder=1)
    ax['pitch'][idx].text(39, -8, f"{int(name['oppthird_def_actions'])}", fontsize=8, color='w', zorder=1)
    
    if norm_mode  == '_100opp_pass':
        ax['pitch'][idx].text(48, -8, "Per 100 Opp. Passes:", fontsize=8, fontweight='bold', color='w', zorder=1)
        ax['pitch'][idx].text(95, -8, f"{round(name['oppthird_def_actions_100opp_pass'],1)}", fontsize=8, color='w', zorder=1)
    
    if norm_mode  == '_90':
        ax['pitch'][idx].text(50, -8, "Per 90 Mins:", fontsize=8, fontweight='bold', color='w', zorder=1)
        ax['pitch'][idx].text(85, -8, f"{round(name['oppthird_def_actions_90'],1)}", fontsize=8, color='w', zorder=1)
    
    team = name['team']
    team_logo, _ = lab.get_team_badge_and_colour(team)
            
    ax_pos = ax['pitch'][idx].get_position()
    
    logo_ax = fig.add_axes([ax_pos.x1-0.035, ax_pos.y1, 0.035, 0.035])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx += 1

# Create title and subtitles, using highlighting as figure legend
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship'}

title_text = f"{leagues[league]} {year}/{int(year) + 1} - Top 12 {title_pos_str} by Tendency to Defend from the Front"
subtitle_text = f"Players ranked by total number of defensive actions in opposition third, {title_addition}"
subsubtitle_text = "Heatmaps of defensive actions, including ball recoveries, blocks, clearances, interceptions and tackles shown"
subsubsubtitle_text = f"Correct as of {run_date}.\nPlayers with less than {min_mins}\nmins play-time omitted."

# Title
fig.text(0.1, 0.945, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.1, 0.915, subtitle_text, fontweight="regular", fontsize=13, color='w')
fig.text(0.1, 0.8875, subsubtitle_text, fontweight="regular", fontsize=10, color='w')
fig.text(0.847, 0.902, subsubsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.05, 0.18, 0.01])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.03, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.04, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add competition logo
ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
ax.axis("off")
ax.imshow(comp_logo)

# Add twitter logo
ax = fig.add_axes([0.92, 0.025, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save image
fig.savefig(f"top_defensive_actions/{league}-{year}-top-defensive-actions{file_pos_str.replace(' & ','-').replace(' ','-')}-{title_addition.replace(' ','-')}", dpi=300)

