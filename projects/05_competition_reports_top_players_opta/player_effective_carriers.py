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
league = 'EFLC'

# Select position to exclude
pos_exclude=['GK']

# Position formatting on title
pos_input = 'outfield players'

# Input run-date
run_date = '09/02/2023'

# Normalisation mode
norm_mode = '_90'

# Min minutes played (only used if normalising)
min_mins = 900

# Brighten logo
logo_brighten = False

# %% League logo and league naming

comp_logo = lab.get_competition_logo(league, year, logo_brighten)
    
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

# Calculate longest consistent xi
players_df = wde.longest_xi(players_df)

# Add progressive pass and box entry information to event dataframe
events_df['progressive_carry'] = events_df.apply(wce.progressive_carry, axis=1)
events_df['carry_into_box'] = events_df.apply(wce.carry_into_box, axis=1)

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df)

# Passes and total xT
all_carries = events_df[events_df['eventType']=='Carry']
playerinfo_df = wde.group_player_events(all_carries, playerinfo_df, primary_event_name='carries')
playerinfo_df = wde.group_player_events(all_carries, playerinfo_df, group_type='sum', event_types = ['xThreat', 'xThreat_gen'])

# Progressive passes
prog_carries = all_carries[all_carries['progressive_carry']==True]
playerinfo_df = wde.group_player_events(prog_carries, playerinfo_df, primary_event_name='prog_carries')

# Successful progressive carries in opposition half
opphalf_prog_carries = prog_carries[prog_carries['x'] > 50]
playerinfo_df = wde.group_player_events(opphalf_prog_carries, playerinfo_df, primary_event_name='opphalf_prog_carries')

# Carriers into opposition box
box_carries = all_carries[all_carries['carry_into_box'] == True]
playerinfo_df = wde.group_player_events(box_carries, playerinfo_df, primary_event_name='box_carries')

# %% Calculate statistics per 90 mins

# Passes and xT generated
playerinfo_df['carries_90'] = round(90*playerinfo_df['carries']/playerinfo_df['mins_played'],2)
playerinfo_df['xThreat_90'] = round(90*playerinfo_df['xThreat']/playerinfo_df['mins_played'],3)
playerinfo_df['xThreat_gen_90'] = round(90*playerinfo_df['xThreat_gen']/playerinfo_df['mins_played'],3)

# Progressive Passes
playerinfo_df['prog_carries_pct'] = round(100*playerinfo_df['prog_carries']/playerinfo_df['carries'],1)
playerinfo_df['prog_carries_90'] = round(90*playerinfo_df['prog_carries']/playerinfo_df['mins_played'],2)

# Successful progressive passes in opposition half
playerinfo_df['opphalf_prog_carries_pct'] = round(100*playerinfo_df['opphalf_prog_carries']/playerinfo_df['carries'],1)
playerinfo_df['opphalf_prog_carries_90'] = round(90*playerinfo_df['opphalf_prog_carries']/playerinfo_df['mins_played'],2)

# Passes into opposition box
playerinfo_df['box_carries_pct'] = round(100*playerinfo_df['box_carries']/playerinfo_df['carries'],1)
playerinfo_df['box_carries_90'] = round(90*playerinfo_df['box_carries']/playerinfo_df['mins_played'],2)

# %% Filter playerinfo

playerinfo_df = playerinfo_df[(playerinfo_df['mins_played']>=min_mins) & (~playerinfo_df['pos_type'].isin(pos_exclude))]
playerinfo_df = playerinfo_df[~playerinfo_df.index.duplicated(keep='first')]

# %% Order playerinfo for progressive pass plot

if norm_mode == None:
    pp_sorted_df = playerinfo_df.sort_values(['prog_carries', 'prog_carries_90'], ascending=[False, False])
    xt_sorted_df = playerinfo_df.sort_values(['xThreat_gen', 'xThreat_gen_90'], ascending=[False, False])
elif norm_mode == '_90':
    pp_sorted_df = playerinfo_df.sort_values(['prog_carries_90', 'prog_carries'], ascending=[False, False])
    xt_sorted_df = playerinfo_df.sort_values(['xThreat_gen_90', 'xThreat_gen'], ascending=[False, False])

# %% Plot formatting

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
mpl.rcParams['text.color'] = 'w'

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

# %% ------- VISUAL 1 - TOP 12 THREAT CREATORS -------

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
    player_carries = all_carries[all_carries['playerId'] == player_id].sort_values('xThreat_gen', ascending = True)
    
    ax['pitch'][idx].set_title(f"  {idx + 1}: {name['name']}", loc = "left", color='w', fontsize = 10)

    for _, carry_evt in player_carries.iterrows():
        if carry_evt['xThreat_gen'] < 0.005:
            line_colour = 'grey'
            line_alpha = 0.05
        else:
            line_colour = pass_cmap[int(255*min(carry_evt['xThreat_gen']/0.05, 1))]
            line_alpha = 0.7

        pitch.lines(carry_evt['x'], carry_evt['y'], carry_evt['endX'], carry_evt['endY'],
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
title_text = f"Top 12 {title_pos_str}, ranked by threat generated from carries {title_addition}"
subtitle_text = f"{leagues[league]} {year} - <Low Threat> and <High Threat> Successful Carries Shown"
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
fig.savefig(f"player_effective_carriers/{league}-{year}-top-threat-generators-{run_date.replace('/','_')}{file_pos_str.replace(' & ','-').replace(' ','-')}-{title_addition.replace(' ','-')}", dpi=300)