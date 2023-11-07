# %% Imports

import pandas as pd
import bz2
import os
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import numpy as np
import time
from mplsoccer import Pitch, VerticalPitch
import matplotlib.patheffects as path_effects  
import matplotlib as mpl
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Rectangle
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
from datetime import datetime
import textwrap as tw
from mplsoccer import PyPizza

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.get_football_data as gfd
import analysis_tools.statsbomb_custom_events as sce
import analysis_tools.statsbomb_data_engineering as sde
import analysis_tools.logos_and_badges as lab
import analysis_tools.models as mod

# %% User inputs

# Data to use
data_grab =[['England', 'Premier League', '2023']]

# Run date
run_date = '07-11-23'

# %% Load data

# Statsbomb
data_dict = gfd.load_statsbomb_sql(data_grab, events=True, matches = True, lineups = True, player_stats=True)
events_df = data_dict['events']
matches_df = data_dict['matches']
lineups_df = data_dict['lineups']
playerstats_df = data_dict['player_stats']

# %% Simulate match outcomes

sim_count = 200000
for match_id in matches_df['match_id'].values:
    matches_df, match_simulation_df = mod.simulate_match_outcome(events_df, matches_df, match_id, sim_count=200000)

# %% Generate league table

leaguetable_df = sde.create_league_table(matches_df, xmetrics=True)

# %% Plot league table

fig = plt.figure(figsize=(9,10), facecolor='#333332')

ax = fig.add_axes([0.05,0.075,0.9,0.8])
ax.patch.set_alpha(0)

# Set up plotting parameters
header_height = 0.07
row_height = (1 - header_height)/len(leaguetable_df)

# Horizontal Header lines abd shading
ax.plot([0, 1], [0.998, 0.998], color='darkgrey', zorder = 3, lw=0.5)
ax.plot([0, 1], [1-header_height, 1-header_height], color='darkgrey', zorder = 3, lw=0.5)
ax.add_patch(Rectangle([0, 1-header_height], 1, header_height-0.002, color = '#262625'))

# Header titles
ax.text(0.04, 0.998 -header_height/2, "Team Name", ha = "left", va = "center_baseline", fontweight = "bold", color = "w")
ax.text(0.39, 0.998 -header_height/2, "MP", ha = "center", va = "center_baseline", fontweight = "bold", color = "w")
ax.text(0.455, 0.998 -header_height/2, "Pts", ha = "center", va = "center_baseline", fontweight = "bold", color = "w")
ax.text(0.55, 0.998 -header_height/2, "xPts", ha = "center", va = "center_baseline", fontweight = "bold", color = "w")
ax.text(0.645, 0.998 -header_height/2, "G", ha = "center", va = "center_baseline", fontweight = "bold", color = "w")
ax.text(0.74, 0.998 -header_height/2, "xG", ha = "center", va = "center_baseline", fontweight = "bold", color = "w")
ax.text(0.835, 0.998 -header_height/2, "GA", ha = "center", va = "center_baseline", fontweight = "bold", color = "w")
ax.text(0.935, 0.998 -header_height/2, "xGA", ha = "center", va = "center_baseline", fontweight = "bold", color = "w")
#ax.text(0.97, 0.998 -header_height/2, "Actual\nPos", ha = "center", va = "center_baseline", fontweight = "bold", color = "w")

# Iterate over league table to position rows, icons and text
for idx, table_team in leaguetable_df.iterrows():
    
    pos = table_team['expected_position']
    
    # Add bottom horizontal line
    row_bottom = 1-header_height-row_height*pos
    row_centre = row_bottom + row_height/2
    ax.plot([0, 1], [row_bottom, row_bottom], color='darkgrey', lw = 0.5, zorder = 3)

    # Add position
    ax.text(0.02, row_centre, pos, ha = "center", va = "center_baseline", color = "w")

    # Add logo
    team_logo, _ = lab.get_team_badge_and_colour(table_team['team'])
    ab = AnnotationBbox(OffsetImage(team_logo, zoom = 1/len(leaguetable_df)+0.01, resample = True), (0.075,row_centre), frameon=False)    
    ax.add_artist(ab)

    # Add information
    ax.text(0.095, row_centre, table_team['team'], ha = "left", va = "center_baseline", color = "w")
    ax.text(0.39, row_centre, int(table_team['matches_played']), ha = "center", va = "center_baseline", color = "w")
    ax.text(0.455, row_centre, int(table_team['points']), ha = "center", va = "center_baseline", color = "w")
    ax.text(0.535, row_centre, f"{table_team['expected_points']:.2f}", ha = "center", va = "top", color = "w")
    ax.text(0.645, row_centre, int(table_team['goals_for']), ha = "center", va = "center_baseline", color = "w")
    ax.text(0.725, row_centre, f"{table_team['xg_for']:.2f}", ha = "center", va = "top", color = "w")
    ax.text(0.835, row_centre, int(table_team['goals_against']), ha = "center", va = "center_baseline", color = "w")
    ax.text(0.92, row_centre, f"{table_team['xg_against']:.2f}", ha = "center", va = "top", color = "w")
    #ax.text(0.97, row_centre, int(table_team['position']), ha = "center", va = "center_baseline", color = "w")

    # Add differences
    xg_delta_str = '+' if table_team['xg_for'] > table_team['goals_for'] else ''
    xg_col = 'green' if xg_delta_str == '+' else 'indianred'
    xga_delta_str = '+' if table_team['xg_against'] > table_team['goals_against'] else ''
    xga_col = 'green' if xga_delta_str == '' else 'indianred'
    xgd_delta_str = '+' if table_team['xg_difference'] > table_team['goal_difference'] else ''
    xgd_col = 'green' if xgd_delta_str == '+' else 'indianred'
    xp_delta_str = '+' if table_team['expected_points'] > table_team['points'] else ''
    xp_col = 'green' if xp_delta_str == '+' else 'indianred'
    xpos_delta_str = '+' if table_team['position'] > table_team['expected_position'] else ''
    xpos_col = 'green' if table_team['expected_position'] < table_team['position'] else 'w' if table_team['expected_position'] == table_team['position'] else 'indianred'

    ax.text(0.04, row_centre, f"{xpos_delta_str}{table_team['position']-table_team['expected_position']}", ha = "center", va = "bottom", fontweight = "bold", color = xpos_col, fontsize=7)
    ax.text(0.575, row_centre, f"{xp_delta_str}{(table_team['expected_points']-table_team['points']):.2f}", ha = "center", va = "bottom", color = xp_col, fontsize=7)
    ax.text(0.765, row_centre, f"{xg_delta_str}{(table_team['xg_for']-table_team['goals_for']):.2f}", ha = "center", va = "bottom", color = xg_col, fontsize=7)
    ax.text(0.96, row_centre, f"{xga_delta_str}{(table_team['xg_against']-table_team['goals_against']):.2f}", ha = "center", va = "bottom", color = xga_col, fontsize=7)
    
    # Add intermittent shading
    if pos % 2 == 0:
        ax.add_patch(Rectangle([0, row_bottom], 1, row_height, color = '#262625'))
        
# Remove axis spines
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['bottom'].set_visible(False)  
ax.spines['left'].set_visible(False)
ax.set_xticks([])
ax.set_yticks([])

# Enforce axis limits
ax.set_xlim([0,1])
ax.set_ylim([0,1])

# Add legend
legend_ax = fig.add_axes([0.72, 0.88, 0.24, 0.1])
legend_ax.add_patch(Rectangle([0.15, 0.65], 0.055, 0.12, color = 'g'))
legend_ax.text(0.24, 0.72, "Expected metric stronger than\nactual outcome", color = "w", va = "center_baseline", fontsize=7)
legend_ax.add_patch(Rectangle([0.15, 0.3], 0.055, 0.12, color = 'indianred'))
legend_ax.text(0.24, 0.37, "Expected metric weaker than\nactual outcome", color = "w", va = "center_baseline", fontsize=7)
legend_ax.axis("off")


# Add title and logo
title_text = f"{data_grab[0][1]} {data_grab[0][2]}/{str(int(data_grab[0][2]) + 1).replace('20','',1)} − Justice League"
subtitle_text = "League Table Standings based on Expected Points" 
fig.text(0.12, 0.94, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.915, subtitle_text, fontweight="bold", fontsize=11, color='w')

# Add competition logo
comp_logo = lab.get_competition_logo(data_grab[0][1], data_grab[0][2], logo_brighten=True)
comp_ax = fig.add_axes([0.022, 0.885, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Add description
fig.text(0.5, 0.045, f"Monte Carlo method implemented to model the probability of individual match outcomes based on shot events, with {sim_count} repetitions completed per match. Expected\n"+
         "points calculated using weighted outcome probabilities. Method reliant on assumption that xG represents scoring probability, and that individual shot events are independent.",
         color = 'lightgrey', fontsize = 6.5, ha = "center")
         
# Add footer information
fig.text(0.5, 0.012, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.94, 0.001, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

# Save fig
fig.savefig(f"justice_league/{data_grab[0][1].replace(' ','-').lower()}-{data_grab[0][2]}-justice-league-{run_date}.png", dpi=300)