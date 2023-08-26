# %% Points Model

# %% Imports

import pandas as pd
import bz2
import os
import sys
import pickle
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
import seaborn as sns
from scipy import stats
from mplsoccer.pitch import Pitch, VerticalPitch

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% User inputs

# Data to use
data_grab = [['EPL', '2022'],
             ['EPL', '2021'],
             ['EPL', '2020'],
             ['EPL', '2019'],
             ['EPL', '2018'],
             ['EPL', '2017'],
             ['EPL', '2016'],
             ['EPL', '2015'],
             ['EPL', '2014'],
             ['EPL', '2013'],
             ['EPL', '2012'],
             ['EPL', '2011']]

# League name
league_name = 'Premier League'
comp_logo = lab.get_competition_logo(league_name, logo_brighten=True)

# Logo

# Pitch dimensions in yards
PITCH_LENGTH_X = 110
PITCH_WIDTH_Y = 70

# %% Import data

# Initialise storage dataframes
events_df = pd.DataFrame()
players_df = pd.DataFrame()
leaguetable_df = pd.DataFrame()
match_dict = dict.fromkeys([f"{data[0]} {data[1]}" for data in data_grab])

for data in data_grab:
    league = data[0]
    year = data[1]
    league_events = pd.DataFrame()
    league_players = pd.DataFrame()
        
    file_path_evts = f"../../data_directory/whoscored_data/{data[1]}_{str(int(data[1].replace('20','', 1)) + 1)}/{data[0]}"
    files = os.listdir(file_path_evts)
    idx = 1
    
    # Load event data match by match
    for file in files:
        if file == 'event-types.pbz2':
            event_types = bz2.BZ2File(f"{file_path_evts}/{file}", 'rb')
            event_types = pickle.load(event_types)
        elif '-eventdata-' in file:
            match_events = bz2.BZ2File(f"{file_path_evts}/{file}", 'rb')
            match_events = pickle.load(match_events)
            if idx == 1:
                match_shot_events = match_events
            else:
                match_shot_events = match_events[match_events['eventType'].isin(['Goal', 'MissedShots', 'SavedShot', 'ShotOnPost'])]
            league_events = pd.concat([league_events, match_shot_events])
            print(f"event file {idx}/{int((len(files))/2-1)} loaded")
            idx += 1
        elif '-playerdata-' in file:
            match_players = bz2.BZ2File(f"{file_path_evts}/{file}", 'rb')
            match_players = pickle.load(match_players)
            league_players = pd.concat([league_players, match_players])
        else:
            pass
        
    # Add match ids to match dictionary
    match_dict[f"{data[0]} {data[1]}"] = set(league_events['match_id'].tolist())
    
    # Append league data to combined dataset
    events_df = pd.concat([events_df, league_events])
    players_df = pd.concat([players_df, league_players])
    
    print(f"{league}, {year} data import complete")

events_df = wde.add_team_name(events_df, players_df)

# %% Isolate all shots and add shot characteristics

all_shots = events_df[events_df['eventType'].isin(['Goal', 'MissedShots', 'SavedShot', 'ShotOnPost'])]
all_shots['x_distance'] = PITCH_LENGTH_X * (100 - all_shots['x'])/100
all_shots['y_distance'] = PITCH_WIDTH_Y * (50 - all_shots['y'])/100             # -ve is to the left of the goal, +ve is to the right of the goal
all_shots['distance'] = np.sqrt(all_shots['x_distance'] **2 + all_shots['y_distance'] ** 2)
all_shots['angle'] = np.arctan2(all_shots['y_distance'],all_shots['x_distance']) * 180 / np.pi

# %% Get ground inplay shots and headed shots

all_ip_shots = all_shots[~all_shots['satisfiedEventsTypes'].apply(lambda x: 5 in x or 6 in x)]
all_ip_ground_shots = all_ip_shots[~all_ip_shots['satisfiedEventsTypes'].apply(lambda x: 14 in x)]

# %% Create shot characteristics dataframe and populate

shot_characteristics_df = pd.DataFrame.from_dict(data_grab)
shot_characteristics_df.columns = ['league','year']
shot_characteristics_df['year'] = shot_characteristics_df['year'].astype(int)

# Iterate through each season
for idx, league_entry in shot_characteristics_df.iterrows():
    
    # Get matches within the season and isolate teams and all shots
    match_ids = match_dict[f"{league_entry['league']} {league_entry['year']}"]
    season_shots = all_ip_shots[all_ip_shots['match_id'].isin(match_ids)]
    shooting_teams = list(set(season_shots['team_name']))
                                
    # Split shot dataframe to isolate headers, left foot shots and right foot shots
    season_headers = season_shots[season_shots['satisfiedEventsTypes'].apply(lambda x: 14 in x)]
    season_foot_shots = season_shots[season_shots['satisfiedEventsTypes'].apply(lambda x: 12 in x or 13 in x)]        
    season_rfoot_shots = season_foot_shots[season_foot_shots['satisfiedEventsTypes'].apply(lambda x: 12 in x)]        
    season_lfoot_shots = season_foot_shots[season_foot_shots['satisfiedEventsTypes'].apply(lambda x: 13 in x)]        
    season_out_box_shots = season_foot_shots[season_foot_shots[['x', 'y']].apply(lambda x: x.x < 83 or x.y < 21.1 or x.y > 78.9, axis=1)]
    
    # Average shot and goal count per match
    shot_characteristics_df.loc[idx, 'total_ip_shots_match'] = len(season_shots)/len(match_ids)
    shot_characteristics_df.loc[idx, 'total_ip_goals_match'] = len(season_shots[season_shots['eventType']=='Goal'])/len(match_ids)
    
    # Average shot distance and angle
    shot_characteristics_df.loc[idx, 'mean_ip_foot_shot_dist'] = season_foot_shots['distance'].mean()
    shot_characteristics_df.loc[idx, 'mean_ip_foot_shot_angle'] = season_foot_shots['angle'].mean()

    # Proportion of shots by shot type
    shot_characteristics_df.loc[idx, 'proportion_ip_oob_shots'] = 100*len(season_out_box_shots)/len(season_foot_shots)
    shot_characteristics_df.loc[idx, 'proportion_ip_headers'] = 100*len(season_headers)/len(season_shots)
    shot_characteristics_df.loc[idx, 'proportion_ip_foot_shots_left'] = 100*len(season_lfoot_shots)/len(season_foot_shots)

    # Goal rates
    shot_characteristics_df.loc[idx, 'ip_foot_shot_goal_conv'] = 100*len(season_foot_shots[season_foot_shots['eventType']=='Goal']) / len(season_foot_shots) 
    shot_characteristics_df.loc[idx, 'ip_shot_goal_conv'] = 100*len(season_shots[season_shots['eventType']=='Goal'])/ len(season_shots)
        
    # Iterate over teams and get team stats
    for team in shooting_teams:
        team_shots = season_shots[season_shots['team_name']==team]
        team_foot_shots = season_foot_shots[season_foot_shots['team_name']==team]
        team_rfoot_shots = season_rfoot_shots[season_rfoot_shots['team_name']==team]
        team_lfoot_shots = season_lfoot_shots[season_lfoot_shots['team_name']==team]
        
        # Average shot distance
        shot_characteristics_df.loc[idx, f'{team}_team_gcr'] = 100*len(team_foot_shots[team_foot_shots['eventType']=='Goal'])/ len(team_foot_shots)
        shot_characteristics_df.loc[idx, f'{team}_team_dist'] = team_foot_shots['distance'].mean()
        shot_characteristics_df.loc[idx, f'{team}_team_angle'] = team_foot_shots['angle'].mean()
        shot_characteristics_df.loc[idx, f'{team}_team_lf_shot'] = 100*len(team_lfoot_shots)/len(team_foot_shots)

# Remove columns that have more than 8 nulls
for column in shot_characteristics_df.columns.values:
    if shot_characteristics_df[column].count() < 7:
        shot_characteristics_df.drop(column, axis=1, inplace=True)
        
# Order by year
shot_characteristics_df.sort_values('year', inplace=True)       

# %% FIGURE 0 - Shot distance trend plot

# Define custom colourmap
CustomCmap = mpl.colors.LinearSegmentedColormap.from_list("", ["#313332","#47516B", "#848178", "#B2A66F", "#FDE636"])

# Set-up pitch subplots
pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, half=True, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=4, grid_height=0.79, title_height = 0.15, endnote_height = 0.04, space=0.1, axis=False)
fig.set_size_inches(10, 7)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)
idx = 0

# Iterate through top players
for _, league_entry in shot_characteristics_df.head(12).iterrows():    
    
    # Get shots
    match_ids = match_dict[f"{league_entry['league']} {league_entry['year']}"]
    season_shots = all_ip_shots[all_ip_shots['match_id'].isin(match_ids)]
    
    # Title
    year = league_entry['year']
    ax['pitch'][idx].set_title(f"{year}/{str(year+1).replace('20','',1)}", loc = "center", color='w', fontsize = 10, pad=-2)

    
    # Plot density of start positions of box entries
    kde_plot = pitch.kdeplot(season_shots['x'], season_shots['y'], ax=ax['pitch'][idx],
                              fill=True, levels=10, shade_lowest=False,
                              cut=4, cmap=CustomCmap, zorder=0)
        
    # Add text 
    ax['pitch'][idx].text(96, 57.5, "Mean Dist:", fontsize=8, fontweight='regular', color='w', zorder=3)
    ax['pitch'][idx].text(96, 53, f"{round(league_entry['mean_ip_foot_shot_dist'],1)} yds", fontsize=8, fontweight='bold', color='w', zorder=3)
                
    idx += 1

# Titles
title_text = f"{league_name}: Shot Characteristics by Season"
subtitle_text = "Where are In-Play Ground Shots taken from?" 
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.9, subtitle_text, fontweight="regular", fontsize=13, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)
    
# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.94, 0.007, 0.03, 0.03])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

fig.savefig(f"shot_characteristics_trending/{league_name}-shot-position", dpi=300)

# %% FIGURE 1 - Shot distance trend

mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
mpl.rcParams['text.color'] = 'w'
fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (8,8), facecolor = '#313332')
ax.patch.set_alpha(0)
twin_ax = plt.twinx()

# Add line
sns.lineplot(shot_characteristics_df, x = 'year', y = 'mean_ip_foot_shot_dist', color = 'coral', ax=ax)
sns.regplot(shot_characteristics_df, x = 'year', y = 'mean_ip_foot_shot_dist', scatter = True, line_kws={"color": "mistyrose", "lw":1, "ls" :'--'}, scatter_kws={"color": "coral", "s":50}, ax=ax)
sns.lineplot(shot_characteristics_df, x = 'year', y = 'ip_foot_shot_goal_conv', color = 'turquoise', ax=twin_ax)
sns.regplot(shot_characteristics_df, x = 'year', y = 'ip_foot_shot_goal_conv', scatter = True, line_kws={"color": "lightblue", "lw":1, "ls" :'--'}, scatter_kws={"color": "turquoise", "s":50}, ax=twin_ax)

# Format
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_color('w')
ax.tick_params(axis='y', colors='mistyrose')
twin_ax.tick_params(axis='y', colors='lightblue')
twin_ax.spines['left'].set_visible(False) 
twin_ax.spines['bottom'].set_visible(False) 
twin_ax.spines['top'].set_visible(False) 
twin_ax.spines['right'].set_color('w') 
ax.grid(lw = 0.5, color= 'grey', ls = ':')

# Labels and ticks
twin_ax.set_yticks(np.linspace(twin_ax.get_yticks()[0], twin_ax.get_yticks()[-1], len(ax.get_yticks())))
ax.set_yticks(np.linspace(ax.get_yticks()[0], ax.get_yticks()[-1], len(twin_ax.get_yticks())))
ax.xaxis.set_ticks([year for year in shot_characteristics_df['year']])
ax.set_xticklabels([f"{str(year).replace('20','',1)}/{str(year+1).replace('20','',1)}" for year in shot_characteristics_df['year']], rotation=270)
ax.set_xlabel("Season", fontsize=12, fontweight = "bold", labelpad = 10)
ax.set_ylabel("Mean Shot Distance (yards)", fontsize=12, color = "coral", fontweight = "bold", labelpad = 10)
twin_ax.set_ylabel("Ground Shot Conversion Rate (%)", fontsize=12, color = "turquoise", fontweight = "bold", labelpad = 20, rotation=270)

# Titles
title_text = f"{league_name}: Shot Characteristics by Season"
subtitle_text = "Mean Distance of In-Play Ground Shots from Goal" 
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.9, subtitle_text, fontweight="regular", fontsize=13, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

fig.tight_layout(rect=[0.03, 0.04, 0.97, 0.86])

fig.savefig(f"shot_characteristics_trending/{league_name}-shot-distance", dpi=300)

# %% FIGURE 2 - Shots and goals per game

fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (8,8), facecolor = '#313332')
ax.patch.set_alpha(0)
twin_ax = plt.twinx()

# Add line
sns.lineplot(shot_characteristics_df, x = 'year', y = 'total_ip_shots_match', color = 'coral', ax=ax)
sns.regplot(shot_characteristics_df, x = 'year', y = 'total_ip_shots_match', scatter = True, line_kws={"color": "mistyrose", "lw":1, "ls" :'--'}, scatter_kws={"color": "coral", "s":50}, ax=ax)
sns.lineplot(shot_characteristics_df, x = 'year', y = 'total_ip_goals_match', color = 'mediumaquamarine', ax=twin_ax)
sns.regplot(shot_characteristics_df, x = 'year', y = 'total_ip_goals_match', scatter = True, line_kws={"color": "paleturquoise", "lw":1, "ls" :'--'}, scatter_kws={"color": "mediumaquamarine", "s":50}, ax=twin_ax)

# Format
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_color('w')
ax.tick_params(axis='y', colors='mistyrose')
twin_ax.tick_params(axis='y', colors='paleturquoise')
twin_ax.spines['left'].set_visible(False) 
twin_ax.spines['bottom'].set_visible(False) 
twin_ax.spines['top'].set_visible(False) 
twin_ax.spines['right'].set_color('w') 
ax.grid(lw = 0.5, color= 'grey', ls = ':')

# Labels and ticks
twin_ax.set_ylim([1.95,2.25])
twin_ax.set_yticks(np.linspace(twin_ax.get_yticks()[0], twin_ax.get_yticks()[-1], len(ax.get_yticks())))
ax.set_yticks(np.linspace(ax.get_yticks()[0], ax.get_yticks()[-1], len(twin_ax.get_yticks())))
ax.xaxis.set_ticks([year for year in shot_characteristics_df['year']])
ax.set_xticklabels([f"{str(year).replace('20','',1)}/{str(year+1).replace('20','',1)}" for year in shot_characteristics_df['year']], rotation=270)
ax.set_xlabel("Season", fontsize=12, fontweight = "bold", labelpad = 10)
ax.set_ylabel("Mean Shots per Game", fontsize=12, color = "coral", fontweight = "bold", labelpad = 10)
twin_ax.set_ylabel("Mean Goals per Game", fontsize=12, color = "mediumaquamarine", fontweight = "bold", labelpad = 20, rotation=270)

# Titles
title_text = f"{league_name}: Shot Characteristics by Season"
subtitle_text = "Mean Number of Shots and Goals per Game" 
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.9, subtitle_text, fontweight="regular", fontsize=13, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

fig.tight_layout(rect=[0.03, 0.04, 0.97, 0.86])

fig.savefig(f"shot_characteristics_trending/{league_name}-shot-per-game", dpi=300)

# %% FIGURE 3 - Shots type proportion

fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (8,8), facecolor = '#313332')
ax.patch.set_alpha(0)
twin_ax = plt.twinx()

# Add line
sns.lineplot(shot_characteristics_df, x = 'year', y = 'proportion_ip_foot_shots_left', color = 'coral', ax=ax)
sns.regplot(shot_characteristics_df, x = 'year', y = 'proportion_ip_foot_shots_left', scatter = True, line_kws={"color": "mistyrose", "lw":1, "ls" :'--'}, scatter_kws={"color": "coral", "s":50}, ax=ax)
sns.lineplot(shot_characteristics_df, x = 'year', y = 'proportion_ip_headers', color = 'mediumaquamarine', ax=twin_ax)
sns.regplot(shot_characteristics_df, x = 'year', y = 'proportion_ip_headers', scatter = True, line_kws={"color": "paleturquoise", "lw":1, "ls" :'--'}, scatter_kws={"color": "mediumaquamarine", "s":50}, ax=twin_ax)

# Format
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_color('w')
ax.tick_params(axis='y', colors='mistyrose')
twin_ax.tick_params(axis='y', colors='paleturquoise')
twin_ax.spines['left'].set_visible(False) 
twin_ax.spines['bottom'].set_visible(False) 
twin_ax.spines['top'].set_visible(False) 
twin_ax.spines['right'].set_color('w') 
ax.grid(lw = 0.5, color= 'grey', ls = ':')

# Labels and ticks
ax.set_ylim([34,42])
twin_ax.set_ylim([8,12])
twin_ax.set_yticks(np.linspace(twin_ax.get_yticks()[0], twin_ax.get_yticks()[-1], len(ax.get_yticks())))
ax.set_yticks(np.linspace(ax.get_yticks()[0], ax.get_yticks()[-1], len(twin_ax.get_yticks())))
ax.xaxis.set_ticks([year for year in shot_characteristics_df['year']])
ax.set_xticklabels([f"{str(year).replace('20','',1)}/{str(year+1).replace('20','',1)}" for year in shot_characteristics_df['year']], rotation=270)
ax.set_xlabel("Season", fontsize=12, fontweight = "bold", labelpad = 10)
ax.set_ylabel("% of Ground Shots with Left Foot", fontsize=12, color = "coral", fontweight = "bold", labelpad = 10)
twin_ax.set_ylabel("% of All Shots with Head", fontsize=12, color = "mediumaquamarine", fontweight = "bold", labelpad = 20, rotation=270)

# Titles
title_text = f"{league_name}: Shot Characteristics by Season"
subtitle_text = "In-Play Left Footed Shots and Headers" 
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.9, subtitle_text, fontweight="regular", fontsize=13, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

fig.tight_layout(rect=[0.03, 0.04, 0.97, 0.86])

fig.savefig(f"shot_characteristics_trending/{league_name}-shot-types", dpi=300)

# %% FIGURE 4 - Box shots

fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (8,8), facecolor = '#313332')
ax.patch.set_alpha(0)

# Add line
sns.lineplot(shot_characteristics_df, x = 'year', y = 'proportion_ip_oob_shots', color = 'mediumaquamarine', ax=ax)
reg = sns.regplot(shot_characteristics_df, x = 'year', y = 'proportion_ip_oob_shots', scatter = True, line_kws={"color": "paleturquoise", "lw":1, "ls" :'--'}, scatter_kws={"color": "mediumaquamarine", "s":50}, ax=ax)

# Format
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_color('w')
ax.tick_params(axis='y', colors='paleturquoise')
ax.grid(lw = 0.5, color= 'grey', ls = ':')

# Labels and ticks
ax.xaxis.set_ticks([year for year in shot_characteristics_df['year']])
ax.set_xticklabels([f"{str(year).replace('20','',1)}/{str(year+1).replace('20','',1)}" for year in shot_characteristics_df['year']], rotation=270)
ax.set_xlabel("Season", fontsize=12, fontweight = "bold", labelpad = 10)
ax.set_ylabel("Proportion of Shots Outside Box (%)", fontsize=12, color = "mediumaquamarine", fontweight = "bold", labelpad = 10)

# Titles
title_text = f"{league_name}: Shot Characteristics by Season"
subtitle_text = "Proportion of In-Play Ground Shots taken Outside the Box" 
fig.text(0.12, 0.935, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.9, subtitle_text, fontweight="regular", fontsize=13, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.877, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

fig.tight_layout(rect=[0.03, 0.04, 0.97, 0.86])

fig.savefig(f"shot_characteristics_trending/{league_name}-oob-shots", dpi=300)


# %% FIGURE 5 - Shot distance by team

stat_name = 'team_dist'
columns = list(filter(lambda x: x is not None, [col if stat_name in col or 'year' in col else None for col in shot_characteristics_df.columns]))

df_to_plot = shot_characteristics_df.loc[:,columns]

# Iterate over teams, and calculate slope of regression line that models trend
trend_dict = {}
for team_col in df_to_plot.columns[1:]:
    team_data = pd.concat([df_to_plot['year'], df_to_plot[team_col]], axis=1)
    team = team_data.columns[1].replace(f'_{stat_name}','')
    mask = ~np.isnan(team_data['year']) & ~np.isnan(team_data[f'{team}_{stat_name}'])
    slope, intercept, r_value, p_value, std_err = stats.linregress(team_data['year'][mask], team_data[f'{team}_{stat_name}'][mask])
    trend_dict[team] = slope
    
# Calculate min and max mean shot distance
min_sd = int(np.floor(min(df_to_plot.iloc[:,1:].min())))  
max_sd = int(np.ceil(max(df_to_plot.iloc[:,1:].max())))
min_yr = min(df_to_plot.iloc[:,0])
max_yr = max(df_to_plot.iloc[:,0])

# Set-up pitch subplots
n_cols = 4
n_rows = 5
fig, ax = plt.subplots(nrows=n_rows, ncols=n_cols ,figsize = (8,10), facecolor = '#313332')
ax = ax.reshape(-1)
plt.subplots_adjust(left=0.09,
                    bottom=0.06,
                    right=0.94,
                    top=0.86,
                    hspace=0.5,
                    wspace=0.3)

idx = 0
# Iterate through each team, starting with highest slope of trend
for team in pd.DataFrame.from_dict(trend_dict, orient = 'index').sort_values(0).index:
    
    # Get team data. logo and colour
    team_data = pd.concat([df_to_plot['year'], df_to_plot[f'{team}_{stat_name}']], axis=1)
    team_logo, team_cmap = lab.get_team_badge_and_colour(team)
    team_color = team_cmap(120)
    
    # Plot team data
    sns.lineplot(df_to_plot, x = 'year', y = f'{team}_{stat_name}', color = team_color, ax=ax[idx])
    sns.regplot(df_to_plot, x = 'year', y = f'{team}_{stat_name}', scatter = True, line_kws={"color": team_color, "alpha":0.5, "lw":1, "ls" :'--'}, scatter_kws={"color": team_color, "s":25}, ax=ax[idx])
    ax[idx].text(2019, 22.75, f"Mean dist. {'drops' if trend_dict[team] < 0 else 'rises'}\nby {abs(round(trend_dict[team],2))} yds/yr", ha = "center", color = "w", fontsize = 5.5)
   
    # Plot formatting
    ax[idx].patch.set_alpha(0)
    ax[idx].spines['bottom'].set_color('w')
    ax[idx].spines['top'].set_visible(False) 
    ax[idx].spines['right'].set_visible(False) 
    ax[idx].spines['left'].set_color('w')
    ax[idx].set_ylabel("")
    ax[idx].set_xlabel("")
    ax[idx].grid(lw = 0.5, color= 'grey', ls = ':')
    ax[idx].set_ylim([min_sd, max_sd])
    ax[idx].xaxis.set_ticks([year for year in shot_characteristics_df['year'] if year%3==0])
    ax[idx].set_xticklabels([f"{str(year).replace('20','',1)}/{str(year+1).replace('20','',1)}" for year in shot_characteristics_df['year'] if year%3==0])
    ax[idx].tick_params(axis='x', labelsize=6)
    ax[idx].tick_params(axis='y', labelsize=6)
    ax[idx].set_xlim([min_yr-0.5, max_yr+0.5])

    if idx%n_cols == 0:
        ax[idx].set_ylabel("Mean Shot Dist. (yds)", fontsize = 7)
    
    # Plot labeling
    ax[idx].set_title(f"{idx + 1}: {team}", loc = "left", color='w', fontweight = "bold", fontsize = 9)
    ax_pos = ax[idx].get_position()
    logo_ax = fig.add_axes([ax_pos.x1-0.02, ax_pos.y1, 0.025, 0.025])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx+=1
    
# Remove unused subplots
if len(trend_dict) < n_rows*n_cols:
    for i in range(len(trend_dict), n_rows*n_cols):
        fig.delaxes(ax[i])
        
# Titles
title_text = f"{league_name}: Team Shot Characteristics by Season"
subtitle_text = "Mean Distance of In-Play Ground Shots from Goal" 
subsubtitle_text = "Teams ranked by mean reduction in shot distance per season (teams in league for > 6/12 seasons included)"
fig.text(0.11, 0.955, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.11, 0.93, subtitle_text, fontweight="regular", fontsize=13, color='w')
fig.text(0.11, 0.91, subsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.89, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

fig.savefig(f"shot_characteristics_trending/{league_name}-team-shot-distance", dpi=300)

# %% FIGURE 6 - Shot conversion rate by team

stat_name = 'team_gcr'
columns = list(filter(lambda x: x is not None, [col if stat_name in col or 'year' in col else None for col in shot_characteristics_df.columns]))

df_to_plot = shot_characteristics_df.loc[:,columns]

# Iterate over teams, and calculate slope of regression line that models trend
trend_dict = {}
for team_col in df_to_plot.columns[1:]:
    team_data = pd.concat([df_to_plot['year'], df_to_plot[team_col]], axis=1)
    team = team_data.columns[1].replace(f'_{stat_name}','')
    mask = ~np.isnan(team_data['year']) & ~np.isnan(team_data[f'{team}_{stat_name}'])
    slope, intercept, r_value, p_value, std_err = stats.linregress(team_data['year'][mask], team_data[f'{team}_{stat_name}'][mask])
    trend_dict[team] = slope
    
# Calculate min and max mean shot distance
min_rate = np.floor(min(0.2*df_to_plot.iloc[:,1:].min()))*5
max_rate = np.ceil(max(0.2*df_to_plot.iloc[:,1:].max()))*5
min_yr = min(df_to_plot.iloc[:,0])
max_yr = max(df_to_plot.iloc[:,0])

# Set-up pitch subplots
n_cols = 4
n_rows = 5
fig, ax = plt.subplots(nrows=n_rows, ncols=n_cols ,figsize = (8,10), facecolor = '#313332')
ax = ax.reshape(-1)
plt.subplots_adjust(left=0.09,
                    bottom=0.06,
                    right=0.94,
                    top=0.86,
                    hspace=0.5,
                    wspace=0.3)

idx = 0
# Iterate through each team, starting with highest slope of trend
for team in pd.DataFrame.from_dict(trend_dict, orient = 'index').sort_values(0, ascending = False).index:
    
    # Get team data. logo and colour
    team_data = pd.concat([df_to_plot['year'], df_to_plot[f'{team}_{stat_name}']], axis=1)
    team_logo, team_cmap = lab.get_team_badge_and_colour(team)
    team_color = team_cmap(120)
    
    # Plot team data
    sns.lineplot(df_to_plot, x = 'year', y = f'{team}_{stat_name}', color = team_color, ax=ax[idx])
    sns.regplot(df_to_plot, x = 'year', y = f'{team}_{stat_name}', scatter = True, line_kws={"color": team_color, "alpha":0.5, "lw":1, "ls" :'--'}, scatter_kws={"color": team_color, "s":25}, ax=ax[idx])
    
    ax[idx].text(2015, 17.3, f"Shot conversion rate\n{'drops' if trend_dict[team] < 0 else 'rises'} by mean {abs(round(trend_dict[team],1))} %/yr", ha = "center", color = "w", fontsize = 5.5)
    
    # Plot formatting
    ax[idx].patch.set_alpha(0)
    ax[idx].spines['bottom'].set_color('w')
    ax[idx].spines['top'].set_visible(False) 
    ax[idx].spines['right'].set_visible(False) 
    ax[idx].spines['left'].set_color('w')
    ax[idx].set_ylabel("")
    ax[idx].set_xlabel("")
    ax[idx].grid(lw = 0.5, color= 'grey', ls = ':')
    ax[idx].set_ylim([min_rate, max_rate])
    ax[idx].xaxis.set_ticks([year for year in shot_characteristics_df['year'] if year%3==0])
    ax[idx].set_xticklabels([f"{str(year).replace('20','',1)}/{str(year+1).replace('20','',1)}" for year in shot_characteristics_df['year'] if year%3==0])
    ax[idx].tick_params(axis='x', labelsize=6)
    ax[idx].tick_params(axis='y', labelsize=6)
    ax[idx].set_xlim([min_yr-0.5, max_yr+0.5])

    if idx%n_cols == 0:
        ax[idx].set_ylabel("Shot conversion (%)", fontsize = 7)
    
    # Plot labeling
    ax[idx].set_title(f"{idx + 1}: {team}", loc = "left", color='w', fontweight = "bold", fontsize = 9)
    ax_pos = ax[idx].get_position()
    logo_ax = fig.add_axes([ax_pos.x1-0.02, ax_pos.y1, 0.025, 0.025])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx+=1
    
# Remove unused subplots
if len(trend_dict) < n_rows*n_cols:
    for i in range(len(trend_dict), n_rows*n_cols):
        fig.delaxes(ax[i])
        
# Titles
title_text = f"{league_name}: Team Shot Characteristics by Season"
subtitle_text = "In-Play Ground Shot Conversion Rate" 
subsubtitle_text = "Teams ranked by mean increase in conversion rate per season (teams in league for > 6/12 seasons included)"
fig.text(0.11, 0.955, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.11, 0.93, subtitle_text, fontweight="regular", fontsize=13, color='w')
fig.text(0.11, 0.91, subsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.89, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

fig.savefig(f"shot_characteristics_trending/{league_name}-team-goal-per-shot", dpi=300)

# %% FIGURE 7 - Left Footed Shots by Team

stat_name = 'team_lf_shot'
columns = list(filter(lambda x: x is not None, [col if stat_name in col or 'year' in col else None for col in shot_characteristics_df.columns]))

df_to_plot = shot_characteristics_df.loc[:,columns]

# Iterate over teams, and calculate slope of regression line that models trend
trend_dict = {}
for team_col in df_to_plot.columns[1:]:
    team_data = pd.concat([df_to_plot['year'], df_to_plot[team_col]], axis=1)
    team = team_data.columns[1].replace(f'_{stat_name}','')
    mask = ~np.isnan(team_data['year']) & ~np.isnan(team_data[f'{team}_{stat_name}'])
    slope, intercept, r_value, p_value, std_err = stats.linregress(team_data['year'][mask], team_data[f'{team}_{stat_name}'][mask])
    trend_dict[team] = slope
    
# Calculate min and max mean shot distance
min_lfoot = np.floor(min(0.2*df_to_plot.iloc[:,1:].min()))*5
max_lfoot = np.ceil(max(0.2*df_to_plot.iloc[:,1:].max()))*5
min_yr = min(df_to_plot.iloc[:,0])
max_yr = max(df_to_plot.iloc[:,0])

# Set-up pitch subplots
n_cols = 4
n_rows = 5
fig, ax = plt.subplots(nrows=n_rows, ncols=n_cols ,figsize = (8,10), facecolor = '#313332')
ax = ax.reshape(-1)
plt.subplots_adjust(left=0.09,
                    bottom=0.06,
                    right=0.94,
                    top=0.86,
                    hspace=0.5,
                    wspace=0.3)

idx = 0
# Iterate through each team, starting with highest slope of trend
for team in pd.DataFrame.from_dict(trend_dict, orient = 'index').sort_values(0, ascending = False).index:
    
    # Get team data. logo and colour
    team_data = pd.concat([df_to_plot['year'], df_to_plot[f'{team}_{stat_name}']], axis=1)
    team_logo, team_cmap = lab.get_team_badge_and_colour(team)
    team_color = team_cmap(120)
    
    # Plot team data
    sns.lineplot(df_to_plot, x = 'year', y = f'{team}_{stat_name}', color = team_color, ax=ax[idx])
    sns.regplot(df_to_plot, x = 'year', y = f'{team}_{stat_name}', scatter = True, line_kws={"color": team_color, "alpha":0.5, "lw":1, "ls" :'--'}, scatter_kws={"color": team_color, "s":25}, ax=ax[idx])
    
    ax[idx].text(2018.5, 22, f"Pct. left foot {'drops' if trend_dict[team] < 0 else 'rises'}\nby mean {abs(round(trend_dict[team],1))} %/yr", ha = "center", color = "w", fontsize = 5.5)
    
    # Plot formatting
    ax[idx].patch.set_alpha(0)
    ax[idx].spines['bottom'].set_color('w')
    ax[idx].spines['top'].set_visible(False) 
    ax[idx].spines['right'].set_visible(False) 
    ax[idx].spines['left'].set_color('w')
    ax[idx].set_ylabel("")
    ax[idx].set_xlabel("")
    ax[idx].grid(lw = 0.5, color= 'grey', ls = ':')
    ax[idx].set_ylim([min_lfoot, max_lfoot])
    ax[idx].xaxis.set_ticks([year for year in shot_characteristics_df['year'] if year%3==0])
    ax[idx].set_xticklabels([f"{str(year).replace('20','',1)}/{str(year+1).replace('20','',1)}" for year in shot_characteristics_df['year'] if year%3==0])
    ax[idx].tick_params(axis='x', labelsize=6)
    ax[idx].tick_params(axis='y', labelsize=6)
    ax[idx].set_xlim([min_yr-0.5, max_yr+0.5])

    if idx%n_cols == 0:
        ax[idx].set_ylabel("Proportion Left", fontsize = 7)
    
    # Plot labeling
    ax[idx].set_title(f"{idx + 1}: {team}", loc = "left", color='w', fontweight = "bold", fontsize = 9)
    ax_pos = ax[idx].get_position()
    logo_ax = fig.add_axes([ax_pos.x1-0.02, ax_pos.y1, 0.025, 0.025])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    idx+=1
    
# Remove unused subplots
if len(trend_dict) < n_rows*n_cols:
    for i in range(len(trend_dict), n_rows*n_cols):
        fig.delaxes(ax[i])
        
# Titles
title_text = f"{league_name}: Team Shot Characteristics by Season"
subtitle_text = "Proportion of In-Play Ground Shots taken with Left Foot" 
subsubtitle_text = "Teams ranked by mean increase in left foot shots per season (teams in league for > 6/12 seasons included)"
fig.text(0.11, 0.955, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.11, 0.93, subtitle_text, fontweight="regular", fontsize=13, color='w')
fig.text(0.11, 0.91, subsubtitle_text, fontweight="regular", fontsize=9, color='w')

# Add competition logo
comp_ax = fig.add_axes([0.015, 0.89, 0.1, 0.1])
comp_ax.axis("off")
comp_ax.imshow(comp_logo)

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

fig.savefig(f"shot_characteristics_trending/{league_name}-team-left-foot-shots", dpi=300)

