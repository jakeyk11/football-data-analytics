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
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
from datetime import datetime
import textwrap as tw
from mplsoccer import PyPizza
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.get_football_data as gfd
import analysis_tools.statsbomb_custom_events as sce
import analysis_tools.statsbomb_data_engineering as sde
import analysis_tools.logos_and_badges as lab

# %% User inputs

# Data to use
data_grab =[['England', 'Premier League', '2023']]

# %% Load data

# Statsbomb
data_dict = gfd.load_statsbomb_sql(data_grab, events=True, matches = True, lineups = True, player_stats=True)
events_df = data_dict['events']
matches_df = data_dict['matches']
lineups_df = data_dict['lineups']
playerstats_df = data_dict['player_stats']

# Logo
comp_logo = lab.get_competition_logo(data_grab[0][1], data_grab[0][2], logo_brighten=True)

# %% Error metrics

all_errors = events_df[events_df['type_name']=='Error']
events_following_error = pd.DataFrame()

for idx, error in all_errors.iterrows():
    
    error_evts = events_df[(events_df['match_id']==error['match_id']) &
                            (events_df['period']==error['period']) & 
                            (events_df['cumulative_mins'] >= error['cumulative_mins']) &
                            (events_df['cumulative_mins'] <= error['cumulative_mins'] + (15/60)) & 
                            (events_df['team_name']!=error['team_name'])]
    events_following_error = pd.concat([events_following_error, error_evts])
    
# %% Get team information

# Get team list
teaminfo_df = sde.create_team_list(lineups_df)

# In-play shots, goals and xG
shots_for = events_df[events_df['type_name']=='Shot']
ip_shots_for = shots_for[shots_for['in_play_event']==1]
ip_goals_for = pd.concat([ip_shots_for[ip_shots_for['outcome_name']=='Goal'], events_df[events_df['type_name']=='Own Goal For']])
teaminfo_df = sde.group_team_events(shots_for, teaminfo_df, group_type='sum', agg_columns ='shot_statsbomb_xg', primary_event_name = 'xg_for')
teaminfo_df = sde.group_team_events(ip_shots_for, teaminfo_df, group_type='sum', agg_columns ='shot_statsbomb_xg', primary_event_name = 'ip_xg_for')
teaminfo_df = sde.group_team_events(ip_goals_for, teaminfo_df, group_type='count', primary_event_name = 'ip_goals_for')

# In play offensive OBV
ip_obv_events = events_df[(events_df['type_name'].isin(['Pass','Carry','Dribble'])) &
                          (events_df['in_play_event']==1)]
teaminfo_df = sde.group_team_events(ip_obv_events, teaminfo_df, group_type='sum', agg_columns ='obv_for_net_z', primary_event_name = 'ip_xt_for')

# In-play shots, goals and xG against
for team_name, _ in teaminfo_df.iterrows():
    
    # Get matches and events by team
    match_ids = matches_df[(matches_df['home_team']==team_name) | (matches_df['away_team']==team_name)]['match_id'].tolist()
    team_match_evts = events_df[events_df['match_id'].isin(match_ids)]
    evts_against = team_match_evts[team_match_evts['team_name']!=team_name]
    shots_against = evts_against[evts_against['type_name']=='Shot']
    ip_shots_against = shots_against[shots_against['in_play_event']==1]
    ip_goals_against = pd.concat([ip_shots_against[ip_shots_against['outcome_name']=='Goal'], evts_against[evts_against['type_name']=='Own Goal For']])
    ip_obv_events_against = evts_against[(evts_against['type_name'].isin(['Pass','Carry','Dribble'])) &
                                         (evts_against['in_play_event']==1)]
    teaminfo_df.loc[team_name, 'xg_against'] = shots_against['shot_statsbomb_xg'].sum(numeric_only=True)
    teaminfo_df.loc[team_name, 'ip_xg_against'] = ip_shots_against['shot_statsbomb_xg'].sum(numeric_only=True)
    teaminfo_df.loc[team_name, 'ip_goals_against'] = len(ip_goals_against)    
    teaminfo_df.loc[team_name, 'ip_xt_against'] = ip_obv_events_against['obv_for_net_z'].sum(numeric_only=True)
    
    team_post_error_evts_against = events_following_error[(events_following_error['match_id'].isin(match_ids)) & (events_following_error['team_name']!=team_name)]
    post_error_shots_against = team_post_error_evts_against[(team_post_error_evts_against['type_name']=='Shot') & (team_post_error_evts_against['in_play_event']==1)] 
    teaminfo_df.loc[team_name, 'xg_against_following_error'] = post_error_shots_against['shot_statsbomb_xg'].sum(numeric_only=True)

teaminfo_df['non-error_ip_xg_against'] =  teaminfo_df['ip_xg_against'] - teaminfo_df['xg_against_following_error']
teaminfo_df['xg_difference'] =  teaminfo_df['xg_for'] - teaminfo_df['xg_against']
teaminfo_df['ip_xg_difference'] =  teaminfo_df['ip_xg_for'] - teaminfo_df['ip_xg_against']
teaminfo_df['ip_xg_xt_ratio'] =  teaminfo_df['ip_xg_for']/teaminfo_df['ip_xt_for']
teaminfo_df['ip_xg_xt_against_ratio'] =  teaminfo_df['ip_xg_against']/teaminfo_df['ip_xt_against']
teaminfo_df['ip_goal_xg_ratio'] =  teaminfo_df['ip_goals_for'] / teaminfo_df['ip_xg_for']
teaminfo_df['ip_goal_xg_against_ratio'] =  teaminfo_df['ip_goals_against'] / teaminfo_df['ip_xg_against']


ti = teaminfo_df[['ip_xg_xt_ratio','ip_goal_xg_ratio']]
ti['product'] = ti['ip_xg_xt_ratio'] * ti['ip_goal_xg_ratio']
ti['mean'] = (ti['ip_xg_xt_ratio'] + ti['ip_goal_xg_ratio'])/2
ti['h_mean'] = 1/((1/ti['ip_xg_xt_ratio']) + (1/ti['ip_goal_xg_ratio']))
# %% Normalise

for column in teaminfo_df.columns:
    
    if ('xg' in column or 'xt' in column) and ('ratio' not in column):
        teaminfo_df[column + '_90'] =  90*teaminfo_df[column] /  teaminfo_df['time_played']
        
# %% VISUAL 1: XG AND XT RATIO SCATTER

# rc params
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Metrics to plot
plot_y = ['ip_goal_xg_ratio']
plot_x = ['ip_xg_xt_ratio']

# Set up figure
fig, ax = plt.subplots(figsize = (8.5,9), facecolor = '#313332')
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)
#ax.set_position([0.1,0.15,0.8,0.65], which='both')

# Format axes
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_color('w')
ax.grid(color='gray', alpha = 0.2)

# Label axes
ax.set_ylabel("Ratio between In-Play Goals and Expected Goals (Goals/xG)", labelpad = 10, fontweight="bold", fontsize=12, color='w')
ax.set_xlabel("Ratio between In-Play Expected Goals and Expected Threat (xG/xT)", labelpad = 10, fontweight="bold", fontsize=12, color='w')

# Define axis limits
xmin = np.floor(10*teaminfo_df[plot_x].min())/10
xmax = np.ceil(10*teaminfo_df[plot_x].max())/10
ymin = np.floor(10*teaminfo_df[plot_y].min())/10
ymax = np.ceil(10*teaminfo_df[plot_y].max())/10
ax.set_xlim([xmin.values, xmax.values])
ax.set_ylim([ymin.values, ymax.values])

# Iterate through each team
for team, team_metrics in teaminfo_df.iterrows():
    
    # Get logo
    team_logo, _ = lab.get_team_badge_and_colour(team)
    
    # Plot logo
    ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.07, resample = True), (team_metrics[plot_x], team_metrics[plot_y]), frameon=False)    
    ax.add_artist(ab)
    
# %% VISUAL 2: XG AND XT RATIO TABLE

fig, ax = plt.subplots(figsize = (8,9.5), facecolor = '#313332')
ax.patch.set_alpha(0)

# Sort
teaminfo_df = teaminfo_df.sort_values('ip_xg_xt_ratio', ascending=False)

# Title
title_text = f"{data_grab[0][1]} {data_grab[0][2]}/{str(int(data_grab[0][2]) + 1).replace('20','',1)}"
subtitle_text = "Team Chance Creation Effectiveness and Chance Conversion Effectiveness" 
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.907, subtitle_text, fontweight="bold", fontsize=11, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.879, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Horizontal Header lines
ax.plot([0.05, 1], [0.995, 0.995], color='w', zorder = 3)
ax.plot([0, 1], [0.93, 0.93], color='w', zorder = 3)
ax.plot([0, 1], [-0.02, -0.02], color='w', zorder = 3)
ax.text(0.08, 0.96, "Team", ha = "left", va = "center", fontweight = "bold", color = "w")
ax.text(0.5875, 0.96, "Open-play\nxG/xT Ratio", ha = "center", va = "center", fontweight = "bold", color = "w")
ax.text(0.8625, 0.96, "Open-play\nGoals/xG Ratio", ha = "center", va = "center", fontweight = "bold", color = "w")

# Vertical Header lines
ax.plot([0.002, 0.002], [-0.02, 0.93], color='w', zorder = 2)
ax.plot([0.05, 0.05], [-0.02, 0.93], color='grey', lw =0.5, zorder = 2)
ax.plot([0.05, 0.05], [-0.02, 0.995], color='w', zorder = 2)
ax.plot([0.45, 0.45], [-0.02, 0.93], color='grey', lw =0.5, zorder = 2)
ax.plot([0.45, 0.45], [0.93, 0.995], color='w', lw =0.5, zorder = 2)
ax.plot([0.725, 0.725], [-0.02, 0.93], color='grey', lw =0.5, zorder = 2)
ax.plot([0.725, 0.725], [0.93, 0.995], color='w', lw =0.5, zorder = 2)
ax.plot([0.999, 0.999], [-0.02, 0.995], color='w', zorder = 2)

# Iterate through each team
idx = 0
for team, team_metrics in teaminfo_df.iterrows():
    
    # Plot team name and badge
    ax.text(0.025 ,0.9*(1-idx/19), idx+1, va="center", ha = "center", color = "w" )
    ax.text(0.11 ,0.9*(1-idx/19), team, va="center", color = "w" )
    team_logo, _ = lab.get_team_badge_and_colour(team)
    ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.06, resample = True), (0.08,0.9*(1-idx/19)+0.003), frameon=False)    
    ax.add_artist(ab)

    # Plot metrics
    ax.text(0.5875 ,0.9*(1-idx/19), round(team_metrics['ip_xg_xt_ratio'],2), va="center", ha = "center", color = "w" )
    ax.text(0.8625 ,0.9*(1-idx/19), round(team_metrics['ip_goal_xg_ratio'],2), va="center", ha = "center", color = "w" )

    # Plot hline
    ax.plot([0, 1], [0.9*(1-idx/19)-0.02, 0.9*(1-idx/19)-0.02], color='grey', lw = 0.5, zorder = 1)
  
    idx+=1

# Format axis
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['bottom'].set_visible(False)  
ax.spines['left'].set_visible(False)
ax.set_xticks([])
ax.set_yticks([])
ax.yaxis.label.set_color('w')
ax.set_position([0.1,0.06,0.8,0.81], which='both')
ax.set_xlim([0,1])
ax.set_ylim([-0.03,1])

# Create footer
fig.text(0.5, 0.024, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.94, 0.007, 0.05, 0.05])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

fig.savefig(f"team_xg_metrics/{data_grab[0][1].replace(' ','-').lower()}-{data_grab[0][2]}-xg-xt-table", dpi=300)