# %% Create visualisation of top players penalty quality
#
# Inputs:   List containing years and leagues
#           Minimum penalties to quality
#           Plot mode
#
# Outputs:  Top 12 players by penalty quality

# %% Imports

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as patch
import matplotlib.cm as cm
from PIL import Image
from mplsoccer.pitch import VerticalPitch, Pitch
import matplotlib.patheffects as path_effects
import os
import sys
import bz2
import pickle
import numpy as np
import highlight_text as htext
import glob

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.pitch_zones as pz
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% User inputs

# Input WhoScored range of match id
data_grab = [['La_Liga', '2021'],
             ['La_Liga', '2020'],
             ['La_Liga', '2019'],
             ['EPL', '2021'],
             ['EPL', '2020'],
             ['EPL', '2019'],
             ['Bundesliga', '2021'],
             ['Bundesliga', '2020'],
             ['Bundesliga', '2019'],
             ['Serie_A', '2021'],
             ['Serie_A', '2020'],
             ['Serie_A', '2019'],
             ['Ligue_1', '2021'],
             ['Ligue_1', '2020'],
             ['Ligue_1', '2019']]

data_grab = [['EFLC', '2022']]

# Min minutes played
min_pens = 1

# Special mode (e.g. normal, top_5_europe)
mode = "normal"

#%% Get logos

logo = lab.get_competition_logo(data_grab[0][0], data_grab[0][1]) 
epl_logo = lab.get_competition_logo('EPL') 
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
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League One', 'EFL2': 'EFL League Two'}

# Add titles
if mode == "europe_top_5":
    title_str = "Europe Big Five Leagues"
elif mode == "normal":
    title_str = leagues[data_grab[0][0]]
    
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
            
    print(f"{league}, {year} data import complete")

event_types = bz2.BZ2File(f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','', 1)) + 1)}/{league}/event-types.pbz2", 'rb')
event_types = pickle.load(event_types)

# %% Create player list

players_df = wde.minutes_played(players_df, events_df)
playerinfo_df = wde.create_player_list(players_df)

# %% Reformat player list to show multiple teams per player

playerinfo_df_formatted = pd.DataFrame()

for idx, player in playerinfo_df.iterrows():
    if type(playerinfo_df.loc[idx]['team']) == str:
        player['team'] = [playerinfo_df.loc[idx]['team']]
    else:
        player['team'] = playerinfo_df.loc[idx]['team'].values.tolist()
    
    playerinfo_df_formatted = pd.concat([playerinfo_df_formatted, player], axis=1)
    
playerinfo_df_formatted = playerinfo_df_formatted.T
playerinfo_df_formatted = playerinfo_df_formatted[~playerinfo_df_formatted.index.duplicated(keep='first')]
playerinfo_df_formatted.index.name = 'playerId'

# %% Aggregate penalties

penalty_events = events_df[(events_df['satisfiedEventsTypes'].apply(lambda x: 22 in x or 135 in x or 207 in x or 208 in x or 209 in x))]

playerinfo_df_formatted = wde.group_player_events(penalty_events, playerinfo_df_formatted, primary_event_name='penalties_taken')
playerinfo_df_formatted = wde.group_player_events(penalty_events[penalty_events['eventType']=='Goal'], playerinfo_df_formatted, primary_event_name='penalties_scored')
playerinfo_df_formatted['penalty_conversion'] = 100*playerinfo_df_formatted['penalties_scored'] / playerinfo_df_formatted['penalties_taken']

# %% Calculate distance to gk midriff (assign zero if off target)

# Goal height
goal_height_opta = 39.85
goal_height_yards = 2.66667
goal_height_factor = goal_height_yards / goal_height_opta

# Goal width
goal_width_yards = 8
goal_width_opta = 9.6
goal_width_factor = goal_width_yards / goal_width_opta

# Goalkeeper midriff position
gk_y_pos_yards = 0
gk_y_pos_opta = 50
gk_z_pos_yards = 2.06667/2
gk_z_pos_opta = gk_z_pos_yards * (1/goal_height_factor)

# Distance of penalty from gk in yards
penalty_events['goal_marker'] = penalty_events['eventType'].apply(lambda x: 1 if x == 'Goal' else 0)
penalty_events.loc[:,'y_dist_from_gk']= abs((penalty_events['goalMouthY']-50)*goal_width_factor - gk_y_pos_yards)
penalty_events.loc[:,'z_dist_from_gk'] = abs(penalty_events['goalMouthZ']*goal_height_factor - gk_z_pos_yards)
penalty_events.loc[:,'dist_from_gk'] = np.sqrt(penalty_events.loc[:,'y_dist_from_gk']**2 + penalty_events.loc[:,'z_dist_from_gk']**2) #* penalty_events.loc[:,'goal_marker']

# Reset distance for off target shots
penalty_events.loc[penalty_events['eventType'].isin(['MissedShots', 'ShotOnPost']), 'dist_from_gk'] = 0

# Calculate average per player and add to player info dataframe
playerinfo_df_formatted = wde.group_player_events(penalty_events, playerinfo_df_formatted, group_type = 'mean', event_types = 'dist_from_gk')

# %% Filter out penalty takers

pentaker_df = playerinfo_df_formatted[playerinfo_df_formatted['penalties_taken']>=min_pens]
pentaker_df = pentaker_df.sort_values(['dist_from_gk', 'penalty_conversion'], ascending = [False, False])

# %% Draw figure

# Set up figure
fig = plt.figure(constrained_layout=False, figsize = (14, 10))
fig.set_facecolor('#313332')
gs = fig.add_gridspec(3, 4, left=0.03, right=0.97, top = 0.845, bottom = 0.07, wspace=0.2, hspace=0.08, height_ratios=[1, 1, 1])

# Define colourmap
marker_cmap = cm.get_cmap('RdYlGn')
marker_cmap = marker_cmap(np.linspace(0,1,256))

# Define list of goal axes
goal = [0] * 12
goal[0] = fig.add_subplot(gs[0,0])
goal[1] = fig.add_subplot(gs[0,1])
goal[2] = fig.add_subplot(gs[0,2])
goal[3] = fig.add_subplot(gs[0,3])
goal[4] = fig.add_subplot(gs[1,0])
goal[5] = fig.add_subplot(gs[1,1])
goal[6] = fig.add_subplot(gs[1,2])
goal[7] = fig.add_subplot(gs[1,3])
goal[8] = fig.add_subplot(gs[2,0])
goal[9] = fig.add_subplot(gs[2,1])
goal[10] = fig.add_subplot(gs[2,2])
goal[11] = fig.add_subplot(gs[2,3])

# Set width and height to include per goal
width_lower_lim = 43.5
width_upper_lim = 56.5
height_upper_lim = 55
height_lower_lim = -45

# Format goals
for goal_ax in goal:
    
    # Colour and axes
    goal_ax.set_facecolor('#313332')
    for axis in ['bottom', 'left', 'right', 'top']:
        goal_ax.spines[axis].set_color('w')
    
    goal_ax.tick_params(axis='x', which = 'both', bottom = False, labelbottom = False)
    goal_ax.tick_params(axis='y', which = 'both', left = False, labelleft = False)
                
    # Draw goal-line and goal posts
    goal_ax.plot([width_lower_lim, width_upper_lim],[0,0], lw = 1, color = "w")
    goal_ax.plot([45.2,45.2],[0,39.85], lw=2.5, color = "w")
    goal_ax.plot([54.8,54.8],[0,39.85], lw=2.5, color = "w")
    goal_ax.plot([45.2,54.8],[39.85,39.85], lw=2.5, color = "w")
        
    # Add pitch colouring
    pitch_alpha = 0.5
    goal_ax.fill_between((width_lower_lim, width_upper_lim), (0, 0), (-4.367, -4.367), color = (0.38612245, 0.77142857, 0.3744898, pitch_alpha), lw=0)
    goal_ax.fill_between((width_lower_lim, width_upper_lim), (-4.367, -4.367), (-10.175, -10.175), color = (0.25, 0.44, 0.12, pitch_alpha), lw=0)
    goal_ax.fill_between((width_lower_lim, width_upper_lim), (-10.175, -10.175), (-17.900, -17.900), color = (0.38612245, 0.77142857, 0.3744898, pitch_alpha), lw=0)
    goal_ax.fill_between((width_lower_lim, width_upper_lim), (-17.900, -17.900), (-28.174, -28.174), color = (0.25, 0.44, 0.12, pitch_alpha), lw=0)
    goal_ax.fill_between((width_lower_lim, width_upper_lim), (-28.174, -28.174), (-41.838, -41.838), color = (0.38612245, 0.77142857, 0.3744898, pitch_alpha), lw=0)
    goal_ax.fill_between((width_lower_lim, width_upper_lim), (-41.838, -41.838), (-60, -60), color = (0.25, 0.44, 0.12, pitch_alpha), lw=0)
    
    # Draw 6-yard box horizontal line
    goal_ax.plot([40,60], [-10.175,-10.175], lw=1.5, color = "w")
    
    # Draw penalty spot
    ellipse = patch.Ellipse(xy=(50, -40), width=0.5, height=0.5, edgecolor='w', fc='w', lw=2)
    goal_ax.add_artist(ellipse)
    
    # Draw and label GK position
    goal_ax.scatter(gk_y_pos_opta, gk_z_pos_opta, color ="w", s=10, lw = 0.5, edgecolor ='#313332', zorder=1)
    goal_ax.text(gk_y_pos_opta, gk_z_pos_opta+2, "GK", ha = "center", fontsize = 7, color ="w", zorder=1)

    # Set axis limits
    goal_ax.set_xlim(width_upper_lim, width_lower_lim)
    goal_ax.set_ylim(height_lower_lim,height_upper_lim)
    
    # Set aspect ratio
    goal_ax.set_aspect(10.7/(3*39.85))

# Loop through top players
idx = 0
for player_id, player in pentaker_df.head(12).iterrows():
    
    # Get player penalties
    player_penalties = penalty_events[penalty_events['playerId'] == player_id]
    
    # Add player name title
    goal[idx].set_title(f"  {idx + 1}: {player['name']}", loc = "left", pad = 12, color='w', fontsize = 10)

    # Plot penalty tarjectory and end location
    for _,pen in player_penalties.iterrows():
        goal[idx].plot([50,pen['goalMouthY']], [-40, pen['goalMouthZ']], 'w', ls = 'dashed', zorder=3, lw = 0.5)
        
        # Define marker colour and add marker
        dist_norm = max((pen['dist_from_gk']-1) / 3,0)
        marker_colour = marker_cmap[int(255*min(dist_norm,1))]
        goal[idx].scatter(pen['goalMouthY'], pen['goalMouthZ'], color = marker_colour, s=70, lw = 0.5, edgecolor ='#313332', zorder=2)
        if pen['eventType']!='Goal':
            if pen['eventType']=='SavedShot':
                goal[idx].scatter(pen['goalMouthY'], pen['goalMouthZ'], marker = 'x', color='#313332', edgecolor ='#313332', s=30, lw = 1.5, zorder=2)
            else:
                goal[idx].scatter(pen['goalMouthY'], pen['goalMouthZ'], color = 'grey', s=70, lw = 0.5, edgecolor ='#313332', zorder=2)              
    
    goal[idx].text(56.2, 46.5, "Av dist from GK:", ha = "left", fontsize = 7, fontweight = 'bold', color ="w", zorder=4)
    goal[idx].text(52, 46.5, f"{round(player['dist_from_gk'],2)}yds", ha = "left", fontsize = 7, color ="w", zorder=4)
    goal[idx].text(47.5, 46.5, "Scored:", ha = "left", fontsize = 7, fontweight = 'bold', color ="w", zorder=4)
    goal[idx].text(45.4, 46.5, f"{int(player['penalties_scored'])} / {int(player['penalties_taken'])}", ha = "left", fontsize = 7, color ="w", zorder=4)

    
    # Add logo for each team 
    logo_delta = 0
    for team in player['team']:
        team_logo, _ = lab.get_team_badge_and_colour(team)
        ax_pos = goal[idx].get_position()
        logo_ax = fig.add_axes([ax_pos.x1-0.03-logo_delta, ax_pos.y1+0.004, 0.035, 0.035])
        logo_ax.axis("off")
        logo_ax.imshow(team_logo)
        logo_delta -= -0.028
    idx += 1

title_text = f"{title_str} {year_str}/{int(year_str)+1} - Top 12 Players by Penalty Placement"
subtitle_text = "Players ranked by mean distance of on-target penalties from Goalkeeper midriff"
subsubtitle_text = f"Off target penalties are penalised by\nassigning a distance of 0 yards. Saved\npenalties are not penalised. Only\nplayers that have taken {min_pens}+ penalties\nare included."

fig.text(0.137, 0.932, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.137, 0.907, subtitle_text, fontweight="regular", fontsize=13, color='w')
fig.text(0.8, 0.89, subsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add competition logos
if mode == "europe_top_5":
    ax = fig.add_axes([0.02, 0.93, 0.05, 0.05])
    ax.axis("off")
    ax.imshow(epl_logo)
    ax = fig.add_axes([0.05, 0.93, 0.05, 0.05])
    ax.axis("off")
    ax.imshow(ligue1_logo)
    ax = fig.add_axes([0.083, 0.931, 0.048, 0.048])
    ax.axis("off")
    ax.imshow(seriea_logo)
    ax = fig.add_axes([0.039, 0.877, 0.045, 0.045])
    ax.axis("off")
    ax.imshow(bundesliga_logo)
    ax = fig.add_axes([0.071, 0.875, 0.05, 0.05])
    ax.axis("off")
    ax.imshow(laliga_logo)
elif mode == "normal":
   ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
   ax.axis("off")
   ax.imshow(logo)

# Add legend
path_eff = [path_effects.Stroke(linewidth=1, foreground='#313332'), path_effects.Normal()]
legend_ax = fig.add_axes([0.03, 0.03, 0.3, 0.05])
legend_ax.axis("off")
point_delta = 0.27
for point in np.arange(0,7):
    dist = 0.5 + ((point+1)/6)*3
    dist_norm = max((dist-1) / 3,0)
    marker_colour = marker_cmap[int(255*min(dist_norm,1))]
    legend_ax.scatter(0.05+point_delta, 0.5, color=marker_colour, edgecolor ='#313332', s=700, lw=2)
    legend_ax.text(0.05+point_delta, 0.49, round(dist,1), fontweight="bold", fontsize=9, color='w', zorder=2, ha = "center", va = "center", path_effects = path_eff)
    point_delta+=0.08
legend_ax.text(0.03, 0.49, "Distance\nfrom GK (yds):", fontsize=9, color='w', zorder=1, va = "center", path_effects = path_eff)
legend_ax.set_xlim(0, 1)
legend_ax.set_ylim(0, 1)
    

# Add footer text
fig.text(0.5, 0.04, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.92, 0.025, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

fig.savefig(f"player_penalty_takers/{title_str.replace(' ','_')}-{year_str}-top-penalty-takers", dpi=300)
