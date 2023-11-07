# %% Tool to identifier players that have significant impact on their respective teams when on the pitch

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
league = 'EPL'

# Select position to exclude
pos_exclude=['GK']

# Position formatting on title
pos_input = 'outfield players'

# Min minutes played (only used if normalising)
min_mp = 900
min_mnp = 900

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


# %% Build dictionary of players that have been in the matchday squad for each team

playerinfo_df = wde.create_player_list(players_df,  pass_extra=['teamId'])
playerinfo_df = playerinfo_df[playerinfo_df['mins_played']>=min_mp]

team_players_dict = {}

for team_id in playerinfo_df['teamId'].unique():    
    team_players_dict[team_id] = playerinfo_df[playerinfo_df['teamId']==team_id].index.unique().tolist()

# %% Build out full player dataframe acccounting for players in squad

playerinfo_list = list()
playerid_list = list()

for match in players_df['match_id'].unique():
    
    for team_id in players_df[players_df['match_id']==match]['teamId'].unique(): 
        team_players_in_squad = players_df[(players_df['match_id']==match) & (players_df['teamId']==team_id)]
        match_mins = team_players_in_squad['time_off'].max()
        
        for player_id in team_players_dict[team_id]:
            
            if player_id in team_players_in_squad.index.tolist():
                player = team_players_in_squad[team_players_in_squad.index == player_id]
                playerinfo_list.append([player['name'].values[0],
                                        player['position'].values[0],
                                        player['isFirstEleven'].values[0],
                                        True,
                                        team_id,
                                        player['team'].values[0],
                                        match,
                                        player['time_on'].values[0] if player['time_on'].values[0] == player['time_on'].values[0] else 0,
                                        player['time_off'].values[0] if player['time_off'].values[0] == player['time_off'].values[0] else 0,
                                        player['mins_played'].values[0] if player['mins_played'].values[0] == player['mins_played'].values[0] else 0,
                                        match_mins - player['mins_played'].values[0] if player['mins_played'].values[0] == player['mins_played'].values[0] else match_mins
                                        ])                
            else:
                
                playerinfo_list.append([players_df[players_df.index==player_id]['name'].values[0],
                                        'Out',
                                        np.nan,
                                        False,
                                        team_id,
                                        players_df[players_df['teamId'] == team_id]['team'].values[0],
                                        match,
                                        0,
                                        0,
                                        0,
                                        match_mins
                                        ])
            playerid_list.append(player_id)  

full_players_df = pd.DataFrame(data = playerinfo_list,
                               columns = ['name', 'position', 'isFirstEleven', 'isSquad', 'teamId', 'team', 'match_id', 'time_on', 'time_off', 'mins_played', 'mins_not_played'],
                               index = playerid_list)


# %% Determine threat created and chances created by team when player is on and off the pitch

xT_gen_list_on = list()
xT_conc_list_on = list()
shots_for_list_on = list()
shots_against_list_on = list()
xT_gen_list_off = list()
xT_conc_list_off = list()
shots_for_list_off = list()
shots_against_list_off = list()

for idx, lineup_player in full_players_df.iterrows():
    match_events = events_df[events_df['match_id']==lineup_player['match_id']]

    ip_events_when_on = match_events[(match_events['cumulative_mins'] >= lineup_player['time_on']) &
                                     (match_events['cumulative_mins'] <= lineup_player['time_off']) &
                                     (match_events['satisfiedEventsTypes'].apply(lambda x: not any(item in x for item in [48, 50, 51, 42, 44, 45, 31, 34, 212])))
                                     ]
    ip_events_when_off = match_events[((match_events['cumulative_mins'] < lineup_player['time_on']) |
                                       (match_events['cumulative_mins'] > lineup_player['time_off'])) &
                                      (match_events['satisfiedEventsTypes'].apply(lambda x: not any(item in x for item in [48, 50, 51, 42, 44, 45, 31, 34, 212])))
                                      ]
    match_mins = match_events['expandedMinute'].max()
    
    ip_team_events_when_on = ip_events_when_on[ip_events_when_on['teamId']==lineup_player['teamId']]
    ip_opp_events_when_on = ip_events_when_on[ip_events_when_on['teamId']!=lineup_player['teamId']]
    ip_team_events_when_off = ip_events_when_off[ip_events_when_off['teamId']==lineup_player['teamId']]
    ip_opp_events_when_off = ip_events_when_off[ip_events_when_off['teamId']!=lineup_player['teamId']]

    xT_gen_list_on.append(ip_team_events_when_on['xThreat_gen'].sum())
    xT_conc_list_on.append(ip_opp_events_when_on['xThreat_gen'].sum())
    shots_for_list_on.append(ip_team_events_when_on[ip_team_events_when_on['eventType'].isin(['MissedShots', 'SavedShot', 'Goal'])]['id'].count())
    shots_against_list_on.append(ip_opp_events_when_on[ip_opp_events_when_on['eventType'].isin(['MissedShots', 'SavedShot', 'Goal'])]['id'].count())

    xT_gen_list_off.append(ip_team_events_when_off['xThreat_gen'].sum())
    xT_conc_list_off.append(ip_opp_events_when_off['xThreat_gen'].sum())
    shots_for_list_off.append(ip_team_events_when_off[ip_team_events_when_off['eventType'].isin(['MissedShots', 'SavedShot', 'Goal'])]['id'].count())
    shots_against_list_off.append(ip_opp_events_when_off[ip_opp_events_when_off['eventType'].isin(['MissedShots', 'SavedShot', 'Goal'])]['id'].count())

# %% Assign lists to columns

full_players_df.loc[:,'team_xT_on'] = xT_gen_list_on
full_players_df.loc[:,'opp_xT_on'] = xT_conc_list_on
full_players_df.loc[:,'team_shots_on'] = shots_for_list_on
full_players_df.loc[:,'opp_shots_on'] =shots_against_list_on
full_players_df.loc[:,'team_xT_off'] = xT_gen_list_off
full_players_df.loc[:,'opp_xT_off'] = xT_conc_list_off
full_players_df.loc[:,'team_shots_off'] = shots_for_list_off
full_players_df.loc[:,'opp_shots_off'] = shots_against_list_off

# %% Create player dataframe and account for players that have played for multiple teams

playerinfo_df = wde.create_player_list(full_players_df, additional_cols=['mins_not_played', 'team_xT_on', 'opp_xT_on',
                                                                    'team_shots_on', 'opp_shots_on', 'team_xT_off',
                                                                    'opp_xT_off', 'team_shots_off', 'opp_shots_off'])

playerinfo_df = playerinfo_df[(~playerinfo_df['position'].isin(pos_exclude)) & (playerinfo_df['mins_not_played']>=min_mnp)]

# %% Normalise per 90 and split into valid offensive and defensive positions

playerinfo_df['increase_team_xT_90_on'] = (90*playerinfo_df['team_xT_on']/playerinfo_df['mins_played']) - (90*playerinfo_df['team_xT_off']/playerinfo_df['mins_not_played'])
playerinfo_df['increase_team_shots_90_on'] = (90*playerinfo_df['team_shots_on']/playerinfo_df['mins_played']) - (90*playerinfo_df['team_shots_off']/playerinfo_df['mins_not_played'])
playerinfo_df['decrease_opp_xT_90_on'] = (90*playerinfo_df['opp_xT_off']/playerinfo_df['mins_not_played']) - (90*playerinfo_df['opp_xT_on']/playerinfo_df['mins_played'])
playerinfo_df['decrease_opp_shots_90_on'] = (90*playerinfo_df['opp_shots_off']/playerinfo_df['mins_not_played']) - (90*playerinfo_df['opp_shots_on']/playerinfo_df['mins_played'])
playerinfo_df['increase_delta_xT_90_on'] = (90*(playerinfo_df['team_xT_on'] - playerinfo_df['opp_xT_on'])/playerinfo_df['mins_played']) - (90*(playerinfo_df['team_xT_off'] - playerinfo_df['opp_xT_off'])/playerinfo_df['mins_not_played'])

att_playerinfo_df = playerinfo_df[playerinfo_df['position'].isin(['FW', 'FWL', 'FWR', 'DMC', 'DMR', 'DML', 'MR', 'ML', 'MC', 'AMC', 'AML', 'AMR', 'DR', 'DL', 'Sub'])]
def_playerinfo_df = playerinfo_df[playerinfo_df['position'].isin(['DMC', 'DMR', 'DML', 'MC', 'DC', 'DR', 'DL'])]

# Manually drop players that are miscategorised
def_playerinfo_df = def_playerinfo_df[~def_playerinfo_df['name'].isin(['Eberechi Eze'])]

# %% FIGURE 1 - Best and worst players by impact on team threat creation

# Select top and botton number of players to show
n_players = 10

#  Get top 10 and bottom 10 players and pad with empty rows
att_playerinfo_df = att_playerinfo_df.sort_values('increase_team_xT_90_on', ascending=False)
empty_df = pd.DataFrame(index = [0], columns = att_playerinfo_df.columns)
empty_df['increase_team_xT_90_on']=0
empty_df['name']=""
plot_df = pd.concat([att_playerinfo_df.head(n_players), empty_df, att_playerinfo_df.tail(n_players), empty_df])
plot_df.reset_index(drop=True, inplace=True)

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Set-up bar plot
fig, ax = plt.subplots(figsize=(8.5, 9.5))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Define colour scale
my_cmap = plt.get_cmap("viridis")
my_cmap = my_cmap(np.linspace(0.2,0.94,256))
color_scale = 255*(plot_df['increase_team_xT_90_on'] - plot_df['increase_team_xT_90_on'].min())/(plot_df['increase_team_xT_90_on'].max() - plot_df['increase_team_xT_90_on'].min())
color_scale = [int(color) for color in color_scale.values.tolist()]

# Plot data
ax.barh(plot_df.index, plot_df["increase_team_xT_90_on"], color=my_cmap[color_scale])
ax.plot([0, 0], [2*n_players+2, -2], color = 'w', lw = 0.5)

# Get x limits and draw seperating line
xlim = ax.get_xlim()
ylim = ax.get_ylim()
xlim = ax.set_xlim([-max([abs(xlim[0]), abs(xlim[1])]),max([abs(xlim[0]), abs(xlim[1])])] )

xdist = xlim[1] - xlim[0]
ydist = ylim[1] - ylim[0]
ax.plot([0.8*xlim[0] , 0.8*xlim[1]], [n_players, n_players], color = 'w', lw = 0.5)

# Position top and bottom player labels 5% from either edge of imagr
ax.text(xlim[0]+0.1*xdist, n_players-0.5, f"Top {n_players}", fontweight = "bold", c = "w", fontsize = 12, ha = "left", va = "bottom")
ax.text(xlim[1]-0.1*xdist, n_players+0.5, f"Bottom {n_players}", fontweight = "bold", c = "w", fontsize = 12, ha = "right", va = "top")

# Create title
title_text = f"{leagues[league]} {year}/{str(int(year)+1).replace('20','',1)} − Player Impact on Team"
subtitle_text = "A Comparison of Team Threat Creation when Player is On vs. Off the Pitch"
subsubtitle_text = f"GKs & CBs removed. Players that have played  >{min_mp} mins and not played >{min_mnp} mins included"
fig.text(0.135, 0.94, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.135, 0.914, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.135, 0.89, subsubtitle_text, fontweight="regular", fontsize=10, color='w')

# Define axes
ax.set_xlabel("Improvement in total xT created by team when on pitch (ΔxT For/90)", labelpad = 10, fontweight="bold", fontsize=12, color='w')
ax.set_ylim(-0.5, len(plot_df)-0.5)
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_visible(False)
ax.set_axisbelow(True)
ax.grid(color='gray', alpha = 0.2)
ax.set_yticks([])
plt.gca().invert_yaxis()

# Add axes labels and badges
path_eff = [path_effects.Stroke(linewidth=3, foreground='#313332'), path_effects.Normal()]
for idx, plot_pos in enumerate(np.arange(0.2, len(plot_df))):
    if idx not in [n_players,2*n_players+1]:
        team = plot_df.loc[idx,"team"]
        team_logo, _ = lab.get_team_badge_and_colour(team)
        if plot_df.loc[idx,"increase_team_xT_90_on"] > 0:
            ax.text(plot_df.loc[idx,"increase_team_xT_90_on"], plot_pos, "+" + str(round(plot_df.loc[idx,"increase_team_xT_90_on"],2))+ " ", fontsize = 8, color = 'w', va = "bottom", ha = "right", path_effects = path_eff)
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.05, resample = True), (-xdist*0.025, plot_pos-ydist*0.007), frameon=False)    
            ax.add_artist(ab)
            ax.text(-xdist*0.05, plot_pos, plot_df.loc[idx,"name"], fontsize = 8, color = 'w', va = "bottom", ha = "right")

        else:
            ax.text(plot_df.loc[idx,"increase_team_xT_90_on"], plot_pos, " " + str(round(plot_df.loc[idx,"increase_team_xT_90_on"],2)), fontsize = 8, color = 'w', va = "bottom", ha = "left", path_effects = path_eff)
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.05, resample = True), (xdist*0.025, plot_pos-ydist*0.007), frameon=False)    
            ax.add_artist(ab)
            ax.text(xdist*0.05, plot_pos, plot_df.loc[idx,"name"], fontsize = 8, color = 'w', va = "bottom", ha = "left")

# Add competition Logo
ax2 = fig.add_axes([0.032, 0.875, 0.1, 0.1])
ax2.axis("off")
ax2.imshow(comp_logo)

# Create footer
fig.text(0.5, 0.024, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.93, 0.006, 0.05, 0.05])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

# Tight layout
fig.tight_layout(rect=[-0.08, 0.02, 0.95, 0.86])

# Save image to file 
fig.savefig(f"player_impact_on_team/{league}-{year}-player_impact_on_threat_creation", dpi=300)


# %% FIGURE 2 - Best and worst players by impact on team threat concession

# Select top and botton number of players to show
n_players = 10

#  Get top 10 and bottom 10 players and pad with empty rows
def_playerinfo_df = def_playerinfo_df.sort_values('decrease_opp_xT_90_on', ascending=False)
empty_df = pd.DataFrame(index = [0], columns = att_playerinfo_df.columns)
empty_df['decrease_opp_xT_90_on']=0
empty_df['name']=""
plot_df = pd.concat([def_playerinfo_df.head(n_players), empty_df, def_playerinfo_df.tail(n_players), empty_df])
plot_df.reset_index(drop=True, inplace=True)

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Set-up bar plot
fig, ax = plt.subplots(figsize=(8.5, 9.5))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Define colour scale
my_cmap = plt.get_cmap("viridis")
my_cmap = my_cmap(np.linspace(0.2,0.94,256))
color_scale = 255*(plot_df['decrease_opp_xT_90_on'] - plot_df['decrease_opp_xT_90_on'].min())/(plot_df['decrease_opp_xT_90_on'].max() - plot_df['decrease_opp_xT_90_on'].min())
color_scale = [int(color) for color in color_scale.values.tolist()]

# Plot data
ax.barh(plot_df.index, plot_df["decrease_opp_xT_90_on"], color=my_cmap[color_scale])
ax.plot([0, 0], [2*n_players+2, -2], color = 'w', lw = 0.5)

# Get x limits and draw seperating line
xlim = ax.get_xlim()
ylim = ax.get_ylim()
xlim = ax.set_xlim([-max([abs(xlim[0]), abs(xlim[1])]),max([abs(xlim[0]), abs(xlim[1])])] )

xdist = xlim[1] - xlim[0]
ydist = ylim[1] - ylim[0]
ax.plot([0.8*xlim[0] , 0.8*xlim[1]], [n_players, n_players], color = 'w', lw = 0.5)

# Position top and bottom player labels 5% from either edge of imagr
ax.text(xlim[0]+0.1*xdist, n_players-0.5, f"Top {n_players}", fontweight = "bold", c = "w", fontsize = 12, ha = "left", va = "bottom")
ax.text(xlim[1]-0.1*xdist, n_players+0.5, f"Bottom {n_players}", fontweight = "bold", c = "w", fontsize = 12, ha = "right", va = "top")

# Create title
title_text = f"{leagues[league]} {year}/{str(int(year)+1).replace('20','',1)} − Player Impact on Team"
subtitle_text = "A Comparison of Team Threat Concession when Player is On vs. Off the Pitch"
subsubtitle_text = f"Attackers removed. Players that have played  >{min_mp} mins and not played >{min_mnp} mins included"
fig.text(0.135, 0.94, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.135, 0.914, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.135, 0.89, subsubtitle_text, fontweight="regular", fontsize=10, color='w')

# Define axes
ax.set_xlabel("Reduction in total xT conceded by team when on pitch (ΔxT Against/90)", labelpad = 10, fontweight="bold", fontsize=12, color='w')
ax.set_ylim(-0.5, len(plot_df)-0.5)
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_visible(False)
ax.set_axisbelow(True)
ax.grid(color='gray', alpha = 0.2)
ax.set_yticks([])
plt.gca().invert_yaxis()

# Add axes labels and badges
path_eff = [path_effects.Stroke(linewidth=3, foreground='#313332'), path_effects.Normal()]
for idx, plot_pos in enumerate(np.arange(0.2, len(plot_df))):
    if idx not in [n_players,2*n_players+1]:
        team = plot_df.loc[idx,"team"]
        team_logo, _ = lab.get_team_badge_and_colour(team)
        if plot_df.loc[idx,"decrease_opp_xT_90_on"] > 0:
            ax.text(plot_df.loc[idx,"decrease_opp_xT_90_on"], plot_pos, "+" + str(round(plot_df.loc[idx,"decrease_opp_xT_90_on"],2))+ " ", fontsize = 8, color = 'w', va = "bottom", ha = "right", path_effects = path_eff)
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.05, resample = True), (-xdist*0.025, plot_pos-ydist*0.007), frameon=False)    
            ax.add_artist(ab)
            ax.text(-xdist*0.05, plot_pos, plot_df.loc[idx,"name"], fontsize = 8, color = 'w', va = "bottom", ha = "right")

        else:
            ax.text(plot_df.loc[idx,"decrease_opp_xT_90_on"], plot_pos, " " + str(round(plot_df.loc[idx,"decrease_opp_xT_90_on"],2)), fontsize = 8, color = 'w', va = "bottom", ha = "left", path_effects = path_eff)
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.05, resample = True), (xdist*0.025, plot_pos-ydist*0.007), frameon=False)    
            ax.add_artist(ab)
            ax.text(xdist*0.05, plot_pos, plot_df.loc[idx,"name"], fontsize = 8, color = 'w', va = "bottom", ha = "left")

# Add competition Logo
ax2 = fig.add_axes([0.032, 0.875, 0.1, 0.1])
ax2.axis("off")
ax2.imshow(comp_logo)

# Create footer
fig.text(0.5, 0.024, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.93, 0.006, 0.05, 0.05])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

# Tight layout
fig.tight_layout(rect=[-0.08, 0.02, 0.95, 0.86])

# Save image to file 
fig.savefig(f"player_impact_on_team/{league}-{year}-player_impact_on_threat_concession", dpi=300)

# %% FIGURE 3 - Best and worst players by impact on team difference in threat creation and concession

# Select top and botton number of players to show
n_players = 10

#  Get top 10 and bottom 10 players and pad with empty rows
playerinfo_df = playerinfo_df.sort_values('increase_delta_xT_90_on', ascending=False)
empty_df = pd.DataFrame(index = [0], columns = att_playerinfo_df.columns)
empty_df['increase_delta_xT_90_on']=0
empty_df['name']=""
plot_df = pd.concat([playerinfo_df.head(n_players), empty_df, playerinfo_df.tail(n_players), empty_df])
plot_df.reset_index(drop=True, inplace=True)

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Set-up bar plot
fig, ax = plt.subplots(figsize=(8.5, 9.5))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Define colour scale
my_cmap = plt.get_cmap("viridis")
my_cmap = my_cmap(np.linspace(0.2,0.94,256))
color_scale = 255*(plot_df['increase_delta_xT_90_on'] - plot_df['increase_delta_xT_90_on'].min())/(plot_df['increase_delta_xT_90_on'].max() - plot_df['increase_delta_xT_90_on'].min())
color_scale = [int(color) for color in color_scale.values.tolist()]

# Plot data
ax.barh(plot_df.index, plot_df["increase_delta_xT_90_on"], color=my_cmap[color_scale])
ax.plot([0, 0], [2*n_players+2, -2], color = 'w', lw = 0.5)

# Get x limits and draw seperating line
xlim = ax.get_xlim()
ylim = ax.get_ylim()
xlim = ax.set_xlim([-max([abs(xlim[0]), abs(xlim[1])]),max([abs(xlim[0]), abs(xlim[1])])] )

xdist = xlim[1] - xlim[0]
ydist = ylim[1] - ylim[0]
ax.plot([0.8*xlim[0] , 0.8*xlim[1]], [n_players, n_players], color = 'w', lw = 0.5)

# Position top and bottom player labels 5% from either edge of imagr
ax.text(xlim[0]+0.1*xdist, n_players-0.5, f"Top {n_players}", fontweight = "bold", c = "w", fontsize = 12, ha = "left", va = "bottom")
ax.text(xlim[1]-0.1*xdist, n_players+0.5, f"Bottom {n_players}", fontweight = "bold", c = "w", fontsize = 12, ha = "right", va = "top")

# Create title
title_text = f"{leagues[league]} {year}/{str(int(year)+1).replace('20','',1)} − Player Impact on Team"
subtitle_text = "A Comparison of Team Threat Difference when Player is On vs. Off the Pitch"
subsubtitle_text = f"GKs removed. Players that have played  >{min_mp} mins and not played >{min_mnp} mins included"
fig.text(0.135, 0.94, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.135, 0.914, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.135, 0.89, subsubtitle_text, fontweight="regular", fontsize=10, color='w')

# Define axes
ax.set_xlabel("Improvement in team 'xT For' − 'xT Against' when on pitch (ΔxT Diff/90)", labelpad = 10, fontweight="bold", fontsize=12, color='w')
ax.set_ylim(-0.5, len(plot_df)-0.5)
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_visible(False)
ax.set_axisbelow(True)
ax.grid(color='gray', alpha = 0.2)
ax.set_yticks([])
plt.gca().invert_yaxis()

# Add axes labels and badges
path_eff = [path_effects.Stroke(linewidth=3, foreground='#313332'), path_effects.Normal()]
for idx, plot_pos in enumerate(np.arange(0.2, len(plot_df))):
    if idx not in [n_players,2*n_players+1]:
        team = plot_df.loc[idx,"team"]
        team_logo, _ = lab.get_team_badge_and_colour(team)
        if plot_df.loc[idx,"increase_delta_xT_90_on"] > 0:
            ax.text(plot_df.loc[idx,"increase_delta_xT_90_on"], plot_pos, "+" + str(round(plot_df.loc[idx,"increase_delta_xT_90_on"],2))+ " ", fontsize = 8, color = 'w', va = "bottom", ha = "right", path_effects = path_eff)
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.05, resample = True), (-xdist*0.025, plot_pos-ydist*0.007), frameon=False)    
            ax.add_artist(ab)
            ax.text(-xdist*0.05, plot_pos, plot_df.loc[idx,"name"], fontsize = 8, color = 'w', va = "bottom", ha = "right")

        else:
            ax.text(plot_df.loc[idx,"increase_delta_xT_90_on"], plot_pos, " " + str(round(plot_df.loc[idx,"increase_delta_xT_90_on"],2)), fontsize = 8, color = 'w', va = "bottom", ha = "left", path_effects = path_eff)
            ab = AnnotationBbox(OffsetImage(team_logo, zoom = 0.05, resample = True), (xdist*0.025, plot_pos-ydist*0.007), frameon=False)    
            ax.add_artist(ab)
            ax.text(xdist*0.05, plot_pos, plot_df.loc[idx,"name"], fontsize = 8, color = 'w', va = "bottom", ha = "left")

# Add competition Logo
ax2 = fig.add_axes([0.032, 0.875, 0.1, 0.1])
ax2.axis("off")
ax2.imshow(comp_logo)

# Create footer
fig.text(0.5, 0.024, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.93, 0.006, 0.05, 0.05])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

# Tight layout
fig.tight_layout(rect=[-0.08, 0.02, 0.95, 0.86])

# Save image to file 
fig.savefig(f"player_impact_on_team/{league}-{year}-player_impact_on_threat_difference", dpi=300)