# %% Create visualisation of team open play crosses and cross success
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Date of run
#           Selection of whether to brighten logo
#
# Output:   Pass maps showing all crosses, successful crosses & crosses leading to goal

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
from scipy.spatial import Delaunay

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

# Select whether to brighten logo
logo_brighten = False

# %% Get competition logo

if logo_brighten:
    comp_logo = lab.get_competition_logo(league, year)
    enhancer = ImageEnhance.Brightness(comp_logo)
    comp_logo = enhancer.enhance(100)
else:
    comp_logo = lab.get_competition_logo(league, year)

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

# %% Get cumulative minutes info

events_df = wde.cumulative_match_mins(events_df)
events_df = wde.add_team_name(events_df, players_df)

# %% Get crosses

all_crosses = events_df[(events_df['eventType']=='Pass') & (abs(events_df['endY'] - events_df['y']) >= 10) & (events_df['satisfiedEventsTypes'].apply(lambda x: True if (125 in x or 126 in x) else False))]
open_play_crosses = all_crosses[~all_crosses['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 212 in x) else False)]

# %% Calculate pressure action retention (bespoke method for carries)

# Add new column to categorise cross
open_play_crosses['cross_outcome'] = np.nan

for idx, cross in open_play_crosses.iterrows():
    next_evts = events_df[(events_df['match_id'] == cross['match_id']) & (events_df['period'] == cross['period']) & (events_df['cumulative_mins'] > cross['cumulative_mins']) & (events_df['cumulative_mins'] <= cross['cumulative_mins']+(5/60))]
    team_next_evts = next_evts[next_evts['teamId'] == cross['teamId']]  
    if ('Goal' in next_evts['eventType'].tolist()) or (92 in cross['satisfiedEventsTypes']):
        open_play_crosses.loc[idx, 'cross_outcome'] = 'Goal'
    elif ('SavedShot' in team_next_evts['eventType'].tolist()) or ('ShotOnPost' in team_next_evts['eventType'].tolist()) or ('MissedShots' in team_next_evts['eventType'].tolist()):
        open_play_crosses.loc[idx, 'cross_outcome'] = 'Shot'
    elif bool(set([item for sublist in next_evts['satisfiedEventsTypes'].tolist() for item in sublist]) & set(np.arange(39,47))):
        open_play_crosses.loc[idx, 'cross_outcome'] = 'Key Pass'
    elif cross['outcomeType'] == 'Successful':
        open_play_crosses.loc[idx, 'cross_outcome'] = 'To Team-mate'
    else:
        open_play_crosses.loc[idx, 'cross_outcome'] = 'Unsuccessful'

# %% Get teams and order on count of effective crosses

# Sort alphabetically initially
teams = sorted(set(players_df['team']))

# Set up dictionary to cross count per team
team_effective_cross = dict.fromkeys(teams, 0)
team_count = len(teams)

for team in teams:
    
    # Get team events
    team_id = players_df[players_df['team']==team]['teamId'].values[0]
    team_crosses = open_play_crosses[open_play_crosses['teamId']==team_id]
    team_effective_crosses = team_crosses[team_crosses['cross_outcome'].isin(['Goal', 'Shot', 'Key Pass'])]
    
    # Get cross pct
    team_effective_cross[team] = 100*(len(team_effective_crosses)/len(team_crosses))
      
# Sort cross count
team_effective_cross = sorted(team_effective_cross.items(), key=lambda x: x[1], reverse=True)        

# %% Create visual

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Define grid dimensions
ncols = 5
nrows = int(np.ceil(len(team_effective_cross)/ncols))

# Set-up pitch subplots
pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, half=True, stripe=False)
fig, ax = pitch.grid(nrows=nrows, ncols=ncols, grid_height=0.79, title_height = 0.15, endnote_height = 0.04, space=0.1, axis=False)
fig.set_size_inches(12, 9.5)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)
idx = 0

# Set colours
normal_col = 'grey'
key_col = 'lightseagreen'
assist_col = 'yellow'


# Plot crosses for each team
for team in team_effective_cross:
    
    # Get team name and events
    team_name = team[0]
    team_id = players_df[players_df['team']==team_name]['teamId'].values[0]
    team_crosses = open_play_crosses[open_play_crosses['teamId']==team_id]
    team_unsuc_crosses = team_crosses[team_crosses['cross_outcome']=='Unsuccessful']
    team_suc_crosses = team_crosses[team_crosses['cross_outcome']=='To Team-mate']
    team_key_crosses = team_crosses[team_crosses['cross_outcome'].isin(['Shot','Key Pass'])]
    team_goal_crosses = team_crosses[team_crosses['cross_outcome']=='Goal']

    # Get team logo and colour
    team_logo, _ = lab.get_team_badge_and_colour(team_name)
    
    # Plot unsuccessful crosses
    pitch.lines(team_unsuc_crosses['x'], team_unsuc_crosses['y'], team_unsuc_crosses['endX'], team_unsuc_crosses['endY'],
                color = normal_col, alpha = 0.3, zorder = 1, lw = 1,ax = ax['pitch'][idx])
    
    # Plot successful crosses
    pitch.lines(team_suc_crosses['x'], team_suc_crosses['y'], team_suc_crosses['endX'], team_suc_crosses['endY'],
                color = normal_col, alpha = 0.3, zorder = 2, lw = 1,ax = ax['pitch'][idx])

    # Plot key crosses
    for _, cross in team_key_crosses.iterrows():    
        pitch.lines(cross['x'], cross['y'], cross['endX'], cross['endY'],
                    color = key_col, alpha = 0.7, zorder = 3, lw = 1,ax = ax['pitch'][idx])
        pitch.scatter(cross['endX'], cross['endY'], color = key_col, alpha = 0.7, s=15, ax = ax['pitch'][idx], zorder = 4)
        pitch.scatter(cross['endX'], cross['endY'], color = '#313332', alpha = 1, s=5, ax = ax['pitch'][idx], zorder = 4)

    # Plot cross assists
    for _, cross in team_goal_crosses.iterrows():    
        pitch.lines(cross['x'], cross['y'], cross['endX'], cross['endY'],
                    color = assist_col, alpha = 0.8, zorder = 4, lw = 1,ax = ax['pitch'][idx])
        pitch.scatter(cross['endX'], cross['endY'], color = assist_col, alpha = 0.8, s=15, ax = ax['pitch'][idx], zorder = 5)
        pitch.scatter(cross['endX'], cross['endY'], color = '#313332', alpha = 1, s=5, ax = ax['pitch'][idx], zorder = 5)
    
    # Find box containing most points
    x_min = 50
    x_max = 100
    y_min = 0
    y_max = 100
    x_range = 12.5
    y_range = 17.5
    
    in_hull_dict = dict()
    
    for x in np.arange(x_min, x_max-x_range+1, 2.5):
        x1 = x
        x2 = x + x_range
        for y in np.arange(y_min, y_max-y_range+1, 2.5):
            y1 = y
            y2 = y + y_range
            
            hull = [(x1,y1), (x2,y1), (x2,y2), (x1,y2)]
            in_hull_cnt = 0
            
            for _, cross in pd.concat([team_goal_crosses, team_key_crosses], axis=0).iterrows():
                
                p = [cross['x'], cross['y']]
                
                if not isinstance(hull, Delaunay):
                    hull = Delaunay(hull)
                
                if hull.find_simplex(p) >= 0:
                    in_hull_cnt += 1
            
            in_hull_dict[(x1,y1,x2,y2)] = in_hull_cnt
    
    zone_st = max(in_hull_dict, key=in_hull_dict.get)
    ax['pitch'][idx].fill([zone_st[1], zone_st[3], zone_st[3], zone_st[1]], [zone_st[0], zone_st[0], zone_st[2], zone_st[2]],
                          edgecolor = 'w', facecolor='#313332', hatch = "////\\\\\\\\", alpha = 0.7, zorder=0)

    path_eff = [path_effects.Stroke(linewidth=3, foreground='#313332'), path_effects.Normal()]
    ax['pitch'][idx].text(zone_st[1], zone_st[0], max(in_hull_dict.values()), color = "w", fontsize = 8, fontweight = "bold", va = "center", ha = "center", path_effects=path_eff)
        
    # Add axis text
    ax['pitch'][idx].text(98, 56, "Crosses:", color = "w", fontsize = 6, fontweight = "bold", va = "center")
    ax['pitch'][idx].text(68, 56, len(team_crosses), color = "w", fontsize = 6, va = "center")    
    ax['pitch'][idx].text(98, 52, "Effective:", color = "w", fontsize = 6, fontweight = "bold", va = "center")
    ax['pitch'][idx].text(68, 52, len(team_key_crosses) + len(team_goal_crosses), color = "w", fontsize = 6, va = "center")  
    ax['pitch'][idx].text(2, 54, str(round(100*(len(team_key_crosses)+len(team_goal_crosses))/len(team_crosses),1)) + "%", color = "w", fontsize = 12, ha = "right", va = "center")  
    
    # Add team rank and title
    ax['pitch'][idx].set_title(f"  {idx + 1}: {team_name}", loc = "left", color='w', fontsize = 11, pad = 2)
    
    # Add team logo
    ax_pos = ax['pitch'][idx].get_position()    
    logo_ax = fig.add_axes([ax_pos.x1-0.025, ax_pos.y1-0.002, 0.025, 0.025])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx+=1

# Title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup'}

title_text = f"{leagues[league]} {year}/{int(year)+1} − Teams Ranked by In-Play Cross Effectiveness"
subtitle_text = "In-Play Crosses Shown: <Cross Assists> and <Effective Crosses> highlighted"
subsubtitle_text = f"Effective Cross defined as any cross followed by a shot or key pass within next 5 seconds. Correct as of {run_date}"

fig.text(0.11, 0.945, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.11, 0.933, s=subtitle_text, fontweight="bold", fontsize=13, color='w',
               highlight_textprops=[{"color": assist_col, "fontweight": 'bold'}, {"color": key_col, "fontweight": 'bold'}])
fig.text(0.11, 0.894, subsubtitle_text, fontweight="regular", fontsize=10, color='w')
    
# Add legend axis
ax = fig.add_axes([0.027, 0.007, 0.24, 0.04])
ax.fill([0.1, 0.8, 0.8, 0.1], [0.1, 0.1, 0.8, 0.8], edgecolor = 'w', facecolor='#313332', hatch = "////\\\\\\\\", alpha = 0.7)
ax.text(0.8, 0.1, "#", color = "w", fontsize = 10, fontweight = "bold", va = "center", ha = "center", path_effects=path_eff)
ax.text(1.2, 0.4, "12.5m x 12.5m area from which largest volume\nof effective crosses are made. # represents number\nof crosses from the area", color = "w", fontsize = 7, va = "center", ha = "left")
ax.set_xlim([0,6])
ax.set_ylim([0,1])
ax.axis("off")

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")


# Add competition logo
ax = fig.add_axes([0.017, 0.88, 0.1, 0.1])
ax.axis("off")
ax.imshow(comp_logo)

# Add twitter logo
ax = fig.add_axes([0.94, 0.007, 0.03, 0.03])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

fig.savefig(f"team_cross_success/{league}-{year}-team_cross_success", dpi=300)
