# %% Create defensive positions and defensive line report
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Whoscored match id
#           Home team
#           Away team
#           Convex hull actions to include
#           Team to analyse
#
# Outputs:  Defensive line report

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image, ImageEnhance
from mplsoccer.pitch import VerticalPitch
import os
import sys
import bz2
import pickle
import numpy as np
from collections import Counter
import highlight_text as htext

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
match_id = '1632096'

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'World_Cup'

# Select team codes
home_team = 'Argentina'
away_team = 'Saudi Arabia'

# Team name to print
home_team_print = None
away_team_print = None

# Pass flow zone type
analysis_team = 'away'

# Pass hull inclusion
central_pct = '1std'

# All goals or goals scored
all_goals = False

# %% Logos, colours and printed names

analysis_team = home_team if analysis_team == 'home' else away_team

home_logo, _ = lab.get_team_badge_and_colour(home_team)
away_logo, _ = lab.get_team_badge_and_colour(away_team)

if home_team_print is None:
    home_team_print = home_team

if away_team_print is None:
    away_team_print = away_team

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

analysis_team_id = np.unique(players_df[players_df['team']==analysis_team]['teamId'].tolist())[0]

# Add pass recipient
events_df = wde.get_recipient(events_df)

# Add cumulative mins
events_df = wde.cumulative_match_mins(events_df)

# Add cumulative minutes information
players_df = wde.minutes_played(players_df, events_df)

# Calculate longest consistent xi
players_df = wde.longest_xi(players_df)

playerinfo_df = wde.create_player_list(players_df)

# %% Get defender ids

fb_player_ids = playerinfo_df[(playerinfo_df['pos_type']=='DEF') & (playerinfo_df['position']!='DC') & (playerinfo_df['team']==analysis_team)].index.tolist()
cb_player_ids = playerinfo_df[(playerinfo_df['position']=='DC') & (playerinfo_df['team']==analysis_team)].index.tolist()

# %% Get all events between goals

goal_mins = events_df[(events_df['eventType']=='Goal') & (events_df['teamId']==analysis_team_id)]['cumulative_mins']
goal_mins = goal_mins.drop(goal_mins.index.values[0]).tolist()
events_between_goals = list(np.zeros(len(goal_mins)+1))

for idx in np.arange(len(goal_mins)):
    
    if idx == 0:
        events_between_goals[idx] = events_df[events_df['cumulative_mins']<goal_mins[idx]]
        events_between_goals[idx+1] = events_df[(events_df['cumulative_mins']>goal_mins[idx])]   
    elif idx == len(goal_mins)-1:
        events_between_goals[idx] = events_df[(events_df['cumulative_mins']<goal_mins[idx]) & (events_df['cumulative_mins']>goal_mins[idx-1])]
        events_between_goals[idx+1] = events_df[(events_df['cumulative_mins']>goal_mins[idx])]   
    else:
        events_between_goals[idx] = events_df[(events_df['cumulative_mins']<goal_mins[idx]) & (events_df['cumulative_mins']>goal_mins[idx-1])]

# %% Defensive actions between goals

def_action_beteen_goals = list(np.zeros(len(goal_mins)+1))
def_line_heights = list(np.zeros(len(goal_mins)+1))
def_cvx_hulls = list(np.zeros(len(goal_mins)+1))

for idx, events in enumerate(events_between_goals):
    fb_evts = events[events['playerId'].isin(fb_player_ids)]
    cb_evts = events[events['playerId'].isin(cb_player_ids)]
    cb_def_action_heights = cb_evts['x']
    num_stds = float(central_pct.split('std')[0])
    sqrt_variance_dh = np.sqrt(sum((cb_def_action_heights - np.mean(cb_def_action_heights))**2) /
                              (len(cb_def_action_heights) - 1))
    def_line_event_heights = np.array(cb_def_action_heights)[abs(cb_def_action_heights -
                                                                      np.mean(cb_def_action_heights)) <= sqrt_variance_dh * num_stds]
    def_line_heights[idx] = np.median(def_line_event_heights)
    
    cvx_hulls = pd.DataFrame()
    for player_id in fb_player_ids + cb_player_ids:
        player_hull = wce.create_convex_hull(events[events['playerId'] == player_id], name=players_df.loc[player_id,'name'],
            min_events=4, include_events=central_pct, pitch_area = 10000)
        cvx_hulls = pd.concat([cvx_hulls, player_hull])

    def_cvx_hulls[idx] = cvx_hulls

# %% Plot convex hulls

pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=1, ncols=2, title_height=0.17,
                     grid_height=0.75, endnote_height=0, space = 0.1, axis=False)
fig.set_size_inches(8.5, 8.5)
fig.set_facecolor('#313332')

ax['title'].text(0.22, -0.3, "Defender Actions when Losing or Drawing",  va='center', ha='center', fontsize = 10, fontweight = "bold")
ax['title'].text(0.78, -0.3, "Defender Actions when Winning",  va='center', ha='center', fontsize = 10, fontweight = "bold")

cb_count = 0
fb_count = 0
for hull_idx, hull_row in def_cvx_hulls[0].iterrows():
    
    player_pos = players_df[players_df['name']==hull_idx]['position'].values
    
    if player_pos in ['DR', 'DL', '']:
        hull_colour = ['lawngreen', 'cyan'][fb_count]
        fb_count+=1
    elif player_pos in ['DC']:
        hull_colour = ['tomato', 'gold', 'lawngreen'][cb_count]
        cb_count+=1 
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
  
cb_count = 0
fb_count = 0
for hull_idx, hull_row in def_cvx_hulls[1].iterrows():
    
    player_pos = players_df[players_df['name']==hull_idx]['position'].values
    
    if player_pos in ['DR', 'DL', '']:
        hull_colour = ['lawngreen', 'cyan'][fb_count]
        fb_count+=1
    elif player_pos in ['DC']:
        hull_colour = ['tomato', 'gold', 'lawngreen'][cb_count]
        cb_count+=1 
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

# Draw median defensive line height
pitch.lines(def_line_heights[0], 0, def_line_heights[0], 100, lw = 1, color = 'w', ls=':', zorder=1, ax=ax['pitch'][0])
pitch.arrows(1, -2.5, def_line_heights[0]-1, -2.5, width = 0.5, headwidth=12, headlength=12, color = 'w', zorder=5, ax=ax['pitch'][0])
pitch.lines(0, 0, 0, -4, lw = 0.5, color = 'w', ls='-', zorder=5, ax=ax['pitch'][0])
pitch.lines(def_line_heights[0], -0.5, def_line_heights[0], -4, lw = 0.5, color = 'w', ls='-', zorder=5, ax=ax['pitch'][0])

# Add axis adjacent to pitch to label median defensive line height
lineheight_ax = fig.add_axes([ax['pitch'][0].get_position().x0 + ax['pitch'][0].get_position().width - 0.01, ax['pitch'][0].get_position().y0 + 0.009, 0.06, ax['pitch'][0].get_position().height - 0.009 - 0.009])
lineheight_ax.axis("off")
def_line_height_pct = round(100*def_line_heights[0]/100,1)
if def_line_height_pct < 12:
    y_pos = 0.12
else:
    y_pos = (def_line_height_pct/2)/100
lineheight_ax.text(0.24, y_pos, f"{def_line_height_pct}% up pitch",
                       color = 'w', rotation=270, va='center', ha = 'center', fontsize=10)    

# Draw median defensive line height
pitch.lines(def_line_heights[1], 0, def_line_heights[1], 100, lw = 1, color = 'w', ls=':', zorder=1, ax=ax['pitch'][1])
pitch.arrows(1, 102.5, def_line_heights[1]-1, 102.5, width = 0.5, headwidth=12, headlength=12, color = 'w', zorder=5, ax=ax['pitch'][1])
pitch.lines(0, 100, 0, 104, lw = 0.5, color = 'w', ls='-', zorder=5, ax=ax['pitch'][1])
pitch.lines(def_line_heights[1], 100.5, def_line_heights[1], 104, lw = 0.5, color = 'w', ls='-', zorder=5, ax=ax['pitch'][1])

# Add axis adjacent to pitch to label median defensive line height
lineheight_ax = fig.add_axes([ax['pitch'][1].get_position().x0 -0.02, ax['pitch'][1].get_position().y0 + 0.009, 0.06, ax['pitch'][1].get_position().height - 0.009 - 0.009])
lineheight_ax.axis("off")
def_line_height_pct = round(100*def_line_heights[1]/100,1)
if def_line_height_pct < 12:
    y_pos = 0.12
else:
    y_pos = (def_line_height_pct/2)/100
lineheight_ax.text(0.24, y_pos, f"{def_line_height_pct}% up pitch",
                       color = 'w', rotation=90, va='center', ha = 'center', fontsize=10)    

# Title text
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'FIFA World Cup'}

title_text = f"{leagues[league]} - {year}/{int(year) + 1}" if not league in ['World_Cup'] else f"{leagues[league]} − {year}"
subtitle_text = f"<{home_team_print} {home_score}>-{away_score} {away_team_print}"
subsubtitle_text = f"{analysis_team} − Defensive Positioning and\nHeight of Defender Actions"

fig.text(0.5, 0.91, title_text, ha='center',
         fontweight="bold", fontsize=20, color='w')
htext.fig_text(0.5, 0.892, s=subtitle_text, ha='center', fontweight="bold", fontsize=18, color='w', highlight_textprops=[{"color": 'grey', "fontweight": 'bold'}])
fig.text(0.5, 0.813, subsubtitle_text, ha='center',
         fontweight="regular", fontsize=13, color='w')

# Add home team Logo
ax = fig.add_axes([0.07, 0.805, 0.14, 0.14])
ax.axis("off")
ax.imshow(home_logo.convert('LA'))

# Add away team Logo
ax = fig.add_axes([0.79, 0.805, 0.14, 0.14])
ax.axis("off")
ax.imshow(away_logo)

# Footer text
fig.text(0.5, 0.035, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.875, 0.01, 0.07, 0.07])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save
fig.savefig(f"misc_work_images/saudi-argentina-world-cup-def-pos", dpi=500)
