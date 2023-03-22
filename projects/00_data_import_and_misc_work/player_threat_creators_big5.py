# %% Create threat creators by zone visual for Europes top 5 leagues

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
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
pos_input = 'outfield players'

# Input run-date
run_date = '19/03/2023'

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
            match_events = wde.cumulative_match_mins(match_events)
            match_events = wce.insert_ball_carries(match_events)
            match_events = wce.get_xthreat(match_events, interpolate = True)
            events_df = pd.concat([events_df, match_events])
            print(f"event file {idx}/{int((len(files))/2-2)} loaded")
            idx+=1
        elif '-playerdata-' in file:
            match_players = bz2.BZ2File(f"{file_path}/{file}", 'rb')
            match_players = pickle.load(match_players)
            players_df = pd.concat([players_df, match_players])
        else:
            pass
            
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

# %% Filter playerinfo based on minutes played

playerinfo_df = playerinfo_df[(playerinfo_df['mins_played']>=min_mins) & (~playerinfo_df['pos_type'].isin(pos_exclude))]
playerinfo_df = playerinfo_df[playerinfo_df['name']!='Paul Joly']

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