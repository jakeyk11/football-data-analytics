# %% Create shape visualisation

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
from mplsoccer.pitch import VerticalPitch
import os
import sys
import bz2
import pickle
import numpy as np
from collections import Counter

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

# Input WhoScored match id
match_id = '1640989'

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Select team codes
home_team = 'Liverpool'
away_team = 'Aston Villa'

# Team name to print
home_team_print = None
away_team_print = None

# Pass flow zone type
zone_type = 'jdp_custom'

# Pass hull inclusion
central_pct_off = '1std'
central_pct_def = '1std'

# %% Logos, colours and printed names

home_logo, home_colourmap = lab.get_team_badge_and_colour(home_team, 'home')
away_logo, away_colourmap = lab.get_team_badge_and_colour(away_team, 'home')

if home_team_print is None:
    home_team_print = home_team

if away_team_print is None:
    away_team_print = away_team
    
cmaps = [home_colourmap, away_colourmap]

leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League 1', 'EFL2': 'EFL League 2'}

# %% Read in data

# Opta data

events_df = bz2.BZ2File(f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}/match-eventdata-{match_id}-{home_team}-{away_team}.pbz2", 'rb')
events_df = pickle.load(events_df)
players_df = bz2.BZ2File(f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}/match-playerdata-{match_id}-{home_team}-{away_team}.pbz2", 'rb')
players_df = pickle.load(players_df)

# %% Calculate Scoreline (special accounting for own goals)

if 'isOwnGoal' in events_df.columns:
    home_score = len(events_df[(events_df['teamId']==players_df['teamId'].unique()[0]) & (events_df['eventType'] == 'Goal') & (events_df['isOwnGoal'] != events_df['isOwnGoal'])])
    home_score += len(events_df[(events_df['teamId']==players_df['teamId'].unique()[1]) & (events_df['eventType'] == 'Goal') & (events_df['isOwnGoal'] == events_df['isOwnGoal'])])
    away_score = len(events_df[(events_df['teamId']==players_df['teamId'].unique()[1]) & (events_df['eventType'] == 'Goal') & (events_df['isOwnGoal'] != events_df['isOwnGoal'])])
    away_score += len(events_df[(events_df['teamId']==players_df['teamId'].unique()[0]) & (events_df['eventType'] == 'Goal') & (events_df['isOwnGoal'] == events_df['isOwnGoal'])])
else:
    home_score = len(events_df[(events_df['teamId']==players_df['teamId'].unique()[0]) & (events_df['eventType'] == 'Goal')])
    away_score = len(events_df[(events_df['teamId']==players_df['teamId'].unique()[1]) & (events_df['eventType'] == 'Goal')])

# %% Pre-process data

# Add cumulative minutes information
players_df = wde.minutes_played(players_df, events_df)

# Calculate longest consistent xi
players_df = wde.longest_xi(players_df)

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df)

# %% Create dataframes of defensive and offensive actions

defensive_actions_df = wde.find_defensive_actions(events_df)
offensive_actions_df = wde.find_offensive_actions(events_df)

# Initialise dataframes
defensive_hull_df = pd.DataFrame()
offensive_hull_df = pd.DataFrame()

# Create convex hull for each player
for player_id in players_df[players_df['longest_xi']==True].index:
    player_def_hull = wce.create_convex_hull(defensive_actions_df[defensive_actions_df['playerId'] == player_id], name=players_df.loc[player_id,'name'],
        min_events=5, include_events=central_pct_def, pitch_area = 10000)
    player_off_hull = wce.create_convex_hull(offensive_actions_df[offensive_actions_df['playerId'] == player_id], name=players_df.loc[player_id,'name'],
        min_events=5, include_events=central_pct_off, pitch_area = 10000)
    offensive_hull_df = pd.concat([offensive_hull_df, player_off_hull])
    defensive_hull_df = pd.concat([defensive_hull_df, player_def_hull])

# %% Create viz of area covered by each player when passing

plot_team = 'away'

# Plot pitches
pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=1, ncols=2, title_height=0.22,
                     grid_height=0.7, endnote_height=0.06, axis=False)
fig.set_size_inches(8.5, 7.5)
fig.set_facecolor('#313332')

# Initialise player position counts
cf_count = 0
cm_count = 0
cb_count = 0
last_idx = 0

# Team to plot
plot_team = home_team if plot_team == 'home' else away_team

# Plot attacking convex hulls
for hull_idx, hull_row in offensive_hull_df.iterrows():
    
    # Determine team the hull applies to
    if players_df[players_df['name']==hull_idx]['team'].values[0] == plot_team:
                    
        # Get player position and assign colour based on position
        position = players_df[players_df['name']==hull_idx]['position'].values
        if position in ['DR', 'DL', '']:
            hull_colour = 'lawngreen'
        elif position in ['MR', 'ML', 'AML', 'AMR', 'FWR', 'FWL']:
            hull_colour = 'deepskyblue'
        elif position in ['FW']:
            hull_colour = ['tomato', 'lightpink'][cf_count]
            cf_count+=1
        elif position in ['MC', 'DMC', 'AMC']:
            hull_colour = ['snow', 'violet', 'cyan', 'yellow'][cm_count]
            cm_count+=1
        elif position in ['DC']:
            hull_colour = ['tomato', 'gold', 'lawngreen'][cb_count]
            cb_count+=1
        else:
            hull_colour = 'lightpink'
            
        # Define text colour based on marker colour
        if hull_colour in ['snow', 'white']:
            text_colour = 'k'
        else:
            text_colour = 'w'
        
        # Player initials
        if len(hull_idx.split(' ')) == 1:
            initials = hull_idx.split(' ')[0][0:2]
        else:
            initials = hull_idx.split(' ')[0][0].upper() + hull_idx.split(' ')[1][0].upper()
        
        # Plot
        ax['pitch'][0].scatter(hull_row['hull_reduced_y'], hull_row['hull_reduced_x'], color=hull_colour, s=20, alpha = 0.3, zorder=2)
        plot_hull = pitch.convexhull(hull_row['hull_reduced_x'], hull_row['hull_reduced_y'])
        pitch.polygon(plot_hull, ax=ax['pitch'][0], facecolor=hull_colour, alpha=0.2, capstyle = 'round', zorder=1)
        pitch.polygon(plot_hull, ax=ax['pitch'][0], edgecolor=hull_colour, alpha=0.3, facecolor='none', capstyle = 'round', zorder=1)
        ax['pitch'][0].scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', color = hull_colour, alpha = 0.6, s = 400, zorder = 3)
        ax['pitch'][0].scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', edgecolor = hull_colour, facecolor = 'none', alpha = 1, lw = 2, s = 400, zorder = 3)
        ax['pitch'][0].text(hull_row['hull_centre'][1], hull_row['hull_centre'][0], initials, fontsize = 8, fontweight = 'bold', va = 'center', ha = 'center', color = text_colour, zorder = 4)

# Plot attacking convex hulls
cf_count = 0
cm_count = 0
cb_count = 0
last_idx = 0
for hull_idx, hull_row in defensive_hull_df.iterrows():
    
    # Determine team the hull applies to
    if players_df[players_df['name']==hull_idx]['team'].values[0] == plot_team:
                    
        # Get player position and assign colour based on position
        position = players_df[players_df['name']==hull_idx]['position'].values
        if position in ['DR', 'DL', '']:
            hull_colour = 'lawngreen'
        elif position in ['MR', 'ML', 'AML', 'AMR', 'FWR', 'FWL']:
            hull_colour = 'deepskyblue'
        elif position in ['FW']:
            hull_colour = ['tomato', 'lightpink'][cf_count]
            cf_count+=1
        elif position in ['MC', 'DMC', 'AMC']:
            hull_colour = ['snow', 'violet', 'cyan', 'yellow'][cm_count]
            cm_count+=1
        elif position in ['DC']:
            hull_colour = ['tomato', 'gold', 'lawngreen'][cb_count]
            cb_count+=1
        else:
            hull_colour = 'lightpink'
            
        # Define text colour based on marker colour
        if hull_colour in ['snow', 'white']:
            text_colour = 'k'
        else:
            text_colour = 'w'
        
        # Player initials
        if len(hull_idx.split(' ')) == 1:
            initials = hull_idx.split(' ')[0][0:2]
        else:
            initials = hull_idx.split(' ')[0][0].upper() + hull_idx.split(' ')[1][0].upper()
        
        # Plot
        ax['pitch'][1].scatter(hull_row['hull_reduced_y'], hull_row['hull_reduced_x'], color=hull_colour, s=20, alpha = 0.3, zorder=2)
        plot_hull = pitch.convexhull(hull_row['hull_reduced_x'], hull_row['hull_reduced_y'])
        pitch.polygon(plot_hull, ax=ax['pitch'][1], facecolor=hull_colour, alpha=0.2, capstyle = 'round', zorder=1)
        pitch.polygon(plot_hull, ax=ax['pitch'][1], edgecolor=hull_colour, alpha=0.3, facecolor='none', capstyle = 'round', zorder=1)
        ax['pitch'][1].scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', color = hull_colour, alpha = 0.6, s = 400, zorder = 3)
        ax['pitch'][1].scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', edgecolor = hull_colour, facecolor = 'none', alpha = 1, lw = 2, s = 400, zorder = 3)
        ax['pitch'][1].text(hull_row['hull_centre'][1], hull_row['hull_centre'][0], initials, fontsize = 8, fontweight = 'bold', va = 'center', ha = 'center', color = text_colour, zorder = 4)
          
# Ax titles
ax['pitch'][0].set_title(f"{plot_team} Offensive Shape", pad = 0, color = "w", fontweight = "bold")      
ax['pitch'][1].set_title(f"{plot_team} Defensive Shape", pad = 0, color = "w", fontweight = "bold")      

# Label based on include parameter
hull_include = central_pct_off.replace('std','') + ' Std. Dev' if 'std' in str(central_pct_off) else str(central_pct_off) + '%'
hull_include_s = central_pct_off.replace('std','') + ' SD' if 'std' in str(central_pct_off) else str(central_pct_off) + '%'

# Title text
title_text = f"{leagues[league]} - {year}/{int(year) + 1}" if not league in ['World_Cup'] else f"{leagues[league]} - {year}"
subtitle_text = f"{home_team_print} {home_score}-{away_score} {away_team_print}"
subsubtitle_text = f"Offensive and defensive territories, defined by central\n{hull_include} of offensive and defensive actions per player"

fig.text(0.5, 0.93, title_text, ha='center',
         fontweight="bold", fontsize=20, color='w')
fig.text(0.5, 0.882, subtitle_text, ha='center',
         fontweight="bold", fontsize=18, color='w')
fig.text(0.5, 0.82, subsubtitle_text, ha='center',
         fontweight="regular", fontsize=11, color='w')

# Add home team Logo
ax = fig.add_axes([0.07, 0.825, 0.14, 0.14])
ax.axis("off")
ax.imshow(home_logo)

# Add away team Logo
ax = fig.add_axes([0.79, 0.825, 0.14, 0.14])
ax.axis("off")
ax.imshow(away_logo)

# Add direction of play arrow
ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.arrow(0.65, 0.2, 0, 0.58, color="w", width=0.001, head_width = 0.1, head_length = 0.02)
ax.text(0.495, 0.48, "Direction of play", ha="center", va="center", fontsize=10, color="w", fontweight="regular", rotation=90)

# Footer text
fig.text(0.5, 0.035, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.875, 0.01, 0.07, 0.07])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save image
fig.savefig(f"shape_reports/{league}-{match_id}-{plot_team}-shape", dpi=300)