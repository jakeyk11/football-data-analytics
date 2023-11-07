# Investigation of various factors on fouls and cards per match

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image, ImageEnhance
from mplsoccer.pitch import VerticalPitch, Pitch
import matplotlib.patheffects as path_effects
import os
import sys
import bz2
import pickle
import numpy as np
from collections import Counter
import highlight_text as htext
import glob
import seaborn as sns

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.pitch_zones as pz
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% Team name processing

def team_name_clean(name):
    
    processed_name = name
    if 'Manchester' not in processed_name:
        processed_name = processed_name.replace('United','')
        processed_name = processed_name.replace('City','')
    
    mapping_dict = {'Brighton & Hove Albion': 'Brighton',
                    'Brighton and Hove Albion': 'Brighton',
                    'Tottenham Hotspur': 'Tottenham',
                    'Manchester United': 'Man Utd',
                    'Manchester City': 'Man City',
                    'Wolverhampton Wanderers': 'Wolves',
                    }    
    
    if processed_name.strip() in mapping_dict.keys():
        processed_name = mapping_dict[processed_name.strip()]
    
    return processed_name.strip()

# %% User Inputs

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Logo brighten
logo_brighten = True

# Angle that qualifies as side pass (deg)
side_angle = 30

# Mode (count or threat)
mode = 'count'

# %% Get competition logo

comp_logo = lab.get_competition_logo(league, year, logo_brighten=logo_brighten)

# %% Get event data for current year

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

events_df = wde.add_team_name(events_df, players_df)

# %% Get league table data

file_path_league = f"../../data_directory/leaguetable_data/{year}_{str(int(year.replace('20','', 1)) + 1)}"
file = f"{league}-table-{year}.pbz2"
league_table = bz2.BZ2File(f"{file_path_league}/{file}", 'rb')
league_table = pickle.load(league_table)
league_table['team'] = league_table['team'].apply(team_name_clean)

# %% Isolate different event types that will be counted

# Passes
ip_passes = events_df[(events_df['eventType'].isin(['Pass', 'OffsidePass'])) & (~events_df['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 212 in x) else False))].reset_index(drop=True)
                                                         
# Shots
ip_shots = events_df[(events_df['eventType'].isin(['Goal', 'MissedShots', 'SavedShot', 'ShotOnPost'])) & (~events_df['satisfiedEventsTypes'].apply(lambda x: True if (5 in x or 6 in x or 22 in x or 135 in x) else False))].reset_index(drop=True)
                     
# Carries                   
carries = events_df[events_df['eventType']=='Carry']

# Crosses or long balls
cross_longballs = ip_passes[ip_passes['satisfiedEventsTypes'].apply(lambda x: 59 in x or 125 in x or 126 in x or 127 in x or 128 in x)]

# %% Breakdown standard passes by direction

def pass_direction(df_row, side_angle):
    xs = df_row['x']
    ys = df_row['y']
    xe = df_row['endX']
    ye = df_row['endY']
    dx = 120*(xe - xs)
    dy = 80*(ye - ys)
    ang =  np.rad2deg(np.arctan2(dx, dy))
    if (ang > side_angle) and (ang < 180-side_angle):
        direction = 'fwd'
    elif (ang > -180 + side_angle) and (ang < -side_angle):
        direction = 'back'
    else:
        direction = 'side'
    return ang, direction
    

# Standard passes
standardpasses = ip_passes.loc[~ip_passes.index.isin(list(cross_longballs.index))]
standardpasses[['angle', 'direction']] = standardpasses.apply(pass_direction, side_angle = side_angle, result_type = 'expand', axis=1)
forwardpasses = standardpasses[standardpasses['direction'] == 'fwd']
backpasses = standardpasses[standardpasses['direction'] == 'back']
sidepasses = standardpasses[standardpasses['direction'] == 'side']

# %% Calculate count of action within each zone

all_common_action_bins = list()

for team in league_table['team'].tolist():
    team_shots = ip_shots[ip_shots['team_name'] == team]
    team_carries = carries[carries['team_name'] == team]
    team_cross_longballs = cross_longballs[cross_longballs['team_name'] == team]
    team_backpasses = backpasses[backpasses['team_name'] == team]
    team_forwardpasses = forwardpasses[forwardpasses['team_name'] == team]
    team_sidepasses = sidepasses[sidepasses['team_name'] == team]
        
    pitch = Pitch(pitch_type='opta')
    if mode == 'threat':
        bin_shots = pitch.bin_statistic(team_shots['x'], team_shots['y'], statistic='sum', bins=(6, 5) , values = team_shots['xThreat_gen'],normalize=False)
        bin_carries = pitch.bin_statistic(team_carries['x'], team_carries['y'], statistic='sum', bins=(6, 5), values = team_carries['xThreat_gen'], normalize=False)
        bin_crosses_longballs = pitch.bin_statistic(team_cross_longballs['x'], team_cross_longballs['y'], statistic='sum', bins=(6, 5), values = team_cross_longballs['xThreat_gen'], normalize=False)
        bin_backpasses = pitch.bin_statistic(team_backpasses['x'], team_backpasses['y'], statistic='sum', bins=(6, 5), values = team_backpasses['xThreat_gen'], normalize=False)
        bin_forwardpasses = pitch.bin_statistic(team_forwardpasses['x'], team_forwardpasses['y'], statistic='sum', bins=(6, 5), values = team_forwardpasses['xThreat_gen'], normalize=False)
        bin_sidepasses = pitch.bin_statistic(team_sidepasses['x'], team_sidepasses['y'], statistic='sum', bins=(6, 5), values = team_sidepasses['xThreat_gen'], normalize=False)      
    else:
        bin_shots = pitch.bin_statistic(team_shots['x'], team_shots['y'], statistic='count', bins=(6, 5), normalize=False)
        bin_carries = pitch.bin_statistic(team_carries['x'], team_carries['y'], statistic='count', bins=(6, 5), normalize=False)
        bin_crosses_longballs = pitch.bin_statistic(team_cross_longballs['x'], team_cross_longballs['y'], statistic='count', bins=(6, 5), normalize=False)
        bin_backpasses = pitch.bin_statistic(team_backpasses['x'], team_backpasses['y'], statistic='count', bins=(6, 5), normalize=False)
        bin_forwardpasses = pitch.bin_statistic(team_forwardpasses['x'], team_forwardpasses['y'], statistic='count', bins=(6, 5), normalize=False)
        bin_sidepasses = pitch.bin_statistic(team_sidepasses['x'], team_sidepasses['y'], statistic='count', bins=(6, 5), normalize=False)
   
    bin_max = np.maximum.reduce([bin_shots['statistic'], bin_carries['statistic'], bin_crosses_longballs['statistic'], bin_backpasses['statistic'],
                         bin_forwardpasses['statistic'], bin_sidepasses['statistic']])
    
    common_action_bin = pitch.bin_statistic(team_shots['x'], team_shots['y'], statistic='count', bins=(6, 5) , normalize=False)
    common_action_bin['statistic'][bin_sidepasses['statistic'] == bin_max] = 5
    common_action_bin['statistic'][bin_backpasses['statistic'] == bin_max] = 4
    common_action_bin['statistic'][bin_forwardpasses['statistic'] == bin_max] = 3
    common_action_bin['statistic'][bin_carries['statistic'] == bin_max] = 2
    common_action_bin['statistic'][bin_crosses_longballs['statistic'] == bin_max] = 1
    common_action_bin['statistic'][bin_shots['statistic'] == bin_max] = 0
    if mode == 'threat':
      common_action_bin['statistic'][2,5] = 0
    all_common_action_bins.append(common_action_bin)
    
# %% Define colours for each action

shot_col = "khaki"
cross_longball_col = "mediumpurple"
carry_col = "lightskyblue"
fwdpass_col = "palegreen"
backpass_col = "lightsalmon"
sidepass_col = "#6a6a6a"

CustomCmap = mpl.colors.LinearSegmentedColormap.from_list("", [shot_col, cross_longball_col, carry_col, fwdpass_col, backpass_col, sidepass_col])

# %% Create visual

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Define grid dimensions
ncols = 4
nrows = int(np.ceil(len(all_common_action_bins)/ncols))  

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=nrows, ncols=ncols, grid_height=0.8, title_height = 0.13, endnote_height = 0.04, space=0.12, axis=False)
fig.set_size_inches(14, 15)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)
idx = 0

# Loop through each team
for idx, team in enumerate(league_table['team'].tolist()):
    
    # Get team heatmap
    team_common_action_bins = all_common_action_bins[idx]
        
    # Get team logo and colour
    team_logo, _ = lab.get_team_badge_and_colour(team)
    team_name = team
    if len(team_name) > 14:
        team_name = team_name[0:13] + '...'
        
    # Draw heatmap
    pitch.heatmap(team_common_action_bins, ax['pitch'][idx], cmap=CustomCmap, edgecolor='#313332', lw=0.5, zorder=0.6, alpha=0.5, vmin=0, vmax=5)

    ax['pitch'][idx].set_title(f"  {idx + 1}:  {team_name}", loc = "left", color='w', fontsize = 16)
    
    # Add team logo
    ax_pos = ax['pitch'][idx].get_position()    
    logo_ax = fig.add_axes([ax_pos.x1-0.02, ax_pos.y1, 0.02, 0.02])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    idx+=1

# Title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League One', 'EFL2': 'EFL League Two'}

title_text = f"{leagues[league]} {year}/{str(int(year)+1).replace('20','',1)} - Team Actions by Zone"
if mode == 'threat':
    subtitle_text = "Which Offensive Actions have Teams Created the most Threat with in each Zone of the Pitch?"
else:
    subtitle_text = "Which Offensive Actions have Teams Completed Most Frequently in each Zone of the Pitch?"
    
subsubtitle_text = "Action Types Included (In-Play): <Shots>, <Carries>, <Crosses & Long Balls>, <Fwd-Passes>, <Back-passes> and <Side-passes>"

fig.text(0.12, 0.945, title_text, fontweight="bold", fontsize=20, color='w')
fig.text(0.12, 0.922, subtitle_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.12, 0.911, s=subsubtitle_text, fontweight="bold", fontsize=13, color='w',
               highlight_textprops=[{"color": 'khaki', "fontweight": 'bold'}, {"color": 'lightskyblue', "fontweight": 'bold'},
                                    {"color": 'mediumpurple', "fontweight": 'bold'}, {"color": 'palegreen', "fontweight": 'bold'},
                                    {"color": 'lightsalmon', "fontweight": 'bold'}, {"color": '#6a6a6a', "fontweight": 'bold'}])

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.028, 0.18, 0.005])
ax.axis("off")
plt.arrow(-0.1, 0.3, 0.61, 0, color="white")
fig.text(0.13, 0.02, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.022, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add competition logo
ax = fig.add_axes([0.017, 0.88, 0.1, 0.1])
ax.axis("off")
ax.imshow(comp_logo)

# Add twitter logo
ax = fig.add_axes([0.92, 0.005, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

fig.savefig(f"team_common_actions/{league}-{year}-team_common_actions-{mode}", dpi=300)

# %% Create visual



fig, ax = pitch.grid(endnote_height=0.05, endnote_space=0, title_height=0.12, axis=False, grid_height=0.79)
fig.set_size_inches(7, 9)
fig.set_facecolor('#313332')

b = sidepasses.head(1000)

pitch.lines(b['x'], b['y'], b['endX'], b['endY'], ax = ax['pitch'],lw = 3, comet=True, transparent=True)




