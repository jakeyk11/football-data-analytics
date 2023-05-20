# %% Create multiple visualisations highlighting effective carriers over a competition
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Positions not to include, and position title formatting 
#           Normalisation mode
#           Minimum play time
#           Date of run
#           Brighten logo
#           Threat grid pitch mode
#           Threat grid density
#
# Outputs:  Top threat creators (scatter)
#           Top threat creators by pitch zone

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
from mplsoccer.pitch import Pitch, VerticalPitch
from mplsoccer import add_image
from matplotlib.colors import ListedColormap
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

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
league = 'EFLC'

# Select position to exclude
pos_exclude=['GK']

# Position formatting on title
pos_input = 'outfield players'

# Input run-date
run_date = '08/05/2023'

# Normalisation mode
norm_mode = '_90'

# Min minutes played (only used if normalising)
min_mins = 1800

# Brighten logo
logo_brighten = False

# Threat pitch grid mode (3 = top 3, else = top 1. dense = dense grid, else = sparse grid)
pitch_mode = '1'
grid_density = 'sparse'

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

# %% Tag in-play successful box entries and progressive acions

events_df['progressive'] = events_df.apply(wce.progressive_action, axis=1, inplay = True, successful_only = True)
events_df['box_entry'] = events_df.apply(wce.box_entry, axis=1, inplay = True, successful_only = True)

# %% Create player dataframe and account for players that have played for multiple teams

playerinfo_df = wde.create_player_list(players_df)

# Sum mins played for each player, into new dataframe
playerinfo_mp = playerinfo_df.groupby(by='playerId', axis=0).sum()

# Retain the player entry against the club he's played the most minutes for
playerinfo_df = playerinfo_df.sort_values('mins_played', ascending = False)
playerinfo_df = playerinfo_df[~playerinfo_df.index.duplicated(keep='first')]

# Remove minutes played info and use the summed minutes
playerinfo_df = playerinfo_df.drop('mins_played', axis=1).join(playerinfo_mp)

# %% Aggregate data per player

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

# Box entries and progresive actions
playerinfo_df = wde.group_player_events(all_passes[all_passes['box_entry']==True], playerinfo_df, primary_event_name='pass_into_box')
playerinfo_df = wde.group_player_events(all_carries[all_carries['box_entry']==True], playerinfo_df, primary_event_name='carry_into_box')
playerinfo_df = wde.group_player_events(all_passes[all_passes['progressive']==True], playerinfo_df, primary_event_name='progressive_pass')
playerinfo_df = wde.group_player_events(all_carries[all_carries['progressive']==True], playerinfo_df, primary_event_name='progressive_carry')

# Aggregate carries
playerinfo_df['carries_90'] = round(90*playerinfo_df['carries']/playerinfo_df['mins_played'],2)
playerinfo_df['xThreat_carry_90'] = round(90*playerinfo_df['xThreat_carry']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_gen_carry_90'] = round(90*playerinfo_df['xThreat_gen_carry']/playerinfo_df['mins_played'],3)
playerinfo_df['box_carries_90'] = round(90*playerinfo_df['carry_into_box']/playerinfo_df['mins_played'],2)
playerinfo_df['prog_carries_90'] = round(90*playerinfo_df['progressive_carry']/playerinfo_df['mins_played'],2)

# Aggregate passes
playerinfo_df['passes_90'] =  round(90*playerinfo_df['passes']/playerinfo_df['mins_played'],2)
playerinfo_df['xThreat_pass_90'] =  round(90*playerinfo_df['xThreat_pass']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_gen_pass_90'] =  round(90*playerinfo_df['xThreat_gen_pass']/playerinfo_df['mins_played'],3)
playerinfo_df['box_passes_90'] = round(90*playerinfo_df['pass_into_box']/playerinfo_df['mins_played'],2)
playerinfo_df['prog_passes_90'] = round(90*playerinfo_df['progressive_pass']/playerinfo_df['mins_played'],2)

# Aggregate carries + passes
playerinfo_df['box_actions'] = playerinfo_df['pass_into_box'] + playerinfo_df['carry_into_box']
playerinfo_df['box_actions_90'] = playerinfo_df['box_passes_90'] + playerinfo_df['box_carries_90']
playerinfo_df['prog_actions_90'] = playerinfo_df['prog_passes_90'] + playerinfo_df['prog_carries_90']

# Threat creating events
all_threat_events = pd.concat([all_carries, all_passes], axis = 0)

# %% Calculate player threat creation per zone

pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)

for player_id, player_details in playerinfo_df.iterrows():
    player_events = all_threat_events[all_threat_events['playerId']==player_id]
    bin_statistic = pitch.bin_statistic(player_events['x'], player_events['y'],
                                        statistic='sum', bins=(12, 10) if grid_density == 'dense' else (6, 5) , normalize=False, values = player_events['xThreat_gen'])
    bin_statistic['statistic'] = 90*(bin_statistic['statistic']/player_details['mins_played'])
    
    for idx, zone_threat in enumerate(bin_statistic['statistic'].reshape(-1, order = 'F')):
        playerinfo_df.loc[player_id, f'zone_{idx}_xT' ] = zone_threat

# %% Filter playerinfo

playerinfo_df = playerinfo_df[(playerinfo_df['mins_played']>=min_mins) & (~playerinfo_df['pos_type'].isin(pos_exclude))]
playerinfo_df = playerinfo_df[~playerinfo_df.index.duplicated(keep='first')]

playerinfo_df = playerinfo_df[playerinfo_df['name']!='João Cancelo']

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

plot_quantile_left = left_ax_norm_plot.quantile([0,0.5,0.95]).tolist()
plot_quantile_right = right_ax_norm_plot.quantile([0,0.5,0.95]).tolist()
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

# %% ------- VISUAL 2 - TOP THREAT CREATORS BY ZONE -------

fig, ax = pitch.grid(endnote_height=0.05, endnote_space=0, title_height=0.12, axis=False, grid_height=0.79)
fig.set_size_inches(7, 9)
fig.set_facecolor('#313332')

# Draw Pitch Zones
pitch.heatmap(bin_statistic, ax=ax['pitch'], cmap = ListedColormap(['#313332']), edgecolor='grey', lw=0.5, alpha = 1, zorder = 0.6)

# Label players
xs = bin_statistic['cx'].reshape(-1, order = 'F')
ys = bin_statistic['cy'].reshape(-1, order = 'F')
path_eff = [path_effects.Stroke(linewidth=2, foreground='#313332'), path_effects.Normal()]

for idx in np.arange(0, len(bin_statistic['statistic'].reshape(-1))):
    playerinfo_df.sort_values(by = f'zone_{idx}_xT', ascending = False, inplace = True)
    if pitch_mode == '3' and grid_density != 'dense':
        cnt = 0
        for p_id, p_info in playerinfo_df.head(3).iterrows():
            player_name = p_info['name']
            format_name = player_name.split(' ')[0][0] + ". " + player_name.split(' ')[len(player_name.split(' '))-1] if len(player_name.split(' '))>1 else player_name
            format_name = format_name if len(format_name) <= 13 else format_name[0:11] + '...'
            format_text = format_name + '\n' + 'xT: ' +str(round(p_info[f'zone_{idx}_xT'],3))
            team_logo, _ = lab.get_team_badge_and_colour(p_info['team'])
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.05, resample = True), (ys[idx]+6.75, xs[idx]+5-cnt), frameon=False)
            ax['pitch'].add_artist(ab)
            pitch.annotate(text = format_text, xy = (xs[idx]+5-cnt, ys[idx]+3.5), ha = "left", va = "center", ax=ax['pitch'], fontsize = 6, path_effects=path_eff)
            cnt+=5
        title_plural = 's'
        file_ext = 'top3'
    else:
        player_name = playerinfo_df.head(1)['name'].values[0]
        format_name = player_name.split(' ')[0][0] + ". " + player_name.split(' ')[len(player_name.split(' '))-1] if len(player_name.split(' '))>1 else player_name
        format_name = format_name if len(format_name) <= 13 else format_name[0:13] + '\n' + format_name[13:]
        format_text = format_name + '\n' + 'xT: ' +str(round(playerinfo_df.head(1)[f'zone_{idx}_xT'].values[0],3))
        team_logo, _ = lab.get_team_badge_and_colour(playerinfo_df.head(1)['team'].values[0])
        title_plural = ''
        if grid_density == 'dense':
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.05, resample = True), (ys[idx], xs[idx]+2), frameon=False)
            pitch.annotate(text = format_text, xy = (xs[idx]-0.5, ys[idx]), ha = "center", va = "top", ax=ax['pitch'], fontsize = 5, path_effects=path_eff)
            file_ext = 'top1-dense'
        else:
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.1, resample = True), (ys[idx], xs[idx]+2.5), frameon=False)
            pitch.annotate(text = format_text, xy = (xs[idx]-2.5, ys[idx]), ha = "center", va = "top", ax=ax['pitch'], fontsize = 8, path_effects=path_eff)
            file_ext = 'top1'
        ax['pitch'].add_artist(ab)
        
# Title
title_text = f"{leagues[league]} {year}/{int(year)+1} − Threat Creators"
subtitle_text = f"Top Threat Creator{title_plural} from each Pitch Zone"
subsubtitle_text = f"In-Play Pass, Carry and Dribble events included. Negative threat events excluded.\nOnly includes {pos_input} with >{min_mins} total mins played. Correct as of {run_date}"
fig.text(0.17, 0.945, title_text, fontweight="bold", fontsize=13, color='w')
fig.text(0.17, 0.9175, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.17, 0.8775, subsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add competition logo
ax = fig.add_axes([0.03, 0.85, 0.14, 0.14])
ax.axis("off")
ax.imshow(comp_logo)

# Add direction of play arrow
ax = fig.add_axes([0.85, 0.31, 0.01, 0.3])
ax.axis("off")
plt.arrow(0.5, 0.15, 0, 0.5, width = 0.004, color="white")
fig.text(0.875, 0.4, "Direction of play", ha="center", rotation=270, fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.5, 0.025, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.91, -0.005, 0.07, 0.07])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

# Save image
fig.savefig(f"player_threat_creators/{league}-{year}-top_threat_creator_by_zone-{file_ext}-{run_date.replace('/','_')}", dpi=300)

# %% ------- VISUAL 3 - TOP 20 BOX ENTRIES -------

# Order dataframe
be_sorted_df = playerinfo_df.sort_values('box_actions_90', ascending=False)

# Define custom colourmap
CustomCmap = mpl.colors.LinearSegmentedColormap.from_list("", ["#313332","#47516B", "#848178", "#B2A66F", "#FDE636"])

# Set-up pitch subplots
pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, half=True, stripe=False)
fig, ax = pitch.grid(nrows=4, ncols=5, grid_height=0.79, title_height = 0.15, endnote_height = 0.04, space=0.1, axis=False)
fig.set_size_inches(12, 10)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)
idx = 0

# Iterate through top players
for player_id, name in be_sorted_df.head(20).iterrows():
    
    # Get box entries
    player_box_entries = events_df[(events_df['box_entry']==True) & (events_df['playerId'] == player_id)]
    
    # Format and print player name
    format_name =  name['name'].split(' ')[0][0] + " " + name['name'].split(' ')[len(name['name'].split(' '))-1] if len(name['name'].split(' '))>1 else name['name']
    ax['pitch'][idx].set_title(f"  {idx + 1}: {format_name}", loc = "left", color='w', fontsize = 10, pad=-2)

    # Plot density of start positions of box entries
    kde_plot = pitch.kdeplot(player_box_entries['x'], player_box_entries['y'], ax=ax['pitch'][idx],
                              fill=True, levels=100, shade_lowest=True,
                              cut=4, cmap=CustomCmap, zorder=0)
    
    # Scatter starting points
    pitch.scatter(player_box_entries['x'], player_box_entries['y'], color = 'w', alpha = 0.4, s = 12, zorder=1, ax=ax['pitch'][idx])
    
    # Plot polygon within penalty box
    ax['pitch'][idx].fill([21.1, 78.9, 78.9, 21.1], [83, 83, 100, 100], '#313332', alpha = 1, zorder=0)
        
    # Add text 
    ax['pitch'][idx].text(96, 58, "Total:", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(96, 53, f"{int(name['box_actions'])}", fontsize=8, color='w', zorder=3)
    if norm_mode == '_90':
        ax['pitch'][idx].text(4, 58, "/90 mins:", fontsize=8, fontweight='bold', color='w', zorder=3, ha = 'right')
        ax['pitch'][idx].text(4, 53, f"{round(name['box_actions_90'],2)}", fontsize=8, color='w', zorder=3, ha = 'right')        
    
    team = name['team']
    team_logo, _ = lab.get_team_badge_and_colour(team)
            
    ax_pos = ax['pitch'][idx].get_position()
    
    logo_ax = fig.add_axes([ax_pos.x1-0.03, ax_pos.y1-0.002, 0.025, 0.025])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx += 1

# Title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League 1', 'EFL2': 'EFL League 2'}

title_text = f"{leagues[league]} {year}/{int(year)+1} − Players Ranked by Box Entries per 90"
subtitle_text = "Heatmaps showing <Distribution> in starting position of player box entries"
subsubtitle_text = f"Box entry defined as in-play pass or carry that begins outside and ends inside the opposition box. Includes players with >{min_mins} total mins played."

fig.text(0.11, 0.945, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.11, 0.933, s=subtitle_text, fontweight="bold", fontsize=13, color='w',
               highlight_textprops=[{"color": "yellow", "fontweight": 'bold'}])
fig.text(0.11, 0.894, subsubtitle_text, fontweight="regular", fontsize=10, color='w')
    
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

fig.savefig(f"player_threat_creators/{league}-{year}-player-box-entries", dpi=300)
