# %% Create threat creators by zone visual for Europes top 5 leagues

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

# Data to use
data_grab = [['La_Liga', '2022'],
             ['EPL', '2022'],
             ['Serie_A', '2022'],
             ['Bundesliga', '2022'],
             ['Ligue_1', '2022']]

# Select position to exclude
pos_exclude=['GK']

# Position formatting on title
pos_input = 'forwards'

# Input run-date
run_date = '07/04/2023'

# Normalisation mode
norm_mode = '_90'

# Min minutes played (only used if normalising)
min_mins = 900

# Threat pitch grid mode (3 = top 3, else = top 1. dense = dense grid, else = sparse grid)
pitch_mode = '1'
grid_density = 'sparse'

#%% Get logos

logo = lab.get_competition_logo(data_grab[0][0], data_grab[0][1]) 
epl_logo = lab.get_competition_logo('EPL', logo_brighten = True) 
bundesliga_logo = lab.get_competition_logo('Bundesliga') 
ligue1_logo = lab.get_competition_logo('Ligue_1') 
seriea_logo = lab.get_competition_logo('Serie_A') 
laliga_logo = lab.get_competition_logo('La_Liga')

# %% Calculate year range

min_year = int(data_grab[0][1])
max_year = int(data_grab[0][1])

for data in data_grab:
    year = int(data[1])
    min_year = year if year < min_year else min_year
    max_year = year if year > max_year else max_year

# %% Create titles

# Create title and subtitles
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup'}

# Add titles
title_str = "Europe Big Five Leagues"
    
if min_year == max_year:
    year_str = f"{min_year}"
else:
    year_str = f"{min_year}-{max_year}"

# %% Get data

# Initialise storage dataframes
events_df = pd.DataFrame()
players_df = pd.DataFrame()

for data in data_grab:
    league = data[0]
    year = data[1]
    league_events = pd.DataFrame()
    league_players = pd.DataFrame()
    
    file_path = f"../../data_directory/whoscored_data/{data[1]}_{str(int(data[1].replace('20','')) + 1)}/{data[0]}"
    files = os.listdir(file_path)
    idx=1
    
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
            league_events = pd.concat([league_events, match_events])
            print(f"event file {idx}/{int((len(files))/2-1)} loaded")
            idx+=1
        elif '-playerdata-' in file:
            match_players = bz2.BZ2File(f"{file_path}/{file}", 'rb')
            match_players = pickle.load(match_players)
            league_players = pd.concat([league_players, match_players])
        else:
            pass
    
    events_df = pd.concat([events_df, league_events])
    players_df = pd.concat([players_df, league_players])
    print(f"{league}, {year} data import complete")

# %% Add cumulative minutes information

players_df = wde.minutes_played(players_df, events_df)

# %% Get relevant events

all_carries = events_df[events_df['eventType']=='Carry']
all_passes = events_df[(events_df['eventType']=='Pass') & (~events_df['satisfiedEventsTypes'].apply(lambda x: 31 in x or 32 in x or 33 in x or 34 in x or 212 in x))]
all_threat_events = pd.concat([all_carries, all_passes], axis = 0)

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df)

# %% Account for players that have played for multiple teams

# Sum mins played for each player, into new dataframe
playerinfo_mp = playerinfo_df.groupby(by='playerId', axis=0).sum()

# Retain the player entry against the club he's played the most minutes for
playerinfo_df = playerinfo_df.sort_values('mins_played', ascending = False)
playerinfo_df = playerinfo_df[~playerinfo_df.index.duplicated(keep='first')]

# Remove minutes played info and use the summed minutes
playerinfo_df = playerinfo_df.drop('mins_played', axis=1).join(playerinfo_mp)

# %% Calculate player threat creation per zone

pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)

for player_id, player_details in playerinfo_df.iterrows():
    player_events = all_threat_events[all_threat_events['playerId']==player_id]
    bin_statistic = pitch.bin_statistic(player_events['x'], player_events['y'],
                                        statistic='sum', bins=(12, 10) if grid_density == 'dense' else (6, 5) , normalize=False, values = player_events['xThreat_gen'])
    bin_statistic['statistic'] = 90*(bin_statistic['statistic']/player_details['mins_played'])
    
    for idx, zone_threat in enumerate(bin_statistic['statistic'].reshape(-1, order = 'F')):
        playerinfo_df.loc[player_id, f'zone_{idx}_xT' ] = zone_threat

# %% Aggregate xT per player

# Carries and total xT
playerinfo_df = wde.group_player_events(all_carries, playerinfo_df, primary_event_name='carries')
playerinfo_df = wde.group_player_events(all_carries, playerinfo_df, group_type='sum', event_types = ['xThreat', 'xThreat_gen'])
playerinfo_df.rename(columns = {'xThreat':'xThreat_carry','xThreat_gen':'xThreat_gen_carry'}, inplace=True)

# Passes and total xT
playerinfo_df = wde.group_player_events(all_passes, playerinfo_df, primary_event_name='passes')
playerinfo_df = wde.group_player_events(all_passes, playerinfo_df, group_type='sum', event_types = ['xThreat', 'xThreat_gen'])
playerinfo_df.rename(columns = {'xThreat':'xThreat_pass','xThreat_gen':'xThreat_gen_pass'}, inplace=True)

# Carries and xT generated
playerinfo_df['carries_90'] = round(90*playerinfo_df['carries']/playerinfo_df['mins_played'],2)
playerinfo_df['xThreat_carry_90'] = round(90*playerinfo_df['xThreat_carry']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_gen_carry_90'] = round(90*playerinfo_df['xThreat_gen_carry']/playerinfo_df['mins_played'],3)

# Passes and xT generated
playerinfo_df['passes_90'] =  round(90*playerinfo_df['passes']/playerinfo_df['mins_played'],2)
playerinfo_df['xThreat_pass_90'] =  round(90*playerinfo_df['xThreat_pass']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_gen_pass_90'] =  round(90*playerinfo_df['xThreat_gen_pass']/playerinfo_df['mins_played'],3)

# Total xT
playerinfo_df['xThreat_gen_90'] =  playerinfo_df['xThreat_gen_pass_90'] + playerinfo_df['xThreat_gen_carry_90'] 

# %% Isolate/include specific players

specific_label = ["Real Sociedad"]
specific_label_c = 'b'

# %% Filter playerinfo

playerinfo_df = playerinfo_df[((playerinfo_df['mins_played']>=min_mins) & (~playerinfo_df['pos_type'].isin(pos_exclude))) | (playerinfo_df['name'].isin(specific_label))]
playerinfo_df = playerinfo_df[~playerinfo_df.index.duplicated(keep='first')]

# %% Plot formatting

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
mpl.rcParams['text.color'] = 'w'

# %% ------- VISUAL 1 - TOP THREAT CREATORS BY ZONE -------

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
title_text = f"{title_str} {year}/{int(year)+1} − Threat Creators"
subtitle_text = f"Top Threat Creator{title_plural} from each Pitch Zone"
subsubtitle_text = f"In-Play Pass, Carry and Dribble events included. Negative threat events excluded.\nOnly includes {pos_input} with >{min_mins} total mins played. Correct as of {run_date}"
fig.text(0.17, 0.945, title_text, fontweight="bold", fontsize=13, color='w')
fig.text(0.17, 0.9175, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.17, 0.8775, subsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add competition logo
ax = fig.add_axes([0.018, 0.915, 0.05, 0.05])
ax.axis("off")
ax.imshow(epl_logo)
ax = fig.add_axes([0.06, 0.915, 0.05, 0.05])
ax.axis("off")
ax.imshow(ligue1_logo)
ax = fig.add_axes([0.105, 0.916, 0.048, 0.048])
ax.axis("off")
ax.imshow(seriea_logo)
ax = fig.add_axes([0.044, 0.87, 0.045, 0.045])
ax.axis("off")
ax.imshow(bundesliga_logo)
ax = fig.add_axes([0.09, 0.868, 0.05, 0.05])
ax.axis("off")
ax.imshow(laliga_logo)

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
fig.savefig(f"../05_competition_reports_top_players_opta/player_threat_creators/europe_big_five-{year}-top_threat_creator_by_zone-{file_ext}-{run_date.replace('/','_')}", dpi=300)

# %% ------- VISUAL 2 - DIAMOND PLOT XTHREAT -------

# Plotting metrics
left_metric = 'xThreat_gen_pass_90'
right_metric = 'xThreat_gen_carry_90'
show_top_pct = 2
left_ax_plot = playerinfo_df[left_metric]
right_ax_plot = playerinfo_df[right_metric]

left_ax_plot.replace(np.nan, 0, inplace=True)
right_ax_plot.replace(np.nan, 0, inplace=True)

left_ax_norm_plot = 0.99 * left_ax_plot / max(left_ax_plot)
right_ax_norm_plot = 0.99 * right_ax_plot / max(right_ax_plot)

left_ax_quantile = left_ax_norm_plot.quantile([0.2,0.5,0.8]).tolist()
right_ax_quantile = right_ax_norm_plot.quantile([0.2,0.5,0.8]).tolist()

if len(specific_label) == 0:
    plot_quantile_left = left_ax_norm_plot.quantile([0,0.5,(100-show_top_pct)/100]).tolist()
    plot_quantile_right = right_ax_norm_plot.quantile([0,0.5,(100-show_top_pct)/100]).tolist()
    plot_player = playerinfo_df[(left_ax_norm_plot>plot_quantile_left[2]) | (right_ax_norm_plot>plot_quantile_right[2])]
else:
    plot_player = playerinfo_df[(playerinfo_df['name'].isin(specific_label)) |
                                (playerinfo_df['team'].isin(specific_label))]

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

if len(specific_label)!=0:
    aux_ax.scatter(0.99*plot_player[right_metric] / max(right_ax_plot), 0.99*plot_player[left_metric] / max(left_ax_plot), c = specific_label_c, edgecolor = 'w', s = 50, lw = 0.3, zorder=2)

# Add text
text = list()
path_eff = [path_effects.Stroke(linewidth=1.5, foreground='#313332'), path_effects.Normal()]
for i, player in plot_player.iterrows():
    format_name =  player['name'].split(' ')[0][0] + " " + player['name'].split(' ')[len(player['name'].split(' '))-1] if len(player['name'].split(' '))>1 else player['name']
    text.append(aux_ax.text(right_ax_norm_plot[i]+0.01, left_ax_norm_plot[i], format_name, color='w', fontsize=7, zorder=3, path_effects = path_eff))
adjustText.adjust_text(text, ax = ax, expand_text=(0.1,1.5))

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

logo_ax_left = fig.add_axes([0.19,0.73,0.11,0.1])
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

title_text = f"{title_str} {year}/{int(year)+1} − Threat Creators"
subtitle_text = "Threat Created through Successful In-Play Passes and Carries" 

# Title
fig.text(0.16, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.16, 0.905, subtitle_text, fontweight="regular", fontsize=13, color='w')

# Add competition logo
ax = fig.add_axes([0.018, 0.925, 0.05, 0.05])
ax.axis("off")
ax.imshow(epl_logo)
ax = fig.add_axes([0.06, 0.925, 0.05, 0.05])
ax.axis("off")
ax.imshow(ligue1_logo)
ax = fig.add_axes([0.105, 0.926, 0.048, 0.048])
ax.axis("off")
ax.imshow(seriea_logo)
ax = fig.add_axes([0.044, 0.88, 0.045, 0.045])
ax.axis("off")
ax.imshow(bundesliga_logo)
ax = fig.add_axes([0.09, 0.878, 0.05, 0.05])
ax.axis("off")
ax.imshow(laliga_logo)

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
fig.savefig(f"../05_competition_reports_top_players_opta/player_threat_creators/europe_big_five-{year}-diamond-{run_date.replace('/','_')}-{left_metric}-vs-{right_metric}-player-variant", dpi=300)
