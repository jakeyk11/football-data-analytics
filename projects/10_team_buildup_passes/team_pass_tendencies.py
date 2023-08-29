# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image, ImageEnhance
from mplsoccer.pitch import VerticalPitch, Pitch
import matplotlib.patheffects as path_effects
import os
import sys
import bz2
import pickle
import numpy as np
from collections import Counter
import highlight_text as htext
import glob
import joblib
from scipy.spatial import Delaunay
from sklearn.base import BaseEstimator, TransformerMixin
from time import time

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.get_football_data as gfd
import analysis_tools.whoscored_custom_events as wce
import analysis_tools.models as models
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% User Inputs

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Select team
team = 'Brighton'

# %% Get whoscored data and get statsbomb data

file_path = f"../../data_directory/whoscored_data/{year}_{str(int(year.replace('20','')) + 1)}/{league}"
files = os.listdir(file_path)

# Initialise storage dataframes
events_df = pd.DataFrame()
players_df = pd.DataFrame()

# Load whoscored data
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

# %% Isolate matches that team feature in

# Get match ids and team id
team_match_ids = players_df[players_df['team'] == team]['match_id'].unique()
team_id = players_df[players_df['team'] == team]['teamId'].unique()[0]

# Filter events
team_events_df = events_df[events_df['match_id'].isin(team_match_ids)]

# %% Group possessions and count passes in each possession

team_events_df = wce.get_possession_chains(team_events_df)
team_events_df = team_events_df[team_events_df['teamId']==team_id]

# Initialise possession chain dataframe
pos_chain_df = pd.DataFrame()

# Iterate over match
for match_id in team_match_ids:
    
    # Iterate over possessions
    for pos_id in team_events_df[(team_events_df['match_id']==match_id) & (team_events_df['possession_team']==team_id)]['possession_id'].unique():
        
        # Get possession chain and count up passes
        possession_chain = team_events_df[(team_events_df['match_id']==match_id) & (team_events_df['possession_id']==pos_id)].copy()
        possession_chain['evt_number'] = np.arange(1,len(possession_chain)+1)
        possession_chain['pass_number'] = np.nan
        
        # First pass can be a corner, others can't
        first_pass =  possession_chain[(possession_chain['eventType']=='Pass')].head(1)
        if len(first_pass) == 1:
            possession_chain_passes = possession_chain[(possession_chain['eventId']!=first_pass['eventId'].values[0]) & (possession_chain['eventType']=='Pass') & (~possession_chain['satisfiedEventsTypes'].apply(lambda x: 31 in x))]
            possession_chain_passes = pd.concat([first_pass, possession_chain_passes])
        else:
            possession_chain_passes = pd.DataFrame()
        if len(possession_chain_passes) > 0:
            possession_chain.loc[possession_chain_passes.index.values, 'pass_number'] = np.arange(1,len(possession_chain_passes)+1)

        pos_chain_df = pd.concat([pos_chain_df, possession_chain])

# %% Identify possession chains starting in each third

pos_chain_df.loc[(pos_chain_df['evt_number']==1) & (pos_chain_df['x']<100/3), 'pos_start'] = 'Own 3' 
pos_chain_df.loc[(pos_chain_df['evt_number']==1) & (pos_chain_df['x']>=100/3) & (pos_chain_df['x']<200/3), 'pos_start'] = 'Mid 3' 
pos_chain_df.loc[(pos_chain_df['evt_number']==1) & (pos_chain_df['x']>=200/3), 'pos_start'] = 'Opp 3' 
pos_chain_df['pos_start'] = pos_chain_df['pos_start'].fillna(method='ffill')

# %% Cluster passes in each possession zone

convertYards = models.convertYards
customScaler = models.customScaler
pos_chain_df = models.get_pass_clusters(pos_chain_df)

# %% Plot first 6 passes in each possession type

# Choose number of passes to plot
first_n_passes = 6
clusters_shown = 5
cluster_colours = ['orchid','cornflowerblue', 'mediumseagreen', 'khaki', 'lightcoral', 'lightgrey']

# Set up pitch and figure
pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=3, ncols=first_n_passes, title_height=0.155, grid_height=0.785, endnote_height=0.03, space=0.07, axis=False)
fig.set_size_inches(10, 10)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)

# Iterate through each pitch
for idx in np.arange(3*first_n_passes):
    
    # Set up pass plot indexing
    if idx <= first_n_passes-1:
        pitch.lines(100, 101.5, 100, -1.5, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(100, 0, 200/3, 0, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(100, 100, 200/3, 100, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(200/3, -1.5, 200/3, 101.5, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pass_num = idx+1
        possession_plot = pos_chain_df[pos_chain_df['pos_start'] == 'Opp 3']
    elif idx <= 2*first_n_passes-1:
        pitch.lines(200/3, 101.5, 200/3, -1.5, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(100/3, 0, 200/3, 0, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(100/3, 100, 200/3, 100, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(100/3, -1.5, 100/3, 101.5, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pass_num = idx-first_n_passes+1
        possession_plot = pos_chain_df[pos_chain_df['pos_start'] == 'Mid 3']
    else:
        pitch.lines(100/3, 101.5, 100/3, -1.5, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(100/3, 0, 0, 0, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(100/3, 100, 0, 100, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pitch.lines(0, -1.5, 0, 101.5, lw=3, color = 'lightsteelblue', zorder = 1, ax=ax['pitch'][idx])
        pass_num = idx-2*first_n_passes+1
        possession_plot = pos_chain_df[pos_chain_df['pos_start'] == 'Own 3']
        
    # Passes to plot
    pass_plot = possession_plot[possession_plot['pass_number']==pass_num]
    pass_top_cluster_ids = pass_plot.groupby('pass_cluster_id').count()['id'].sort_values(ascending=False).head(clusters_shown).index.values
    cluster_rank_dict = dict(zip(pass_top_cluster_ids, np.arange(1,len(pass_top_cluster_ids)+1)))
    cluster_color_dict = dict(zip(pass_top_cluster_ids, cluster_colours[0:clusters_shown]))
    pass_top_clusters =  pass_plot[pass_plot['pass_cluster_id'].isin(pass_top_cluster_ids)].copy()
    pass_top_clusters['cluster_rank'] = pass_top_clusters['pass_cluster_id'].apply(lambda x: cluster_rank_dict[x])    
    pass_top_clusters['cluster_c'] = pass_top_clusters['pass_cluster_id'].apply(lambda x: cluster_color_dict[x])    
    pass_top_clusters = pass_top_clusters.sort_values('cluster_rank', ascending=False)
    
    # Plot passes
    for _, single_pass in pass_top_clusters.iterrows():
        pitch.lines(single_pass['x'], single_pass['y'], single_pass['endX'], single_pass['endY'],
                    lw=1.5, comet=False, capstyle='round', color = single_pass['cluster_c'], alpha = 0.8, ax=ax['pitch'][idx], zorder=2)
        pitch.scatter(single_pass['endX'], single_pass['endY'], s=10, color = single_pass['cluster_c'], alpha = 0.8, zorder=3, ax=ax['pitch'][idx])
        pitch.scatter(single_pass['endX'], single_pass['endY'], s=5, color = '#313332', alpha = 1, zorder=3, ax=ax['pitch'][idx])

    # Add title
    if pass_num == 1:
        suffix = 'st'
    elif pass_num == 2:
        suffix = 'nd'
    elif pass_num == 3:
        suffix = 'rd'
    else:
        suffix = 'th'
    ax['pitch'][idx].set_title(f"{pass_num}{suffix} Pass", pad=-1, color = 'w', fontsize = 9)
    
# Add title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League One', 'EFL2': 'EFL League Two'}

title_text = f"{team} Passing Tendencies − {leagues[league]} {year}/{(str(int(year)+1)).replace('20','',1)}"
subtitle_text = f"Where {team} directed passes during possessions starting in each third"
subsubtitle_text = f"First {first_n_passes} passes in each possession chain. {clusters_shown} most common pass types shown"
fig.text(0.12, 0.945, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.12, 0.918, subtitle_text, fontweight="bold", fontsize=13, color='w')
fig.text(0.12, 0.896, subsubtitle_text, fontweight="regular", fontsize=10, color='w')
    
# Add figure text
for loc in [[0.38,0.84], [0.42,0.57], [0.381,0.3]]:
    sep_ax = fig.add_axes([0.02, loc[1], 0.96, 0.02]); sep_ax.axis("off")
    sep_ax.plot([0,0.05],[0,0], color = 'grey', lw = 1)
    sep_ax.plot([loc[0],1],[0,0], color = 'grey', lw = 1)
    sep_ax.set_xlim([0,1])

fig.text(0.075, 0.845, "Possessions Initiated in Final Third", fontweight="bold", fontsize=11, color='w')
fig.text(0.075, 0.575, "Possessions Initiated in Centre of Pitch", fontweight="bold", fontsize=11, color='w')
fig.text(0.075, 0.305, "Possessions Initiated in Own Third", fontweight="bold", fontsize=11, color='w')

# Add legend logo
fig.text(0.14, 0.032, "nth Most Common Pass Cluster", fontweight="bold", fontsize=9, color='w', ha = "center")
ax = fig.add_axes([0, 0, 0.3, 0.05])
for idx in np.arange(0,clusters_shown):
    ax.scatter(0.07+idx*0.17, 0.35, color=cluster_colours[idx])
    ax.text(0.1+idx*0.17, 0.295, f"n={1+idx}",fontsize=8, c='w')
ax.set_xlim([0,1])
ax.set_ylim([0,1])
ax.axis('off')

# Add team logo
logo, _ = lab.get_team_badge_and_colour(team)
ax = fig.add_axes([0.017, 0.88, 0.1, 0.1])
ax.axis("off")
ax.imshow(logo)

# Add footer text
fig.text(0.55, 0.022, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.92, 0.005, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

# Save
plt.savefig(f"team_pass_tendencies/{team.lower().replace(' ','')}-{league.lower().replace(' ','')}-{year}", dpi=300)
