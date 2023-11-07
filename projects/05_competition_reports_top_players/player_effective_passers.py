# %% Create multiple visualisations highlighting effective passers over a competition
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Whoscored match ids
#           Positions not to include
#           Date of run
#           Normalisation mode
#           Minimum play time
#
# Outputs:  Diamond scatter of user selected variables
#           Top 12 Progressive Passers
#           Top 12 threat creators

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.transforms import Affine2D
from matplotlib.ticker import MultipleLocator
import mpl_toolkits.axisartist.floating_axes as floating_axes
from mpl_toolkits.axisartist.grid_finder import (FixedLocator, MaxNLocator, DictFormatter)
import matplotlib.patheffects as path_effects
import matplotlib.cm as cm
from PIL import Image, ImageEnhance
import adjustText
import os
import sys
import bz2
import pickle
import numpy as np
import highlight_text as htext
import glob
from mplsoccer.pitch import Pitch

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% User inputs

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Select position to exclude
pos_exclude=['GK']

# Position formatting on title
pos_input = 'outfield players'

# Input run-date
run_date = '28/05/2023'

# Normalisation (None, '_90', '_100pass', '_100teampass')
norm_mode = '_90'

# Min minutes played (only used if normalising)
min_mins = 1800

# Brighten logo
logo_brighten = True

# %% League logo and league naming

comp_logo = lab.get_competition_logo(league, year, logo_brighten)
    
# Create title and subtitles
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League One', 'EFL2': 'EFL League Two'}

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

# %% Pre-process data

# Add pass recipient
events_df = wde.get_recipient(events_df)

# Add cumulative minutes information
players_df = wde.minutes_played(players_df, events_df)

# Add pre-assist information
events_df = wce.pre_assist(events_df)

# Calculate longest consistent xi
players_df = wde.longest_xi(players_df)

# Calculate pass events that each player's team makes per game
players_df = wde.events_while_playing(events_df, players_df, event_name = 'Pass', event_team = 'own')

# Add progressive pass and box entry information to event dataframe
events_df['progressive_action'] = events_df.apply(wce.progressive_action, axis=1, inplay = True, successful_only = False)
events_df['into_box'] = events_df.apply(wce.box_entry, axis=1, inplay = True, successful_only = False)

# Determine substitute positions (TBC)
#for idx, player in players_df.iterrows():
 #   if player['subbedOutPlayerId'] == player['subbedOutPlayerId']:
  #      subbed_on_position = players_df[players_df['match_id'] == player['match_id']].loc[player['subbedOutPlayerId'], 'position']
   #     players_df.loc[idx,'position'] = subbed_on_position

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df, additional_cols = ['team_pass'])

# Passes and total xT
all_passes = events_df[(events_df['eventType']=='Pass') & (~events_df['satisfiedEventsTypes'].apply(lambda x: 31 in x or 32 in x or 33 in x or 34 in x or 212 in x))]
playerinfo_df = wde.group_player_events(all_passes, playerinfo_df, primary_event_name='passes')
playerinfo_df = wde.group_player_events(all_passes, playerinfo_df, group_type='sum', event_types = ['xThreat', 'xThreat_gen'])

# Successful passes
suc_passes = all_passes[all_passes['outcomeType']=='Successful']
playerinfo_df = wde.group_player_events(suc_passes, playerinfo_df, primary_event_name='suc_passes')

# Progressive passes
prog_passes = all_passes[all_passes['progressive_action']==True]
playerinfo_df = wde.group_player_events(prog_passes, playerinfo_df, primary_event_name='prog_passes')
suc_prog_passes = prog_passes[prog_passes['outcomeType']=='Successful']
playerinfo_df = wde.group_player_events(suc_prog_passes, playerinfo_df, primary_event_name='suc_prog_passes')

# Successful progressive passes in opposition half
opphalf_prog_pass = suc_prog_passes[suc_prog_passes['x'] > 50]
playerinfo_df = wde.group_player_events(opphalf_prog_pass, playerinfo_df, primary_event_name='opphalf_prog_passes')

# Forward passes
forward_passes = all_passes[all_passes['endX'] > all_passes['x']]
playerinfo_df = wde.group_player_events(forward_passes, playerinfo_df, primary_event_name='fwd_passes')
suc_forward_passes = forward_passes[forward_passes['outcomeType']=='Successful']
playerinfo_df = wde.group_player_events(suc_forward_passes, playerinfo_df, primary_event_name='suc_fwd_passes')

# Crosses
crosses = all_passes[all_passes['satisfiedEventsTypes'].apply(lambda x: 125 in x or 126 in x)]
playerinfo_df = wde.group_player_events(crosses, playerinfo_df, primary_event_name='crosses')
suc_crosses = all_passes[all_passes['satisfiedEventsTypes'].apply(lambda x: 125 in x)]
playerinfo_df = wde.group_player_events(suc_crosses, playerinfo_df, primary_event_name='suc_crosses')

# Through balls
through_balls = all_passes[all_passes['satisfiedEventsTypes'].apply(lambda x: 129 in x or 130 in x or 131 in x)]
playerinfo_df = wde.group_player_events(through_balls, playerinfo_df, primary_event_name='through_balls')
suc_through_balls = all_passes[all_passes['satisfiedEventsTypes'].apply(lambda x: 129 in x)]
playerinfo_df = wde.group_player_events(suc_through_balls, playerinfo_df, primary_event_name='suc_through_balls')

# Long balls
long_balls = all_passes[all_passes['satisfiedEventsTypes'].apply(lambda x: 127 in x or 128 in x)]
playerinfo_df = wde.group_player_events(long_balls, playerinfo_df, primary_event_name='long_balls')
suc_long_balls = all_passes[all_passes['satisfiedEventsTypes'].apply(lambda x: 127 in x)]
playerinfo_df = wde.group_player_events(suc_long_balls, playerinfo_df, primary_event_name='suc_long_balls')

# Key passes
key_passes = all_passes[all_passes['satisfiedEventsTypes'].apply(lambda x: 123 in x)]
playerinfo_df = wde.group_player_events(key_passes, playerinfo_df, primary_event_name='key_passes')

# Key progressive passes
key_prog_passes = suc_prog_passes[suc_prog_passes['satisfiedEventsTypes'].apply(lambda x: 123 in x)]
playerinfo_df = wde.group_player_events(key_prog_passes, playerinfo_df, primary_event_name='key_prog_passes')

# Assists
assists = all_passes[all_passes['satisfiedEventsTypes'].apply(lambda x: 92 in x)]
touch_assists = events_df[(events_df['eventType']!='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 92 in x))]
playerinfo_df = wde.group_player_events(assists, playerinfo_df, primary_event_name='assists')

# Pre assists
pre_assists = all_passes[all_passes['pre_assist']==True]
playerinfo_df = wde.group_player_events(pre_assists, playerinfo_df, primary_event_name='pre_assists')

# Passes into opposition box
box_passes = all_passes[all_passes['into_box'] == True]
playerinfo_df = wde.group_player_events(box_passes, playerinfo_df, primary_event_name='box_passes')
suc_box_passes = box_passes[box_passes['outcomeType']=='Successful']
playerinfo_df = wde.group_player_events(suc_box_passes, playerinfo_df, primary_event_name='suc_box_passes')

# %% Calculate statistics as percentages and per 90 mins

# Passes and xT generated
playerinfo_df['passes_90'] =  round(90*playerinfo_df['passes']/playerinfo_df['mins_played'],2)
playerinfo_df['passes_100teampass'] =  round(100*playerinfo_df['passes']/playerinfo_df['team_pass'],1)
playerinfo_df['xThreat_100pass'] =  round(100*playerinfo_df['xThreat']/playerinfo_df['passes'],2)
playerinfo_df['xThreat_90'] =  round(90*playerinfo_df['xThreat']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_100teampass'] = round(100*playerinfo_df['xThreat']/playerinfo_df['team_pass'],3)
playerinfo_df['xThreat_gen_100pass'] =  round(100*playerinfo_df['xThreat_gen']/playerinfo_df['passes'],2)
playerinfo_df['xThreat_gen_90'] =  round(90*playerinfo_df['xThreat_gen']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_gen_100teampass'] = round(100*playerinfo_df['xThreat_gen']/playerinfo_df['team_pass'],3)

# Successful Passes
playerinfo_df['suc_passes_pct'] = round(100*playerinfo_df['suc_passes']/playerinfo_df['passes'],1)
playerinfo_df['suc_passes_90'] = round(90*playerinfo_df['suc_passes']/playerinfo_df['mins_played'],2)
playerinfo_df['suc_passes_100teampass'] = round(100*playerinfo_df['suc_passes']/playerinfo_df['team_pass'],1)

# Progressive Passes
playerinfo_df['prog_passes_pct'] = round(100*playerinfo_df['prog_passes']/playerinfo_df['passes'],1)
playerinfo_df['prog_passes_90'] = round(90*playerinfo_df['prog_passes']/playerinfo_df['mins_played'],2)
playerinfo_df['prog_passes_100teampass'] = round(100*playerinfo_df['prog_passes']/playerinfo_df['team_pass'],1)
playerinfo_df['suc_prog_passes_pct'] = round(100*playerinfo_df['suc_prog_passes']/playerinfo_df['passes'],1)
playerinfo_df['suc_prog_passes_pctpp'] = round(100*playerinfo_df['suc_prog_passes']/playerinfo_df['prog_passes'],1)
playerinfo_df['suc_prog_passes_90'] = round(90*playerinfo_df['suc_prog_passes']/playerinfo_df['mins_played'],2)
playerinfo_df['suc_prog_passes_100teampass'] = round(100*playerinfo_df['suc_prog_passes']/playerinfo_df['team_pass'],1)

# Successful progressive passes in opposition half
playerinfo_df['opphalf_prog_passes_pct'] = round(100*playerinfo_df['opphalf_prog_passes']/playerinfo_df['passes'],1)
playerinfo_df['opphalf_prog_passes_90'] = round(90*playerinfo_df['opphalf_prog_passes']/playerinfo_df['mins_played'],2)

# Forward passes
playerinfo_df['fwd_passes_pct'] = round(100*playerinfo_df['fwd_passes']/playerinfo_df['passes'],1)
playerinfo_df['fwd_passes_90'] = round(90*playerinfo_df['fwd_passes']/playerinfo_df['mins_played'],2)
playerinfo_df['suc_fwd_passes_pct'] = round(100*playerinfo_df['suc_fwd_passes']/playerinfo_df['passes'],1)
playerinfo_df['suc_fwd_passes_pctfwd'] = round(100*playerinfo_df['suc_fwd_passes']/playerinfo_df['fwd_passes'],1)
playerinfo_df['suc_fwd_passes_90'] = round(90*playerinfo_df['suc_fwd_passes']/playerinfo_df['mins_played'],2)

# Crosses
playerinfo_df['crosses_pct'] = round(100*playerinfo_df['crosses']/playerinfo_df['passes'],1)
playerinfo_df['crosses_90'] = round(90*playerinfo_df['crosses']/playerinfo_df['mins_played'],2)
playerinfo_df['suc_crosses_pct'] = round(100*playerinfo_df['suc_crosses']/playerinfo_df['passes'],1)
playerinfo_df['suc_crosses_pctcross'] = round(100*playerinfo_df['suc_crosses']/playerinfo_df['crosses'],1)
playerinfo_df['suc_crosses_90'] = round(90*playerinfo_df['suc_crosses']/playerinfo_df['mins_played'],2)

# Through balls
playerinfo_df['through_balls_pct'] = round(100*playerinfo_df['through_balls']/playerinfo_df['passes'],1)
playerinfo_df['through_balls_90'] = round(90*playerinfo_df['through_balls']/playerinfo_df['mins_played'],2)
playerinfo_df['suc_through_balls_pct'] = round(100*playerinfo_df['suc_through_balls']/playerinfo_df['passes'],1)
playerinfo_df['suc_through_balls_pcttb'] = round(100*playerinfo_df['suc_through_balls']/playerinfo_df['through_balls'],1)
playerinfo_df['suc_through_balls_90'] = round(90*playerinfo_df['suc_through_balls']/playerinfo_df['mins_played'],2)

# Long balls
playerinfo_df['long_balls_pct'] = round(100*playerinfo_df['long_balls']/playerinfo_df['passes'],1)
playerinfo_df['long_balls_90'] = round(90*playerinfo_df['long_balls']/playerinfo_df['mins_played'],2)
playerinfo_df['suc_long_balls_pct'] = round(100*playerinfo_df['suc_long_balls']/playerinfo_df['passes'],1)
playerinfo_df['suc_long_balls_pctlb'] = round(100*playerinfo_df['suc_long_balls']/playerinfo_df['long_balls'],1)
playerinfo_df['suc_long_balls_90'] = round(90*playerinfo_df['suc_long_balls']/playerinfo_df['mins_played'],2)

# Key Passes
playerinfo_df['key_passes_pct'] = round(100*playerinfo_df['key_passes']/playerinfo_df['passes'],1)
playerinfo_df['key_passes_90'] = round(90*playerinfo_df['key_passes']/playerinfo_df['mins_played'],2)

# Key Progressive Passes
playerinfo_df['key_prog_passes_pct'] = round(100*playerinfo_df['key_prog_passes']/playerinfo_df['passes'],1)
playerinfo_df['key_prog_passes_90'] = round(90*playerinfo_df['key_prog_passes']/playerinfo_df['mins_played'],2)

# Assists
playerinfo_df['assists_90'] = round(90*playerinfo_df['assists']/playerinfo_df['mins_played'],2)

# Pre-assists
playerinfo_df['pre_assists_90'] = round(90*playerinfo_df['pre_assists']/playerinfo_df['mins_played'],2)

# Passes into opposition box
playerinfo_df['box_passes_pct'] = round(100*playerinfo_df['box_passes']/playerinfo_df['passes'],1)
playerinfo_df['box_passes_90'] = round(90*playerinfo_df['box_passes']/playerinfo_df['mins_played'],2)
playerinfo_df['suc_box_passes_pct'] = round(100*playerinfo_df['suc_box_passes']/playerinfo_df['passes'],1)
playerinfo_df['suc_box_passes_pctbp'] = round(100*playerinfo_df['suc_box_passes']/playerinfo_df['box_passes'],1)
playerinfo_df['suc_box_passes_90'] = round(90*playerinfo_df['suc_box_passes']/playerinfo_df['mins_played'],2)

# %% Filter playerinfo

playerinfo_df = playerinfo_df[(playerinfo_df['mins_played']>=min_mins) & (~playerinfo_df['pos_type'].isin(pos_exclude))]
playerinfo_df = playerinfo_df[~playerinfo_df.index.duplicated(keep='first')]

# %% Order playerinfo for progressive pass plot

if norm_mode == None:
    pp_sorted_df = playerinfo_df.sort_values(['suc_prog_passes', 'suc_prog_passes_90'], ascending=[False, False])
    xt_sorted_df = playerinfo_df.sort_values(['xThreat_gen', 'xThreat_gen_90'], ascending=[False, False])
elif norm_mode == '_90':
    pp_sorted_df = playerinfo_df.sort_values(['suc_prog_passes_90', 'suc_prog_passes'], ascending=[False, False])
    xt_sorted_df = playerinfo_df.sort_values(['xThreat_gen_90', 'xThreat_gen'], ascending=[False, False])
elif norm_mode == '_100pass':
    pp_sorted_df = playerinfo_df.sort_values(['suc_prog_passes_pct', 'suc_prog_passes'], ascending=[False, False])
    xt_sorted_df = playerinfo_df.sort_values(['xThreat_gen_100pass', 'xThreat_gen'], ascending=[False, False])
elif norm_mode == '_100teampass':
    pp_sorted_df = playerinfo_df.sort_values(['suc_prog_passes_100teampass', 'suc_prog_passes'], ascending=[False, False])
    xt_sorted_df = playerinfo_df.sort_values(['xThreat_gen_100teampass', 'xThreat_gen'], ascending=[False, False])

# %% Plot formatting

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
mpl.rcParams['text.color'] = 'w'

# %% ------- VISUAL 1 - DIAMOND PLOT X VS Y METRIC -------

# Plotting metrics
left_metric = 'suc_box_passes_90'
right_metric = 'opphalf_prog_passes_90'
left_ax_plot = playerinfo_df[left_metric]
right_ax_plot = playerinfo_df[right_metric]

left_ax_plot.replace(np.nan, 0, inplace=True)
right_ax_plot.replace(np.nan, 0, inplace=True)

left_ax_norm_plot = 0.99 * left_ax_plot / max(left_ax_plot)
right_ax_norm_plot = 0.99 * right_ax_plot / max(right_ax_plot)

left_ax_quantile = left_ax_norm_plot.quantile([0.2,0.5,0.8]).tolist()
right_ax_quantile = right_ax_norm_plot.quantile([0.2,0.5,0.8]).tolist()

plot_quantile_left = left_ax_norm_plot.quantile([0,0.5,0.9]).tolist()
plot_quantile_right = right_ax_norm_plot.quantile([0,0.5,0.9]).tolist()
plot_player = playerinfo_df[(left_ax_norm_plot>plot_quantile_left[2]) | (right_ax_norm_plot>plot_quantile_right[2])]
#plot_player = playerinfo_df[playerinfo_df['team']=='Man Utd']

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
ax.axis['left'].set_label("Successful in-play passes into opp. box per 90mins")
ax.axis['left'].label.set_rotation(0)
ax.axis['left'].label.set_color("w")
ax.axis['left'].label.set_fontweight("bold")
ax.axis['left'].label.set_fontsize(9)
ax.axis['left'].LABELPAD += 7

ax.axis['bottom'].set_label("Successful in-play progressive passes within opp. half per 90mins")
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
    text.append(aux_ax.text(right_ax_norm_plot[i]+0.01, left_ax_norm_plot[i], format_name, color='w', fontsize=7, zorder=3, path_effects = path_eff))
adjustText.adjust_text(text, ax = aux_ax)

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
text_ax_left.text(0.23, 0.78, "Players towards this side\nof the grid frequently\npass the ball into the\nopposition box successfully", ha = "center", fontsize = 8, alpha=0.8)
text_ax_left.axis("off")
text_ax_left.set_xlim([0,1])
text_ax_left.set_ylim([0,1])

logo_ax_left = fig.add_axes([0.135,0.7,0.09,0.09])
box_logo = Image.open('..\..\data_directory\misc_data\images\BoxLogo.png')
logo_ax_left.imshow(box_logo)
logo_ax_left.axis("off")
logo_ax_left.set_aspect(0.55)

# Add right text axis
text_ax_right = fig.add_axes([0.5, 0.47, 0.415, 0.392])
text_ax_right.plot([0.61,0.41], [0.41,0.61], color = 'w', alpha = 0.9, lw=0.5)
text_ax_right.plot([0.51,0.64], [0.51,0.64], color = 'w', alpha = 0.9, lw=0.5)
text_ax_right.text(0.89, 0.71, "Players towards\nthis side of the\ngrid frequently play\nprogressive passes\nwithin the opposition\nhalf successfully", ha = "center", fontsize = 8, alpha = 0.8)
text_ax_right.axis("off")
text_ax_right.set_xlim([0,1])
text_ax_right.set_ylim([0,1])

logo_ax_right = fig.add_axes([0.72,0.73,0.1,0.1])
tackle_logo = Image.open('..\..\data_directory\misc_data\images\RecoveryLogo.png')
logo_ax_right.imshow(tackle_logo)
logo_ax_right.axis("off")

# Add bottom text axis
text_ax_bottom = fig.add_axes([0.085, 0.078, 0.415, 0.392])
text_ax_bottom.text(0.23, 0.05, f"Players with over {min_mins}\nmins played are included.\nShaded region represents\nplayers in the 20th to 80th\npercentile in either metric.", ha = "center", fontsize = 8, alpha = 0.8)
text_ax_bottom.axis("off")
text_ax_bottom.set_xlim([0,1])
text_ax_bottom.set_ylim([0,1])

title_text = f"{leagues[league]} {year}/{int(year) + 1}: Dangerous Passers"
subtitle_text = "Passes into Opposition Box & Progressive Passes within Opposition Half" 

# Title
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.905, subtitle_text, fontweight="regular", fontsize=13, color='w')

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
fig.savefig(f"player_effective_passers/{league}-{year}-diamond-{run_date.replace('/','_')}-{left_metric}-vs-{right_metric}-player-variant", dpi=300)

# %% ------- VISUAL 2 - TOP 12 PROGRESSIVE PASSERS -------

# Text formatting 
if norm_mode == None:
    title_addition = ''
    subsubtitle_addition = ''
elif norm_mode == '_90':
    title_addition = 'per 90mins'
    subsubtitle_addition = f"Players with less than {min_mins} mins play-time omitted."
elif norm_mode == '_100pass':
    title_addition = 'per 100 passes'
    subsubtitle_addition = f"Players with less than {min_mins} mins play-time omitted."
elif norm_mode == '_100teampass':
    title_addition = 'per 100 team passes'
    subsubtitle_addition = f"Players with less than {min_mins} mins play-time omitted." 
if len(pos_exclude)==0:
    title_pos_str = 'players'
    file_pos_str = ''
else:
    title_pos_str = pos_input
    file_pos_str = '-' + pos_input

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.75, space=0.12, axis=False)
fig.set_size_inches(14, 9)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Plot successful prog passes as arrows, using for loop to iterate through each player and each pass
idx = 0

for player_id, name in pp_sorted_df.head(12).iterrows():
    player_passes = suc_prog_passes[suc_prog_passes['playerId'] == player_id]
    player_assists = assists[assists['playerId'] == player_id]
    player_touch_assists = touch_assists[touch_assists['playerId'] == player_id]
    player_key_passes = key_prog_passes[key_prog_passes['playerId'] == player_id]

    ax['pitch'][idx].set_title(f"  {idx + 1}: {name['name']}", loc = "left", color='w', fontsize = 10)

    pitch.lines(player_passes['x'], player_passes['y'], player_passes['endX'], player_passes['endY'],
                lw = 2, comet=True, capstyle='round', label = 'Progressive Pass', color = 'cyan', transparent=True, alpha = 0.1, zorder=1, ax=ax['pitch'][idx])
  
    pitch.lines(player_key_passes['x'], player_key_passes['y'], player_key_passes['endX'], player_key_passes['endY'],
                lw = 2, comet=True, capstyle='round', label = 'Assists', color = 'lime', transparent=True, alpha = 0.5, zorder=2, ax=ax['pitch'][idx])
      
    pitch.lines(player_assists['x'], player_assists['y'], player_assists['endX'], player_assists['endY'],
            lw = 2, comet=True, capstyle='round', label = 'Assists', color = 'magenta', transparent=True, alpha = 0.5, zorder=3, ax=ax['pitch'][idx])

    pitch.scatter(player_touch_assists['x'], player_touch_assists['y'], color = 'magenta', alpha = 0.8, s = 12, zorder=3, ax=ax['pitch'][idx])

    ax['pitch'][idx].text(2, 4, "Total:", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(15, 4, f"{int(name['suc_prog_passes'])}", fontsize=8, color='w', zorder=3)
    
    if norm_mode == '_90':
        ax['pitch'][idx].text(2, 12, "/90 mins:", fontsize=8, fontweight='bold', color='w', zorder=3)
        ax['pitch'][idx].text(24, 12, f"{name['suc_prog_passes_90']}", fontsize=8, color='w', zorder=3) 
    elif norm_mode  == '_100pass':
        ax['pitch'][idx].text(2, 12, "/100 pass:", fontsize=8, fontweight='bold', color='w', zorder=3)
        ax['pitch'][idx].text(26, 12, f"{round(name['suc_prog_passes_pct'],1)}", fontsize=8, color='w', zorder=3)
    elif norm_mode  == '_100teampass':
        ax['pitch'][idx].text(2, 12, "/100 team pass:", fontsize=8, fontweight='bold', color='w', zorder=3)
        ax['pitch'][idx].text(38, 12, f"{round(name['suc_prog_passes_100teampass'],1)}", fontsize=8, color='w', zorder=3)
    
    team = name['team']
    team_logo, _ = lab.get_team_badge_and_colour(team)
            
    ax_pos = ax['pitch'][idx].get_position()
    
    logo_ax = fig.add_axes([ax_pos.x1-0.035, ax_pos.y1, 0.035, 0.035])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx += 1

# Create title and subtitles, using highlighting as figure legend
title_text = f"{leagues[league]} {year}/{int(year) + 1} - Top 12 {title_pos_str} by in-play progressive passes {title_addition}"
subtitle_text = f"<Successful Progressive Passes>, <Key Progressive Passes> and <Assists>"
subsubtitle_text = f"Correct as of {run_date}. {subsubtitle_addition}"
fig.text(0.1, 0.945, title_text, fontweight="bold", fontsize=14.5, color='w')
htext.fig_text(0.1, 0.93, s=subtitle_text, fontweight="regular", fontsize=13, color='w',
               highlight_textprops=[{"color": 'cyan', "fontweight": 'bold'}, {"color": 'lime', "fontweight": 'bold'},
                                    {"color": 'magenta', "fontweight": 'bold'}])
fig.text(0.1, 0.8875, subsubtitle_text, fontweight="regular", fontsize=10, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.05, 0.18, 0.01])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.03, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.04, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add competition logo
ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
ax.axis("off")
ax.imshow(comp_logo)

# Add twitter logo
ax = fig.add_axes([0.92, 0.025, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save image
fig.savefig(f"player_effective_passers/{league}-{year}-top-progressive-passers-{run_date.replace('/','_')}{file_pos_str.replace(' & ','-').replace(' ','-')}-{title_addition.replace(' ','-')}", dpi=300)


# %% ------- VISUAL 3 - TOP 12 THREAT CREATORS -------

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.75, space=0.12, axis=False)
fig.set_size_inches(14, 9)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Manual implentation of colourmap
pass_cmap = cm.get_cmap('viridis')
pass_cmap = pass_cmap(np.linspace(0.35,1,256))

# Plot successful prog passes as arrows, using for loop to iterate through each player and each pass
idx = 0

for player_id, name in xt_sorted_df.head(12).iterrows():
    player_passes = suc_passes[suc_passes['playerId'] == player_id].sort_values('xThreat_gen', ascending = True)
    
    ax['pitch'][idx].set_title(f"  {idx + 1}: {name['name']}", loc = "left", color='w', fontsize = 10)

    for _, pass_evt in player_passes.iterrows():
        if pass_evt['xThreat_gen'] < 0.005:
            line_colour = 'grey'
            line_alpha = 0.05
        else:
            line_colour = pass_cmap[int(255*min(pass_evt['xThreat_gen']/0.05, 1))]
            line_alpha = 0.7

        pitch.lines(pass_evt['x'], pass_evt['y'], pass_evt['endX'], pass_evt['endY'],
                    lw = 2, comet=True, capstyle='round', label = 'Pass', color = line_colour, transparent=True, alpha = line_alpha, zorder=1, ax=ax['pitch'][idx])

    ax['pitch'][idx].text(2, 4, "Total:", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(15, 4, f"{round(name['xThreat_gen'],2)}", fontsize=8, color='w', zorder=3)
    if norm_mode == '_90':
        ax['pitch'][idx].text(2, 12, "/90 mins:", fontsize=8, fontweight='bold', color='w', zorder=3)
        ax['pitch'][idx].text(24, 12, f"{name['xThreat_gen_90']}", fontsize=8, color='w', zorder=3)        
    if norm_mode  == '_100pass':
        ax['pitch'][idx].text(2, 12, "/100 pass:", fontsize=8, fontweight='bold', color='w', zorder=3)
        ax['pitch'][idx].text(26, 12, f"{round(name['xThreat_gen_100pass'],3)}", fontsize=8, color='w', zorder=3)
    elif norm_mode  == '_100teampass':
        ax['pitch'][idx].text(2, 12, "/100 team pass:", fontsize=8, fontweight='bold', color='w', zorder=3)
        ax['pitch'][idx].text(38, 12, f"{round(name['xThreat_gen_100teampass'],3)}", fontsize=8, color='w', zorder=3)
    
    team = name['team']
    team_logo, _ = lab.get_team_badge_and_colour(team)
            
    ax_pos = ax['pitch'][idx].get_position()
    
    logo_ax = fig.add_axes([ax_pos.x1-0.035, ax_pos.y1, 0.035, 0.035])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx += 1
    
# Create title and subtitles, using highlighting as figure legend
title_text = f"{leagues[league]} {year} - Top 12 {title_pos_str} by threat generated from in-play passes {title_addition}"
subtitle_text = f"<Low Threat> and <High Threat> Successful Passes Shown"
subsubtitle_text = f"Correct as of {run_date}. {subsubtitle_addition}"
fig.text(0.1, 0.945, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.1, 0.93, s=subtitle_text, fontweight="bold", fontsize=13, color='w',
               highlight_textprops=[{"color": 'grey', "fontweight": 'bold'}, {"color": 'yellow', "fontweight": 'bold'}])
fig.text(0.1, 0.8875, subsubtitle_text, fontweight="regular", fontsize=10, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.05, 0.18, 0.01])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.03, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add legend
legend_ax = fig.add_axes([0.275, 0.023, 0.2, 0.06])
legend_ax.axis("off")
plt.xlim([0, 8])
plt.ylim([0, 1])
hex_count = 6
path_eff = [path_effects.Stroke(linewidth=1.25, foreground='k'), path_effects.Normal()]


for idx in np.arange(0,hex_count):
    
    if idx%2 == 0:
        ypos = 0.36
    else:
        ypos= 0.64
    xpos = idx/1.05 + 2.5
    
    if idx == 0:
        xt = '<0.005'
        color = 'grey'
    elif idx == 1:
        xt = round(0.005 + (0.05-0.005) * ((idx-1)/(hex_count-2)),3)
        color = pass_cmap[int(255*(idx-1)/(hex_count-2))]
    else:
        xt = round(0.005 + (0.05-0.005) * ((idx-1)/(hex_count-2)),2)
        color = pass_cmap[int(255*(idx-1)/(hex_count-2))]
    
    legend_ax.scatter(xpos, ypos, marker='H', s=600, color=color, edgecolors=None)
    legend_ax.text(xpos+0.03, ypos-0.02, xt, color='w', fontsize = 8, ha = "center", va = "center", path_effects = path_eff)
    legend_ax.text(0.1, 0.5, "xThreat:", color='w', fontsize = 10, ha = "left", va = "center", fontweight="regular")

# Add footer text
fig.text(0.75, 0.04, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add competition logo
ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
ax.axis("off")
ax.imshow(comp_logo)

# Add twitter logo
ax = fig.add_axes([0.92, 0.025, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save image
fig.savefig(f"player_effective_passers/{league}-{year}-top-threat-generators-{run_date.replace('/','_')}{file_pos_str.replace(' & ','-').replace(' ','-')}-{title_addition.replace(' ','-')}", dpi=300)