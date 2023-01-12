# %% Create visualisation of team threat creation zones
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Date of run
#           Selection of whether to include percentages on visual

# %% Imports and parameters

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm
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
run_date = '10/01/2023'

# Select whether to brighten logo
logo_brighten = True

# Max time between a pass and shot that tags the pass as "shot-creating"
min_delta = 1/6

# %% Get competition logo

comp_logo = lab.get_competition_logo(league, year) 

if logo_brighten:
    comp_logo = lab.get_competition_logo(league, year)
    enhancer = ImageEnhance.Brightness(comp_logo)
    comp_logo = enhancer.enhance(100)
else:
    comp_logo = lab.get_competition_logo(league, year)

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

# %% Synthesis additional info

# Pass recipient
events_df = wde.get_recipient(events_df)

# Add cumulative minutes played information
players_df_test = wde.minutes_played(players_df, events_df)
events_df = wde.cumulative_match_mins(events_df)

# xThreat

events_df = wce.get_xthreat(events_df, interpolate = True)

# %% Create dictionary of teams, and store full back pass combinations against each team

# Get all team names
teams = sorted(set(players_df['team']))

# Initialise dictionary to store full-back combos per team
team_fb_combos = dict.fromkeys(teams, 0)

# Initialise dictionary to store xT generated per 90 from full-back combos
team_fb_combo_xt = dict.fromkeys(teams, 0)

# Loop through each team
for team in teams:
    
    # Get team id and all matches team have played
    team_id = players_df[players_df['team']==team]['teamId'].values[0]
    match_ids = set(players_df[players_df['team']==team]['match_id'])
    fb_pass_combos = pd.DataFrame()
    
    # Loop through each match
    for match_id in match_ids:
        
        # Get ids of full backs that started in match for team
        team_match_players = players_df[(players_df['teamId']==team_id) & (players_df['match_id']==match_id)]
        starting_rb_id = team_match_players[team_match_players['position'].isin(['DMR','DR'])].index.values.tolist()
        starting_lb_id = team_match_players[team_match_players['position'].isin(['DML','DL'])].index.values.tolist()
        
        # Get all events completed by team within match
        team_match_events = events_df[(events_df['teamId']==team_id) & (events_df['match_id']==match_id)]

        # If both a LB/LWB and RB/RWB start, then look for passes between
        if (len(starting_rb_id)>0) & (len(starting_lb_id)>0): 
            
            # Get in-play successful passes between
            fb_pass_combos_match = team_match_events[(team_match_events['eventType']=='Pass') &
                                                     (team_match_events['outcomeType']=='Successful') &
                                                     (~team_match_events['satisfiedEventsTypes'].apply(lambda x: 31 in x or 32 in x or 33 in x or 34 in x or 212 in x)) &
                                                     (((team_match_events['playerId'] == starting_rb_id[0]) & (team_match_events['pass_recipient'] == starting_lb_id[0])) |
                                                      ((team_match_events['playerId'] == starting_lb_id[0]) & (team_match_events['pass_recipient'] == starting_rb_id[0])))]
            
            # Add column to store whether a shot happens within certain time of pass being made
            fb_pass_combos_match['leads_to_shot'] = False
            
            # Loop through full-back combos, find next sequence of events and check whether shot occured
            for idx, fb_pass in fb_pass_combos_match.iterrows():
                following_evts = team_match_events[(team_match_events['match_id']==fb_pass['match_id']) &
                                                   (team_match_events['period']==fb_pass['period']) &
                                                   (team_match_events['cumulative_mins']>fb_pass['cumulative_mins']) &
                                                   (team_match_events['cumulative_mins']<=fb_pass['cumulative_mins']+min_delta)]
                fb_pass_combos_match.loc[idx,'leads_to_shot'] = True if True in following_evts['isShot'].tolist() else False
        
        # Build up dataframe of full back combos for team across multiple matches
        fb_pass_combos = pd.concat([fb_pass_combos, fb_pass_combos_match])
    
    # Store full back combo in dictionary
    team_fb_combos[team] = fb_pass_combos
    
    # Calculate xT generated from full back combos per 90 and store in dictionary
    team_fb_combo_xt[team] = fb_pass_combos['xThreat_gen'].sum()/len(match_ids)

# Order teams by xT generated per 90
team_order_xt_90 = sorted(team_fb_combo_xt, key=team_fb_combo_xt.get, reverse=True)

#%% Create plot of individual teams and full back passes

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Set-up pitch subplots
pitch = Pitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=5, ncols=4, grid_height=0.8, title_height = 0.13, endnote_height = 0.04, space=0.12, axis=False)
fig.set_size_inches(14, 15)
fig.set_facecolor('#313332')
ax['pitch'] = ax['pitch'].reshape(-1)
idx = 0

# Manual implentation of colourmap
pass_cmap = cm.get_cmap('viridis')
pass_cmap = pass_cmap(np.linspace(0.35,1,256))

# Loop through each team
for team in team_order_xt_90:
    
    # Get team passes from dict
    team_fb_passes = team_fb_combos[team].sort_values('xThreat')
    
    # Loop through individual passes to format
    for _, pass_evt in team_fb_passes.iterrows():
        if pass_evt['xThreat_gen'] < 0.001:
            line_colour = 'grey'
            line_alpha = 0.1
        else:
            line_colour = pass_cmap[int(255*min(pass_evt['xThreat_gen']/0.05, 1))]
            line_alpha = 0.7
    
        # Format differently if event is followed by a shot
        if not pass_evt['leads_to_shot']:
            pitch.lines(pass_evt['x'], pass_evt['y'], pass_evt['endX'], pass_evt['endY'], color = line_colour, alpha = line_alpha,
                        comet=True, capstyle='round', lw=2, ax = ax['pitch'][idx], zorder = 2)
            pitch.scatter(pass_evt['endX'], pass_evt['endY'], color = line_colour, alpha = line_alpha+0.2, s=30, ax = ax['pitch'][idx], zorder = 3)
        else:
            pitch.lines(pass_evt['x'], pass_evt['y'], pass_evt['endX'], pass_evt['endY'], color = 'w', alpha = 0.7,
                        comet=True, capstyle='round', lw=2, ax = ax['pitch'][idx], zorder = 2)
            pitch.scatter(pass_evt['endX'], pass_evt['endY'], color = 'w', alpha = 0.9, s=30, ax = ax['pitch'][idx], zorder = 3)
        pitch.scatter(pass_evt['endX'], pass_evt['endY'], color = '#313332', alpha = 1, s=10, ax = ax['pitch'][idx], zorder = 3)
        
    # Add xT text to plot
    ax['pitch'][idx].text(2, 3, "xT / match", fontsize=8, fontweight='bold', color='w', zorder=3)
    ax['pitch'][idx].text(28, 3, round(team_fb_combo_xt[team],3), fontsize=8, color='w', zorder=3)   

    # Add team logo
    team_logo, _ = lab.get_team_badge_and_colour(team)
            
    ax_pos = ax['pitch'][idx].get_position()
    
    logo_ax = fig.add_axes([ax_pos.x1-0.025, ax_pos.y1, 0.025, 0.025])
    logo_ax.axis("off")
    logo_ax.imshow(team_logo)
    
    # Add title
    ax['pitch'][idx].set_title(f"  {idx + 1}:  {team}", loc = "left", color='w', fontsize = 14)
    
    idx+=1
    
# Title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup'}

title_text = f"{leagues[league]} {year} − Threat Generated through Full Back Interplay"
subtitle_text = "Successful in-play passes between Full Backs shown and coloured by <Threat> for each team"
subsubtitle_text = f"Teams ranked by mean threat generated by passes between full-backs in starting XI. Correct as of {run_date}"

fig.text(0.12, 0.945, title_text, fontweight="bold", fontsize=20, color='w')
htext.fig_text(0.12, 0.934, s=subtitle_text, fontweight="regular", fontsize=18, color='w',
               highlight_textprops=[{"color": 'yellow', "fontweight": 'bold'}])
fig.text(0.12, 0.9, subsubtitle_text, fontweight="regular", fontsize=14, color='w')

# Add direction of play arrow
ax = fig.add_axes([0.042, 0.028, 0.18, 0.005])
ax.axis("off")
plt.arrow(0.51, 0.15, 0.1, 0, color="white")
fig.text(0.13, 0.015, "Direction of play", ha="center", fontsize=10, color="white", fontweight="regular")

# Add legend
legend_ax = fig.add_axes([0.245, 0.01, 0.2, 0.04])
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
        xt = '<0.001'
        color = 'grey'
    elif idx == 1:
        xt = round(0.001 + (0.05-0.001) * ((idx-1)/(hex_count-2)),3)
        color = pass_cmap[int(255*(idx-1)/(hex_count-2))]
    else:
        xt = round(0.001 + (0.05-0.001) * ((idx-1)/(hex_count-2)),2)
        color = pass_cmap[int(255*(idx-1)/(hex_count-2))]
    
    legend_ax.scatter(xpos, ypos, marker='H', s=600, color=color, edgecolors=None)
    legend_ax.text(xpos+0.03, ypos-0.02, xt, color='w', fontsize = 8, ha = "center", va = "center", path_effects = path_eff)
    legend_ax.text(0.1, 0.5, "xThreat:", color='w', fontsize = 10, ha = "left", va = "center", fontweight="regular")

legend_ax_2 = fig.add_axes([0.46, 0.01, 0.2, 0.04])
legend_ax_2.axis("off")
legend_ax_2.scatter(0.1, 0.5, color = 'w', alpha = 1, s=80)
legend_ax_2.scatter(0.1, 0.5, color = '#313332', alpha = 1, s=30)
legend_ax_2.text(0.15, 0.5, '= Shot-creating action', va = "center", color = 'w')
plt.xlim([0, 1])
plt.ylim([0, 1])

# Add footer text
fig.text(0.77, 0.022, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add competition logo
ax = fig.add_axes([0.017, 0.88, 0.1, 0.1])
ax.axis("off")
ax.imshow(comp_logo)

# Add twitter logo
ax = fig.add_axes([0.92, 0.005, 0.04, 0.04])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

fig.savefig(f"team_fullback_combinations/{league}-{year}-team_fullback_combinations", dpi=300)