# %% Create visualisation of team threat creation zones
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Date of run
#           Selection of whether to include percentages on visual

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

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.pitch_zones as pz
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% User Inputs

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EFLC'

# Input run-date
run_date = '12/02/2023'

# Select whether to label %
label_pct = False

# Logo brighten
logo_brighten = False

# %% Get competition logo

comp_logo = lab.get_competition_logo(league, year, logo_brighten=logo_brighten) 

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
    
# %% Synethesise additional information

events_df = wde.cumulative_match_mins(events_df)
events_df = wce.insert_ball_carries(events_df)
events_df = wce.get_xthreat(events_df, interpolate = True)

# %% Isolate events of choice (in play only)

threat_creating_events_df = events_df[events_df['xThreat']==events_df['xThreat']]
threat_creating_events_df = threat_creating_events_df[~threat_creating_events_df['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 212 in x) else False)]

# %% Get teams and order on total threat created

# Sort alphabetically initially
teams = sorted(set(players_df['team']))

# Set up dictionary to store xt per 90 per team
team_xt_90 = dict.fromkeys(teams, 0)
team_count = len(teams)

for team in teams:
    
    # Get team events
    team_id = players_df[players_df['team']==team]['teamId'].values[0]
    team_threat_creating_events = threat_creating_events_df[threat_creating_events_df['teamId']==team_id]
    
    # Get each team match and accumulate total mins
    team_matches = set(team_threat_creating_events['match_id'])
    team_mins = 0
    for match in team_matches:
        team_mins += events_df[events_df['match_id']==match]['cumulative_mins'].max()
      
    # Team xT created per 90
    team_xt_90[team] = 90*(team_threat_creating_events['xThreat_gen'].sum() / team_mins)

# Sort dictionary by xT/90
team_xt_90 = sorted(team_xt_90.items(), key=lambda x: x[1], reverse=True)

# %% Create visual

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Path effects
path_eff = [path_effects.Stroke(linewidth=4, foreground='#313332'), path_effects.Normal()]

# Define grid dimensions
ncols = 4
nrows = int(np.ceil(len(team_xt_90)/ncols))

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=nrows, ncols=ncols, grid_height=0.8, title_height = 0.13, endnote_height = 0.04, space=0.12, axis=False)
fig.set_size_inches(14, 15)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)
idx = 0

# Loop through each team
for team in team_xt_90:
    
    # Get team name and events
    team_name = team[0]
    team_id = players_df[players_df['team']==team_name]['teamId'].values[0]
    team_threat_creating_events = threat_creating_events_df[threat_creating_events_df['teamId']==team_id]

    # Get team logo and colour
    team_logo, team_cmap = lab.get_team_badge_and_colour(team[0])

    # Draw heatmap
    bin_statistic = pitch.bin_statistic(team_threat_creating_events['x'], team_threat_creating_events['y'],
                                        statistic='sum', bins=(6, 5), normalize=True, values = team_threat_creating_events['xThreat'])
    pitch.heatmap(bin_statistic, ax['pitch'][idx], cmap=team_cmap, edgecolor='w', lw=0.5, zorder=0, alpha=0.7)

    # Label heatmap zones with pressure count if selected
    path_eff = [path_effects.Stroke(linewidth=1.5, foreground='#313332'), path_effects.Normal()]
    if label_pct:
        labels = pitch.label_heatmap(bin_statistic, color='w', fontsize=10, fontweight = 'bold',
                                     ax=ax['pitch'][idx], ha='center', va='center', str_format='{:.0%}', path_effects=path_eff)
    
    # Label xt
    ax['pitch'][idx].text(2, 2, "xT/90:", fontsize=10, fontweight='bold', color='w', zorder=3, path_effects = path_eff)
    ax['pitch'][idx].text(24, 2, round(team[1],2), fontsize=10, color='w', zorder=3, path_effects = path_eff)
    
    # Set title
    ax['pitch'][idx].set_title(f"  {idx + 1}:  {team[0]}", loc = "left", color='w', fontsize = 16)
            
    ax_pos = ax['pitch'][idx].get_position()
    
    logo_ax = fig.add_axes([ax_pos.x1-0.02, ax_pos.y1, 0.02, 0.02])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx+=1
    
# Title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup'}

title_text = f"{leagues[league]} {year}/{int(year)+1} - Teams Ranked by In-Play Threat Creation"
subtitle_text = "Heatmaps showing Zones of <High Threat Creation> and <Low Threat Creation>"
subsubtitle_text = f"Pass, Carry and Dribble events included. Negative threat events excluded. Correct as of {run_date}"

fig.text(0.12, 0.945, title_text, fontweight="bold", fontsize=20, color='w')
htext.fig_text(0.12, 0.934, s=subtitle_text, fontweight="bold", fontsize=18, color='w',
               highlight_textprops=[{"color": 'orange', "fontweight": 'bold'}, {"color": 'grey', "fontweight": 'bold'}])
fig.text(0.12, 0.9, subsubtitle_text, fontweight="regular", fontsize=16, color='w')
    
# Add direction of play arrow
ax = fig.add_axes([0.042, 0.028, 0.18, 0.005])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
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

fig.savefig(f"team_threat_creation/{league}-{year}-team-threat-creation", dpi=300)