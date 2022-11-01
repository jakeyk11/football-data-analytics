# %% Create visualisation of player defensive contribution across a selection of games
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Whoscored match ids
#           Positions not to include
#           Date of run
#           Normalisation mode
#           Minimum play time
#
# Outputs:  Scatter plot of defensive contributions

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.transforms import Affine2D
from matplotlib.ticker import MultipleLocator
import mpl_toolkits.axisartist.floating_axes as floating_axes
from mpl_toolkits.axisartist.grid_finder import (FixedLocator, MaxNLocator, DictFormatter)
import matplotlib.patheffects as path_effects
from PIL import Image
import adjustText
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

# %% User inputs

# Input WhoScored range of match id
match_id_start = 1640674
match_id_end = 1640800
match_ids = np.arange(match_id_start, match_id_end+1)

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Select position to exclude
pos_exclude=['GK']

# Position formatting on title
pos_input = ''

# Input run-date
run_date = '23/10/2022'

# Normalisation (None, '_90', '_100opp_pass')
norm_mode = '_100opp_pass'
#norm_mode = '_90'

# Min minutes played
min_mins = 450

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

# Add cumulative minutes information
players_df = wde.minutes_played(players_df, events_df)

# Calculate pass events that each player faces per game
players_df = wde.events_while_playing(events_df, players_df, event_name = 'Pass', event_team = 'opposition')

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df, additional_cols = ['opp_pass'])

# %% Isolate interceptions

interception = events_df[(events_df['eventType']=='Interception') & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(interception, playerinfo_df, primary_event_name='interception')
playerinfo_df['interception'].replace(np.nan, 0, inplace=True)
playerinfo_df['interception_90'] = round(90*playerinfo_df['interception']/playerinfo_df['mins_played'],2)
playerinfo_df['interception_100opp_pass'] = round(100*playerinfo_df['interception']/playerinfo_df['opp_pass'],2)

# %% Isolate blocked passes

block = events_df[(events_df['eventType']=='BlockedPass') & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(block, playerinfo_df, primary_event_name='block_pass')
playerinfo_df['block_pass'].replace(np.nan, 0, inplace=True)
playerinfo_df['block_pass_90'] = round(90*playerinfo_df['block_pass']/playerinfo_df['mins_played'],2)
playerinfo_df['block_pass_100opp_pass'] = round(100*playerinfo_df['block_pass']/playerinfo_df['opp_pass'],2)

# %% Isolate tackles

tackle = events_df[(events_df['eventType']=='Tackle') & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(tackle, playerinfo_df, primary_event_name='tackle')
playerinfo_df['tackle'].replace(np.nan, 0, inplace=True)
playerinfo_df['tackle_90'] = round(90*playerinfo_df['tackle']/playerinfo_df['mins_played'],2)
playerinfo_df['tackle_100opp_pass'] = round(100*playerinfo_df['tackle']/playerinfo_df['opp_pass'],2)

# %% Recovery

recovery = events_df[(events_df['eventType']=='BallRecovery') & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(recovery, playerinfo_df, primary_event_name='recovery')
playerinfo_df['recovery'].replace(np.nan, 0, inplace=True)
playerinfo_df['recovery_90'] = round(90*playerinfo_df['recovery']/playerinfo_df['mins_played'],2)
playerinfo_df['recovery_100opp_pass'] = round(100*playerinfo_df['recovery']/playerinfo_df['opp_pass'],2)

# %% Aerial

duel = events_df[(events_df['eventType']=='Aerial') & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(duel, playerinfo_df, primary_event_name='duel_won')
playerinfo_df['duel_won'].replace(np.nan, 0, inplace=True)
playerinfo_df['duel_won_90'] = round(90*playerinfo_df['duel_won']/playerinfo_df['mins_played'],2)
playerinfo_df['duel_won_100opp_pass'] = round(100*playerinfo_df['duel_won']/playerinfo_df['opp_pass'],2)

# %% Filter playerinfo

playerinfo_df = playerinfo_df[(playerinfo_df['mins_played']>=min_mins) & (~playerinfo_df['pos_type'].isin(pos_exclude))]
playerinfo_df = playerinfo_df[~playerinfo_df.index.duplicated(keep='first')]

# %% Calculate metrics

playerinfo_df['tackle_duel_90'] = playerinfo_df['duel_won_90'] + playerinfo_df['tackle_90']
playerinfo_df['tackle_duel_100opp_pass'] = playerinfo_df['duel_won_100opp_pass'] + playerinfo_df['tackle_100opp_pass']
playerinfo_df['interception_block_90'] = playerinfo_df['interception_90'] + playerinfo_df['block_pass_90']
playerinfo_df['interception_block_100opp_pass'] = playerinfo_df['interception_100opp_pass'] + playerinfo_df['block_pass_100opp_pass']
playerinfo_df['balls_won_from_opp_100opp_pas'] = playerinfo_df['interception_block_100opp_pass'] + playerinfo_df['tackle_duel_100opp_pass']

#playerinfo_df.dropna(subset=['interception_block_100opp_pass', 'balls_won_from_opp_100opp_pas'], inplace = True)

left_ax_plot = playerinfo_df['balls_won_from_opp_100opp_pas']
right_ax_plot = playerinfo_df['recovery_100opp_pass']

left_ax_plot.replace(np.nan, 0, inplace=True)
right_ax_plot.replace(np.nan, 0, inplace=True)

left_ax_norm_plot = 0.99 * left_ax_plot / max(left_ax_plot)
right_ax_norm_plot = 0.99 * right_ax_plot / max(right_ax_plot)

left_ax_quantile = left_ax_norm_plot.quantile([0.1,0.5,0.9]).tolist()
right_ax_quantile = right_ax_norm_plot.quantile([0.1,0.5,0.9]).tolist()

plot_player = playerinfo_df[(left_ax_norm_plot>left_ax_quantile[2]) | (right_ax_norm_plot>right_ax_quantile[2]) | ((left_ax_norm_plot<left_ax_quantile[0]) | (right_ax_norm_plot<right_ax_quantile[0]))]
left_points = left_ax_norm_plot[(left_ax_norm_plot>left_ax_quantile[2]) | (right_ax_norm_plot>right_ax_quantile[2]) | ((left_ax_norm_plot<left_ax_quantile[0]) | (right_ax_norm_plot<right_ax_quantile[0]))]
right_points = right_ax_norm_plot[(left_ax_norm_plot>left_ax_quantile[2]) | (right_ax_norm_plot>right_ax_quantile[2])| ((left_ax_norm_plot<left_ax_quantile[0]) | (right_ax_norm_plot<right_ax_quantile[0]))]

#plot_player = playerinfo_df[playerinfo_df['team']=='Chelsea']
#plot_player = plot_player[plot_player['name']=='Declan Rice']
# %% Build visual

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
mpl.rcParams['text.color'] = 'w'

# Set-up figure
fig = plt.figure(figsize = (8.5,9), facecolor = '#313332')

# Set up diamond axis extent (we normalise for simplicity)
left_extent = 1.001
right_extent = 1.001
plot_extents = 0, right_extent, 0, left_extent

# Create reference dictionary for ticks
ticks = list(np.arange(0, 1.1, 0.1))
right_dict = {}
left_dict = {}

for i in ticks:
    if i == 0:
        left_dict[i] = ''
        right_dict[i] =  ''
    else:
        left_dict[i] = str(round((i * left_ax_plot.max())/0.99,2))
        right_dict[i] = str(round((i * right_ax_plot.max())/0.99,2))
    
tick_formatter1 = DictFormatter(right_dict)
tick_formatter2 = DictFormatter(left_dict)

# Define axis transformation, build axis and auxillary axis
transform = Affine2D().rotate_deg(45)
helper = floating_axes.GridHelperCurveLinear(transform, plot_extents,
                                             grid_locator1=MaxNLocator(nbins=1+right_extent/0.1), grid_locator2=MaxNLocator(nbins=1+left_extent/0.1),
                                             tick_formatter1=tick_formatter1, tick_formatter2=tick_formatter2)
ax = floating_axes.FloatingSubplot(fig, 111, grid_helper=helper)
ax.patch.set_alpha(0)
ax.set_position([0.075,0.07,0.85,0.8], which='both')
aux_ax = ax.get_aux_axes(transform)

# Add transformed axis
ax = fig.add_axes(ax)
aux_ax.patch = ax.patch 

# Format axes
ax.axis['left'].line.set_color("w")
ax.axis['bottom'].line.set_color("w")
ax.axis['right'].set_visible(False)
ax.axis['top'].set_visible(False)
ax.axis['left'].major_ticklabels.set_rotation(0)
ax.axis['left'].major_ticklabels.set_horizontalalignment("center")

# Label axes
ax.axis['left'].set_label("Balls Won Directly from opposition per 100 opposition touches")
ax.axis['left'].label.set_rotation(0)
ax.axis['left'].label.set_color("w")
ax.axis['left'].label.set_fontweight("bold")
ax.axis['left'].label.set_fontsize(9)
ax.axis['left'].LABELPAD += 7

ax.axis['bottom'].set_label("Ball Recoveries per 100 opposition touches")
ax.axis['bottom'].label.set_color("w")
ax.axis['bottom'].label.set_fontweight("bold")
ax.axis['bottom'].label.set_fontsize(9)
ax.axis['bottom'].LABELPAD += 7
ax.axis['bottom'].major_ticklabels.set_pad(8)

# Overwrite 0 labels

z_ax1 = fig.add_axes([0.47,0.05,0.06,0.0245])
z_ax1.patch.set_color('#313332')
z_ax1.spines['right'].set_visible(False)
z_ax1.spines['top'].set_visible(False)
z_ax1.spines['bottom'].set_visible(False)
z_ax1.spines['left'].set_visible(False)
z_ax1.axes.xaxis.set_visible(False)
z_ax1.axes.yaxis.set_visible(False)
z_ax1.text(0.5, 0.5, 0, ha = "center", va = "center")

# Axis grid
ax.grid(alpha=0.2, color ='w')

# Plot points on auxilary axis
aux_ax.scatter(right_ax_norm_plot, left_ax_norm_plot, c = left_ax_norm_plot+right_ax_norm_plot, cmap = 'viridis', edgecolor = 'w', s = 50, lw = 0.3, zorder=2)

# Add text
text = list()
path_eff = [path_effects.Stroke(linewidth=1.5, foreground='#313332'), path_effects.Normal()]
for i, player in plot_player.iterrows():
    format_name =  player['name'].split(' ')[0][0] + " " + player['name'].split(' ')[len(player['name'].split(' '))-1] if len(player['name'].split(' '))>1 else player['name']
    text.append(aux_ax.text(right_ax_norm_plot[i]+0.01, left_ax_norm_plot[i]+0.01, format_name, color='w', fontsize=7, zorder=3, path_effects = path_eff))
adjustText.adjust_text(text, ax = ax)

# Add axis shading
aux_ax.fill([right_ax_quantile[0], right_ax_quantile[0], right_ax_quantile[2], right_ax_quantile[2]], [0, 100, 100, 0], color='grey', alpha = 0.15, zorder=0)
aux_ax.plot([right_ax_quantile[0], right_ax_quantile[0]], [0,left_ax_quantile[0]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[0], right_ax_quantile[0]], [left_ax_quantile[2],100], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[2], right_ax_quantile[2]], [0,left_ax_quantile[0]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[2], right_ax_quantile[2]], [left_ax_quantile[2],100], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)

aux_ax.fill([0, right_ax_quantile[0], right_ax_quantile[0], 0], [left_ax_quantile[0], left_ax_quantile[0], left_ax_quantile[2], left_ax_quantile[2]], color='grey', alpha = 0.15, zorder=0)
aux_ax.fill([right_ax_quantile[2], 100, 100, right_ax_quantile[2]], [left_ax_quantile[0], left_ax_quantile[0], left_ax_quantile[2], left_ax_quantile[2]], color='grey', alpha = 0.15, zorder=0)
aux_ax.plot([0, right_ax_quantile[0]], [left_ax_quantile[0], left_ax_quantile[0]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[2], 100], [left_ax_quantile[0], left_ax_quantile[0]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([0, right_ax_quantile[0]], [left_ax_quantile[2], left_ax_quantile[2]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[2], 100], [left_ax_quantile[2], left_ax_quantile[2]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)

# Add left text axis
text_ax_left = fig.add_axes([0.085, 0.47, 0.415, 0.392])
text_ax_left.plot([0.39,0.59], [0.41,0.61], color = 'w', alpha = 0.9, lw=0.5)
text_ax_left.plot([0.49,0.36], [0.51,0.64], color = 'w', alpha = 0.9, lw=0.5)
text_ax_left.text(0.23, 0.76, "Players towards this side\nof the grid frequently win\nthe ball back directly from the\nopposition through tackles,\naerials and interceptions", ha = "center", fontsize = 8, alpha=0.8)
text_ax_left.axis("off")
text_ax_left.set_xlim([0,1])
text_ax_left.set_ylim([0,1])

logo_ax_left = fig.add_axes([0.1,0.67,0.15,0.15])
tackle_logo = Image.open('..\..\data_directory\misc_data\images\TackleLogo.png')
logo_ax_left.imshow(tackle_logo)
logo_ax_left.axis("off")

# Add right text axis
text_ax_right = fig.add_axes([0.5, 0.47, 0.415, 0.392])
text_ax_right.plot([0.61,0.41], [0.41,0.61], color = 'w', alpha = 0.9, lw=0.5)
text_ax_right.plot([0.51,0.64], [0.51,0.64], color = 'w', alpha = 0.9, lw=0.5)
text_ax_right.text(0.89, 0.69, "Players towards this\nside of the grid\nfrequently recover\n the ball for their\nteam in situations\nwhere neither team\nhad possession", ha = "center", fontsize = 8, alpha = 0.8)
text_ax_right.axis("off")
text_ax_right.set_xlim([0,1])
text_ax_right.set_ylim([0,1])

logo_ax_right = fig.add_axes([0.72,0.73,0.1,0.1])
tackle_logo = Image.open('..\..\data_directory\misc_data\images\RecoveryLogo.png')
logo_ax_right.imshow(tackle_logo)
logo_ax_right.axis("off")

# Add bottom text axis
text_ax_bottom = fig.add_axes([0.085, 0.078, 0.415, 0.392])
text_ax_bottom.text(0.23, 0.05, f"Players with over {min_mins}\nmins played, and at least\none possession win are\nincluded.", ha = "center", fontsize = 8, alpha = 0.8)
text_ax_bottom.axis("off")
text_ax_bottom.set_xlim([0,1])
text_ax_bottom.set_ylim([0,1])

# Create title and subtitles
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship'}

title_text = f"{leagues[league]} {year}/{int(year) + 1}: Defensive Contributions"
subtitle_text = "Possessions Won & Ball Recoveries - Outfield Players"

# Title
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.905, subtitle_text, fontweight="regular", fontsize=13, color='w')
#fig.text(0.847, 0.902, subsubsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)
ax.set_xticks([0.1, 0.2, 0.3])

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

# Save image
fig.savefig(f"top_defensive_contributions/{league}-{year}-top-defensive-actions", dpi=300)


# %% Calculate metrics

#playerinfo_df.dropna(subset=['interception_block_100opp_pass', 'balls_won_from_opp_100opp_pas'], inplace = True)

left_ax_plot = playerinfo_df['balls_won_from_opp_100opp_pas']
right_ax_plot = playerinfo_df['recovery_100opp_pass']

left_ax_plot.replace(np.nan, 0, inplace=True)
right_ax_plot.replace(np.nan, 0, inplace=True)

left_ax_norm_plot = 0.99 * left_ax_plot / max(left_ax_plot)
right_ax_norm_plot = 0.99 * right_ax_plot / max(right_ax_plot)

left_ax_quantile = left_ax_norm_plot.quantile([0.1,0.5,0.9]).tolist()
right_ax_quantile = right_ax_norm_plot.quantile([0.1,0.5,0.9]).tolist()

plot_player =pd.DataFrame()

for team in set(playerinfo_df['team'].values):
    team_players = playerinfo_df[playerinfo_df['team']==team]
    team_players['lnorm'] = 0.99 * team_players['balls_won_from_opp_100opp_pas'] / max(team_players['balls_won_from_opp_100opp_pas'])
    team_players['rnorm'] = 0.99 * team_players['recovery_100opp_pass'] / max(team_players['recovery_100opp_pass'])
    team_players['norm'] = team_players['lnorm'] + team_players['rnorm']
    team_players['lnorm_plot'] =  0.99 * team_players['balls_won_from_opp_100opp_pas'] / max(playerinfo_df['balls_won_from_opp_100opp_pas'])
    team_players['rnorm_plot'] =  0.99 * team_players['recovery_100opp_pass'] / max(playerinfo_df['recovery_100opp_pass'])
    team_players.sort_values('norm', ascending = False, inplace =True)
    
    if len(set(team_players[team_players['norm']==team_players['norm'].quantile(0.5)])) == 2:
        top_mid_low_player = team_players[(team_players['norm'] == team_players['norm'].quantile(0.5)) | (team_players['norm'] == team_players['norm'].quantile(0)) | (team_players['norm'] == team_players['norm'].quantile(1))]
    else:
        top_mid_low_player = team_players[(team_players['norm'] == team_players['norm'].quantile(0)) | (team_players['norm'] == team_players['norm'].quantile(1))]
        top_mid_low_player = pd.concat([top_mid_low_player, pd.DataFrame(team_players.iloc[int(len(team_players)/2),:]).T])
    
    plot_player = pd.concat([plot_player, top_mid_low_player])

left_points = left_ax_norm_plot[(left_ax_norm_plot>left_ax_quantile[2]) | (right_ax_norm_plot>right_ax_quantile[2]) | ((left_ax_norm_plot<left_ax_quantile[0]) | (right_ax_norm_plot<right_ax_quantile[0]))]
right_points = right_ax_norm_plot[(left_ax_norm_plot>left_ax_quantile[2]) | (right_ax_norm_plot>right_ax_quantile[2])| ((left_ax_norm_plot<left_ax_quantile[0]) | (right_ax_norm_plot<right_ax_quantile[0]))]

#plot_player = playerinfo_df[playerinfo_df['team']=='Chelsea']
#plot_player = plot_player[plot_player['name']=='Declan Rice']
# %% Build visual

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
mpl.rcParams['text.color'] = 'w'

# Set-up figure
fig = plt.figure(figsize = (8.5,9), facecolor = '#313332')

# Set up diamond axis extent (we normalise for simplicity)
left_extent = 1.001
right_extent = 1.001
plot_extents = 0, right_extent, 0, left_extent

# Create reference dictionary for ticks
ticks = list(np.arange(0, 1.1, 0.1))
right_dict = {}
left_dict = {}

for i in ticks:
    if i == 0:
        left_dict[i] = ''
        right_dict[i] =  ''
    else:
        left_dict[i] = str(round((i * left_ax_plot.max())/0.99,2))
        right_dict[i] = str(round((i * right_ax_plot.max())/0.99,2))
    
tick_formatter1 = DictFormatter(right_dict)
tick_formatter2 = DictFormatter(left_dict)

# Define axis transformation, build axis and auxillary axis
transform = Affine2D().rotate_deg(45)
helper = floating_axes.GridHelperCurveLinear(transform, plot_extents,
                                             grid_locator1=MaxNLocator(nbins=1+right_extent/0.1), grid_locator2=MaxNLocator(nbins=1+left_extent/0.1),
                                             tick_formatter1=tick_formatter1, tick_formatter2=tick_formatter2)
ax = floating_axes.FloatingSubplot(fig, 111, grid_helper=helper)
ax.patch.set_alpha(0)
ax.set_position([0.075,0.07,0.85,0.8], which='both')
aux_ax = ax.get_aux_axes(transform)

# Add transformed axis
ax = fig.add_axes(ax)
aux_ax.patch = ax.patch 

# Format axes
ax.axis['left'].line.set_color("w")
ax.axis['bottom'].line.set_color("w")
ax.axis['right'].set_visible(False)
ax.axis['top'].set_visible(False)
ax.axis['left'].major_ticklabels.set_rotation(0)
ax.axis['left'].major_ticklabels.set_horizontalalignment("center")

# Label axes
ax.axis['left'].set_label("Balls Won Directly from opposition per 100 opposition touches")
ax.axis['left'].label.set_rotation(0)
ax.axis['left'].label.set_color("w")
ax.axis['left'].label.set_fontweight("bold")
ax.axis['left'].label.set_fontsize(9)
ax.axis['left'].LABELPAD += 7

ax.axis['bottom'].set_label("Ball Recoveries per 100 opposition touches")
ax.axis['bottom'].label.set_color("w")
ax.axis['bottom'].label.set_fontweight("bold")
ax.axis['bottom'].label.set_fontsize(9)
ax.axis['bottom'].LABELPAD += 7
ax.axis['bottom'].major_ticklabels.set_pad(8)

# Overwrite 0 labels

z_ax1 = fig.add_axes([0.47,0.05,0.06,0.0245])
z_ax1.patch.set_color('#313332')
z_ax1.spines['right'].set_visible(False)
z_ax1.spines['top'].set_visible(False)
z_ax1.spines['bottom'].set_visible(False)
z_ax1.spines['left'].set_visible(False)
z_ax1.axes.xaxis.set_visible(False)
z_ax1.axes.yaxis.set_visible(False)
z_ax1.text(0.5, 0.5, 0, ha = "center", va = "center")

# Axis grid
ax.grid(alpha=0.2, color ='w')

# Plot points on auxilary axis
aux_ax.scatter(right_ax_norm_plot, left_ax_norm_plot, c = 'w', alpha = 0.1, edgecolor = 'w', s = 50, lw = 0.3, zorder=2)

for idx, player in plot_player.iterrows():
    col = []
    if player['team'] == 'Arsenal':
        col = '#EF0107'
    elif player['team'] == 'Aston Villa':
        col = '#670E36'
    elif player['team'] == 'Bournemouth':
        col = '#DA291C'
    elif player['team'] == 'Brentford':
        col = '#E30613'
    elif player['team'] == 'Brighton':
        col = '#0057B8'
    elif player['team'] == 'Chelsea':
        col = '#034694'
    elif player['team'] == 'Crystal Palace':
        col = '#1B458F'
    elif player['team'] == 'Everton':
        col = '#003399'
    elif player['team'] == 'Fulham':
        col = '#FFFFFF'
    elif player['team'] == 'Leeds':
        col = '#FFCD00'
    elif player['team'] == 'Leicester':
        col = '#003090'
    elif player['team'] == 'Liverpool':
        col = '#C8102E'
    elif player['team'] == 'Man City':
        col = '#6CABDD'
    elif player['team'] == 'Man Utd':
        col = '#DA291C'
    elif player['team'] == 'Newcastle United':
        col = 'k'
    elif player['team'] == 'Nottingham Forest':
        col = '#E53233'
    elif player['team'] == 'Southampton':
        col = '#D71920'
    elif player['team'] == 'Tottenham':
        col = '#132257'
    elif player['team'] == 'West Ham':
        col = '#7A263A'
    elif player['team'] == 'Wolves':
        col = '#FDB913'
    aux_ax.scatter(player['rnorm_plot'], player['lnorm_plot'], c = col, edgecolor = 'w', s = 50, lw = 0.3, zorder=3)


# Add text
text = list()
text2 = list()
path_eff = [path_effects.Stroke(linewidth=1.5, foreground='#313332'), path_effects.Normal()]
for i, player in plot_player.iterrows():
    format_name =  player['name'].split(' ')[0][0] + " " + player['name'].split(' ')[len(player['name'].split(' '))-1] if len(player['name'].split(' '))>1 else player['name']
    text.append(aux_ax.text(right_ax_norm_plot[i]+0.01, left_ax_norm_plot[i], format_name, color='w', fontsize=7, zorder=3, path_effects = path_eff))

adjustText.adjust_text(text, ax = ax)

# Add axis shading
aux_ax.fill([right_ax_quantile[0], right_ax_quantile[0], right_ax_quantile[2], right_ax_quantile[2]], [0, 100, 100, 0], color='grey', alpha = 0.15, zorder=0)
aux_ax.plot([right_ax_quantile[0], right_ax_quantile[0]], [0,left_ax_quantile[0]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[0], right_ax_quantile[0]], [left_ax_quantile[2],100], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[2], right_ax_quantile[2]], [0,left_ax_quantile[0]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[2], right_ax_quantile[2]], [left_ax_quantile[2],100], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)

aux_ax.fill([0, right_ax_quantile[0], right_ax_quantile[0], 0], [left_ax_quantile[0], left_ax_quantile[0], left_ax_quantile[2], left_ax_quantile[2]], color='grey', alpha = 0.15, zorder=0)
aux_ax.fill([right_ax_quantile[2], 100, 100, right_ax_quantile[2]], [left_ax_quantile[0], left_ax_quantile[0], left_ax_quantile[2], left_ax_quantile[2]], color='grey', alpha = 0.15, zorder=0)
aux_ax.plot([0, right_ax_quantile[0]], [left_ax_quantile[0], left_ax_quantile[0]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[2], 100], [left_ax_quantile[0], left_ax_quantile[0]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([0, right_ax_quantile[0]], [left_ax_quantile[2], left_ax_quantile[2]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)
aux_ax.plot([right_ax_quantile[2], 100], [left_ax_quantile[2], left_ax_quantile[2]], color = 'w', lw = 1, alpha = 0.3, ls = 'dashed', zorder=0)

# Add left text axis
text_ax_left = fig.add_axes([0.085, 0.47, 0.415, 0.392])
text_ax_left.plot([0.39,0.59], [0.41,0.61], color = 'w', alpha = 0.9, lw=0.5)
text_ax_left.plot([0.49,0.36], [0.51,0.64], color = 'w', alpha = 0.9, lw=0.5)
text_ax_left.text(0.23, 0.76, "Players towards this side\nof the grid frequently win\nthe ball back directly from the\nopposition through tackles,\naerials and interceptions", ha = "center", fontsize = 8, alpha=0.8)
text_ax_left.axis("off")
text_ax_left.set_xlim([0,1])
text_ax_left.set_ylim([0,1])

logo_ax_left = fig.add_axes([0.1,0.67,0.15,0.15])
tackle_logo = Image.open('..\..\data_directory\misc_data\images\TackleLogo.png')
logo_ax_left.imshow(tackle_logo)
logo_ax_left.axis("off")

# Add right text axis
text_ax_right = fig.add_axes([0.5, 0.47, 0.415, 0.392])
text_ax_right.plot([0.61,0.41], [0.41,0.61], color = 'w', alpha = 0.9, lw=0.5)
text_ax_right.plot([0.51,0.64], [0.51,0.64], color = 'w', alpha = 0.9, lw=0.5)
text_ax_right.text(0.89, 0.69, "Players towards this\nside of the grid\nfrequently recover\n the ball for their\nteam in situations\nwhere neither team\nhad possession", ha = "center", fontsize = 8, alpha = 0.8)
text_ax_right.axis("off")
text_ax_right.set_xlim([0,1])
text_ax_right.set_ylim([0,1])

logo_ax_right = fig.add_axes([0.72,0.73,0.1,0.1])
tackle_logo = Image.open('..\..\data_directory\misc_data\images\RecoveryLogo.png')
logo_ax_right.imshow(tackle_logo)
logo_ax_right.axis("off")

# Add bottom text axis
text_ax_bottom = fig.add_axes([0.085, 0.078, 0.415, 0.392])
text_ax_bottom.text(0.23, 0.05, f"Players with over {min_mins}\nmins played, and at least\none possession win are\nincluded.", ha = "center", fontsize = 8, alpha = 0.8)
text_ax_bottom.axis("off")
text_ax_bottom.set_xlim([0,1])
text_ax_bottom.set_ylim([0,1])

# Create title and subtitles
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship'}

title_text = f"{leagues[league]} {year}/{int(year) + 1}: Defensive Contributions"
subtitle_text = "Possessions Won & Ball Recoveries - Outfield Players"

# Title
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.905, subtitle_text, fontweight="regular", fontsize=13, color='w')
#fig.text(0.847, 0.902, subsubsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)
ax.set_xticks([0.1, 0.2, 0.3])

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

# Save image
fig.savefig(f"top_defensive_contributions/{league}-{year}-top-defensive-actions", dpi=300)
