# %% Create visualisation of team threat creation zones
#
# Inputs:   Year to plot data from
#           League to plot data from
#           League above core league (accounting for relegated teams)
#           League below core league (accounting for promoted teams)
#           Date of run
#           Selection of whether to include percentages on visual
#           Selection of whether to brighten logo

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image, ImageEnhance
from mplsoccer.pitch import VerticalPitch, Pitch
import matplotlib.patheffects as path_effects
import matplotlib.cm as cm
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


# %% User Inputs

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'
league_below = 'EFLC'
league_above = None

# Input run-date
run_date = '28/05/2023'

# Select whether to label %
label_pct = False

# Logo brighten
logo_brighten = True

# %% Get competition logo

comp_logo = lab.get_competition_logo(league, year, logo_brighten=logo_brighten) 

# %% Get data for current year, selected league

file_path = f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','',1)) + 1)}/{league}"
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

# %% Identify all teams in selected league, current year

all_teams = set(players_df['team'])
    
# %% Get data for year before, selected league

year_before = int(year)-1
file_path = f"../../data_directory/whoscored_data/{year_before}_{str(int(str(year_before).replace('20','')) + 1)}/{league}"
files = os.listdir(file_path)

# Initialise storage dataframes
events_prev_df = pd.DataFrame()
players_prev_df = pd.DataFrame()

# Load data
for file in files:
    if '-eventdata-' in file:
        if (file.split('-')[3] in all_teams) or (file.split('-')[4].replace('.pbz2','') in all_teams):
            match_events = bz2.BZ2File(f"{file_path}/{file}", 'rb')
            match_events = pickle.load(match_events)
            events_prev_df = pd.concat([events_prev_df, match_events])
    elif '-playerdata-' in file:
        if (file.split('-')[3] in all_teams) or (file.split('-')[4].replace('.pbz2','') in all_teams):
            match_players = bz2.BZ2File(f"{file_path}/{file}", 'rb')
            match_players = pickle.load(match_players)
            players_prev_df = pd.concat([players_prev_df, match_players])
    else:
        pass

# %% Get data for current year, league below selected league

file_path = f"../../data_directory/whoscored_data/{year_before}_{str(int(str(year_before).replace('20','')) + 1)}/{league_below}"
files = os.listdir(file_path)

# Initialise storage dataframes
events_prev_below_df = pd.DataFrame()
players_prev_below_df = pd.DataFrame()

# Load data
for file in files:
    if '-eventdata-' in file:
        if (file.split('-')[3] in all_teams) or (file.split('-')[4].replace('.pbz2','') in all_teams):
            match_events = bz2.BZ2File(f"{file_path}/{file}", 'rb')
            match_events = pickle.load(match_events)
            events_prev_below_df = pd.concat([events_prev_below_df, match_events])
    elif '-playerdata-' in file:
        if (file.split('-')[3] in all_teams) or (file.split('-')[4].replace('.pbz2','') in all_teams):
            match_players = bz2.BZ2File(f"{file_path}/{file}", 'rb')
            match_players = pickle.load(match_players)
            players_prev_below_df = pd.concat([players_prev_below_df, match_players])
    else:
        pass
    
# %% Get data for current year, league above selected league

events_prev_above_df = pd.DataFrame()
players_prev_above_df = pd.DataFrame()

if league_above != None:
    
    file_path = f"../../data_directory/whoscored_data/{year_before}_{str(int(str(year_before).replace('20','')) + 1)}/{league_above}"
    files = os.listdir(file_path)
    
    # Load data
    for file in files:
        if '-eventdata-' in file:
            if (file.split('-')[3] in all_teams) or (file.split('-')[4].replace('.pbz2','') in all_teams):
                match_events = bz2.BZ2File(f"{file_path}/{file}", 'rb')
                match_events = pickle.load(match_events)
                events_prev_above_df = pd.concat([events_prev_above_df, match_events])
        elif '-playerdata-' in file:
            if (file.split('-')[3] in all_teams) or (file.split('-')[4].replace('.pbz2','') in all_teams):
                match_players = bz2.BZ2File(f"{file_path}/{file}", 'rb')
                match_players = pickle.load(match_players)
                players_prev_above_df = pd.concat([players_prev_above_df, match_players])
        else:
            pass

# %% Function to process data

def process_event_data(events_in):
    threat_creating_events = events_in[events_in['xThreat']==events_in['xThreat']]
    threat_creating_events = threat_creating_events[~threat_creating_events['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 212 in x) else False)]

    return threat_creating_events, events_in
    

threat_creating_events_df, events_df = process_event_data(events_df)
threat_creating_events_prev_df, events_prev_df = process_event_data(events_prev_df)
threat_creating_events_prev_below_df, events_prev_below_df = process_event_data(events_prev_below_df)
if league_above != None:
    threat_creating_events_prev_above_df, events_prev_above_df = process_event_data(events_prev_above_df)

# %% Get teams and order on total threat created

# Set up dictionary to store xt per 90 per team
team_xt_df = pd.DataFrame(columns = ['team', 'mins_played', 'xT_90', 'mins_played_prev', 'xT_90_prev'])
team_xt_events = dict.fromkeys(all_teams, 0)
team_xt_events_prev = dict.fromkeys(all_teams, 0)

for idx, team in enumerate(all_teams):
    
    # Store team in dataframe
    team_xt_df.loc[idx, 'team'] = team
    
    # Get team events
    team_id = players_df[players_df['team']==team]['teamId'].values[0]
    team_threat_creating_events = threat_creating_events_df[threat_creating_events_df['teamId']==team_id]
    
    # Get each team match and accumulate total mins
    team_matches = set(team_threat_creating_events['match_id'])
    team_mins = 0
    for match in team_matches:
        team_mins += events_df[events_df['match_id']==match]['cumulative_mins'].max()
     
    # Check for team in current league
    if team in set(players_prev_df['team']):
        team_threat_creating_events_prev = threat_creating_events_prev_df[threat_creating_events_prev_df['teamId']==team_id]   
        all_events_prev = events_prev_df.copy()
    elif team in set(players_prev_below_df['team']):
        team_threat_creating_events_prev = threat_creating_events_prev_below_df[threat_creating_events_prev_below_df['teamId']==team_id]  
        all_events_prev = events_prev_below_df.copy()         
    elif team in set(players_prev_above_df['team']):
        team_threat_creating_events_prev = threat_creating_events_prev_above_df[threat_creating_events_prev_above_df['teamId']==team_id]   
        all_events_prev = events_prev_above_df.copy()         

    # Get each team prev. match and accumulate total mins
    team_matches_prev = set(team_threat_creating_events_prev['match_id'])
    team_mins_prev = 0
    for match in team_matches_prev: 
        team_mins_prev += all_events_prev[all_events_prev['match_id']==match]['cumulative_mins'].max()

    # Store team mins played and  xT created per 90 in dataframe
    team_xt_df.loc[idx, 'mins_played'] = team_mins
    team_xt_df.loc[idx, 'mins_played_prev'] = team_mins_prev
    team_xt_df.loc[idx, 'xT_90'] = 90*(team_threat_creating_events['xThreat_gen'].sum() / team_mins)
    team_xt_df.loc[idx, 'xT_90_prev'] = 90*(team_threat_creating_events_prev['xThreat_gen'].sum() / team_mins_prev)
    
    # Store events in appropriate dictionary
    team_xt_events[team] = team_threat_creating_events
    team_xt_events_prev[team] = team_threat_creating_events_prev

# %% Calc xT difference and order dataframe

team_xt_df['xT_90_diff'] = team_xt_df['xT_90'] - team_xt_df['xT_90_prev']
team_xt_df.sort_values('xT_90_diff', ascending = False, inplace = True)

# %% Define custom colourmap

selected_cmap = cm.get_cmap('PiYG')

rgb_left = (int(255*selected_cmap(0)[0]), int(255*selected_cmap(0)[1]), int(255*selected_cmap(0)[2]))
rgb_right = (int(255*selected_cmap(255)[0]), int(255*selected_cmap(255)[1]), int(255*selected_cmap(255)[2]))

colorsList = [rgb_left,(49,51,50),rgb_right]
CustomCmap = mpl.colors.LinearSegmentedColormap.from_list("", ["violet","#313332","palegreen"])

# %% Create visual

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Path effects
path_eff = [path_effects.Stroke(linewidth=4, foreground='#313332'), path_effects.Normal()]

# Define grid dimensions
ncols = 4
nrows = int(np.ceil(len(team_xt_df)/ncols))

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=nrows, ncols=ncols, grid_height=0.8, title_height = 0.13, endnote_height = 0.04, space=0.12, axis=False)
fig.set_size_inches(14, 15)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)
idx = 0

# Loop through each team
for _, team_row in team_xt_df.iterrows():
    
    # Get team name and events
    team = team_row['team']
    team_threat_creating_events = team_xt_events[team]
    team_threat_creating_events_prev = team_xt_events_prev[team]

    # Get team logo and colour
    team_logo, team_cmap = lab.get_team_badge_and_colour(team)

    # Bin threat creating events and normalise per 90
    bin_statistic = pitch.bin_statistic(team_threat_creating_events['x'], team_threat_creating_events['y'],
                                        statistic='sum', bins=(6, 5), normalize=False, values = team_threat_creating_events['xThreat_gen'])
    bin_statistic['statistic'] = (90*bin_statistic['statistic']/team_row['mins_played']).round(3)

    bin_statistic_prev = pitch.bin_statistic(team_threat_creating_events_prev['x'], team_threat_creating_events_prev['y'],
                                        statistic='sum', bins=(6, 5), normalize=False, values = team_threat_creating_events_prev['xThreat_gen'])
    bin_statistic_prev['statistic'] = (90*bin_statistic_prev['statistic']/team_row['mins_played_prev']).round(3)
    
    bin_statistic_change = bin_statistic.copy()
    bin_statistic_change['statistic'] = bin_statistic['statistic'] - bin_statistic_prev['statistic']

    # Draw heatmap
    pcm = pitch.heatmap(bin_statistic_change, ax['pitch'][idx], cmap=CustomCmap, edgecolor='w', lw=0.5, vmin= -0.04, vmax = 0.04, zorder=0, alpha=0.7)

    # Label heatmap zones with pressure count if selected
    path_eff = [path_effects.Stroke(linewidth=1.5, foreground='#313332'), path_effects.Normal()]
    if label_pct:
        labels = pitch.label_heatmap(bin_statistic, color='w', fontsize=10, fontweight = 'bold',
                                     ax=ax['pitch'][idx], ha='center', va='center', str_format='{:.0%}', path_effects=path_eff)
    
    # Label xt
    ax['pitch'][idx].text(2, 12, f"xT/90 {int(year.replace('20','',1))}/{int(year.replace('20','',1))+1}:", fontsize=9, fontweight='bold', color='w', zorder=3, path_effects = path_eff)
    ax['pitch'][idx].text(40, 12, round(team_row['xT_90'],2), fontsize=9, fontweight='bold', color='w', zorder=3, path_effects = path_eff)
    ax['pitch'][idx].text(2, 2, f"xT/90 {int(year.replace('20','',1))-1}/{int(year.replace('20','',1))}:", fontsize=9, fontweight='bold', color='w', zorder=3, path_effects = path_eff)
    ax['pitch'][idx].text(40, 2, round(team_row['xT_90_prev'],2), fontsize=9, fontweight='bold', color='w', zorder=3, path_effects = path_eff)
    
    # Set title
    ax['pitch'][idx].set_title(f"  {idx + 1}:  {team}", pad=2, loc = "left", color='w', fontsize = 16)
            
    ax_pos = ax['pitch'][idx].get_position()
    
    logo_ax = fig.add_axes([ax_pos.x1-0.02, ax_pos.y1, 0.02, 0.02])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx+=1
    
# Add colour bar

ax = fig.add_axes([0.35, 0.02, 0.1, 0.04])
ax.axis("off")
cbar = fig.colorbar(pcm, ax=ax, fraction=0.4, shrink=2, orientation='horizontal')
cbar.ax.set_title('Change in xT/90', color='w', fontsize=8, pad = 2)

# Title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League One', 'EFL2': 'EFL League Two'}

title_text = f"{leagues[league]} {year}/{int(year)+1} − Improvement in Threat Creation by Team"
subtitle_text = "Zones of <Improved> and <Reduced> Threat Creation compared to Last Season"
subsubtitle_text = f"In-Play Pass, Carry and Dribble events included. Negative threat events excluded. Correct as of {run_date}"

fig.text(0.12, 0.945, title_text, fontweight="bold", fontsize=20, color='w')
htext.fig_text(0.12, 0.934, s=subtitle_text, fontweight="bold", fontsize=18, color='w',
               highlight_textprops=[{"color": 'palegreen', "fontweight": 'bold'}, {"color": 'violet', "fontweight": 'bold'}])
fig.text(0.12, 0.9, subsubtitle_text, fontweight="regular", fontsize=16, color='w')
    
# Add direction of play arrow
ax = fig.add_axes([0.042, 0.028, 0.18, 0.005])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.02, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add footer text
fig.text(0.72, 0.022, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add competition logo
ax = fig.add_axes([0.02, 0.89, 0.08, 0.08])
ax.axis("off")
ax.imshow(comp_logo)

# Add twitter logo
ax = fig.add_axes([0.92, 0.005, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

fig.savefig(f"team_threat_creation/delta-{league}-{year}-team-threat-creation", dpi=300)


    