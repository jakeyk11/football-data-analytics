# %% Expected Goals Model, using Wyscout data from Top 5 Leagues in 2017/18
#
# Inputs:   Leagues to use to train xg model
#
# Outputs:  xG model, displayed as an xG heatmap
#           Dataframe all shots in chosen leagues, including shot information and xG.
#
# Notes: None

# %% Imports

import os
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression 
from mplsoccer.pitch import VerticalPitch
import pickle
import bz2

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.wyscout_data_engineering as wde

# %% User inputs

# List of leagues to use for xg model
leagues = ["England", "Italy", "France", "Germany", "Spain"]

# %% Set constants

PITCH_WIDTH_Y = 80
PITCH_LENGTH_X = 120
GOAL_WIDTH_Y = 8

# %% Load Wyscout data for all competitions

match_data, event_data, event_data_by_match, player_data, competition_data, team_data = wde.format_wyscout_data(leagues)

# %% Define dataframe of all shots in event data

# Initialise shot model dataframe
shots_model_df = pd.DataFrame()
i = 0

# Loop through shots and obtain/calculate shot information
for _, shot in event_data[event_data['eventName']=='Shot'].iterrows():
    
    # Player, team and competition
    if shot['playerId'] != 0:
        shots_model_df.loc[i, 'player_name'] = player_data.loc[shot['playerId']]['shortName'].encode('ascii', 'strict').decode('unicode-escape')
    else:
        shots_model_df.loc[i, 'player_name'] = np.nan
    shots_model_df.loc[i, 'team_name'] = team_data.loc[shot['teamId']]['name'].encode('ascii', 'strict').decode('unicode-escape')
    shots_model_df.loc[i, 'competition_name'] = competition_data.loc[match_data.loc[shot['matchId']]['competitionId']]['name']
    
    # Position and distance info
    shots_model_df.loc[i, 'x_yards'] = (PITCH_LENGTH_X/100)*(100 - shot['positions'][0]['x'])
    shots_model_df.loc[i, 'c_yards'] = (PITCH_WIDTH_Y/100)*(shot['positions'][0]['y'] - 50)
    shots_model_df.loc[i,'distance_yards'] = np.sqrt(shots_model_df.loc[i, 'x_yards']**2 + shots_model_df.loc[i, 'c_yards']**2)
    
    # Angle info
    angle_denominator = (shots_model_df.loc[i, 'x_yards']**2 + shots_model_df.loc[i, 'c_yards']**2 - (GOAL_WIDTH_Y/2)**2)
    if angle_denominator == 0:
        angle = np.pi/2
    else:
        angle = np.arctan((2*(GOAL_WIDTH_Y/2)*shots_model_df.loc[i, 'x_yards'])/angle_denominator)
    if angle<0:
        angle = np.pi + angle
    shots_model_df.loc[i, 'angle'] = angle
    
    # Header info
    shots_model_df.loc[i, 'header_tag'] = 0
    if {'id': 403} in shot['tags']:
        shots_model_df.loc[i, 'header_tag'] = 1
        
    # Outcome
    shots_model_df.loc[i, 'goal'] = 0
    if {'id': 101} in shot['tags']:
        shots_model_df.loc[i, 'goal'] = 1        
    
    i += 1


#%% Train a logistic regression model

X = shots_model_df.drop(['player_name', 'team_name', 'competition_name','goal'], axis=1)
y = shots_model_df['goal']

# Fit
log_model = LogisticRegression()
log_model.fit(X,y)

# Coefficients
a = log_model.intercept_[0]
b = log_model.coef_[0]

# Calculate xG
shots_model_df['xG'] = log_model.predict_proba(X)[:,1]

# %% Save xG data

with bz2.BZ2File("../../data_directory/misc_data/log_regression_xg_data.pbz2", "wb") as f:
    pickle.dump(shots_model_df, f)

#%% Create an xG test-set, and predict on test set

# Initialise arrays for ground and header test-sets
prob_goal_grnd = np.zeros((int(1+PITCH_LENGTH_X/2), int(1+PITCH_WIDTH_Y)))
prob_goal_head = np.zeros((int(1+PITCH_LENGTH_X/2), int(1+PITCH_WIDTH_Y)))

# Create array of shots
for x_pos in range(0,int(PITCH_LENGTH_X/2 + 1)):
    for y_pos in range(0, int(PITCH_WIDTH_Y + 1)):
        c_pos = y_pos - PITCH_WIDTH_Y/2
        angle_denominator = (x_pos**2 + c_pos**2 - (GOAL_WIDTH_Y/2)**2)
        if angle_denominator == 0:
            angle = np.pi/2
        else:
            angle = np.arctan(2*(GOAL_WIDTH_Y/2)*x_pos/angle_denominator)
        if angle < 0:
            angle = np.pi + angle
        distance = np.sqrt(x_pos**2 + c_pos**2)
        prob_goal_grnd[x_pos, y_pos] = log_model.predict_proba([[x_pos, c_pos, distance, angle, 0]])[:,1]
        prob_goal_head[x_pos, y_pos] = log_model.predict_proba([[x_pos, c_pos, distance, angle, 1]])[:,1]

# %% Plot xG model

# Overwrite rcParams 
mpl.rcParams['xtick.color'] = "white"
mpl.rcParams['ytick.color'] = "white"
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10

# Plot pitches
pitch = VerticalPitch(half=True,pitch_color='#313332', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=1, ncols=2, grid_height=0.75, space = 0.1, axis=False)
fig.set_size_inches(10, 5.5)
fig.set_facecolor('#313332')

# Add xG maps and contours
pos1 = ax['pitch'][0].imshow(prob_goal_grnd, extent = (80,0,60,120) ,aspect='equal',vmin=-0.04,vmax=0.4,cmap=plt.cm.inferno)
pos2 = ax['pitch'][1].imshow(prob_goal_head, extent = (80,0,60,120) ,aspect='equal',vmin=-0.04,vmax=0.4,cmap=plt.cm.inferno)
cs1 = ax['pitch'][0].contour(prob_goal_grnd, extent = (1,80,120,60), levels = [0.01,0.05,0.2,0.5], colors = ['darkgrey','darkgrey','darkgrey','k'], linestyles = 'dotted')
cs2 = ax['pitch'][1].contour(prob_goal_head, extent = (1,80,120,60), levels = [0.01,0.05,0.2,0.5], colors = ['darkgrey','darkgrey','darkgrey','k'], linestyles = 'dotted')
ax['pitch'][0].clabel(cs1)
ax['pitch'][1].clabel(cs2)

# Title
fig.text(0.045,0.9,"Expected Goals - Logistic Regression Model", fontsize=16, color="white", fontweight="bold")
fig.text(0.045,0.85,"Trained on all 40,000+ shots during the 2017/18 season across Europe's 'big five' Leagues", fontsize=14, color="white", fontweight="regular")
fig.text(0.12,0.76,"Shot Type: Left or Right Foot", fontsize=12, color="white", fontweight="bold")
fig.text(0.66,0.76,"Shot Type: Header", fontsize=12, color="white", fontweight="bold")

# Colourbar
cbar = fig.colorbar(pos2, ax=ax['pitch'][1], location="bottom",  fraction = 0.04, pad = 0.0335)
cbar.ax.set_ylabel('xG', loc="bottom", color = "white", fontweight="bold", rotation=0, labelpad=20)

# Footer text
fig.text(0.255, 0.09, "Created by Jake Kolliari. Data provided by Wyscout.com",
         fontstyle="italic", ha="center", fontsize=9, color="white")  

# Format and show
plt.tight_layout()
plt.show()