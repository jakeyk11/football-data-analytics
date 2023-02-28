# %% Create visualisation of team threat creation zones
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Date of run
#           Selection of whether to include percentages on visual
#           Selection of whether to brighten logo

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageEnhance
import matplotlib.patheffects as path_effects
import os
import sys
import bz2
import pickle
import numpy as np

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

# Input run-date
run_date = '28/02/2023'

# Select whether to label %
label_pct = False

# Logo brighten
logo_brighten = True

# %% Get competition logo

comp_logo = lab.get_competition_logo(league, year, logo_brighten=True)

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

# %% Get cumulative minutes info

events_df = wde.cumulative_match_mins(events_df)
events_df = wde.add_team_name(events_df, players_df)

# %% Get free-kicks and corners

all_fks_and_corners = events_df[events_df['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 6 in x or 5 in x) else False)]

fks_and_corners = all_fks_and_corners[(all_fks_and_corners['eventType']=='Pass') |
                                      (all_fks_and_corners['eventType']=='SavedShot') |
                                      ((all_fks_and_corners['eventType']=='MissedShots') & (all_fks_and_corners['blockedX']=='blockedX'))]

# %% Calculate set piece outcome

# Add new column to categorise cross
fks_and_corners['set_piece_outcome'] = np.nan

for idx, set_piece in fks_and_corners.iterrows():
    next_evts = events_df[(events_df['match_id'] == set_piece['match_id']) & (events_df['period'] == set_piece['period']) & (events_df['eventId'] != set_piece['eventId']) & (events_df['cumulative_mins'] >= set_piece['cumulative_mins']) & (events_df['cumulative_mins'] <= set_piece['cumulative_mins']+(5/60))]
    team_next_evts = next_evts[next_evts['teamId'] == set_piece['teamId']]
    opp_next_evts = next_evts[next_evts['teamId'] != set_piece['teamId']]
    if (True in team_next_evts['isGoal'].tolist()) or (True in opp_next_evts['isOwnGoal'].tolist()):
        fks_and_corners.loc[idx, 'set_piece_outcome'] = 'Goal'
    elif (True in team_next_evts['isShot'].tolist()) or ('ChanceMissed' in team_next_evts['eventType'].tolist()) or ('Foul' in opp_next_evts['isOwnGoal'].tolist()):
        fks_and_corners.loc[idx, 'set_piece_outcome'] = 'Chance'
    elif set_piece['isShot']==True:
        fks_and_corners.loc[idx, 'set_piece_outcome'] = 'Direct Shot Only'

# %% Get teams and order on set piece shots conceded

# Sort alphabetically initially
teams = sorted(set(players_df['team']))

# Set up dictionary to cross count per team
team_sp_concede_df = pd.DataFrame(columns = ['team','matches_played','sp_concede', 'sp_chance_concede', 'sp_goal_concede'])

for idx, team in enumerate(teams):
    
    # Get team events
    team_sp_concede = fks_and_corners[fks_and_corners['opp_team_name']==team]
    team_sp_chance_concede = team_sp_concede[team_sp_concede['set_piece_outcome'].isin(['Goal', 'Chance'])]                           
    team_sp_goal_concede = team_sp_concede[team_sp_concede['set_piece_outcome'].isin(['Goal', 'Direct Goal'])]                           
    
    # Add to df
    team_sp_concede_df.loc[idx, 'team'] = team
    team_sp_concede_df.loc[idx, 'matches_played'] = len(set(events_df[events_df['team_name']==team]['match_id']))
    team_sp_concede_df.loc[idx, 'sp_concede'] = len(team_sp_concede)
    team_sp_concede_df.loc[idx, 'sp_chance_concede'] = len(team_sp_chance_concede)
    team_sp_concede_df.loc[idx, 'sp_goal_concede'] = len(team_sp_goal_concede)

# %% Calculations per match and pct

team_sp_concede_df['sp_chance_concede_per_match'] = team_sp_concede_df['sp_chance_concede']/team_sp_concede_df['matches_played']
team_sp_concede_df['sp_goal_concede_per_match'] = team_sp_concede_df['sp_goal_concede']/team_sp_concede_df['matches_played']
team_sp_concede_df['sp_chance_concede_pct'] = 100*team_sp_concede_df['sp_chance_concede']/team_sp_concede_df['sp_concede']
team_sp_concede_df['sp_goal_concede_pct'] = 100*team_sp_concede_df['sp_goal_concede']/team_sp_concede_df['sp_concede']

# %% Set-up bar graph

team_sp_concede_df.sort_values('sp_chance_concede_pct', ascending = True, inplace = True)
team_sp_concede_df.reset_index(drop=True, inplace=True)

# Set-up bar plot showing team position vs. total value
fig, ax = plt.subplots(figsize=(8.5, 8.5))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Define and add colour
my_cmap = plt.get_cmap("viridis_r")
my_cmap = my_cmap(np.linspace(0.06,0.8,256))
color_scale = 255*(team_sp_concede_df['sp_chance_concede_pct'] - team_sp_concede_df['sp_chance_concede_pct'].min())/(team_sp_concede_df['sp_chance_concede_pct'].max() - team_sp_concede_df['sp_chance_concede_pct'].min())
color_scale = [int(color) for color in color_scale.values.tolist()]

# Team rank
team_rank = [str(i) + ": " for i in team_sp_concede_df.index.values+1] + team_sp_concede_df["team"]

# Plot data
ax.barh(team_rank, team_sp_concede_df["sp_chance_concede_pct"], color=my_cmap[color_scale])
ax.barh(team_rank, team_sp_concede_df["sp_goal_concede_pct"], hatch = '////', color = 'none', edgecolor='w', alpha = 0.7)

# Create title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup'}

title_text = f"{leagues[league]} {year}/{str(int(year)+1).replace('20','',1)} − Defending \"Indirect\" Set Pieces"
subtitle_text = "% of Set Pieces Against Resulting in Opp. Chance or Goal (within 5s)"
subsubtitle_text = f"Correct as of {run_date}. \"Indirect\" covers corners or FKs where ball remains in-play after initial action."
fig.text(0.135, 0.94, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.135, 0.912, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.135, 0.884, subsubtitle_text, fontweight="regular", fontsize=10, color='w')


# Define axes
ax.set_xlabel("Percentage of Opposition Set-pieces Resulting in Chance", fontweight="bold", fontsize=12, color='w')
ax.set_ylim(-0.5, len(team_sp_concede_df)-0.5)
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_color('w')
plt.gca().invert_yaxis()

# Add axes labels
path_eff = [path_effects.Stroke(linewidth=3, foreground='#313332'), path_effects.Normal()]

for idx, plot_pos in enumerate(np.arange(0.2, len(team_sp_concede_df))):
    goal_text = ' goal' if team_sp_concede_df.loc[idx,"sp_goal_concede"] == 1 else ' goals'
    chance_text = ' chance' if team_sp_concede_df.loc[idx,"sp_chance_concede"] == 1 else ' chances'
    ax.text(team_sp_concede_df.loc[idx,"sp_goal_concede_pct"], plot_pos, " " + str(team_sp_concede_df.loc[idx,"sp_goal_concede"])+ goal_text, fontsize = 8, path_effects = path_eff)
    ax.text(team_sp_concede_df.loc[idx,"sp_chance_concede_pct"], plot_pos, " " + str(team_sp_concede_df.loc[idx,"sp_chance_concede"])+ chance_text, fontsize = 8, path_effects = path_eff)
    
# Add Championship Logo
ax2 = fig.add_axes([0.035, 0.87, 0.1, 0.1])
ax2.axis("off")
ax2.imshow(comp_logo)

# Create footer
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.93, 0.003, 0.05, 0.05])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

fig.tight_layout(rect=[0.03, 0.06, 0.95, 0.86])

fig.savefig(f"team_setpiece_shot_concession/{league}-{year}-team_setpiece_chance_concession_pct", dpi=300)

# %% Set-up bar graph

team_sp_concede_df.sort_values('sp_chance_concede_per_match', ascending = True, inplace = True)
team_sp_concede_df.reset_index(drop=True, inplace=True)

# Set-up bar plot showing team position vs. total value
fig, ax = plt.subplots(figsize=(8.5, 8.5))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Define and add colour
my_cmap = plt.get_cmap("viridis_r")
my_cmap = my_cmap(np.linspace(0.06,0.8,256))
color_scale = 255*(team_sp_concede_df['sp_chance_concede_per_match'] - team_sp_concede_df['sp_chance_concede_per_match'].min())/(team_sp_concede_df['sp_chance_concede_per_match'].max() - team_sp_concede_df['sp_chance_concede_per_match'].min())
color_scale = [int(color) for color in color_scale.values.tolist()]

# Team rank
team_rank = [str(i) + ": " for i in team_sp_concede_df.index.values+1] + team_sp_concede_df["team"]

# Plot data
ax.barh(team_rank, team_sp_concede_df["sp_chance_concede_per_match"], color=my_cmap[color_scale])
ax.barh(team_rank, team_sp_concede_df["sp_goal_concede_per_match"], hatch = '////', color = 'none', edgecolor='w', alpha = 0.7)

# Create title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup'}

title_text = f"{leagues[league]} {year}/{str(int(year)+1).replace('20','',1)} − Defending \"Indirect\" Set Pieces"
subtitle_text = "Set Pieces Against Resulting in Opp. Chance or Goal (within 5s) per match"
subsubtitle_text = f"Correct as of {run_date}. \"Indirect\" covers corners or FKs where ball remains in-play after initial action."
fig.text(0.135, 0.94, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.135, 0.912, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.135, 0.884, subsubtitle_text, fontweight="regular", fontsize=10, color='w')


# Define axes
ax.set_xlabel("Number of Opposition Set-pieces Resulting in Chance per Match", fontweight="bold", fontsize=12, color='w')
ax.set_ylim(-0.5, len(team_sp_concede_df)-0.5)
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_color('w')
plt.gca().invert_yaxis()

# Add axes labels
path_eff = [path_effects.Stroke(linewidth=3, foreground='#313332'), path_effects.Normal()]

for idx, plot_pos in enumerate(np.arange(0.2, len(team_sp_concede_df))):
    goal_text = ' goal' if team_sp_concede_df.loc[idx,"sp_goal_concede"] == 1 else ' goals'
    chance_text = ' chance' if team_sp_concede_df.loc[idx,"sp_chance_concede"] == 1 else ' chances'
    ax.text(team_sp_concede_df.loc[idx,"sp_goal_concede_per_match"], plot_pos, " " + str(team_sp_concede_df.loc[idx,"sp_goal_concede"])+ goal_text, fontsize = 8, path_effects = path_eff)
    ax.text(team_sp_concede_df.loc[idx,"sp_chance_concede_per_match"], plot_pos, " " + str(team_sp_concede_df.loc[idx,"sp_chance_concede"])+ chance_text, fontsize = 8, path_effects = path_eff)
    
# Add Championship Logo
ax2 = fig.add_axes([0.035, 0.87, 0.1, 0.1])
ax2.axis("off")
ax2.imshow(comp_logo)

# Create footer
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.93, 0.003, 0.05, 0.05])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

fig.tight_layout(rect=[0.03, 0.06, 0.95, 0.86])

fig.savefig(f"team_setpiece_shot_concession/{league}-{year}-team_setpiece_chance_concession_per_match", dpi=300)
