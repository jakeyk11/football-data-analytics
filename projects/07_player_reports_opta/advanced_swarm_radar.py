# %% Generate swarm radar plot

# %% Imports and parameters

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import matplotlib.patheffects as path_effects 
from matplotlib.transforms import Affine2D
from matplotlib.ticker import MultipleLocator
import mpl_toolkits.axisartist.floating_axes as floating_axes
from mpl_toolkits.axisartist.grid_finder import (FixedLocator, MaxNLocator, DictFormatter) 
from mplsoccer.pitch import VerticalPitch
import seaborn as sns
import mplsoccer.pitch
import os
import sys
import bz2
import pickle
import textwrap as tw
from scipy.spatial import ConvexHull
from scipy.interpolate import interp2d
from scipy.spatial import Delaunay
from shapely.geometry.polygon import Polygon
from mpl_toolkits.axes_grid1 import Divider
import mpl_toolkits.axes_grid1.axes_size as Size
from matplotlib.projections import polar
from PIL import Image, ImageEnhance
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from mplsoccer import PyPizza

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.pitch_zones as pz
import analysis_tools.logos_and_badges as lab

# %% User inputs

player_1 = {'name':'Liam Gibbs', 'comp':'EFLC', 'year':'2022'}
player_2 = {'name':'Oliver Norwood', 'comp':'EFLC', 'year':'2022'}
comparison_competition = {'comp':'EPL', 'year':'2022', 'position': 'MID', 'mins':600}
comparison_logo_brighten = True
player_1_colour = 'lightskyblue'
player_2_colour = 'coral'

# %% League logo and league naming
    
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League One', 'EFL2': 'EFL League Two'}

# %% Get required data

# Combine player data and comparison comp data requirements
all_data = [player_1] + [player_2] + [comparison_competition]
all_data_download = []

# Build list of data to download
for data in all_data:
    comp_year = [data['comp']] + [data['year']]
    if comp_year != ['','']:
        all_data_download.append(comp_year)

# Remove duplicates in list
all_data_download = [list(x) for x in set(tuple(x) for x in all_data_download)]

# Download data
events_df = pd.DataFrame()
players_df = pd.DataFrame()

for idx, data in enumerate(all_data_download):
    
    # Determine file path
    file_path = f"../../data_directory/whoscored_data/{data[1]}_{str(int(data[1].replace('20','', 1)) + 1)}/{data[0]}"
    files = os.listdir(file_path)
    
    # Initialise storage dataframes
    comp_events_df = pd.DataFrame()
    comp_players_df = pd.DataFrame()
    
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
            comp_events_df = pd.concat([comp_events_df, match_events])
        elif '-playerdata-' in file:
            match_players = bz2.BZ2File(f"{file_path}/{file}", 'rb')
            match_players = pickle.load(match_players)
            comp_players_df = pd.concat([comp_players_df, match_players])
        else:
            pass

    # Add competition data to player dataframe 
    comp_players_df['competition'] = data[0]
    comp_players_df['year'] = data[1]
    
    # Save data
    events_df = pd.concat([events_df, comp_events_df])
    players_df = pd.concat([players_df, comp_players_df])
    
    # Reset storage dataframes
    del comp_events_df
    del comp_players_df
    
# %% Add to players and events dataframe    

players_df = wde.events_while_playing(events_df, players_df, event_name='Pass', event_team='own')
players_df = wde.events_while_playing(events_df, players_df, event_name='Pass', event_team='opposition')
players_df = wde.events_while_playing(events_df, players_df, event_name='Touch', event_team='own')
players_df = wde.events_while_playing(events_df[events_df['x']<=100/3], players_df, event_name='Touch', event_team='opposition').rename(columns={'opp_touch':'opp_touch_own_3rd'})
players_df = wde.events_while_playing(events_df, players_df, event_name='Touch', event_team='opposition')
events_df['box_entry'] = events_df.apply(wce.box_entry, axis=1)
events_df['prog_action'] = events_df.apply(wce.progressive_action, axis=1)

# %% Aggregate lineups to construct playerinfo dataframe, and then filter

playerinfo_df = wde.create_player_list(players_df, pass_extra = ['competition', 'year'], additional_cols = ['team_touch', 'opp_touch', 'opp_touch_own_3rd', 'team_pass', 'opp_pass'])
playerinfo_df = playerinfo_df[(playerinfo_df['name'].isin([player_1['name'],player_2['name']])) |
                              ((playerinfo_df['pos_type'] == comparison_competition['position']) &
                               (playerinfo_df['mins_played'] >= comparison_competition['mins']) & 
                               (playerinfo_df['competition'] == comparison_competition['comp']))]

# %% Get some metrics

# Touches
touches = events_df[events_df['isTouch'] == True]
playerinfo_df = wde.group_player_events(touches, playerinfo_df, group_type='count', primary_event_name='touches')

# IP Box touches and entries
inplay_touches = touches[touches['satisfiedEventsTypes'].apply(lambda x: False if (5 in x or 31 in x or 34 in x or 212 in x) else True)]
box_touches = inplay_touches[(inplay_touches['x']>=83) & (inplay_touches['y']<=79) & (inplay_touches['y']>=21)]
suc_box_entries = events_df[events_df['box_entry']==True]
playerinfo_df = wde.group_player_events(box_touches, playerinfo_df, group_type='count', primary_event_name='box_touches')
playerinfo_df = wde.group_player_events(suc_box_entries, playerinfo_df, group_type='count', primary_event_name='suc_box_entries')

# xThreat and passing
passes = events_df[events_df['eventType'] == 'Pass']
suc_passes = passes[passes['outcomeType'] == 'Successful']
carries = events_df[events_df['eventType'] == 'Carry']
pass_carry = pd.concat([suc_passes, carries])
prog_pass_carry = pass_carry[pass_carry['prog_action']==True]
pass_carry_f3rd = pass_carry[(pass_carry['x']<100/3) & (pass_carry['endX']>=200/3)]
assists = passes[passes['satisfiedEventsTypes'].apply(lambda x: True if 92 in x else False)]
playerinfo_df = wde.group_player_events(passes, playerinfo_df, group_type='count', primary_event_name='passes')
playerinfo_df = wde.group_player_events(suc_passes, playerinfo_df, group_type='count', primary_event_name='suc_passes')
playerinfo_df = wde.group_player_events(carries, playerinfo_df, group_type='count', primary_event_name='carries')
playerinfo_df = wde.group_player_events(passes, playerinfo_df, group_type='sum', agg_columns='xThreat', primary_event_name='pass_xt')
playerinfo_df = wde.group_player_events(carries, playerinfo_df, group_type='sum', agg_columns='xThreat', primary_event_name='carry_xt')
playerinfo_df = wde.group_player_events(pass_carry_f3rd, playerinfo_df, group_type='count', primary_event_name='final_3rd_entries')
playerinfo_df = wde.group_player_events(prog_pass_carry, playerinfo_df, group_type='count', primary_event_name='prog_actions')

# Shots and big chances
shots = events_df[(events_df['eventType'].isin(['MissedShots', 'SavedShot', 'ShotOnPost', 'Goal'])) & (~events_df['satisfiedEventsTypes'].apply(lambda x: True if( 5 in x or 6 in x) else False))].copy()
shots['shot_distance'] = shots[['x','y']].apply(lambda a: np.sqrt((120*((100-a[0])/100))**2 + (80*((50-a[1])/100))**2),axis = 1)        
goals = shots[shots['eventType'] == 'Goal']
gc = pd.concat([assists,goals])
box_shots = shots[(shots['x']>=83) & (shots['y']<=79) & (shots['y']>=21)]
box_goals = box_shots[box_shots['eventType'] == 'Goal']
big_chances = events_df[events_df['satisfiedEventsTypes'].apply(lambda x: True if 203 in x and not (31 in x or 34 in x or 212 in x) else False)]
playerinfo_df = wde.group_player_events(shots, playerinfo_df, group_type='count', primary_event_name='shots')
playerinfo_df = wde.group_player_events(shots, playerinfo_df, group_type='mean', agg_columns='shot_distance', primary_event_name='mean_shot_dist')
playerinfo_df = wde.group_player_events(goals, playerinfo_df, group_type='count', primary_event_name='goals')
playerinfo_df = wde.group_player_events(gc, playerinfo_df, group_type='count', primary_event_name='goal_contributions')
playerinfo_df = wde.group_player_events(box_shots, playerinfo_df, group_type='count', primary_event_name='box_shots')
playerinfo_df = wde.group_player_events(box_goals, playerinfo_df, group_type='count', primary_event_name='box_goals')
playerinfo_df = wde.group_player_events(big_chances, playerinfo_df, group_type='count', primary_event_name='big_chances')

# Aerials
aerials = events_df[events_df['eventType'] == 'Aerial']
aerials_won = aerials[aerials['outcomeType'] == 'Successful']
playerinfo_df = wde.group_player_events(aerials, playerinfo_df, group_type='count', primary_event_name='aerials')
playerinfo_df = wde.group_player_events(aerials_won, playerinfo_df, group_type='count', primary_event_name='aerials_won')

# Take ons
take_on = events_df[events_df['eventType'] == 'TakeOn']
suc_take_on = take_on[take_on['outcomeType'] == 'Successful']
playerinfo_df = wde.group_player_events(take_on, playerinfo_df, group_type='count', primary_event_name='take_on')
playerinfo_df = wde.group_player_events(suc_take_on, playerinfo_df, group_type='count', primary_event_name='suc_take_on')

# Crosses
crosses = passes[passes['satisfiedEventsTypes'].apply(lambda x: True if (125 in x or 126 in x or 59 in x) and not(31 in x or 34 in x or 212 in x) else False)]   
crosses = wce.get_pass_outcome(crosses, events_df, t=5)
cross_to_chance = crosses[crosses['pass_outcome'].isin(['Goal', 'Shot', 'Key Pass'])]
playerinfo_df = wde.group_player_events(crosses, playerinfo_df, group_type='count', primary_event_name='cross')
playerinfo_df = wde.group_player_events(cross_to_chance, playerinfo_df, group_type='count', primary_event_name='cross_to_chance')

# High ball wins
recoveries = events_df[(events_df['eventType']=='BallRecovery') & (events_df['outcomeType']=='Successful')]
interceptions = events_df[(events_df['eventType']=='Interception') & (events_df['outcomeType']=='Successful')]
bad_tackles = tackles = events_df[(events_df['eventType']=='Tackle') & (events_df['outcomeType']=='Unsuccessful')]
tackles = events_df[(events_df['eventType']=='Tackle') & (events_df['outcomeType']=='Successful')]
pass_blocks = events_df[(events_df['eventType']=='BlockedPass') & (events_df['outcomeType']=='Successful') ]
ball_wins = pd.concat([recoveries, interceptions, tackles, pass_blocks], axis=0)
ball_wins_high_33 = ball_wins[ball_wins['x']>=200/3]
playerinfo_df = wde.group_player_events(tackles, playerinfo_df, group_type='count', primary_event_name='tackles')
playerinfo_df = wde.group_player_events(bad_tackles, playerinfo_df, group_type='count', primary_event_name='bad_tackles')
playerinfo_df = wde.group_player_events(ball_wins, playerinfo_df, group_type='count', primary_event_name='ball_wins')
playerinfo_df = wde.group_player_events(ball_wins_high_33, playerinfo_df, group_type='count', primary_event_name='high_ball_wins')

# Ball losses
bad_touches = events_df[(events_df['eventType']=='BallTouch') & (events_df['outcomeType']=='Unsuccessful')]
bad_pass = events_df[(events_df['eventType']=='Pass') & (events_df['outcomeType']=='Unsuccessful')]
bad_takeon = events_df[(events_df['eventType']=='TakeOn') & (events_df['outcomeType']=='Unsuccessful')]
disspossessed = events_df[events_df['eventType']=='Disspossessed']
ball_losses = pd.concat([bad_touches, bad_pass, bad_takeon, disspossessed], axis=0)
playerinfo_df = wde.group_player_events(ball_losses, playerinfo_df, group_type='count', primary_event_name='ball_losses')

# %% Normalise metrics

playerinfo_df['pass_xt_100_team_touch'] = 100 * playerinfo_df['pass_xt'] / playerinfo_df['team_touch']
playerinfo_df['carry_xt_100_team_touch'] = 100 * playerinfo_df['carry_xt'] / playerinfo_df['team_touch']
playerinfo_df['final_3rd_entries_100_team_touch'] = 100 * playerinfo_df['final_3rd_entries'] / playerinfo_df['team_touch']
playerinfo_df['prog_actions_100_team_touch'] = 100 * playerinfo_df['prog_actions'] / playerinfo_df['team_touch']
playerinfo_df['pass_success_pct'] = 100 * playerinfo_df['suc_passes'] / playerinfo_df['passes']
playerinfo_df['goal_contributions_100_team_pass'] = 100 * playerinfo_df['goal_contributions'] / playerinfo_df['team_pass']
playerinfo_df['goal_contributions_90'] = 90 * playerinfo_df['goal_contributions'] / playerinfo_df['mins_played']
playerinfo_df['box_touches_100_team_pass'] = 100 * playerinfo_df['box_touches'] / playerinfo_df['team_pass']
playerinfo_df['box_entries_pct'] = 100 * playerinfo_df['suc_box_entries'] / (playerinfo_df['passes'] + playerinfo_df['carries'])
playerinfo_df['xt_gen_100_team_pass'] = 100 * (playerinfo_df['pass_xt'] + playerinfo_df['carry_xt']) / playerinfo_df['team_pass']
playerinfo_df['xt_gen_100_team_touch'] = 100 * (playerinfo_df['pass_xt'] + playerinfo_df['carry_xt']) / playerinfo_df['team_touch']
playerinfo_df['box_shot_conversion'] = 100 * playerinfo_df['box_goals'] / playerinfo_df['box_shots']
playerinfo_df['big_chances_100_team_pass'] = 100 * playerinfo_df['big_chances'] / playerinfo_df['team_pass']
playerinfo_df['aerial_win_pct'] = 100 * playerinfo_df['aerials_won'] / playerinfo_df['aerials']
playerinfo_df['tackles_success_pct'] = 100 * playerinfo_df['tackles'] / (playerinfo_df['tackles'] + playerinfo_df['bad_tackles'])
playerinfo_df['takeon_pct'] = 100 * playerinfo_df['suc_take_on'] / playerinfo_df['take_on']
playerinfo_df['cross_chance_pct'] = (100 * playerinfo_df['cross_to_chance'] / playerinfo_df['cross']).fillna(0)
playerinfo_df['ball_wins_100_opp_touch'] = 100 * playerinfo_df['ball_wins'] / playerinfo_df['opp_touch']
playerinfo_df['high_ball_wins_100_opp_pass_own_3rd'] = 100 * playerinfo_df['high_ball_wins'] / playerinfo_df['opp_touch_own_3rd']
playerinfo_df['ball_losses_100_touch'] = 100 * playerinfo_df['ball_losses'] / playerinfo_df['touches']
  
# %% Templates 

# FORWARDS/WINGERS
template = 'Forward'
swarm_radar_metrics = ['goal_contributions_100_team_passes',
                       'box_touches_100_team_pass',
                       'box_entries_pct',
                       'xt_gen_100_team_pass',
                       'box_shot_conversion',
                       'big_chances_100_team_pass',
                       'aerial_win_pct',
                       'takeon_pct',
                       'high_ball_wins_100_opp_pass_own_3rd',
                       'ball_losses_100_touch']
swarm_radar_titles = ['Goal Contributions per\n100 team passes',
                      'Box Touches\nper 100 team passes',
                      '% Actions into\nOpp. Box',
                      'Threat generated per\n100 team passes',
                      '% Box shots\nconverted',
                      'Big chances per\n100 team passes',
                      '% Aerials\nwon',
                      '% Takeons\ncompleted',
                      'High ball wins per\n100 opp passes',
                      'Ball losses per\n100 touches']
neg_metrics = 'ball_losses_100_touch'

# CENTRAL MIDFIELDERS
template = 'Centre Mid'
swarm_radar_metrics = ['goal_contributions_90',
                       'pass_xt_100_team_touch',
                       'carry_xt_100_team_touch',
                       'prog_actions_100_team_touch',
                       'final_3rd_entries_100_team_touch',
                       'pass_success_pct',
                       'aerial_win_pct',
                       'tackles_success_pct',
                       'ball_wins_100_opp_touch',
                       'ball_losses_100_touch']
swarm_radar_titles = ['Goal Contribution\nper 90',
                      'Threat from Passes per\n100 team touches',
                      'Threat from Carries per\n100 team touches',
                      'Final 3rd Entries per\n100 team touches',
                      'Progressive Actions per\n100 team touches',
                      'Pass Accuracy (%)',
                      'Aerial Win\nRate (%)',
                      'Ground Duel\nWin Rate (%)',
                      'Ball Wins per\n100 opposition touches',
                      'Ball losses per\n100 touches']
neg_metrics = 'ball_losses_100_touch'

# %% Generate swarm radar

path_eff = [path_effects.Stroke(linewidth=2, foreground='#313332'), path_effects.Normal()]

# Tag primary players
playerinfo_df['Primary Player'] = 'Untagged'
if player_1['name'] != '':
    player_1_id = playerinfo_df[(playerinfo_df['name'] == player_1['name']) & (playerinfo_df['competition'] == player_1['comp']) & (playerinfo_df['year'] == player_1['year'])].index.values[0]
    playerinfo_df.loc[player_1_id, 'Primary Player'] = 'Primary 1'
if player_2['name'] != '':
    player_2_id = playerinfo_df[(playerinfo_df['name'] == player_2['name']) & (playerinfo_df['competition'] == player_2['comp']) & (playerinfo_df['year'] == player_2['year'])].index.values[0]
    playerinfo_df.loc[player_2_id, 'Primary Player'] = 'Primary 2'
  
playerinfo_df['Plot Size'] = playerinfo_df['Primary Player'].apply(lambda x: 7 if x == 'Untagged' else 7)

# Sort dataframe to highlight tagged players
playerinfo_df = playerinfo_df.sort_values('Primary Player')

# Number of metrics
num_metrics = len(swarm_radar_metrics)

# Define the position and size of the child axes (in polar coordinates)
theta_mid = np.radians(np.linspace(0, 360, num_metrics+1))[:-1]+np.pi/2
theta_mid = [x if x <2*np.pi else x-2*np.pi for x in theta_mid]
theta_base = theta_mid-np.mean(np.diff(theta_mid))/2
theta_delta = np.mean(np.diff(theta_mid))
r_base = np.linspace(0.25, 0.25, num_metrics+1)[:-1]

# Convert to x,y coordinates
x_base, y_base = 0.325 + r_base * np.cos(theta_mid), 0.3 + 0.89 * r_base * np.sin(theta_mid)

# Create large figure
fig = plt.figure(constrained_layout=False, figsize = (9, 11))
fig.set_facecolor('#313332')

# Setup radar axis and object
theta = np.arange(0, 2*np.pi, 0.01)
radar_ax = fig.add_axes([0.025, 0, 0.95, 0.95],polar=True)
radar_ax.plot(theta, theta*0 + 0.17, color = 'w', lw = 1)
radar_ax.plot(theta, theta*0 + 0.3425, color = 'grey', lw = 1, alpha = 0.3)
radar_ax.plot(theta, theta*0 + 0.5150, color = 'grey', lw = 1, alpha = 0.3)
radar_ax.plot(theta, theta*0 + 0.6875, color = 'grey', lw = 1, alpha = 0.3)
radar_ax.plot(theta, theta*0 + 0.86, color = 'grey', lw = 1, alpha = 0.3)
radar_ax.axis('off')

# Store ax limits
ax_mins = []
ax_maxs = []

# Iterate through each metric 
for idx, metric in enumerate(swarm_radar_metrics):

    # Create mini figure
    fig_save, ax_save = plt.subplots(figsize = (4.5, 1.5))
    fig_save.set_facecolor('#313332')
    fig_save.patch.set_alpha(0)
    
    # Plot on axis    
    sns.swarmplot(x=playerinfo_df[metric], y=[""]*len(playerinfo_df), color='grey', edgecolor='w', s=playerinfo_df['Plot Size'], zorder=1)
    ax_save.legend([],[], frameon=False)
    ax_save.patch.set_alpha(0)
    ax_save.spines['bottom'].set_position(('axes', 0.5))
    ax_save.spines['bottom'].set_color('w')
    ax_save.spines['top'].set_color(None)
    ax_save.spines['right'].set_color('w')
    ax_save.spines['left'].set_color(None)
    ax_save.set_xlabel("")
    ax_save.tick_params(left=False, bottom=True)
    ax_save.tick_params(axis='both', which='major', labelsize=8, zorder=10, pad = 0, colors = 'w')
    if theta_mid[idx] < np.pi/2 or theta_mid[idx] > 3*np.pi/2:
        plt.xticks(path_effects=path_eff, fontweight = 'bold')
    else:
        plt.xticks(path_effects=path_eff, fontweight = 'bold', rotation = 180)

    if metric in neg_metrics:
        ax_save.invert_xaxis()
    ax_mins.append(ax_save.get_xlim()[0])
    ax_maxs.append(ax_save.get_xlim()[1]*1.05)

    fig_save.savefig('temp.png', dpi=300)
    
    # Define axis scale
    scales = (0, 1, 0, 1)

    # Add scale and rotation transformations
    t = Affine2D().scale(3,1).rotate_deg(theta_mid[idx]*(180/np.pi))
    
    # Add floating axes to figure, return auxillary axis
    h = floating_axes.GridHelperCurveLinear(t, scales)
    ax = floating_axes.FloatingSubplot(fig, 111, grid_helper=h)
    
    img = Image.open('temp.png')
    ax = fig.add_subplot(ax)
    
    # Return auxillary axis
    aux_ax = ax.get_aux_axes(t)
    
    # Translate axis to desired x,y position
    horiz_scale = [Size.Scaled(1.04)]  
    vert_scale = [Size.Scaled(1.0)]
    ax_div = Divider(fig, [x_base[idx], y_base[idx], 0.35, 0.35], horiz_scale, vert_scale, aspect=True)
    ax_loc = ax_div.new_locator(nx=0,ny=0)
    ax.set_axes_locator(ax_loc)
    
    # Add image to axis
    img = Image.open('temp.png')
    aux_ax.imshow(img, extent=[-0.18, 1.12, -0.15, 1.15])
    ax.axis('off')
    ax.axis['right'].set_visible(False)
    ax.axis['top'].set_visible(False)
    ax.axis['bottom'].set_visible(False)
    ax.axis['left'].set_visible(False)
    
    # Add title text
    if theta_mid[idx] >= np.pi:
        text_rotation_delta = 90
    else:
        text_rotation_delta = -90
    radar_ax.text(theta_mid[idx], 0.92, swarm_radar_titles[idx], ha = "center", va = "center", fontweight = "bold", fontsize = 10, color = 'w',
                  rotation = text_rotation_delta + (180/np.pi) * theta_mid[idx])
    
    # Close and delete image
    plt.close(fig_save)

radar_ax.set_rmax(1)

# Add player logos and details
if player_1['name'] != '':
    team_logo_1, _ = lab.get_team_badge_and_colour(playerinfo_df.loc[player_1_id, 'team'])
    team_logo_ax_1 = fig.add_axes([0.015, 0.897, 0.09, 0.09])
    team_logo_ax_1.axis("off")
    team_logo_ax_1.imshow(team_logo_1)
    title_text_1 = playerinfo_df.loc[player_1_id, 'name']
    title_text_2 = playerinfo_df.loc[player_1_id, 'team']
    title_text_3 = playerinfo_df.loc[player_1_id, 'competition'] + ' ' +playerinfo_df.loc[player_1_id, 'year'] + '/' + str(int(playerinfo_df.loc[player_1_id, 'year']) + 1).replace('20','',1)
    fig.text(0.11, 0.953, title_text_1, fontweight="bold", fontsize=14, color=player_1_colour)
    fig.text(0.11, 0.931, title_text_2, fontweight="bold", fontsize=12, color='w')
    fig.text(0.11, 0.909, title_text_3, fontweight="bold", fontsize=12, color='w')

if player_2['name'] != '':
    team_logo_2, _ = lab.get_team_badge_and_colour(playerinfo_df.loc[player_2_id, 'team'])
    team_logo_ax_2 = fig.add_axes([0.385, 0.897, 0.085, 0.085])
    team_logo_ax_2.axis("off")
    team_logo_ax_2.imshow(team_logo_2)
    title_text_1 = playerinfo_df.loc[player_2_id, 'name']
    title_text_2 = playerinfo_df.loc[player_2_id, 'team']
    title_text_3 = playerinfo_df.loc[player_2_id, 'competition'] + ' ' +playerinfo_df.loc[player_2_id, 'year'] + '/' + str(int(playerinfo_df.loc[player_2_id, 'year']) + 1).replace('20','',1)
    fig.text(0.48, 0.953, title_text_1, fontweight="bold", fontsize=14, color=player_2_colour)
    fig.text(0.48, 0.931, title_text_2, fontweight="bold", fontsize=12, color='w')
    fig.text(0.48, 0.909, title_text_3, fontweight="bold", fontsize=12, color='w')

# Add mplsoccer radar

# Setup radar axis and object
pizza_ax = fig.add_axes([0.09, 0.065, 0.82, 0.82],polar=True)
pizza_ax.set_theta_offset(17)
pizza_ax.axis('off')
pizza_metrics = [swarm_radar_metrics[0]] + list(reversed(swarm_radar_metrics[1:]))
ax_mins = [ax_mins[0]] + list(reversed(ax_mins[1:]))
ax_maxs = [ax_maxs[0]] + list(reversed(ax_maxs[1:]))

radar_values_p1 = playerinfo_df[playerinfo_df['Primary Player']=='Primary 1'][pizza_metrics].values[0].tolist()
radar_values_p2 = playerinfo_df[playerinfo_df['Primary Player']=='Primary 2'][pizza_metrics].values[0].tolist()

radar_object = PyPizza(params=pizza_metrics,
                       background_color="w",
                       straight_line_color="w",
                       min_range = ax_mins,
                       max_range = ax_maxs,
                       straight_line_lw=1,
                       straight_line_limit = 100,
                       last_circle_lw=0.1,
                       other_circle_lw=0.1,
                       inner_circle_size=18)

# Plot radar
radar_object.make_pizza(values = radar_values_p1,
                        compare_values= radar_values_p2,
                        color_blank_space='same',
                        blank_alpha = 0,
                        bottom = 5,
                        kwargs_params=dict(fontsize=0, color='None'),
                        kwargs_values=dict(fontsize=0, color='None'),
                        kwargs_compare_values=dict(fontsize=0, color='None'),
                        kwargs_slices=dict(
                            facecolor=player_1_colour, alpha=0.3, edgecolor='#313332', linewidth=1,
                            zorder=1),
                        kwargs_compare=dict(
                            facecolor=player_2_colour, alpha=0.3, edgecolor='#313332', linewidth=1,
                            zorder=3),
                        ax = pizza_ax)

# Add radar type and description
title_text = f"{template} Template"
description = f"Players compared to {comparison_competition['position']}s having played over {comparison_competition['mins']} mins within {leagues[comparison_competition['comp']]} {comparison_competition['year']}/{str(int(playerinfo_df.loc[player_1_id, 'year']) + 1).replace('20','',1)}" 
description_text = "\n ".join(tw.wrap(description, 30, break_long_words=False, drop_whitespace=True))

fig.text(0.975, 0.953, title_text, fontweight="bold", fontsize=12, color='w', ha = 'right')
fig.text(0.975, 0.942, description_text, fontweight="regular", fontsize=8, color='w', ha = 'right', va = 'top')

# Add footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
logo_ax = fig.add_axes([0.94, 0.005, 0.04, 0.04])
logo_ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
logo_ax.imshow(badge)

# Save fig
plt.savefig(f"advanced_radars/{comparison_competition['comp'].lower()}-{comparison_competition['year']}-{player_1['name'].replace(' ','-').lower()}-{player_2['name'].replace(' ','-').lower()}", dpi=300)