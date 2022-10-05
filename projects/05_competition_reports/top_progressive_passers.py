# %% Create visualisation of top progressive passers over a series of games
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Whoscored match id
#           Positions not to include
#           Date of run
#           Normalisation mode
#           Minimum play time
#
# Outputs:  Top 12 progressive passers

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
match_id_start = 1640674
match_id_end = 1640729
match_ids = np.arange(match_id_start, match_id_end+1)

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Pass flow zone type
zone_type = 'jdp_custom'

# Select positions to exclude and position formatting on title
pos_exclude = ['GK']
pos_input = 'outfield players'

# Input run-date
run_date = '15/09/2022'

# Normalisation (None, '_90', '_100pass')
norm_mode = '_100pass'

# Min minutes played (only used if normalising)
min_mins = 360

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

# Determine substitute positions
#for idx, player in players_df.iterrows():
 #   if player['subbedOutPlayerId'] == player['subbedOutPlayerId']:
  #      subbed_on_position = players_df[players_df['match_id'] == player['match_id']].loc[player['subbedOutPlayerId'], 'position']
   #     players_df.loc[idx,'position'] = subbed_on_position

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df)

# Passes
all_passes = events_df[events_df['eventType']=='Pass']
playerinfo_df = wde.group_player_events(all_passes, playerinfo_df, primary_event_name='passes')

# Successful passes
suc_passes = events_df[(events_df['eventType']=='Pass') & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(suc_passes, playerinfo_df, primary_event_name='suc_passes')

# Progressive passes
events_df['progressive_pass'] = events_df.apply(wce.progressive_pass, axis=1)
prog_passes = events_df[events_df['progressive_pass']==True]
playerinfo_df = wde.group_player_events(prog_passes, playerinfo_df, primary_event_name='prog_passes')
suc_prog_passes = events_df[(events_df['progressive_pass']==True) & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(suc_prog_passes, playerinfo_df, primary_event_name='suc_prog_passes')

# Forward passes
forward_passes = events_df[(events_df['eventType']=='Pass') & (events_df['endX'] > events_df['x'])]
playerinfo_df = wde.group_player_events(forward_passes, playerinfo_df, primary_event_name='fwd_passes')
suc_forward_passes = events_df[(events_df['eventType']=='Pass') & (events_df['outcomeType']=='Successful') & (events_df['endX'] > events_df['x'])]
playerinfo_df = wde.group_player_events(suc_forward_passes, playerinfo_df, primary_event_name='suc_fwd_passes')

# Crosses
crosses = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 125 in x or 126 in x))]
playerinfo_df = wde.group_player_events(crosses, playerinfo_df, primary_event_name='crosses')
suc_crosses = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 125 in x))]
playerinfo_df = wde.group_player_events(suc_crosses, playerinfo_df, primary_event_name='suc_crosses')

# Through balls
through_balls = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 129 in x or 130 in x or 131 in x))]
playerinfo_df = wde.group_player_events(through_balls, playerinfo_df, primary_event_name='through_balls')
suc_through_balls = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 129 in x))]
playerinfo_df = wde.group_player_events(suc_through_balls, playerinfo_df, primary_event_name='suc_through_balls')

# Long balls
long_balls = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 127 in x or 128 in x))]
playerinfo_df = wde.group_player_events(long_balls, playerinfo_df, primary_event_name='long_balls')
suc_long_balls = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 127 in x))]
playerinfo_df = wde.group_player_events(suc_long_balls, playerinfo_df, primary_event_name='suc_long_balls')

# Key passes
key_prog_passes = suc_prog_passes[suc_prog_passes['satisfiedEventsTypes'].apply(lambda x: 123 in x)]
playerinfo_df = wde.group_player_events(key_prog_passes, playerinfo_df, primary_event_name='key_prog_passes')

# Assists
assists = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 92 in x))]
playerinfo_df = wde.group_player_events(assists, playerinfo_df, primary_event_name='assists')
touch_assists = events_df[(events_df['eventType']!='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 92 in x))]

# Pre assists
events_df = wce.pre_assist(events_df)
pre_assists = events_df[events_df['pre_assist']==True]
playerinfo_df = wde.group_player_events(pre_assists, playerinfo_df, primary_event_name='pre_assists')

# %% Normalisation

# Per 100 passes
playerinfo_df['suc_prog_passes_100pass'] = round(100*playerinfo_df['suc_prog_passes']/playerinfo_df['passes'],1)

# Per 90 mins
playerinfo_df['suc_prog_passes_90'] = round(90*playerinfo_df['suc_prog_passes']/playerinfo_df['mins_played'],1)


# %% Player removal

playerinfo_reduced_df = playerinfo_df[playerinfo_df['pos_type'].isin(pos_exclude) == False]

# %% Ordering based on normalisation

if norm_mode == None:
    sorted_df = playerinfo_reduced_df.sort_values(['suc_prog_passes', 'suc_prog_passes_90'], ascending=[False, False])
elif norm_mode == '_90':
    sorted_df = playerinfo_reduced_df.sort_values(['suc_prog_passes_90', 'suc_prog_passes'], ascending=[False, False])
    sorted_df = sorted_df.drop(sorted_df[sorted_df['mins_played'] <= min_mins].index)
elif norm_mode == '_100pass':
    sorted_df = playerinfo_reduced_df.sort_values(['suc_prog_passes_100pass', 'suc_prog_passes'], ascending=[False, False])
    sorted_df = sorted_df.drop(sorted_df[sorted_df['mins_played'] <= min_mins].index)

# %% Text formatting 

if norm_mode == None:
    title_addition = ''
    subsubtitle_addition = ''
elif norm_mode == '_90':
    title_addition = 'per 90mins'
    subsubtitle_addition = f"Players with less than {min_mins} mins play-time omitted."
elif norm_mode == '_100pass':
    title_addition = 'per 100 passes'
    subsubtitle_addition = f"Players with less than {min_mins} mins play-time omitted."
    
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
fig.set_size_inches(14, 9)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Plot successful prog passes as arrows, using for loop to iterate through each player and each pass
idx = 0

for player_id, name in sorted_df.head(12).iterrows():
    player_passes = suc_prog_passes[suc_prog_passes['playerId'] == player_id]
    player_assists = assists[assists['playerId'] == player_id]
    player_touch_assists = touch_assists[touch_assists['playerId'] == player_id]
    player_key_passes = key_prog_passes[key_prog_passes['playerId'] == player_id]

    ax['pitch'][idx].set_title(f"  {idx + 1}: {name['name']}", loc = "left", color='w', fontsize = 10)

    pitch.lines(player_passes['x'], player_passes['y'], player_passes['endX'], player_passes['endY'],
                lw = 2, comet=True, capstyle='round', label = 'Progressive Pass', color = 'cyan', transparent=True, alpha = 0.1, zorder=1, ax=ax['pitch'][idx])
  
    pitch.lines(player_key_passes['x'], player_key_passes['y'], player_key_passes['endX'], player_key_passes['endY'],
                lw = 2, comet=True, capstyle='round', label = 'Assists', color = 'lime', transparent=True, alpha = 0.5, zorder=2, ax=ax['pitch'][idx])
      
    pitch.lines(player_assists['x'], player_assists['y'], player_assists['endX'], player_assists['endY'],
            lw = 2, comet=True, capstyle='round', label = 'Assists', color = 'magenta', transparent=True, alpha = 0.5, zorder=3, ax=ax['pitch'][idx])

    pitch.scatter(player_touch_assists['x'], player_touch_assists['y'], color = 'magenta', alpha = 0.8, s = 12, zorder=3, ax=ax['pitch'][idx])

    ax['pitch'][idx].text(2, 4, "Total:", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(15, 4, f"{int(name['suc_prog_passes'])}", fontsize=8, color='w', zorder=3)
    
    if norm_mode  == '_100pass':
        ax['pitch'][idx].text(2, 12, "/100 pass:", fontsize=8, fontweight='bold', color='w', zorder=3)
        ax['pitch'][idx].text(26, 12, f"{round(name['suc_prog_passes_100pass'],1)}", fontsize=8, color='w', zorder=3)
    
    
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

title_text = f"Top 12 {title_pos_str}, ranked by number of open-play successful progressive passes {title_addition}"
subtitle_text = f"{leagues[league]} {year}/{int(year) + 1} - <Successful Progressive Passes>, <Key Progressive Passes> and <Assists>"
subsubtitle_text = f"Correct as of {run_date}. {subsubtitle_addition}"
fig.text(0.1, 0.945, title_text, fontweight="bold", fontsize=15, color='w')
htext.fig_text(0.1, 0.93, s=subtitle_text, fontweight="regular", fontsize=13, color='w',
               highlight_textprops=[{"color": 'cyan', "fontweight": 'bold'}, {"color": 'lime', "fontweight": 'bold'},
                                    {"color": 'magenta', "fontweight": 'bold'}])
fig.text(0.1, 0.8875, subsubtitle_text, fontweight="regular", fontsize=10, color='w')

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
fig.savefig(f"top_progressive_passers/{league}-top-progressive-passers{file_pos_str.replace(' & ','-').replace(' ','-')}-{title_addition.replace(' ','-')}", dpi=300)

