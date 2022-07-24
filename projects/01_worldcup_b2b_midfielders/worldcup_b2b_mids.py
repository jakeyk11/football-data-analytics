# %% Analysis of Box to Box Midfielders in the 2018 World Cup
#    
# Inputs:   Single dataframe of all World Cup events as .pbz2 compressed pickle
#           Single dataframe of all World Cup lineups as .pbz2 compressed pickle
#  
# Outputs:  Top 12 midfielders by progressive passes per. 90, including pass-maps.
#           Scatter plot of % passes played under pressure vs. pressure pass success %, including all midfielders.
#           Top 12 midfielders by pressures applied per. 100 opposition passes, including pressure heat-maps.
#           Scatter plot of recoveries per 100 opp. passes vs. tackles + interceptions per 100 opp. passes.
#           Top 12 midfielders by sum of areas of offensive and defensive action convex hulls
#           Top 12 midfielders by area of offensive action convex hull
#           Top 12 midfielders by area of defensive action convex hull
#           Dataframe of ball winning, creativity, mobility, and overall scores for each midfielder.
#           Radar plot of chosen midfielder.
#
# Notes: None

# %% Imports

import os
import sys
import pickle
import bz2
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from mplsoccer.pitch import Pitch
import matplotlib.pyplot as plt
import matplotlib as mpl
import highlight_text as htext
import adjustText
from textwrap import wrap
from PIL import Image
import requests
from io import BytesIO

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.statsbomb_data_engineering as sde
import analysis_tools.statsbomb_custom_events as sce

# %% Read in data

# Statsbomb data
events = bz2.BZ2File('../../data_directory/statsbomb_data/fifa-world-cup-2018-eventdata.pbz2', 'rb')
events = pickle.load(events)
lineups = bz2.BZ2File('../../data_directory/statsbomb_data/fifa-world-cup-2018-lineupdata.pbz2', 'rb')
lineups = pickle.load(lineups)

# Misc data
dist_covered = pd.read_excel('../../data_directory/misc_data/worldcup_2010_to_2018_distcovered.xlsx',
                             sheet_name='2018 Mids')

# %% Pre-process data

# Add cumulative minutes information
events, lineups = sde.cumulative_match_mins(events, lineups)

# Add player nickname 
events, lineups = sde.add_player_nickname(events, lineups)

# Add number of opposition passes while each player is on the pitch, for each match
lineups = sde.events_while_playing(events, lineups, event_name='Pass', event_team='opposition')

# %% Add custom event types that require time-based and complete event information, using analysis_tools package

# Pre-assists
events = sce.pre_assist(events)

# xg assisted
events = sce.xg_assisted(events)

# %% Create player information dataframe

playerinfo_df = sde.create_player_list(lineups, additional_cols=['mins_played', 'opp_pass'])

# %% Filter dataframe

# Specify box to box positions
midfielder_pos = ['Left Center Midfield', 'Center Midfield', 'Right Center Midfield',
                  'Center Defensive Midfield', 'Left Defensive Midfield', 'Right Defensive Midfield']

# Specify minimum minutes player must play in total to qualify for analysis
minimum_mins = 180

# Filter player information dataframe based on position and minutes
playerinfo_df = playerinfo_df[(playerinfo_df['mins_played'] >= minimum_mins) &
                              (playerinfo_df['player_name'].isin(
                                  events[events['position'].isin(midfielder_pos)]['player']))]

# Filter events dataframe based on players remaining in player information dataframe, and only include events whilst
# players played in midfield
midfielder_events = events[
    (events['player'].isin(playerinfo_df['player_name'])) & (events['position'].isin(midfielder_pos))]

# %% Add custom event types that do not require time-based event information

# Passes into the box
midfielder_events.loc[:, 'pass_into_box'] = midfielder_events.apply(sce.pass_into_box, axis=1)

# Progressive passes
midfielder_events.loc[:, 'progressive_pass'] = midfielder_events.apply(sce.progressive_pass, axis=1)

# %% Aggregate event information and add to player information dataframe

# Passes
passes = midfielder_events[midfielder_events['type'] == 'Pass']
successful_passes = passes[passes['pass_outcome'] != passes['pass_outcome']]
playerinfo_df = sde.group_player_events(passes, playerinfo_df,
                                        event_types=['pre_assist', 'pass_into_box', 'progressive_pass',
                                                     'under_pressure', 'pass_goal_assist'], primary_event_name='passes')
playerinfo_df = sde.group_player_events(passes, playerinfo_df, group_type='sum', event_types=['xg_assisted'])
playerinfo_df = sde.group_player_events(successful_passes, playerinfo_df, event_types=['under_pressure'],
                                        primary_event_name='successful_passes')

# Shots
shots = midfielder_events[(midfielder_events['type'] == 'Shot') & (midfielder_events['shot_type'] != 'Penalty')]
playerinfo_df = sde.group_player_events(shots, playerinfo_df, group_type='sum', event_types=['shot_statsbomb_xg'])

# Pressures
pressures = midfielder_events[midfielder_events['type'] == 'Pressure']
playerinfo_df = sde.group_player_events(pressures, playerinfo_df, primary_event_name='pressures')

# Tackles
tackles = midfielder_events[(midfielder_events['type'] == 'Duel') & (midfielder_events['duel_type'] != 'Tackle')]
playerinfo_df = sde.group_player_events(tackles, playerinfo_df, primary_event_name='tackles')

# Interceptions
interceptions = midfielder_events[
    (midfielder_events['type'] == 'Interception') & (midfielder_events['interception_outcome'] != 'Lost')]
playerinfo_df = sde.group_player_events(interceptions, playerinfo_df, primary_event_name='interceptions')

# Recoveries
recoveries = midfielder_events[
    (midfielder_events['type'] == 'Ball Recovery') & (midfielder_events['ball_recovery_recovery_failure'] != True)]
playerinfo_df = sde.group_player_events(recoveries, playerinfo_df, primary_event_name='recoveries')

# Distance covered / 90
playerinfo_df = playerinfo_df.merge(dist_covered, left_on='player_name', right_on='Midfielders', how='outer').drop(
    'Midfielders', axis=1)

# %% Normalise information and calculate additional metrics

# Per 90 minutes
for normalised_col in ['progressive_pass', 'pass_into_box', 'pass_goal_assist', 'pre_assist', 'passes',
                       'successful_passes', 'xg_assisted', 'shot_statsbomb_xg']:
    playerinfo_df[normalised_col + '_90'] = round(90 * playerinfo_df[normalised_col] / playerinfo_df['mins_played'], 2)

# Per 100 opposition passes
for normalised_col in ['pressures', 'tackles', 'interceptions', 'recoveries']:
    playerinfo_df[normalised_col + '_100pass'] = round(100 * playerinfo_df[normalised_col] / playerinfo_df['opp_pass'],
                                                       2)

# Percentage-based info
playerinfo_df['successful_passes_%'] = round(100 * (playerinfo_df['successful_passes'] / playerinfo_df['passes']), 0)
playerinfo_df['pass_under_pressure_%'] = round(100 * (playerinfo_df['under_pressure_x'] / playerinfo_df['passes']), 0)
playerinfo_df['pressure_pass_success_%'] = round(
    100 * (playerinfo_df['under_pressure_y'] / playerinfo_df['under_pressure_x']), 0)
playerinfo_df['xGC_90'] = playerinfo_df['shot_statsbomb_xg_90'] + playerinfo_df['xg_assisted_90']

# %% Filter players out who have made a low number of passes, and create list of player in analysis

playerinfo_df = playerinfo_df[playerinfo_df['passes_90'] >= 20]
players_considered = set(playerinfo_df['player_nickname'])

# %% Defensive and offensive actions

defensive_actions_df = sde.find_defensive_actions(midfielder_events)
offensive_actions_df = sde.find_offensive_actions(midfielder_events)

# %% Create convex hulls of defensive and offensive actions

# Initialise dataframes
defensive_hull_df = pd.DataFrame()
offensive_hull_df = pd.DataFrame()

# Create convex hull for each player
for player_choice in players_considered:

    player_def_hull = sce.create_convex_hull(
        defensive_actions_df[defensive_actions_df['player_nickname'] == player_choice], name=player_choice,
        include_percent=75)
    player_off_hull = sce.create_convex_hull(
        offensive_actions_df[offensive_actions_df['player_nickname'] == player_choice], name=player_choice,
        include_percent=75)

    # Include players with over 50 defensive actions 
    if len(player_def_hull['hull_x'].values[0]) >= 50:
        defensive_hull_df = pd.concat([defensive_hull_df, player_def_hull])

    # Include players with over 100 offensive actions 
    if len(player_off_hull['hull_x'].values[0]) >= 100:
        offensive_hull_df = pd.concat([offensive_hull_df, player_off_hull])

# Join offensive and defensive hulls
hull_df = defensive_hull_df.merge(offensive_hull_df, left_index=True, right_index=True, suffixes=('_def', '_off'))

# Total hull area
hull_df['hull_area_tot'] = hull_df['hull_area_def'] + hull_df['hull_area_off']

# Add to relevant columns to player information
playerinfo_df = playerinfo_df.merge(hull_df[['hull_area_%_def', 'hull_area_%_off', 'hull_area_tot']],
                                    left_on='player_name', right_index=True, how='left')

# %% Score creativity

playerscore_df = pd.DataFrame()
playerscore_df[['player_name', 'player_nickname']] = playerinfo_df[['player_name', 'player_nickname']]

scaler = MinMaxScaler()
playerscore_df[['progressive_pass_90', 'xGC_90', 'pressure_pass_success_%', 'xg_assisted_90', 'shot_statsbomb_xg_90',
                'successful_passes_%']] = scaler.fit_transform(playerinfo_df[['progressive_pass_90', 'xGC_90',
                                                                              'pressure_pass_success_%',
                                                                              'xg_assisted_90', 'shot_statsbomb_xg_90',
                                                                              'successful_passes_%']])
playerscore_df['creativity'] = playerscore_df[['progressive_pass_90', 'xGC_90', 'pressure_pass_success_%']].sum(
    axis=1) / 3

# %% Score ball winning

playerscore_df[
    ['pressures_100pass', 'tackles_100pass', 'interceptions_100pass', 'recoveries_100pass']] = scaler.fit_transform(
    playerinfo_df[['pressures_100pass', 'tackles_100pass', 'interceptions_100pass', 'recoveries_100pass']])
playerscore_df['ball_winning'] = playerscore_df[['pressures_100pass', 'tackles_100pass', 'interceptions_100pass',
                                                 'recoveries_100pass']].sum(axis=1) / 4

# %% Score mobility

playerscore_df[['Distance', 'hull_area_%_off', 'hull_area_%_def']] = scaler.fit_transform(
    playerinfo_df[['Distance', 'hull_area_%_off', 'hull_area_%_def']])
playerscore_df['mobility'] = playerscore_df[['Distance', 'hull_area_%_off', 'hull_area_%_def']].sum(axis=1) / 3

# %% Score overall

playerscore_df['total'] = ((4 / 9) * playerscore_df['creativity'] + (2 / 9) * playerscore_df['ball_winning'] + (3 / 9) *
                           playerscore_df['mobility'])

# %% Plot 1, plot top 12 midfielders by number of progressive passes per 90 minutes.

competition = 'FIFA World Cup'
year = 2018

# Isolate all progressive passes, assists and pre-assists (not from set-pieces)
passes_to_plot = midfielder_events[((midfielder_events['progressive_pass'] == True) |
                                    (midfielder_events['pass_goal_assist'] == True) |
                                    (midfielder_events['pre_assist'] == True)) &
                                   (~midfielder_events['pass_type'].isin(['Corner', 'Free Kick', 'Throw-in']))]

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.75, space=0.12, axis=False)
fig.set_size_inches(14, 9)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Plot successful prog passes as arrows, using for loop to iterate through each player and each pass

idx = 0
sorted_df = playerinfo_df.sort_values('progressive_pass_90', ascending=False)
for _, name in sorted_df.head(12).iterrows():
    player_passes = passes_to_plot[passes_to_plot['player'] == name['player_name']]
    ax['pitch'][idx].title.set_text(f"{idx + 1}: {name['player_nickname']}")
    ax['pitch'][idx].title.set_color('w')
    for i, pass_event in player_passes.iterrows():
        x = pass_event['location'][0]
        y = pass_event['location'][1]
        dx = pass_event['pass_end_location'][0] - x
        dy = pass_event['pass_end_location'][1] - y
        if pass_event['pass_goal_assist'] == True:
            ax['pitch'][idx].arrow(x, y, dx, dy, head_width=2, color='red', zorder=3)
        elif pass_event['pre_assist'] == True:
            ax['pitch'][idx].arrow(x, y, dx, dy, head_width=2, color='yellow', zorder=2)
        else:
            ax['pitch'][idx].arrow(x, y, dx, dy, head_width=2, color='orange', zorder=1)
    ax['pitch'][idx].text(3, 71, "Total:", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(25, 71, f"{name['progressive_pass']}", fontsize=8, color='w', zorder=3)
    ax['pitch'][idx].text(3, 77, "Per 90:", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(25, 77, f"{round(name['progressive_pass_90'], 1)}", fontsize=8, color='w', zorder=3)
    idx += 1

# Create title and subtitles, using highlighting as figure legend
title_text = "Top 12 Midfielders, ranked by number of progressive passes per 90 minutes"
subtitle_text = f"{competition} {year} - <Progressive passes>, <Assists> and <Pre-Assists>"
subsubtitle_text = "Players with total game\ntime below 180 minutes\nare not considered. Set\npieces are excluded."
fig.text(0.11, 0.93, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.11, 0.915, s=subtitle_text, fontweight="regular", fontsize=14, color='w',
               highlight_textprops=[{"color": 'orange', "fontweight": 'bold'}, {"color": 'red', "fontweight": 'bold'},
                                    {"color": 'yellow', "fontweight": 'bold'}])
fig.text(0.85, 0.895, subsubtitle_text, fontsize=9, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.05, 0.18, 0.01])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.03, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.04, "Created by Jake Kolliari. Data provided by Statsbomb",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add WC Logo
url = 'https://purepng.com/public/uploads/large/purepng.com-world-cup-russia-2018-fifa-pocal-logofifawmworld-cupsoccer2018footballfussballpocalsport-31528992075ouo57.png'
ax = fig.add_axes([0., 0.85, 0.15, 0.15])
ax.axis("off")
response = requests.get(url)
img = Image.open(BytesIO(response.content))
ax.imshow(img)

# Layout and show
plt.tight_layout()
plt.show()

# %% Plot 2, plot pressure pass success vs. % pressure passes for all midfielders

# Set-up scatter plot
fig, ax = plt.subplots(figsize=(14, 9))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Plot data
ax.grid(ls="dotted", lw="0.5", color="lightgrey", zorder=1)
ax.scatter(playerinfo_df['pass_under_pressure_%'], playerinfo_df['pressure_pass_success_%'],
           s=100, c=playerinfo_df['pressure_pass_success_%'], cmap='coolwarm',
           edgecolors='w', alpha=0.75, lw=0.5, zorder=2)
x80 = np.percentile(playerinfo_df['pass_under_pressure_%'], 80)
y80 = np.percentile(playerinfo_df['pressure_pass_success_%'], 80)
ax.axvline(x=x80, color="white", linestyle="--", lw=0.75)
ax.axhline(y=y80, color="white", linestyle="--", lw=0.75)
ax.text(0.5, y80 + 0.5, '80th Percentile', color='w', fontsize=8, fontweight='bold')
ax.text(x80 + 0.5, 30.5, '80th Percentile', color='w', fontsize=8, fontweight='bold')

# Add player tags
text = list()
for i, player in playerinfo_df.iterrows():
    if player['pressure_pass_success_%'] >= y80 or player['pass_under_pressure_%'] >= x80:
        text.append(ax.text(player['pass_under_pressure_%'] + 0.2, player['pressure_pass_success_%'] + 0.2,
                            player['player_nickname'], color='w', fontsize=8,
                            ha="left", zorder=3))

adjustText.adjust_text(text, arrowprops=dict(arrowstyle="-", color='white', lw=0.5))

# Define axes
ax.set_xlabel("% of Passes Played Under Pressure", fontweight="bold", fontsize=14, color='w')
ax.set_ylabel("Pressured Pass Completion %", fontweight="bold", fontsize=14, color='w')
ax.set_xlim(0, 55)
ax.set_ylim(30, 101)

# Create title and subtitles, using highlighting as figure legend
title_text = "Midfielder passing under pressure"
subtitle_text = f"{competition} {year} - Proportion of passes played under pressure vs. pressured pass completion %"
subsubtitle_text = "Players with total game\ntime below 180 minutes\nor less than 20 passes per\ngame are not considered."
fig.text(0.11, 0.93, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.11, 0.895, subtitle_text, fontweight="regular", fontsize=14, color='w')
fig.text(0.82, 0.89, subsubtitle_text, fontsize=9, color='w')

# Add footer text
fig.text(0.515, 0.02, "Created by Jake Kolliari. Data provided by Statsbomb.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add WC Logo
ax = fig.add_axes([0., 0.85, 0.15, 0.15])
ax.axis("off")
response = requests.get(url)
img = Image.open(BytesIO(response.content))
ax.imshow(img)

# Layout and show
plt.tight_layout(rect=[0.05, 0.04, 0.93, 0.875])
plt.show()

# %% Plot 3, plot top 12 midfielders by number of pressures per 100 opposition passes.

pressures_df = midfielder_events[midfielder_events['type'] == 'Pressure']

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.75, space=0.12, axis=False)
fig.set_size_inches(14, 9)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Plot successful prog passes as arrows, using for loop to iterate through each player and each pass

idx = 0
sorted_df = playerinfo_df.sort_values('pressures_100pass', ascending=False)
for _, name in sorted_df.head(12).iterrows():
    player_pressures = pressures_df[pressures_df['player'] == name['player_name']]
    ax['pitch'][idx].title.set_text(f"{idx + 1}: {name['player_nickname']}")
    ax['pitch'][idx].title.set_color('w')
    x = player_pressures['location'].apply(lambda x: x[0])
    y = player_pressures['location'].apply(lambda x: x[1])
    hist_data = np.histogram2d(y, x, bins=[8, 12], range=[[0, 80], [0, 120]])
    hist = ax['pitch'][idx].imshow(100 * hist_data[0] / name['pressures'], extent=[0, 120, 0, 80], cmap=plt.cm.viridis,
                                   vmin=0, vmax=6)
    ax['pitch'][idx].text(3, 71, "Total:", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(25, 71, f"{name['pressures']}", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(3, 77, "Per 100 passes:", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(49, 77, f"{round(name['pressures_100pass'], 1)}", fontsize=8, fontweight='bold', color='w',
                          zorder=3)
    idx += 1

# Add colour bar
ax = fig.add_axes([0.71, 0.04, 0.3, 0.04])
ax.axis("off")
cbar = fig.colorbar(hist, ax=ax, fraction=0.4, shrink=2, orientation='horizontal')
cbar.ax.tick_params(labelsize=8)
cbar.ax.set_title('% of Total Pressures', color="w", fontweight='bold', fontsize=8)

# Create title and subtitles, using highlighting as figure legend
title_text = "Top 12 Midfielders, ranked by number of pressures per 100 opposition passes"
subtitle_text = f"{competition} {year} - Distribution of pressures applied during competition"
subsubtitle_text = "Players with total game\ntime below 180 minutes\nare not considered."
fig.text(0.11, 0.93, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.11, 0.895, subtitle_text, fontweight="regular", fontsize=14, color='w')
fig.text(0.85, 0.905, subsubtitle_text, fontsize=9, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.05, 0.18, 0.01])
ax.axis("off")
plt.arrow(0.61, 0.15, -0.1, 0, color="white")
fig.text(0.13, 0.03, "Direction of opposition play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.04, "Created by Jake Kolliari. Data provided by Statsbomb",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add WC Logo
url = 'https://purepng.com/public/uploads/large/purepng.com-world-cup-russia-2018-fifa-pocal-logofifawmworld-cupsoccer2018footballfussballpocalsport-31528992075ouo57.png'
ax = fig.add_axes([0, 0.85, 0.15, 0.15])
ax.axis("off")
response = requests.get(url)
img = Image.open(BytesIO(response.content))
ax.imshow(img)

# Layout and show
plt.tight_layout()
plt.show()

# % % Plot 4, plot recoveries per 100 opposition passes vs. tackles and interceptions per 100 opposition passes

# Set-up scatter plot
fig, ax = plt.subplots(figsize=(14, 9))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Plot data
y = playerinfo_df['interceptions_100pass'] + playerinfo_df['tackles_100pass']
ax.grid(ls="dotted", lw="0.5", color="lightgrey", zorder=1)
ax.scatter(playerinfo_df['recoveries_100pass'], y, s=100, c=y + playerinfo_df['recoveries_100pass'],
           cmap='coolwarm', edgecolors='w', alpha=0.75, lw=0.5, zorder=2)
x80 = np.percentile(playerinfo_df['recoveries_100pass'], 80)
y80 = np.percentile(y.dropna(), 80)
ax.axvline(x=x80, color="white", linestyle="--", lw=0.75)
ax.axhline(y=y80, color="white", linestyle="--", lw=0.75)
ax.text(0.01, y80 - 0.03, '80th Percentile', color='w', fontsize=8, fontweight='bold')
ax.text(x80 + 0.01, 0.01, '80th Percentile', color='w', fontsize=8, fontweight='bold')

# Add player tags
text = list()
for i, player in playerinfo_df.iterrows():
    if player['interceptions_100pass'] + player['tackles_100pass'] >= y80 or player['recoveries_100pass'] >= x80:
        text.append(ax.text(player['recoveries_100pass'] + 0.01, player['interceptions_100pass'] +
                            player['tackles_100pass'] + 0.01, player['player_nickname'],
                            color='w', fontsize=8, ha="left", zorder=3))

adjustText.adjust_text(text)

# Define axes
ax.set_xlabel("Ball Recoveries per 100 Opposition Passes", fontweight="bold", fontsize=14, color='w')
ax.set_ylabel("Tackles + Interceptions per 100 Opposition Passes", fontweight="bold", fontsize=14, color='w')
ax.set_xlim(0, 3)
ax.set_ylim(0, 1.4)

# Create title and subtitles, using highlighting as figure legend
title_text = "Midfielder ball winning and recovery"
subtitle_text = f"{competition} {year} - Recoveries vs. Tackles and Interceptions per 100 opposition passes"
subsubtitle_text = "Players with total game\ntime below 180 minutes\nare not considered."
fig.text(0.11, 0.93, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.11, 0.895, subtitle_text, fontweight="regular", fontsize=14, color='w')
fig.text(0.82, 0.905, subsubtitle_text, fontsize=9, color='w')

# Add footer text
fig.text(0.515, 0.02, "Created by Jake Kolliari. Data provided by Statsbomb.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add WC Logo
ax = fig.add_axes([0., 0.85, 0.15, 0.15])
ax.axis("off")
response = requests.get(url)
img = Image.open(BytesIO(response.content))
ax.imshow(img)

# Layout and show
plt.tight_layout(rect=[0.05, 0.04, 0.93, 0.875])
plt.show()

# %% Plot 5, plot top 12 midfielders by combined convex hull area

hull_df.sort_values('hull_area_tot', inplace=True, ascending=False)

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.75, space=0.12, axis=False)
fig.set_size_inches(14, 9)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Plot convex hulls, using for loop to iterate through each player
idx = 0
for hull_idx, hull_row in hull_df.head(12).iterrows():
    ax['pitch'][idx].title.set_text(f"{idx + 1}: {hull_idx}")
    ax['pitch'][idx].title.set_color('w')
    ax['pitch'][idx].scatter(hull_row['hull_x_def'], hull_row['hull_y_def'], color='cornflowerblue', s=10, zorder=2)
    ax['pitch'][idx].scatter(hull_row['hull_x_off'], hull_row['hull_y_off'], color='mediumseagreen', s=10, zorder=2)
    def_hull = pitch.convexhull(hull_row['hull_reduced_x_def'], hull_row['hull_reduced_y_def'])
    off_hull = pitch.convexhull(hull_row['hull_reduced_x_off'], hull_row['hull_reduced_y_off'])
    pitch.polygon(def_hull, ax=ax['pitch'][idx], edgecolor='cornflowerblue', facecolor='cornflowerblue', alpha=0.4)
    pitch.polygon(off_hull, ax=ax['pitch'][idx], edgecolor='mediumseagreen', facecolor='mediumseagreen', alpha=0.4)
    ax['pitch'][idx].text(14, -1.5, "Def. Area:", fontsize=7, fontweight='bold', color='cornflowerblue', zorder=3)
    ax['pitch'][idx].text(42, -1.5, f"{round(hull_row['hull_area_%_def'])}%", fontsize=7, color='w', zorder=3)
    ax['pitch'][idx].text(72, -1.5, "Off. Area:", fontsize=7, fontweight='bold', color='mediumseagreen', zorder=3)
    ax['pitch'][idx].text(100, -1.5, f"{round(hull_row['hull_area_%_off'])}%", fontsize=7, color='w', zorder=3)
    idx += 1

# Create title and subtitles, using highlighting as figure legend
title_text = "Top 12 Midfielders, ranked by distribution of actions over competition"
subtitle_text = f"{competition} {year} - <Defensive> and <Offensive> action convex hulls, enclosing 75% of all actions"
subsubtitle_text = "Players with total game time\nbelow 180 minutes, total number\nof defensive actions below 50,\nor total number of offensive actions\nbelow 100 are not considered."
fig.text(0.11, 0.93, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.11, 0.915, s=subtitle_text, fontweight="regular", fontsize=14, color='w',
               highlight_textprops=[{"color": 'cornflowerblue', "fontweight": 'bold'},
                                    {"color": 'mediumseagreen', "fontweight": 'bold'}])
fig.text(0.82, 0.885, subsubtitle_text, fontsize=9, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.05, 0.18, 0.01])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.03, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.04, "Created by Jake Kolliari. Data provided by Statsbomb",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add WC Logo
ax = fig.add_axes([0., 0.85, 0.15, 0.15])
ax.axis("off")
response = requests.get(url)
img = Image.open(BytesIO(response.content))
ax.imshow(img)

# Layout and show
plt.tight_layout()
plt.show()

# %% Plot 6, plot top 12 midfielders by defensive convex hull area

hull_df.sort_values('hull_area_def', inplace=True, ascending=False)

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.75, space=0.12, axis=False)
fig.set_size_inches(14, 9)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Plot convex huls, using for loop to iterate through each player
idx = 0
for hull_idx, hull_row in hull_df.head(12).iterrows():
    ax['pitch'][idx].title.set_text(f"{idx + 1}: {hull_idx}")
    ax['pitch'][idx].title.set_color('w')
    ax['pitch'][idx].scatter(hull_row['hull_x_def'], hull_row['hull_y_def'], color='cornflowerblue', s=10, zorder=2)
    def_hull = pitch.convexhull(hull_row['hull_reduced_x_def'], hull_row['hull_reduced_y_def'])
    pitch.polygon(def_hull, ax=ax['pitch'][idx], edgecolor='cornflowerblue', facecolor='cornflowerblue', alpha=0.4)
    ax['pitch'][idx].text(42, -1.5, "Def. Area:", fontsize=7, fontweight='bold', color='cornflowerblue', zorder=3)
    ax['pitch'][idx].text(69, -1.5, f"{round(hull_row['hull_area_%_def'])} %", fontsize=7, color='w', zorder=3)
    idx += 1

# Create title and subtitles, using highlighting as figure legend
title_text = "Top 12 Midfielders, ranked by distribution of defensive actions over competition"
subtitle_text = f"{competition} {year} - <Defensive> action convex hull, enclosing 75% of defensive actions"
subsubtitle_text = "Players with total game time\nbelow 180 minutes, or total\nnumber of defensive actions\nbelow 50 are not considered."
fig.text(0.11, 0.93, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.11, 0.915, s=subtitle_text, fontweight="regular", fontsize=14, color='w',
               highlight_textprops=[{"color": 'cornflowerblue', "fontweight": 'bold'}])
fig.text(0.84, 0.895, subsubtitle_text, fontsize=9, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.05, 0.18, 0.01])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.03, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.04, "Created by Jake Kolliari. Data provided by Statsbomb",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add WC Logo
ax = fig.add_axes([0., 0.85, 0.15, 0.15])
ax.axis("off")
response = requests.get(url)
img = Image.open(BytesIO(response.content))
ax.imshow(img)

# Layout and show
plt.tight_layout()
plt.show()

# %% Plot 7, plot top 12 midfielders by offensive convex hull area

hull_df.sort_values('hull_area_off', inplace=True, ascending=False)

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.75, space=0.12, axis=False)
fig.set_size_inches(14, 9)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Plot convex huls, using for loop to iterate through each player
idx = 0
for hull_idx, hull_row in hull_df.head(12).iterrows():
    ax['pitch'][idx].title.set_text(f"{idx + 1}: {hull_idx}")
    ax['pitch'][idx].title.set_color('w')
    ax['pitch'][idx].scatter(hull_row['hull_x_off'], hull_row['hull_y_off'], color='mediumseagreen', s=10, zorder=2)
    def_hull = pitch.convexhull(hull_row['hull_reduced_x_off'], hull_row['hull_reduced_y_off'])
    pitch.polygon(def_hull, ax=ax['pitch'][idx], edgecolor='cornflowerblue', facecolor='mediumseagreen', alpha=0.4)
    ax['pitch'][idx].text(42, -1.5, "Off. Area:", fontsize=7, fontweight='bold', color='mediumseagreen', zorder=3)
    ax['pitch'][idx].text(69, -1.5, f"{round(hull_row['hull_area_%_off'])}%", fontsize=7, color='w', zorder=3)
    idx += 1

# Create title and subtitles, using highlighting as figure legend
title_text = "Top 12 Midfielders, ranked by distribution of offensive actions over competition"
subtitle_text = f"{competition} {year} - <Offensive> action convex hull, enclosing 75% of offensive actions"
subsubtitle_text = "Players with total game time\nbelow 180 minutes, or total\nnumber of offensive actions\nbelow 100 are not considered."
fig.text(0.11, 0.93, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.11, 0.915, s=subtitle_text, fontweight="regular", fontsize=14, color='w',
               highlight_textprops=[{"color": 'mediumseagreen', "fontweight": 'bold'}])
fig.text(0.84, 0.895, subsubtitle_text, fontsize=9, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.05, 0.18, 0.01])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.03, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.04, "Created by Jake Kolliari. Data provided by Statsbomb",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add WC Logo
ax = fig.add_axes([0., 0.85, 0.15, 0.15])
ax.axis("off")
response = requests.get(url)
img = Image.open(BytesIO(response.content))
ax.imshow(img)

# Layout and show
plt.tight_layout()
plt.show()

# %% Plot 8, polar bar plot

# Choose player    
player = 'Toni Kroos'

# Create dataframe of normalised values to plot on polar bar graph
radarNorm_df = pd.DataFrame({'Player': playerscore_df['player_nickname'],
                             'Progressive Passes / 90': playerscore_df['progressive_pass_90'],
                             'xG Assisted / 90': playerscore_df['xg_assisted_90'],
                             'Pass Success (%)': playerscore_df['successful_passes_%'],
                             'Pressure Pass Success (%)': playerscore_df['pressure_pass_success_%'],
                             'Non-Penalty xG / 90': playerscore_df['shot_statsbomb_xg_90'],
                             'Pressures / 100 opp. passes': playerscore_df['pressures_100pass'],
                             'Recoveries / 100 opp. passes': playerscore_df['recoveries_100pass'],
                             'Interceptions / 100 opp. passes': playerscore_df['interceptions_100pass'],
                             'Tackles / 100 opp. passes': playerscore_df['tackles_100pass'],
                             'Def. Cvx Hull Area (% Pitch)': playerscore_df['hull_area_%_def'].astype(float),
                             'Off. Cvx Hull Area (% Pitch)': playerscore_df['hull_area_%_off'].astype(float),
                             'Distance / 90 (km)': playerscore_df['Distance']})
radarNorm_df.replace(np.nan, 0, inplace=True)

# Create dataframe of absolute values to label polar bar graph     
radar_df = pd.DataFrame({'Player': playerinfo_df['player_nickname'],
                         'Progressive Passes / 90': round(playerinfo_df['progressive_pass_90'], 2),
                         'xG Assisted / 90': round(playerinfo_df['xg_assisted_90'], 2),
                         'Pass Success (%)': round(playerinfo_df['successful_passes_%'], 1),
                         'Pressure Pass Success (%)': round(playerinfo_df['pressure_pass_success_%'], 1),
                         'Non-Penalty xG / 90': round(playerinfo_df['shot_statsbomb_xg_90'], 2),
                         'Pressures / 100 opp. passes': round(playerinfo_df['pressures_100pass'], 2),
                         'Recoveries / 100 opp. passes': round(playerinfo_df['recoveries_100pass'], 2),
                         'Interceptions / 100 opp. passes': round(playerinfo_df['interceptions_100pass'], 2),
                         'Tackles / 100 opp. passes': round(playerinfo_df['tackles_100pass'], 2),
                         'Def. Cvx Hull Area (% Pitch)': round(playerinfo_df['hull_area_%_def'].astype(float), 1),
                         'Off. Cvx Hull Area (% Pitch)': round(playerinfo_df['hull_area_%_off'].astype(float), 1),
                         'Distance / 90 (km)': round(playerinfo_df['Distance'] / 1000, 2)})
radar_df.replace(np.nan, 0, inplace=True)

# Define colours to differentiate between metrics
colors = ['seagreen', 'seagreen', 'seagreen', 'seagreen', 'seagreen', 'royalblue',
          'royalblue', 'royalblue', 'royalblue', 'darkorange', 'darkorange', 'darkorange']

# Slice dataframes
radarNorm = radarNorm_df[radarNorm_df['Player'] == player].drop('Player', axis=1)
radar = radar_df[radar_df['Player'] == player].drop('Player', axis=1)

# Store polar bar plot angles and values
radar_angles = np.linspace(0, 2 * np.pi, len(radarNorm.columns), endpoint=False)
radar_values = radarNorm.values.ravel()

# Create polar bar plot
fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={"projection": "polar"})
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)
ax.spines["start"].set_color("none")
ax.spines["polar"].set_color("none")

# Add bars
ax.bar(radar_angles, radar_values, color=colors, alpha=0.7, width=0.45, zorder=10)
ax.vlines(radar_angles, 0, 1, color='w', ls='--', lw=0.5, zorder=11)

# Polar bar plot properties
ax.set_theta_offset(1.001 * np.pi / len(radarNorm.columns))
ax.set_xticks(radar_angles)
ax.xaxis.grid(False)
xticks = ax.xaxis.get_major_ticks()
for tick in xticks:
    tick.set_pad(15)
ax.set_ylim(0, 1)
ax.set_yticklabels([])
ax.set_yticks([0, 0.33, 0.66, 1])

# Add title to each bar
text = ["\n".join(wrap(r + f' = {radar[r].values[0]}', 12, break_long_words=False)) for r in radar.columns.values]
ax.set_xticklabels(text, size=8, zorder=12)

# Manually add labels 
for i, label in enumerate(radar.columns.values):
    max_val = round(max(radar_df[label]), 2)
    onethird_val = round(min(radar_df[label]) + (1 / 3) * (max_val - min(radar_df[label])), 2)
    twothird_val = round(min(radar_df[label]) + (2 / 3) * (max_val - min(radar_df[label])), 2)
    label_val = float(round(radar.loc[:, label], 2))

    if label in ['Pass Success (%)', 'Pressure Pass Success (%)', 'Def. Cvx Hull Area (% Pitch)',
                 'Off. Cvx Hull Area (% Pitch)']:
        max_val = int(round(max_val, 0))
        onethird_val = int(round(onethird_val, 0))
        twothird_val = int(round(twothird_val, 0))
        label_val = int(round(label_val, 0))

    text_angles = [(180 / np.pi) * (radar_angles[i] - 0.13 + np.pi / len(radarNorm.columns)) - 90,
                   (180 / np.pi) * (radar_angles[i] - 0.08 + np.pi / len(radarNorm.columns)) - 90,
                   (180 / np.pi) * (radar_angles[i] - 0.06 + np.pi / len(radarNorm.columns)) - 90]
    for j, text_angle in enumerate(text_angles):
        if text_angle > 90 and text_angle < 270:
            text_angles[j] += 180

    ax.text(radar_angles[i] - 0.13, 0.305, onethird_val, rotation=text_angles[0], ha="center", color='w',
            va="center", size=8, zorder=12)
    ax.text(radar_angles[i] - 0.08, 0.63, twothird_val, rotation=text_angles[1], ha="center", color='w',
            va="center", size=8, zorder=12)
    ax.text(radar_angles[i] - 0.06, 0.96, max_val, rotation=text_angles[2], ha="center", color='w',
            va="center", size=8, zorder=12)

# Add title
fig.subplots_adjust(bottom=0.125, top=0.82)

# Create title and subtitles, using highlighting as figure legend
title_text = f"{player} - Player Radar"
subtitle_text = f"{competition} {year} - <Ball Winning>, <Creativity & Retention> and <Mobility> metrics"
fig.text(0.12, 0.93, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.12, 0.915, s=subtitle_text, fontweight="regular", fontsize=12, color='w',
               highlight_textprops=[{"color": 'royalblue', "fontweight": 'bold'},
                                    {"color": 'seagreen', "fontweight": 'bold'},
                                    {"color": 'darkorange', "fontweight": 'bold'}])

# Add WC Logo
ax = fig.add_axes([0.02, 0.865, 0.12, 0.12])
ax.axis("off")
response = requests.get(url)
img = Image.open(BytesIO(response.content))
ax.imshow(img)

# Add footer text
fig.text(0.5, 0.03, "Created by Jake Kolliari. Data provided by Statsbomb",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Layout and show
plt.show()
