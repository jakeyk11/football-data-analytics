# %% Create visualisation of team ball wins and mean win height
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Date of run
#           Selection of whether to include percentages on visual
#           Selection of whether to brighten logo
#
# Output:   Heatmaps showing ball win zones for each team & mean ball win height

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
run_date = '08/05/2023'

# Select whether to label %
label_pct = False

# Select whether to brighten logo
logo_brighten = False

# Select whether to use team colours
team_colour = False

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

# %% Isolate ball wins

interceptions = events_df[(events_df['eventType']=='Interception') & (events_df['outcomeType']=='Successful')]
tackles = events_df[(events_df['eventType']=='Tackle') & (events_df['outcomeType']=='Successful')]
pass_blocks = events_df[(events_df['eventType']=='BlockedPass') & (events_df['outcomeType']=='Successful') ]

ball_wins_df = pd.concat([interceptions, tackles, pass_blocks], axis=0)

# %% Get teams and order on mean height of ball recovery

# Sort alphabetically initially
teams = sorted(set(players_df['team']))

# Set up dictionary to store xt per 90 per team
team_ball_win_height = dict.fromkeys(teams, 0)
team_count = len(teams)

for team in teams:
    
    # Get team events
    team_id = players_df[players_df['team']==team]['teamId'].values[0]
    team_ball_wins = ball_wins_df[ball_wins_df['teamId']==team_id]
    
    # Get mean recovery height
    team_ball_win_height[team] = team_ball_wins['x'].mean()
      
# Sort dictionary by xT/90
team_ball_win_height = sorted(team_ball_win_height.items(), key=lambda x: x[1], reverse=True)

# %% Custom colormap

CustomCmap = mpl.colors.LinearSegmentedColormap.from_list("", ["#313332","#47516B", "#848178", "#B2A66F", "#FDE636"])

# %% Create visual

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Define grid dimensions
ncols = 4
nrows = int(np.ceil(len(team_ball_win_height)/ncols))  

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=nrows, ncols=ncols, grid_height=0.8, title_height = 0.13, endnote_height = 0.04, space=0.12, axis=False)
fig.set_size_inches(14, 15)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)
idx = 0

# Loop through each team
for team in team_ball_win_height:
    
    # Get team name and events
    team_name = team[0]
    team_id = players_df[players_df['team']==team_name]['teamId'].values[0]
    team_ball_wins = ball_wins_df[ball_wins_df['teamId']==team_id]
        
    # Get team logo and colour
    team_logo, team_cmap = lab.get_team_badge_and_colour(team_name)
    if len(team_name) > 14:
        team_name = team_name[0:13] + '...'
        
    # Set team colour
    if not team_colour:
        team_cmap = CustomCmap

    # Draw heatmap
    bin_statistic = pitch.bin_statistic(team_ball_wins['x'], team_ball_wins['y'],
                                        statistic='count', bins=(6, 5), normalize=True)
    pitch.heatmap(bin_statistic, ax['pitch'][idx], cmap=team_cmap, edgecolor='w', lw=0.5, zorder=0, alpha=0.7)
    
    # Draw mean ball win pos
    pitch.lines(team[1], 0.5, team[1], 99.5, color=team_cmap(255), lw=3, zorder=2, ax=ax['pitch'][idx])
    pitch.lines(team[1]-1, 0.5, team[1]-1, 99.5, color='k', lw=1.5, zorder=4, ax=ax['pitch'][idx])
    pitch.lines(team[1]+1, 0.5, team[1]+1, 99.5, color='k', lw=1.5, zorder=4, ax=ax['pitch'][idx])
    path_eff = [path_effects.Stroke(linewidth=3, foreground='k'), path_effects.Normal()]
    ax['pitch'][idx].text(team[1]+3, 6, f"{round(team[1],1)}%\nup pitch", fontsize=13, color='w',path_effects = path_eff)

    # Label heatmap zones with pressure count if selected
    if label_pct:
        labels = pitch.label_heatmap(bin_statistic, color='w', fontsize=10, fontweight = 'bold',
                                     ax=ax['pitch'][idx], ha='center', va='center', str_format='{:.0%}', path_effects=path_eff)
    
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

title_text = f"{leagues[league]} {year}/{int(year)+1} - Teams Ranked by Average Ball Win Height"
subtitle_text = "Heatmaps showing Zones of <Frequent Ball Winning> and <Infrequent Ball Winning>"
subsubtitle_text = f"Correct as of {run_date}"

fig.text(0.12, 0.945, title_text, fontweight="bold", fontsize=20, color='w')
htext.fig_text(0.12, 0.934, s=subtitle_text, fontweight="bold", fontsize=18, color='w',
               highlight_textprops=[{"color": 'yellow', "fontweight": 'bold'}, {"color": 'grey', "fontweight": 'bold'}])
fig.text(0.12, 0.9, subsubtitle_text, fontweight="regular", fontsize=16, color='w')
    
# Add direction of play arrow
ax = fig.add_axes([0.042, 0.028, 0.18, 0.005])
ax.axis("off")
plt.arrow(0.61, 0.15, -0.1, 0, color="white")
fig.text(0.13, 0.02, "Direction of opposition play", ha="center", fontsize=10, color="white", fontweight="regular")

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

fig.savefig(f"team_ball_winning/{league}-{year}-team-ball-winning", dpi=300)