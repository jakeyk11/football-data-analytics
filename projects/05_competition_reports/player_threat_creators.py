# %% Create multiple visualisations highlighting effective carriers over a competition
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Whoscored match ids
#           Positions not to include
#           Normalisation mode
#           Date of run
#           Minimum play time
#
# Outputs:  Top 12 Progressive Carriers
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
run_date = '30/12/2022'

# Normalisation mode
norm_mode = '_90'

# Min minutes played (only used if normalising)
min_mins = 450

# Brighten logo
logo_brighten = True

# %% League logo and league naming

if logo_brighten:
    comp_logo = lab.get_competition_logo(league, year)
    enhancer = ImageEnhance.Brightness(comp_logo)
    comp_logo = enhancer.enhance(100)
else:
    comp_logo = lab.get_competition_logo(league, year)
    
# Create title and subtitles
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup'}

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

# Add cumulative minutes information
events_df = wde.cumulative_match_mins(events_df)
players_df = wde.minutes_played(players_df, events_df)

# Add ball carries
events_df = wce.insert_ball_carries(events_df)

# Add expected threat information
events_df = wce.get_xthreat(events_df, interpolate = True)

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df)

# Carries and total xT
all_carries = events_df[events_df['eventType']=='Carry']
playerinfo_df = wde.group_player_events(all_carries, playerinfo_df, primary_event_name='carries')
playerinfo_df = wde.group_player_events(all_carries, playerinfo_df, group_type='sum', event_types = ['xThreat', 'xThreat_gen'])
playerinfo_df.rename(columns = {'xThreat':'xThreat_carry','xThreat_gen':'xThreat_gen_carry'}, inplace=True)

# Passes and total xT
all_passes = events_df[(events_df['eventType']=='Pass') & (~events_df['satisfiedEventsTypes'].apply(lambda x: 31 in x or 32 in x or 33 in x or 34 in x or 212 in x))]
playerinfo_df = wde.group_player_events(all_passes, playerinfo_df, primary_event_name='passes')
playerinfo_df = wde.group_player_events(all_passes, playerinfo_df, group_type='sum', event_types = ['xThreat', 'xThreat_gen'])
playerinfo_df.rename(columns = {'xThreat':'xThreat_pass','xThreat_gen':'xThreat_gen_pass'}, inplace=True)

# %% Calculate statistics per 90 mins

# Carries and xT generated
playerinfo_df['carries_90'] = round(90*playerinfo_df['carries']/playerinfo_df['mins_played'],2)
playerinfo_df['xThreat_carry_90'] = round(90*playerinfo_df['xThreat_carry']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_gen_carry_90'] = round(90*playerinfo_df['xThreat_gen_carry']/playerinfo_df['mins_played'],3)

# Passes and xT generated
playerinfo_df['passes_90'] =  round(90*playerinfo_df['passes']/playerinfo_df['mins_played'],2)
playerinfo_df['xThreat_pass_90'] =  round(90*playerinfo_df['xThreat_pass']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_gen_pass_90'] =  round(90*playerinfo_df['xThreat_gen_pass']/playerinfo_df['mins_played'],3)

# %% Filter playerinfo

playerinfo_df = playerinfo_df[(playerinfo_df['mins_played']>=min_mins) & (~playerinfo_df['pos_type'].isin(pos_exclude))]
playerinfo_df = playerinfo_df[~playerinfo_df.index.duplicated(keep='first')]

# %% Plot formatting

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
mpl.rcParams['text.color'] = 'w'

# %% ------- VISUAL 1 - DIAMOND PLOT XTHREAT -------

# Plotting metrics
left_metric = 'xThreat_gen_pass_90'
right_metric = 'xThreat_gen_carry_90'
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
plot_player = playerinfo_df#[(left_ax_norm_plot>plot_quantile_left[2]) | (right_ax_norm_plot>plot_quantile_right[2])]

plot_player = playerinfo_df[playerinfo_df['team']=='Man Utd']

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
        left_dict[i] = str(round((i * left_ax_plot.max())/0.99,3))
        right_dict[i] = str(round((i * right_ax_plot.max())/0.99,3))
    
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
ax.axis['left'].set_label("xT created through successful in-play passes per 90mins")
ax.axis['left'].label.set_rotation(0)
ax.axis['left'].label.set_color("w")
ax.axis['left'].label.set_fontweight("bold")
ax.axis['left'].label.set_fontsize(9)
ax.axis['left'].LABELPAD += 7

ax.axis['bottom'].set_label("xT created through successful carries per 90mins")
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
text_ax_left.text(0.08, 0.73, "Players towards this\nside of the grid\ncreate significant threat\nthrough playing passes", ha = "center", fontsize = 8, alpha=0.8)
text_ax_left.axis("off")
text_ax_left.set_xlim([0,1])
text_ax_left.set_ylim([0,1])

logo_ax_left = fig.add_axes([0.19,0.73,0.1,0.1])
box_logo = Image.open('..\..\data_directory\misc_data\images\PassLogo.png')
logo_ax_left.imshow(box_logo)
logo_ax_left.axis("off")
logo_ax_left.set_aspect(0.55)

# Add right text axis
text_ax_right = fig.add_axes([0.5, 0.47, 0.415, 0.392])
text_ax_right.plot([0.61,0.41], [0.41,0.61], color = 'w', alpha = 0.9, lw=0.5)
text_ax_right.plot([0.51,0.64], [0.51,0.64], color = 'w', alpha = 0.9, lw=0.5)
text_ax_right.text(0.91, 0.73, "Players towards this\nside of the grid\ncreate significant threat\nthrough ball carries", ha = "center", fontsize = 8, alpha = 0.8)
text_ax_right.axis("off")
text_ax_right.set_xlim([0,1])
text_ax_right.set_ylim([0,1])

logo_ax_right = fig.add_axes([0.72,0.73,0.1,0.1])
tackle_logo = Image.open('..\..\data_directory\misc_data\images\CarryLogo.png')
logo_ax_right.imshow(tackle_logo)
logo_ax_right.axis("off")

# Add bottom text axis
text_ax_bottom = fig.add_axes([0.085, 0.078, 0.415, 0.392])
text_ax_bottom.text(0.23, 0.05, f"Players with over {min_mins}\nmins played are included.\nShaded region represents\nplayers in the 20th to 80th\npercentile in either metric.", ha = "center", fontsize = 8, alpha = 0.8)
text_ax_bottom.axis("off")
text_ax_bottom.set_xlim([0,1])
text_ax_bottom.set_ylim([0,1])

title_text = f"{leagues[league]} {year}/{int(year) + 1}: Threat Creators"
subtitle_text = "Threat Created through Successful In-Play Passes and Carries" 

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
fig.savefig(f"player_threat_creators/{league}-{year}-diamond-{run_date.replace('/','_')}-{left_metric}-vs-{right_metric}-player-variant", dpi=300)
