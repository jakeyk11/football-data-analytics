# %% Create pass reports and visualisation from event data
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Whoscored match id
#           Home team
#           Away team
#           JDP zone type
#
# Outputs:  Pass flow diagrams
#           Pass convex hulls 
#           Home and away team pass reports

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
from mplsoccer.pitch import VerticalPitch
import os
import sys
import bz2
import pickle
import numpy as np
from collections import Counter

# %% Function definitions


def protected_divide(n, d):
    return n / d if d else 0

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
match_id = '1640718'

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Select team codes
home_team = 'Leicester'
away_team = 'Man Utd'

# Team name to print
home_team_print = None
away_team_print = 'Manchester Utd'

# Pass flow zone type
zone_type = 'jdp_custom'

# Pass hull inclusion
central_pct = 75

# %% Logos, colours and printed names

home_logo, home_colourmap = lab.get_team_badge_and_colour(home_team, 'home')
away_logo, away_colourmap = lab.get_team_badge_and_colour(away_team, 'home')

if home_team_print is None:
    home_team_print = home_team

if away_team_print is None:
    away_team_print = away_team
    
cmaps = [home_colourmap, away_colourmap]

# %% Read in data

# Opta data

events_df = bz2.BZ2File(f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}/match-{match_id}-eventdata.pbz2", 'rb')
events_df = pickle.load(events_df)
players_df = bz2.BZ2File(f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}/match-{match_id}-playerdata.pbz2", 'rb')
players_df = pickle.load(players_df)
event_types = bz2.BZ2File(f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}/event-types.pbz2", 'rb')
event_types = pickle.load(event_types)

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

# Add pass recipient
events_df = wde.get_recipient(events_df)

# Add cumulative minutes information
players_df = wde.minutes_played(players_df, events_df)

# Calculate longest consistent xi
players_df = wde.longest_xi(players_df)

# Determine positions substitutes played

# %% Aggregate data per player

playerinfo_df = wde.create_player_list(players_df, additional_cols = 'mins_played')

# Passes
all_passes = events_df[events_df['eventType']=='Pass']
playerinfo_df = wde.group_player_events(all_passes, playerinfo_df, primary_event_name='passes')

# Successful passes
suc_passes = events_df[(events_df['eventType']=='Pass') & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(suc_passes, playerinfo_df, primary_event_name='suc_passes')

# Progressive passes
events_df['progressive_pass'] = events_df.apply(wce.progressive_pass, axis=1)
prog_passes = events_df[events_df['progressive_pass']==True]
playerinfo_df = wde.group_player_events(prog_passes, playerinfo_df, primary_event_name='prog_passes')
suc_prog_passes = events_df[(events_df['progressive_pass']==True) & (events_df['outcomeType']=='Successful')]
playerinfo_df = wde.group_player_events(suc_prog_passes, playerinfo_df, primary_event_name='suc_prog_passes')

# Forward passes
forward_passes = events_df[(events_df['eventType']=='Pass') & (events_df['endX'] > events_df['x'])]
playerinfo_df = wde.group_player_events(forward_passes, playerinfo_df, primary_event_name='fwd_passes')
suc_forward_passes = events_df[(events_df['eventType']=='Pass') & (events_df['outcomeType']=='Successful') & (events_df['endX'] > events_df['x'])]
playerinfo_df = wde.group_player_events(suc_forward_passes, playerinfo_df, primary_event_name='suc_fwd_passes')

# Crosses
crosses = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 125 in x or 126 in x))]
playerinfo_df = wde.group_player_events(crosses, playerinfo_df, primary_event_name='crosses')
suc_crosses = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 125 in x))]
playerinfo_df = wde.group_player_events(suc_crosses, playerinfo_df, primary_event_name='suc_crosses')

# Through balls
through_balls = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 129 in x or 130 in x or 131 in x))]
playerinfo_df = wde.group_player_events(through_balls, playerinfo_df, primary_event_name='through_balls')
suc_through_balls = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 129 in x))]
playerinfo_df = wde.group_player_events(suc_through_balls, playerinfo_df, primary_event_name='suc_through_balls')

# Long balls
long_balls = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 127 in x or 128 in x))]
playerinfo_df = wde.group_player_events(long_balls, playerinfo_df, primary_event_name='long_balls')
suc_long_balls = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 127 in x))]
playerinfo_df = wde.group_player_events(suc_long_balls, playerinfo_df, primary_event_name='suc_long_balls')


# %% Add custom events and zonal grouping

# Progressive passes
events_df['progressive_pass'] = events_df.apply(wce.progressive_pass, axis=1)

# Pass zones
events_df[['start_zone','start_zone_center','end_zone','end_zone_center']] = events_df.apply(pz.identify_zone, axis=1, get_centers=True, zone_type = zone_type,result_type = 'expand')

# Pre assists
events_df = wce.pre_assist(events_df)

# %% Create dataframes of specific pass types and pass areas

# Get zone numbers for key zones (half-space and zone 14)
key_zones = pz.get_key_zones(zone_type=zone_type, halfspace = True, zone_14 = True, cross_areas = True)

# Zone 14 passes
z14_passes = events_df[(events_df['eventType']=='Pass') & (events_df['start_zone'].isin(key_zones['zone_14']))]
z14_suc_passes = z14_passes[z14_passes['outcomeType']=='Successful']
z14_prog_passes = z14_suc_passes[z14_passes['progressive_pass']==True]
z14_assists = z14_passes[z14_passes['satisfiedEventsTypes'].apply(lambda x: 92 in x)]  
z14_touch_assists = events_df[(events_df['start_zone'].isin(key_zones['zone_14'])) & (events_df['eventType']!='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 92 in x))]
z14_pre_assists = z14_passes[z14_passes['pre_assist'] == True]
z14_touch_pre_assists = events_df[(events_df['start_zone'].isin(key_zones['zone_14'])) & (events_df['eventType']!='Pass') & (events_df['pre_assist'] == True)]

# Half space passes
hs_passes = events_df[(events_df['eventType']=='Pass') & (events_df['start_zone'].isin(key_zones['halfspace']))]
hs_suc_passes = hs_passes[hs_passes['outcomeType']=='Successful']
hs_prog_passes = hs_suc_passes[hs_passes['progressive_pass']==True]
hs_assists = hs_passes[hs_passes['satisfiedEventsTypes'].apply(lambda x: 92 in x)]
hs_touch_assists = events_df[(events_df['start_zone'].isin(key_zones['halfspace'])) & (events_df['eventType']!='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: 92 in x))]
hs_pre_assists = hs_passes[hs_passes['pre_assist'] == True]
hs_touch_pre_assists = events_df[(events_df['start_zone'].isin(key_zones['halfspace'])) & (events_df['eventType']!='Pass') & (events_df['pre_assist'] == True)]

# %% Determine the most popular end zones that are passed to

zz_pass_popularity = dict()
for team in players_df['teamId'].unique():
    zz_pass_popularity_team = dict()
    for zone_center in events_df[(events_df['eventType'] == 'Pass') & (events_df['teamId']==team)]['start_zone_center'].unique():
        zone_passes = events_df[(events_df['eventType'] == 'Pass') & (events_df['start_zone_center']==zone_center) & (events_df['teamId']==team)]
        zz_pass_popularity_team[zone_center] = (Counter(zone_passes['end_zone_center'].values))
    zz_pass_popularity[team] = zz_pass_popularity_team

# %% Create dataframes of defensive and offensive actions

defensive_actions_df = wde.find_defensive_actions(events_df)
offensive_actions_df = events_df[(events_df['eventType']=='Pass') & (events_df['satisfiedEventsTypes'].apply(lambda x: not(31 in x or 34 in x or 212 in x)))]

# Initialise dataframes
defensive_hull_df = pd.DataFrame()
offensive_hull_df = pd.DataFrame()

# Create convex hull for each player
for player_id in players_df[players_df['longest_xi']==True].index:
    player_def_hull = wce.create_convex_hull(defensive_actions_df[defensive_actions_df['playerId'] == player_id], name=players_df.loc[player_id,'name'],
        min_events=5, include_percent=central_pct, pitch_area = 10000)
    player_off_hull = wce.create_convex_hull(offensive_actions_df[offensive_actions_df['playerId'] == player_id], name=players_df.loc[player_id,'name'],
        min_events=5, include_percent=40)
    offensive_hull_df = pd.concat([offensive_hull_df, player_off_hull])
    defensive_hull_df = pd.concat([defensive_hull_df, player_def_hull])

# %% Create viz of zonal pass flow for each team

# Plot pitches
pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=1, ncols=2, title_height=0.17,
                     grid_height=0.65, endnote_height=0.12, axis=False)
fig.set_size_inches(8.5, 8.5)
fig.set_facecolor('#313332')

# Plot progressive passes
for idx, team in enumerate(players_df['teamId'].unique()):
    pz.add_pitch_zones(ax['pitch'][idx], zone_type = zone_type)
    
    # For each zone apart from opp. penalty area
    for start_pos in zz_pass_popularity[team]:
        if start_pos != (91.5, 50):
            
            # Calculate most common zone position from Counter object of end zones
            end_pos = zz_pass_popularity[team][start_pos]
            rank1_end_pos = orig_rank1_end_pos = end_pos.most_common()[0][0]
            rank1_count = end_pos.most_common()[0][1] 
            
            # Prevent start zone and zone being identical (no line)
            if rank1_end_pos == start_pos and len(end_pos)>1:
                rank1_end_pos = end_pos.most_common()[1][0]
                rank1_count = end_pos.most_common()[1][1]
            
            # Use pass count to manually define plot colour
            color = cmaps[idx](int(255*min(1,rank1_count/15)))
            hex_color = '#%02x%02x%02x' % (int(255*color[0]), int(255*color[1]), int(255*color[2]))                     
            
            # Plot comet
            pitch.lines(start_pos[0], start_pos[1], rank1_end_pos[0], rank1_end_pos[1], lw=10, comet = True, ax=ax['pitch'][idx],
                        color = hex_color, transparent=True, alpha =0.3, zorder=rank1_count)
            
            # Plot comet end point (but only if start and end zones differ)
            if len(end_pos)==1 and orig_rank1_end_pos == start_pos:
                pass
            else:
                pitch.scatter(rank1_end_pos[0], rank1_end_pos[1], s=100, c=hex_color, zorder=rank1_count, ax=ax['pitch'][idx])

# Title text
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship'}

title_text = f"{leagues[league]} - {year}/{int(year) + 1}"
subtitle_text = f"{home_team_print} {home_score}-{away_score} {away_team_print}"
subsubtitle_text = "Pass Flow - Most Frequent Inter-zone Passes"

fig.text(0.5, 0.93, title_text, ha='center',
         fontweight="bold", fontsize=20, color='w')
fig.text(0.5, 0.882, subtitle_text, ha='center',
         fontweight="bold", fontsize=18, color='w')
fig.text(0.5, 0.84, subsubtitle_text, ha='center',
         fontweight="regular", fontsize=13.5, color='w')

# Add home team Logo
ax = fig.add_axes([0.07, 0.825, 0.14, 0.14])
ax.axis("off")
ax.imshow(home_logo)

# Add away team Logo
ax = fig.add_axes([0.78, 0.825, 0.14, 0.14])
ax.axis("off")
ax.imshow(away_logo)

# Add direction of play arrow
ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.arrow(0.65, 0.2, 0, 0.58, color="w", width=0.001, head_width = 0.1, head_length = 0.02)
ax.text(0.495, 0.48, "Direction of play", ha="center", va="center", fontsize=10, color="w", fontweight="regular", rotation=90)

# Add legends
legend_ax_1 = fig.add_axes([0.055, 0.07, 0.4, 0.09])
plt.xlim([0, 8])
plt.ylim([-0.5, 1])
legend_ax_1.axis("off")
legend_ax_2 = fig.add_axes([0.545, 0.07, 0.4, 0.09])
plt.xlim([0, 8])
plt.ylim([-0.5, 1])
legend_ax_2.axis("off")

for idx, pass_count in enumerate(np.arange(1,16,2)):
    if idx%2 == 0:
        ypos = 0.38
    else:
        ypos= 0.62
    xpos = idx/1.4 + 1.5
    if idx<=2:
        text_color = '#313332'
    else:
        text_color = 'w'
    color_1 = cmaps[0](int(255*min(1,pass_count/15)))
    legend_ax_1.scatter(xpos, ypos, marker='H', s=550, color=color_1, edgecolors=None)
    legend_ax_1.text(xpos, ypos, pass_count, color=text_color, ha = "center", va = "center")
    legend_ax_1.text(4, -0.2, "Pass Count", color=text_color, ha = "center", va = "center")
    color_2 = cmaps[1](int(255*min(1,pass_count/15)))
    legend_ax_2.scatter(xpos, ypos, marker='H', s=550, color=color_2, edgecolors=None)
    legend_ax_2.text(xpos, ypos, pass_count, color=text_color, fontsize=10, ha = "center", va = "center")
    legend_ax_2.text(4, -0.2, "Pass Count", color=text_color, fontsize=10, ha = "center", va = "center")
    
# Footer text
fig.text(0.5, 0.035, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.875, 0.01, 0.07, 0.07])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save image
fig.savefig(f"pass_reports/{league}-{match_id}-{home_team}-{away_team}-passflows", dpi=300)

# %% Create viz of area covered by each player when passing

# Plot pitches
pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=1, ncols=2, title_height=0.17,
                     grid_height=0.65, endnote_height=0.12, axis=False)
fig.set_size_inches(8.5, 8.5)
fig.set_facecolor('#313332')

# Initialise player position counts
cf_count = 0
cm_count = 0
cb_count = 0
last_idx = 0

# Plot progressive passes
for hull_idx, hull_row in offensive_hull_df.iterrows():
    
    # Determine team the hull applies to
    if players_df[players_df['name']==hull_idx]['teamId'].values[0] == players_df['teamId'].unique()[0]:
        idx = 0
    elif players_df[players_df['name']==hull_idx]['teamId'].values[0] == players_df['teamId'].unique()[1]:
        idx = 1
    
    # Reset player position counts when changing team
    if idx - last_idx > 0:
        cf_count = 0
        cm_count = 0
        cb_count = 0
        
    # Get player position and assign colour based on position
    position = players_df[players_df['name']==hull_idx]['position'].values
    if position in ['DR', 'DL', '']:
        hull_colour = 'lawngreen'
    elif position in ['MR', 'ML', 'AML', 'AMR', 'FWR', 'FWL']:
        hull_colour = 'deepskyblue'
    elif position in ['FW']:
        hull_colour = ['tomato', 'lightpink'][cf_count]
        cf_count+=1
    elif position in ['MC', 'DMC', 'AMC']:
        hull_colour = ['snow', 'violet', 'cyan', 'yellow'][cm_count]
        cm_count+=1
    elif position in ['DC']:
        hull_colour = ['tomato', 'gold', 'lawngreen'][cb_count]
        cb_count+=1
    else:
        hull_colour = 'lightpink'
        
    # Define text colour based on marker colour
    if hull_colour in ['snow', 'white']:
        text_colour = 'k'
    else:
        text_colour = 'w'
    
    # Player initials
    if len(hull_idx.split(' ')) == 1:
        initials = hull_idx.split(' ')[0][0:2]
    else:
        initials = hull_idx.split(' ')[0][0].upper() + hull_idx.split(' ')[1][0].upper()
    
    # Plot
    ax['pitch'][idx].scatter(hull_row['hull_reduced_y'], hull_row['hull_reduced_x'], color=hull_colour, s=20, alpha = 0.3, zorder=2)
    plot_hull = pitch.convexhull(hull_row['hull_reduced_x'], hull_row['hull_reduced_y'])
    pitch.polygon(plot_hull, ax=ax['pitch'][idx], facecolor=hull_colour, alpha=0.2, capstyle = 'round', zorder=1)
    pitch.polygon(plot_hull, ax=ax['pitch'][idx], edgecolor=hull_colour, alpha=0.3, facecolor='none', capstyle = 'round', zorder=1)
    ax['pitch'][idx].scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', color = hull_colour, alpha = 0.6, s = 400, zorder = 3)
    ax['pitch'][idx].scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', edgecolor = hull_colour, facecolor = 'none', alpha = 1, lw = 2, s = 400, zorder = 3)
    ax['pitch'][idx].text(hull_row['hull_centre'][1], hull_row['hull_centre'][0], initials, fontsize = 8, fontweight = 'bold', va = 'center', ha = 'center', color = text_colour, zorder = 4)
    
    # Remember last team
    last_idx = idx

# Add top three areas to each plot
home_top_area = offensive_hull_df[0:11].sort_values('hull_area', ascending=False)
away_top_area = offensive_hull_df[11:22].sort_values('hull_area', ascending=False)

ax = fig.add_axes([0.053, 0.055, 0.895, 0.11])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

for idx in np.arange(0,3):

    if len(home_top_area.iloc[idx:idx+1].index[0].split(' ')) == 1:
        home_short_name = f"{home_top_area.iloc[idx:idx+1].index[0]}" 
    else:
        home_short_name = f"{home_top_area.iloc[idx:idx+1].index[0][0]}. {home_top_area.iloc[idx:idx+1].index[0].split(' ')[-1]}" 
    if len(away_top_area.iloc[idx:idx+1].index[0].split(' ')) == 1:
        away_short_name = f"{home_top_area.iloc[idx:idx+1].index[0]}"   
    else:
        away_short_name = f"{away_top_area.iloc[idx:idx+1].index[0][0]}. {away_top_area.iloc[idx:idx+1].index[0].split(' ')[-1]}" 

    if len(home_short_name)>= 15:
        home_short_name = home_short_name[0:16] + '...'
    if len(away_short_name)>= 15:
        away_short_name = away_short_name[0:16] + '...'


    ax.text(0.04, 0.71-0.22*idx, f"{idx+1}.     {home_short_name}", color='w')
    ax.text(0.24, 0.71-0.22*idx, f"{round(home_top_area.iloc[idx:idx+1]['hull_area_%'].values[0],1)}%", color='w')
    ax.text(0.71, 0.71-0.22*idx, f"{idx+1}.     {away_short_name}", color='w')
    ax.text(0.91, 0.71-0.22*idx, f"{round(away_top_area.iloc[idx:idx+1]['hull_area_%'].values[0],1)}%", color='w')
 
# Label top three text
ax.plot([0.38, 0.38], [0.22 ,0.87], lw=0.5, color='w')
ax.plot([0.62, 0.62], [0.22 ,0.87], lw=0.5, color='w')
ax.text(0.5, 0.55, f"Top players by area of\nregion containing central\n{central_pct}% passes (as % of total\npitch area)", ha = 'center', va = 'center', color='w', fontsize=9)
ax.arrow(0.375, 0.55, -0.05, 0, color="w", width=0.001, head_width = 0.05, head_length = 0.01, lw=0.5)
ax.arrow(0.625, 0.55, 0.05, 0, color="w", width=0.001, head_width = 0.05, head_length = 0.01, lw=0.5)

# Title text
title_text = f"{leagues[league]} - {year}/{int(year) + 1}"
subtitle_text = f"{home_team_print} {home_score}-{away_score} {away_team_print}"
subsubtitle_text = f"Variation in start position of player passes. Central {central_pct}%\n of passes shown per player, represented by a shaded region"

fig.text(0.5, 0.93, title_text, ha='center',
         fontweight="bold", fontsize=20, color='w')
fig.text(0.5, 0.882, subtitle_text, ha='center',
         fontweight="bold", fontsize=18, color='w')
fig.text(0.5, 0.82, subsubtitle_text, ha='center',
         fontweight="regular", fontsize=12, color='w')

# Add home team Logo
ax = fig.add_axes([0.07, 0.825, 0.14, 0.14])
ax.axis("off")
ax.imshow(home_logo)

# Add away team Logo
ax = fig.add_axes([0.78, 0.825, 0.14, 0.14])
ax.axis("off")
ax.imshow(away_logo)

# Add direction of play arrow
ax = fig.add_axes([0.47, 0.17, 0.06, 0.6])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.arrow(0.65, 0.2, 0, 0.58, color="w", width=0.001, head_width = 0.1, head_length = 0.02)
ax.text(0.495, 0.48, "Direction of play", ha="center", va="center", fontsize=10, color="w", fontweight="regular", rotation=90)

# Footer text
fig.text(0.5, 0.035, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.875, 0.01, 0.07, 0.07])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save image
fig.savefig(f"pass_reports/{league}-{match_id}-{home_team}-{away_team}-passhulls", dpi=300)

# %% Pass report

# Set up plotting grids with titles
full_pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
half_pitch = VerticalPitch(half=True, pitch_color='#313332', line_color='white', linewidth=1, pitch_type = 'opta', stripe=False)

fig1 = plt.figure(constrained_layout=True, figsize = (11.25,9.5))
fig2 = plt.figure(constrained_layout=True, figsize = (11.25,9.5))
fig1.set_facecolor('#313332')
fig2.set_facecolor('#313332')

gs1 = fig1.add_gridspec(4, 3, height_ratios=[0.65,1,1,0.85])
ax10 = fig1.add_subplot(gs1[0,0:])
ax10.axis('off')
ax11 = fig1.add_subplot(gs1[1:3,0])
ax12 = fig1.add_subplot(gs1[1:3:,1])
ax13 = fig1.add_subplot(gs1[1,2])
ax14 = fig1.add_subplot(gs1[2,2])
ax15 = fig1.add_subplot(gs1[3,0:])
ax15.axis('off')

gs2 = fig2.add_gridspec(4, 3, height_ratios=[0.65,1,1,0.85])
ax20 = fig2.add_subplot(gs2[0,0:])
ax20.axis('off')
ax21 = fig2.add_subplot(gs2[1:3,0])
ax22 = fig2.add_subplot(gs2[1:3:,1])
ax23 = fig2.add_subplot(gs2[1,2])
ax24 = fig2.add_subplot(gs2[2,2])
ax25 = fig2.add_subplot(gs2[3,0:])
ax25.axis('off')

full_pitch.draw(ax=ax11)
full_pitch.draw(ax=ax12)
half_pitch.draw(ax=ax13)
half_pitch.draw(ax=ax14)

full_pitch.draw(ax=ax21)
full_pitch.draw(ax=ax22)
half_pitch.draw(ax=ax23)
half_pitch.draw(ax=ax24)

ax11.set_title('Pass Flow - Most frequent\ninter-zone passes', color='w', fontsize = 10, fontweight = 'bold')
ax12.set_title(f'Variation in start position of player passes\nCentral {central_pct}% passes shown per player', color='w', fontsize = 10, fontweight = 'bold')
ax13.set_title('\nHalf-space passes', color='w', fontsize = 10, fontweight = 'bold')
ax14.set_title('Zone 14 passes', color='w', fontsize = 10, fontweight = 'bold')

ax21.set_title('Pass Flow - Most frequent\ninter-zone passes', color='w', fontsize = 10, fontweight = 'bold')
ax22.set_title(f'Variation in start position of player passes\nCentral {central_pct}% passes shown per player', color='w', fontsize = 10, fontweight = 'bold')
ax23.set_title('\nHalf-space passes', color='w', fontsize = 10, fontweight = 'bold')
ax24.set_title('Zone 14 passes', color='w', fontsize = 10, fontweight = 'bold')

# Title border
ax1 = fig1.add_axes([0, 0.84, 1, 0.16])
ax1.set_facecolor('#212126')
ax1.axes.xaxis.set_visible(False)
ax1.axes.yaxis.set_visible(False)
ax1.spines.right.set_visible(False)
ax1.spines.top.set_visible(False)
ax1.spines.bottom.set_visible(False)
ax1.spines.left.set_visible(False)
ax2 = fig2.add_axes([0, 0.84, 1, 0.16])
ax2.set_facecolor('#212126')
ax2.axes.xaxis.set_visible(False)
ax2.axes.yaxis.set_visible(False)
ax2.spines.right.set_visible(False)
ax2.spines.top.set_visible(False)
ax2.spines.bottom.set_visible(False)
ax2.spines.left.set_visible(False)

# Add pitch zones
pz.add_pitch_zones(ax11, zone_type = zone_type)
pz.add_pitch_zones(ax12, zone_type = zone_type)
pz.add_pitch_zones(ax13, zone_type = zone_type)
pz.add_pitch_zones(ax14, zone_type = zone_type)
pz.add_pitch_zones(ax21, zone_type = zone_type)
pz.add_pitch_zones(ax22, zone_type = zone_type)
pz.add_pitch_zones(ax23, zone_type = zone_type)
pz.add_pitch_zones(ax24, zone_type = zone_type)

# Pass flows
for idx, team in enumerate(players_df['teamId'].unique()):
    
    # For each zone apart from opp. penalty area
    for start_pos in zz_pass_popularity[team]:
        if start_pos != (91.5, 50):
            
            # Choose axis based on idx
            if idx == 0:
                ax_to_plot = ax11
            else:
                ax_to_plot = ax21
            
            # Calculate most common zone position from Counter object of end zones
            end_pos = zz_pass_popularity[team][start_pos]
            rank1_end_pos = orig_rank1_end_pos = end_pos.most_common()[0][0]
            rank1_count = end_pos.most_common()[0][1] 
            
            # Prevent start zone and zone being identical (no line)
            if rank1_end_pos == start_pos and len(end_pos)>1:
                rank1_end_pos = end_pos.most_common()[1][0]
                rank1_count = end_pos.most_common()[1][1]
            
            # Use pass count to manually define plot colour
            color = cmaps[idx](int(255*min(1,rank1_count/15)))
            hex_color = '#%02x%02x%02x' % (int(255*color[0]), int(255*color[1]), int(255*color[2]))                     
            
            # Plot comet
            pitch.lines(start_pos[0], start_pos[1], rank1_end_pos[0], rank1_end_pos[1], lw=10, comet = True, ax=ax_to_plot,
                        color = hex_color, transparent=True, alpha =0.3, zorder=rank1_count)
            
            # Plot comet end point (but only if start and end zones differ)
            if len(end_pos)==1 and orig_rank1_end_pos == start_pos:
                pass
            else:
                pitch.scatter(rank1_end_pos[0], rank1_end_pos[1], s=100, c=hex_color, zorder=rank1_count, ax=ax_to_plot)

# Pass flow text
ax1 = fig1.add_axes([0.018, 0.09, 0.28, 0.14])
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.axis("off")
ax2 = fig2.add_axes([0.018, 0.09, 0.28, 0.14])
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.axis("off")

top_suc_passers = playerinfo_df.sort_values('suc_passes', ascending=False)
for idx in np.arange(0,5):
    
    home_player = top_suc_passers[top_suc_passers['team']==home_team].iloc[idx]
    away_player = top_suc_passers[top_suc_passers['team']==away_team].iloc[idx]

    if len(home_player['name'].split(' ')) == 1:
        home_short_name = f"{home_player['name']}" 
    else:
        home_short_name = f"{home_player['name'][0]}. {home_player['name'].split(' ')[-1]}" 
    if len(away_player['name'].split(' ')) == 1:
        away_short_name = f"{away_player['name']}" 
    else:
        away_short_name = f"{away_player['name'][0]}. {away_player['name'].split(' ')[-1]}"
    if len(home_short_name)>= 16:
        home_short_name = home_short_name[0:16] + '...'
    if len(away_short_name)>= 16:
        away_short_name = away_short_name[0:16] + '...'
        
    ax1.text(0.4, 0.81-0.16*idx, f"{idx+1}.   {home_short_name}", color='w')
    ax1.text(0.95, 0.81-0.16*idx, f"{int(home_player['suc_passes'])}", color='w')
    ax2.text(0.4, 0.81-0.16*idx, f"{idx+1}.   {away_short_name}", color='w')
    ax2.text(0.95, 0.81-0.16*idx, f"{int(away_player['suc_passes'])}", color='w')

ax1.plot([0.35, 0.35], [0.15 ,0.92], lw=0.5, color='w')
ax1.text(0.01, 0.52, "Top players\nby number of\nsuccessful\npasses", va = 'center', color='w', fontsize=9)
ax2.plot([0.35, 0.35], [0.15 ,0.92], lw=0.5, color='w')
ax2.text(0.01, 0.52, "Top players\nby number of\nsuccessful\npasses", va = 'center', color='w', fontsize=9)

# Pass flow legends
legend_ax_1 = fig1.add_axes([0.015, 0.014, 0.3, 0.09])
legend_ax_1.set_xlim([0, 8])
legend_ax_1.set_ylim([-0.5, 1])
legend_ax_1.axis("off")
legend_ax_2 = fig2.add_axes([0.015, 0.014, 0.3, 0.09])
legend_ax_2.set_xlim([0, 8])
legend_ax_2.set_ylim([-0.5, 1])
legend_ax_2.axis("off")

for idx, pass_count in enumerate(np.arange(1,16,2)):
    if idx%2 == 0:
        ypos = 0.3
    else:
        ypos= 0.5
    xpos = idx/1.8 + 2
    if idx<=2:
        text_color = '#313332'
    else:
        text_color = 'w'
    color_1 = cmaps[0](int(255*min(1,pass_count/15)))
    legend_ax_1.scatter(xpos, ypos, marker='H', s=350, color=color_1, edgecolor='w', lw=0.5)
    legend_ax_1.text(xpos, ypos, pass_count, color=text_color, ha = "center", va = "center", fontsize = 9)
    legend_ax_1.text(4, -0.2, "Pass Count", color=text_color, ha = "center", va = "center", fontsize = 9)
    color_2 = cmaps[1](int(255*min(1,pass_count/15)))
    legend_ax_2.scatter(xpos, ypos, marker='H', s=350, color=color_2, edgecolor='w', lw=0.5)
    legend_ax_2.text(xpos, ypos, pass_count, color=text_color, ha = "center", va = "center", fontsize = 9)
    legend_ax_2.text(4, -0.2, "Pass Count", color=text_color, ha = "center", va = "center", fontsize = 9)

# Pass convex hulls
cf_count = 0
cm_count = 0
cb_count = 0
last_idx = 0

for hull_idx, hull_row in offensive_hull_df.iterrows():
    
    # Determine team the hull applies to
    if players_df[players_df['name']==hull_idx]['teamId'].values[0] == players_df['teamId'].unique()[0]:
        idx = 0
    elif players_df[players_df['name']==hull_idx]['teamId'].values[0] == players_df['teamId'].unique()[1]:
        idx = 1
    
    # Reset player position counts when changing team
    if idx - last_idx > 0:
        cf_count = 0
        cm_count = 0
        cb_count = 0
        
    # Get player position and assign colour based on position
    position = players_df[players_df['name']==hull_idx]['position'].values
    if position in ['DR', 'DL', '']:
        hull_colour = 'lawngreen'
    elif position in ['MR', 'ML', 'AML', 'AMR', 'FWR', 'FWL']:
        hull_colour = 'deepskyblue'
    elif position in ['FW']:
        hull_colour = ['tomato', 'lightpink'][cf_count]
        cf_count+=1
    elif position in ['MC', 'DMC', 'AMC']:
        hull_colour = ['snow', 'violet', 'cyan', 'yellow'][cm_count]
        cm_count+=1
    elif position in ['DC']:
        hull_colour = ['tomato', 'gold', 'lawngreen'][cb_count]
        cb_count+=1
    else:
        hull_colour = 'lightpink'
        
    # Define text colour based on marker colour
    if hull_colour in ['snow', 'white']:
        text_colour = 'k'
    else:
        text_colour = 'w'
    
    # Player initials
    if len(hull_idx.split(' ')) == 1:
        initials = hull_idx.split(' ')[0][0:2]
    else:
        initials = hull_idx.split(' ')[0][0].upper() + hull_idx.split(' ')[1][0].upper()
    
    # Plot
    if idx == 0:
        ax12.scatter(hull_row['hull_reduced_y'], hull_row['hull_reduced_x'], color=hull_colour, s=20, alpha = 0.3, zorder=2)
        plot_hull = pitch.convexhull(hull_row['hull_reduced_x'], hull_row['hull_reduced_y'])
        pitch.polygon(plot_hull, ax=ax12, facecolor=hull_colour, alpha=0.2, capstyle = 'round', zorder=1)
        pitch.polygon(plot_hull, ax=ax12, edgecolor=hull_colour, alpha=0.3, facecolor='none', capstyle = 'round', zorder=1)
        ax12.scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', color = hull_colour, alpha = 0.6, s = 400, zorder = 3)
        ax12.scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', edgecolor = hull_colour, facecolor = 'none', alpha = 1, lw = 2, s = 400, zorder = 3)
        ax12.text(hull_row['hull_centre'][1], hull_row['hull_centre'][0], initials, fontsize = 8, fontweight = 'bold', va = 'center', ha = 'center', color = text_colour, zorder = 4)
    else:
        ax22.scatter(hull_row['hull_reduced_y'], hull_row['hull_reduced_x'], color=hull_colour, s=20, alpha = 0.3, zorder=2)
        plot_hull = pitch.convexhull(hull_row['hull_reduced_x'], hull_row['hull_reduced_y'])
        pitch.polygon(plot_hull, ax=ax22, facecolor=hull_colour, alpha=0.2, capstyle = 'round', zorder=1)
        pitch.polygon(plot_hull, ax=ax22, edgecolor=hull_colour, alpha=0.3, facecolor='none', capstyle = 'round', zorder=1)
        ax22.scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', color = hull_colour, alpha = 0.6, s = 400, zorder = 3)
        ax22.scatter(hull_row['hull_centre'][1], hull_row['hull_centre'][0], marker ='H', edgecolor = hull_colour, facecolor = 'none', alpha = 1, lw = 2, s = 400, zorder = 3)
        ax22.text(hull_row['hull_centre'][1], hull_row['hull_centre'][0], initials, fontsize = 8, fontweight = 'bold', va = 'center', ha = 'center', color = text_colour, zorder = 4)
        
    # Remember last team
    last_idx = idx

# Convex hull text
ax1 = fig1.add_axes([0.355, 0.09, 0.28, 0.14])
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.axis("off")
ax2 = fig2.add_axes([0.355, 0.09, 0.28, 0.14])
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.axis("off")

for idx in np.arange(0,5):
    if len(home_top_area.iloc[idx:idx+1].index[0].split(' ')) == 1:
        home_short_name = f"{home_top_area.iloc[idx:idx+1].index[0]}" 
    else:
        home_short_name = f"{home_top_area.iloc[idx:idx+1].index[0][0]}. {home_top_area.iloc[idx:idx+1].index[0].split(' ')[-1]}" 
    if len(away_top_area.iloc[idx:idx+1].index[0].split(' ')) == 1:
        away_short_name = f"{home_top_area.iloc[idx:idx+1].index[0]}"   
    else:
        away_short_name = f"{away_top_area.iloc[idx:idx+1].index[0][0]}. {away_top_area.iloc[idx:idx+1].index[0].split(' ')[-1]}" 
    if len(home_short_name)> 16:
        home_short_name = home_short_name[0:16] + '...'
    if len(away_short_name)> 16:
        away_short_name = away_short_name[0:16] + '...'

    ax1.text(0.4, 0.81-0.16*idx, f"{idx+1}.   {home_short_name}", color='w')
    ax1.text(0.91, 0.81-0.16*idx, f"{round(home_top_area.iloc[idx:idx+1]['hull_area_%'].values[0],1)}%", color='w')
    ax2.text(0.4, 0.81-0.16*idx, f"{idx+1}.   {away_short_name}", color='w')
    ax2.text(0.91, 0.81-0.16*idx, f"{round(away_top_area.iloc[idx:idx+1]['hull_area_%'].values[0],1)}%", color='w')
 
ax1.plot([0.35, 0.35], [0.15 ,0.92], lw=0.5, color='w')
ax1.text(0.01, 0.52, f"Top players\nby area\ncontaining\ncentral {central_pct}%\npasses (% tot.\npitch area)", va = 'center', color='w', fontsize=9)
ax2.plot([0.35, 0.35], [0.15 ,0.92], lw=0.5, color='w')
ax2.text(0.01, 0.52, f"Top players\nby area\ncontaining\ncentral {central_pct}%\npasses (% tot.\npitch area)", va = 'center', color='w', fontsize=9)

# Zone 14 and half-space passes
for idx, team in enumerate(players_df['teamId'].unique()):
    
    if idx == 0:
        z14_ax_to_plot = ax14
        hs_ax_to_plot = ax13
    if idx == 1:
        z14_ax_to_plot = ax24
        hs_ax_to_plot = ax23 
        
    plot_z14_passes = z14_passes[z14_passes['teamId'] == team]
    plot_z14_suc_passes = z14_suc_passes[z14_suc_passes['teamId'] == team]
    plot_z14_prog_passes = z14_prog_passes[z14_prog_passes['teamId'] == team]
    plot_z14_assists = z14_assists[z14_assists['teamId'] == team]
    plot_z14_touch_assists = z14_touch_assists[z14_touch_assists['teamId'] == team]
    plot_z14_pre_assists = z14_pre_assists[z14_pre_assists['teamId'] == team]
    plot_z14_touch_pre_assists = z14_touch_pre_assists[z14_touch_pre_assists['teamId'] == team]
    plot_hs_passes = hs_passes[hs_passes['teamId'] == team]
    plot_hs_suc_passes = hs_suc_passes[hs_suc_passes['teamId'] == team]
    plot_hs_prog_passes = hs_prog_passes[hs_prog_passes['teamId'] == team]
    plot_hs_assists = hs_assists[hs_assists['teamId'] == team]
    plot_hs_touch_assists = hs_touch_assists[hs_touch_assists['teamId'] == team]
    plot_hs_pre_assists = hs_pre_assists[hs_pre_assists['teamId'] == team]
    plot_hs_touch_pre_assists = hs_touch_pre_assists[hs_touch_pre_assists['teamId'] == team]

    pitch.lines(plot_z14_passes['x'], plot_z14_passes['y'], plot_z14_passes['endX'], plot_z14_passes['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Unsuccessful Pass', color = 'grey', alpha = 0.1, zorder=2, ax=z14_ax_to_plot)
    pitch.lines(plot_z14_suc_passes['x'], plot_z14_suc_passes['y'], plot_z14_suc_passes['endX'], plot_z14_suc_passes['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Successful Pass', color = 'w', alpha = 0.2, zorder=3, ax=z14_ax_to_plot)
    pitch.lines(plot_z14_prog_passes['x'], plot_z14_prog_passes['y'], plot_z14_prog_passes['endX'], plot_z14_prog_passes['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Progressive Pass', color = 'cyan', alpha = 0.8, zorder=4, ax=z14_ax_to_plot)
    pitch.lines(plot_z14_assists['x'], plot_z14_assists['y'], plot_z14_assists['endX'], plot_z14_assists['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Assist', color = 'magenta', alpha = 0.8, zorder=5, ax=z14_ax_to_plot)
    pitch.lines(plot_z14_pre_assists['x'], plot_z14_pre_assists['y'], plot_z14_pre_assists['endX'], plot_z14_pre_assists['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Pre-assist', color = 'lime', alpha = 0.8, zorder=5, ax=z14_ax_to_plot)
    pitch.scatter(plot_z14_touch_assists['x'], plot_z14_touch_assists['y'], color = 'magenta', alpha = 0.8, s = 15, zorder=5, ax=z14_ax_to_plot)
    pitch.scatter(plot_z14_touch_pre_assists['x'], plot_z14_touch_pre_assists['y'], color = 'lime', alpha = 0.8, s = 15, zorder=5, ax=z14_ax_to_plot)

    pitch.lines(plot_hs_passes['x'], plot_hs_passes['y'], plot_hs_passes['endX'], plot_hs_passes['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Unsuccessful Pass', color = 'grey', alpha = 0.1, zorder=2, ax=hs_ax_to_plot)
    pitch.lines(plot_hs_suc_passes['x'], plot_hs_suc_passes['y'], plot_hs_suc_passes['endX'], plot_hs_suc_passes['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Successful Pass', color = 'w', alpha = 0.2, zorder=3, ax=hs_ax_to_plot)
    pitch.lines(plot_hs_prog_passes['x'], plot_hs_prog_passes['y'], plot_hs_prog_passes['endX'], plot_hs_prog_passes['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Progressive Pass', color = 'cyan', alpha = 0.8, zorder=4, ax=hs_ax_to_plot)
    pitch.lines(plot_hs_assists['x'], plot_hs_assists['y'], plot_hs_assists['endX'], plot_hs_assists['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Assist', color = 'magenta', alpha = 0.8, zorder=5, ax=hs_ax_to_plot)
    pitch.lines(plot_hs_pre_assists['x'], plot_hs_pre_assists['y'], plot_hs_pre_assists['endX'], plot_hs_pre_assists['endY'],
                lw = 3, comet=True, capstyle='round', label = 'Pre-assist', color = 'lime', alpha = 0.8, zorder=5, ax=hs_ax_to_plot)
    pitch.scatter(plot_hs_touch_assists['x'], plot_hs_touch_assists['y'], color = 'magenta', alpha = 0.8, s = 15, zorder=5, ax=hs_ax_to_plot)
    pitch.scatter(plot_hs_touch_pre_assists['x'], plot_hs_touch_pre_assists['y'], color = 'lime', alpha = 0.8, s = 15, zorder=5, ax=hs_ax_to_plot)

ax14.legend(facecolor='#313332', edgecolor='None', fontsize=8, loc='lower center', labelcolor = 'w', ncol = 2, handlelength=3)    
ax24.legend(facecolor='#313332', edgecolor='None', fontsize=8, loc='lower center', labelcolor = 'w', ncol = 2, handlelength=3)    

# Prog Pass text
ax1 = fig1.add_axes([0.7, 0.09, 0.28, 0.14])
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.axis("off")
ax2 = fig2.add_axes([0.7, 0.09, 0.28, 0.14])
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.axis("off")

top_prog_passers = playerinfo_df.sort_values('prog_passes', ascending=False)
for idx in np.arange(0,5):
    
    home_player = top_prog_passers[top_prog_passers['team']==home_team].iloc[idx]
    away_player = top_prog_passers[top_prog_passers['team']==away_team].iloc[idx]

    if len(home_player['name'].split(' ')) == 1:
        home_short_name = f"{home_player['name']}" 
    else:
        home_short_name = f"{home_player['name'][0]}. {home_player['name'].split(' ')[-1]}" 
    if len(away_player['name'].split(' ')) == 1:
        away_short_name = f"{away_player['name']}" 
    else:
        away_short_name = f"{away_player['name'][0]}. {away_player['name'].split(' ')[-1]}"
    if len(home_short_name)>= 16:
        home_short_name = home_short_name[0:16] + '...'
    if len(away_short_name)>= 16:
        away_short_name = away_short_name[0:16] + '...'
                
    ax1.text(0.38, 0.81-0.16*idx, f"{idx+1}.   {home_short_name}", color='w')
    ax1.text(0.9, 0.81-0.16*idx, f"{int(home_player['prog_passes'] if home_player['prog_passes'] == home_player['prog_passes'] else 0)}", color='w')
    ax2.text(0.38, 0.81-0.16*idx, f"{idx+1}.   {away_short_name}", color='w')
    ax2.text(0.9, 0.81-0.16*idx, f"{int(away_player['prog_passes'] if away_player['prog_passes'] == away_player['prog_passes'] else 0)}", color='w')
 
ax1.plot([0.33, 0.33], [0.15 ,0.92], lw=0.5, color='w')
ax1.text(0.05, 0.52, "Top players\nby # of\nprogressive\npasses", va = 'center', color='w', fontsize=9)
ax2.plot([0.33, 0.33], [0.15 ,0.92], lw=0.5, color='w')
ax2.text(0.05, 0.52, "Top players\nby # of\nprogressive\npasses", va = 'center', color='w', fontsize=9)

# Title text
title_text = f"{leagues['EPL']} - {year}/{int(year) + 1}"
subtitle_text = f"{home_team_print} {home_score}-{away_score} {away_team_print}"
subsubtitle_text1 = f"{home_team_print} Pass Report"
subsubtitle_text2 = f"{away_team_print} Pass Report"

fig1.text(0.14, 0.943, title_text, fontweight="bold", fontsize=18, color='w')
fig1.text(0.14, 0.908, subtitle_text, fontweight="bold", fontsize=16, color='w')
fig1.text(0.14, 0.875, subsubtitle_text1, fontweight="bold", fontsize=13.5, color='w')
fig2.text(0.14, 0.943, title_text, fontweight="bold", fontsize=18, color='w')
fig2.text(0.14, 0.908, subtitle_text, fontweight="bold", fontsize=16, color='w')
fig2.text(0.14, 0.875, subsubtitle_text2, fontweight="bold", fontsize=13.5, color='w')

# Prog Pass text
ax1 = fig1.add_axes([0.68, 0.86, 0.28, 0.13])
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.axis("off")
ax2 = fig2.add_axes([0.68, 0.86, 0.28, 0.13])
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.axis("off")

# Calculate stats
h_pass_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_passes'], playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['passes']), 1)
h_fwd_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_fwd_passes'], playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['fwd_passes']), 1)
h_prog_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_prog_passes'], playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['prog_passes']), 1)
h_cross_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_crosses'], playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['crosses']), 1)
h_long_ball_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_long_balls'], playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['long_balls']), 1)
h_through_ball_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_through_balls'], playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['through_balls']), 1)
a_pass_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_passes'], playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['passes']), 1)
a_fwd_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_fwd_passes'], playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['fwd_passes']), 1)
a_prog_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_prog_passes'], playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['prog_passes']), 1)
a_cross_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_crosses'], playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['crosses']), 1)
a_long_ball_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_long_balls'], playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['long_balls']), 1)
a_through_ball_pct = round(100*protected_divide(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_through_balls'], playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['through_balls']), 1)

# Overall stats
ax1.text(0.56, 0.85, "Tot.     Suc.   %Acc", fontweight = "bold", color="white")
ax1.text(0.04, 0.65, "All Passes:", fontsize=10, color="white")
ax1.text(0.6, 0.65, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['passes']), fontsize=10, color="white", ha = "center")
ax1.text(0.775, 0.65, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_passes']), fontsize=10, color="white", ha = "center")
ax1.text(0.95, 0.65, str(h_pass_pct) + "%", fontsize=10, color="white", ha = "center")
ax1.text(0.04, 0.52, "Forward Passes:", fontsize=10,  color="white")
ax1.text(0.6, 0.52, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['fwd_passes']), fontsize=10, color="white", ha = "center")
ax1.text(0.775, 0.52, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_fwd_passes']), fontsize=10, color="white", ha = "center")
ax1.text(0.95, 0.52, str(h_fwd_pct) + "%", fontsize=10, color="white", ha = "center")
ax1.text(0.04, 0.39, "Progressive Passes:", fontsize=10,  color="white")
ax1.text(0.6, 0.39, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['prog_passes']), fontsize=10, color="white", ha = "center")
ax1.text(0.775, 0.39, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_prog_passes']), fontsize=10, color="white", ha = "center")
ax1.text(0.95, 0.39, str(h_prog_pct) + "%", fontsize=10, color="white", ha = "center")
ax1.text(0.04, 0.26, "Crosses:", fontsize=10,  color="white")
ax1.text(0.6, 0.26, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['crosses']), fontsize=10, color="white", ha = "center")
ax1.text(0.775, 0.26, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_crosses']), fontsize=10, color="white", ha = "center")
ax1.text(0.95, 0.26, str(h_cross_pct) + "%", fontsize=10, color="white", ha = "center")
ax1.text(0.04, 0.13, "Long Balls:", fontsize=10,  color="white")
ax1.text(0.6, 0.13, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['long_balls']), fontsize=10, color="white", ha = "center")
ax1.text(0.775, 0.13, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_long_balls']), fontsize=10, color="white", ha = "center")
ax1.text(0.95, 0.13, str(h_long_ball_pct) + "%", fontsize=10, color="white", ha = "center")
ax1.text(0.04, 0, "Through Balls:", fontsize=10,  color="white")
ax1.text(0.6, 0, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['through_balls']), fontsize=10, color="white", ha = "center")
ax1.text(0.775, 0, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[home_team,:]['suc_through_balls']), fontsize=10, color="white", ha = "center")
ax1.text(0.95, 0, str(h_through_ball_pct) + "%", fontsize=10, color="white", ha = "center")
ax1.plot([0.56, 1], [0.8, 0.8], color = "w", lw=1)
ax2.text(0.56, 0.85, "Tot.     Suc.   %Acc.", fontweight = "bold", color="white")
ax2.text(0.04, 0.65, "All Passes:", fontsize=10,  color="white")
ax2.text(0.6, 0.65, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['passes']), fontsize=10, color="white", ha = "center")
ax2.text(0.775, 0.65, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_passes']), fontsize=10, color="white", ha = "center")
ax2.text(0.95, 0.65, str(a_pass_pct) + "%", fontsize=10, color="white", ha = "center")
ax2.text(0.04, 0.52, "Forward Passes:", fontsize=10,  color="white")
ax2.text(0.6, 0.52, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['fwd_passes']), fontsize=10, color="white", ha = "center")
ax2.text(0.775, 0.52, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_fwd_passes']), fontsize=10, color="white", ha = "center")
ax2.text(0.95, 0.52, str(a_fwd_pct) + "%", fontsize=10, color="white", ha = "center")
ax2.text(0.04, 0.39, "Progressive Passes:", fontsize=10,  color="white")
ax2.text(0.6, 0.39, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['prog_passes']), fontsize=10, color="white", ha = "center")
ax2.text(0.775, 0.39, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_prog_passes']), fontsize=10, color="white", ha = "center")
ax2.text(0.95, 0.39, str(a_prog_pct) + "%", fontsize=10, color="white", ha = "center")
ax2.text(0.04, 0.26, "Crosses:", fontsize=10,  color="white")
ax2.text(0.6, 0.26, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['crosses']), fontsize=10, color="white", ha = "center")
ax2.text(0.775, 0.26, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_crosses']), fontsize=10, color="white", ha = "center")
ax2.text(0.95, 0.26, str(a_cross_pct) + "%", fontsize=10, color="white", ha = "center")
ax2.text(0.04, 0.13, "Long Balls:", fontsize=10,  color="white")
ax2.text(0.6, 0.13, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['long_balls']), fontsize=10, color="white", ha = "center")
ax2.text(0.775, 0.13, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_long_balls']), fontsize=10, color="white", ha = "center")
ax2.text(0.95, 0.13, str(a_long_ball_pct) + "%", fontsize=10, color="white", ha = "center")
ax2.text(0.04, 0, "Through Balls:", fontsize=10,  color="white")
ax2.text(0.6, 0, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['through_balls']), fontsize=10, color="white", ha = "center")
ax2.text(0.775, 0, int(playerinfo_df.groupby(by='team', axis=0).sum().loc[away_team,:]['suc_through_balls']), fontsize=10, color="white", ha = "center")
ax2.text(0.95, 0, str(a_through_ball_pct) + "%", fontsize=10, color="white", ha = "center")
ax2.plot([0.56, 1], [0.8, 0.8], color = "w", lw=1)

# Add Logos
ax = fig1.add_axes([0.01, 0.862, 0.12, 0.12])
ax.axis("off")
ax.imshow(home_logo)
ax = fig2.add_axes([0.01, 0.862, 0.12, 0.12])
ax.axis("off")
ax.imshow(away_logo)

# Footer text
fig1.text(0.5, 0.028, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")
fig2.text(0.5, 0.028, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig1.add_axes([0.935, 0.015, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)
ax = fig2.add_axes([0.935, 0.015, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save images
fig1.savefig(f"pass_reports/{league}-{match_id}-{home_team}-{away_team}-passreport_{home_team}", dpi=300)
fig2.savefig(f"pass_reports/{league}-{match_id}-{home_team}-{away_team}-passreport_{away_team}", dpi=300)