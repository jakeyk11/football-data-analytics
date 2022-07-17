# %% Create plot of shot positions and associated xG for user-selected player, team or competition
#
# Inputs:   Player, team or competition to plot xG for
#
# Outputs:  Plot of shot positions and associated xG
#
# Notes: Uses logistic regression xG model.

# %% Imports

import bz2
import pickle
from PIL import Image
import requests
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from mplsoccer.pitch import VerticalPitch

# %% User inputs

# Select player, team or competition to plot shots for
player_team_or_comp = 'Mohamed Salah'

# Logo to add to plot figure
#logo = 'https://1000logos.net/wp-content/uploads/2019/01/German-Bundesliga-Logo-2002.png'
logo = "https://logos-world.net/wp-content/uploads/2020/06/Liverpool-Logo.png"

# %% Set constants

PITCH_WIDTH_Y = 80
PITCH_LENGTH_X = 120

# %% Load xG model and data

shots_model_df = bz2.BZ2File("../../data_directory/misc_data/log_regression_xg_data.pbz2", 'rb')
shots_model_df = pickle.load(shots_model_df)

# %% Isolate shots for selected player or team

if not shots_model_df[shots_model_df['competition_name']==player_team_or_comp].empty:
    selected_shots = shots_model_df[shots_model_df['competition_name']==player_team_or_comp]
    comp_selected = 1

elif not shots_model_df[shots_model_df['team_name']==player_team_or_comp].empty:
    selected_shots = shots_model_df[shots_model_df['team_name']==player_team_or_comp]
    comp_selected = 0

elif not shots_model_df[shots_model_df['player_name']==player_team_or_comp].empty:
    selected_shots = shots_model_df[shots_model_df['player_name']==player_team_or_comp]    
    comp_selected = 0

else:
    selected_shots = pd.DataFrame()
    comp_selected = 0

# Individual dataframe for shots/headers/goals/no-goals etc.
selected_ground_shots = selected_shots[selected_shots['header_tag']==0]
selected_ground_goals = selected_ground_shots[selected_ground_shots['goal']==1]
selected_headers = selected_shots[selected_shots['header_tag']==1]
selected_headed_goals = selected_headers[selected_headers['goal']==1]

# Lowest xG goal
lowest_xg_goal = selected_shots[selected_shots['goal']==1].sort_values('xG').head(1)
highest_xg_miss = selected_shots[selected_shots['goal']==0].sort_values('xG', ascending=False).head(1)

# %% Plot shots

# Overwrite rcParams 
mpl.rcParams['xtick.color'] = "white"
mpl.rcParams['ytick.color'] = "white"
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10

# Plot pitch
pitch = VerticalPitch(half=True,pitch_color='#313332', line_color='white', linewidth=1, stripe=False)
fig, ax = pitch.grid(nrows=1, ncols=1, title_height = 0.03, grid_height=0.7, endnote_height=0.05, axis=False)
fig.set_size_inches(9, 7)
fig.set_facecolor('#313332')

# Plot ground shots
ax['pitch'].scatter(PITCH_WIDTH_Y/2 + selected_ground_shots['c_yards'], PITCH_LENGTH_X - selected_ground_shots['x_yards'], 
                    marker='h', s=200, alpha=0.2, c=selected_ground_shots['xG'], edgecolors='w',vmin=-0.04,vmax=0.4,cmap=plt.cm.inferno, zorder=2)
p1 = ax['pitch'].scatter(PITCH_WIDTH_Y/2 + selected_ground_goals['c_yards'], PITCH_LENGTH_X - selected_ground_goals['x_yards'], 
                    marker='h', s=200, c=selected_ground_goals['xG'], edgecolors='w', lw=2, vmin=-0.04,vmax=0.4,cmap=plt.cm.inferno, zorder=2)

# Plot headers
ax['pitch'].scatter(PITCH_WIDTH_Y/2 + selected_headers['c_yards'], PITCH_LENGTH_X - selected_headers['x_yards'], 
                    marker='o', s=200, alpha=0.2, c=selected_headers['xG'], edgecolors='w',vmin=-0.04,vmax=0.4,cmap=plt.cm.inferno, zorder=2)
ax['pitch'].scatter(PITCH_WIDTH_Y/2 + selected_headed_goals['c_yards'], PITCH_LENGTH_X - selected_headed_goals['x_yards'], 
                    marker='o', s=200, c=selected_headed_goals['xG'], edgecolors='w', lw=2, vmin=-0.04,vmax=0.4,cmap=plt.cm.inferno, zorder=2)

ax['pitch'].set_ylim([59.9,125])

# Plot highest xG miss and lowest xG goal chance
if lowest_xg_goal['header_tag'].values==1:
    lowxg_marker = 'o'
else:
    lowxg_marker = 'h'
if highest_xg_miss['header_tag'].values==1:
    highxg_marker = 'o'
else:
    highxg_marker = 'h'    
    
ax['pitch'].scatter(PITCH_WIDTH_Y/2 + highest_xg_miss['c_yards'], PITCH_LENGTH_X - highest_xg_miss['x_yards'], 
                    marker=highxg_marker, s=200, c='r', edgecolors='grey', lw = 2.5 ,vmin=-0.04,vmax=0.4,cmap=plt.cm.inferno, zorder=3)
ax['pitch'].scatter(PITCH_WIDTH_Y/2 + lowest_xg_goal['c_yards'], PITCH_LENGTH_X - lowest_xg_goal['x_yards'], 
                    marker=lowxg_marker, s=200, c='g', edgecolors='w', lw = 2.5 ,vmin=-0.04,vmax=0.4,cmap=plt.cm.inferno, zorder=3)


# Add colorbar
cb_ax = fig.add_axes([0.53, 0.107, 0.35, 0.03])
cbar = fig.colorbar(p1, cax=cb_ax, orientation='horizontal')
cbar.outline.set_edgecolor('w')
cbar.set_label(" xG", loc = "left", color='w', fontweight='bold', labelpad=-28.5)

# Manual legend
legend_ax = fig.add_axes([0.075, 0.07, 0.5, 0.08])
legend_ax.axis("off")
plt.xlim([0,5])
plt.ylim([0,1])
legend_ax.scatter(0.2, 0.7, marker='h', s=200, c='#313332', edgecolors='w')
legend_ax.scatter(0.2, 0.2, marker='o', s=200, c='#313332', edgecolors='w')
legend_ax.text(0.35, 0.61, "Foot", color="w")
legend_ax.text(0.35, 0.11, "Header", color="w")
legend_ax.scatter(1.3, 0.7, marker='h', s=200, c='purple', edgecolors='w', lw=2)
legend_ax.scatter(1.3, 0.2, marker='h', alpha=0.2, s=200, c='purple', edgecolors='w')
legend_ax.text(1.45, 0.61, "Goal", color="w")
legend_ax.text(1.465, 0.11, "No Goal", color="w")
legend_ax.scatter(2.4, 0.7, marker='h', s=200, c='g', edgecolors='w', lw=2.5)
legend_ax.scatter(2.4, 0.2, marker='h', s=200, c='r', edgecolors='grey', lw=2.5)
legend_ax.text(2.55, 0.61, "Lowest xG Goal", color="w")
legend_ax.text(2.565, 0.11, "Highest xG Miss", color="w")

# Title text
subtitle_text = f"{selected_shots['competition_name'].unique()[0]}"
subsubtitle_text = "2017-2018"
if comp_selected == 1:
    title_text = "Expected Goals"
elif comp_selected == 0:
    title_text = f"{player_team_or_comp} Expected Goals"

fig.text(0.18,0.92, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.18,0.883, subtitle_text, fontweight="regular", fontsize=14, color='w')
fig.text(0.18,0.852, subsubtitle_text, fontweight="regular", fontsize=10, color='w')
    

# Stats
if selected_shots['goal'].sum()-selected_shots.sum()['xG'] > 0:
    sign = '+'
else:
    sign=''
    
fig.text(0.65,0.925, "Shots:", fontweight="bold", fontsize=10, color='w')
fig.text(0.65,0.9, "xG:", fontweight="bold", fontsize=10, color='w')
fig.text(0.65,0.875, "Goals:", fontweight="bold", fontsize=10, color='w')
fig.text(0.65,0.85, "xG Perf:", fontweight="bold", fontsize=10, color='w')
fig.text(0.73,0.925, f"{int(selected_shots.count()[0])}", fontweight="regular", fontsize=10, color='w')
fig.text(0.73,0.9, f"{round(selected_shots.sum()['xG'],1)}", fontweight="regular", fontsize=10, color='w')
fig.text(0.73,0.875, f"{int(selected_shots['goal'].sum())}", fontweight="regular", fontsize=10, color='w')
fig.text(0.73,0.85, f"{sign}{int(round(100*(selected_shots['goal'].sum()-selected_shots.sum()['xG'])/selected_shots.sum()['xG'],0))}%", fontweight="regular", fontsize=10, color='w')

fig.text(0.79,0.927, "xG/shot:", fontweight="bold", fontsize=10, color='w')
fig.text(0.79,0.9, "Goal/shot:", fontweight="bold", fontsize=10, color='w')
fig.text(0.79,0.875, "L xG Goal:", fontweight="bold", fontsize=10, color='w')
fig.text(0.79,0.85, "H xG Miss:", fontweight="bold", fontsize=10, color='w')
fig.text(0.89,0.925, f"{round(selected_shots.sum()['xG']/selected_shots.count()[0],2)}", fontweight="regular", fontsize=10, color='w')
fig.text(0.89,0.9, f"{round(selected_shots['goal'].sum()/selected_shots.count()[0],2)}", fontweight="regular", fontsize=10, color='w')
fig.text(0.89,0.875, f"{round(lowest_xg_goal['xG'].values[0],2)}", fontweight="regular", fontsize=10, color='w')
fig.text(0.89,0.85, f"{round(highest_xg_miss['xG'].values[0],2)}", fontweight="regular", fontsize=10, color='w')


# Footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari. Data provided by Wyscout.com",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add WC Logo
ax = fig.add_axes([0.02,0.8,0.2,0.2])
ax.axis("off")
response = requests.get(logo)
img = Image.open(BytesIO(response.content))
ax.imshow(img)
