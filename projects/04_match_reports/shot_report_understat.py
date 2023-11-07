# %% Create plot of shot positions and associated xG for a game, based on understat data
#
# Inputs:   Year to plot data from
#           League to plot data from
#           Home team
#           Away team
#           
# Outputs:  Plot of shot positions and associated xG
#

# %% Imports and parameters

from understatapi import UnderstatClient
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from mplsoccer.pitch import VerticalPitch
import os
import sys
from PIL import Image

PITCH_WIDTH_Y = 100
PITCH_LENGTH_X = 100

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.logos_and_badges as lab

# %% Function definitions


def protected_divide(n, d):
    return n / d if d else 0


# %% User inputs

# Select year
year = '2022'

# Select league (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
league = 'EPL'

# Select team codes
home_team = 'Liverpool'
away_team = 'Bournemouth'

# Team name to print
home_team_print = None
away_team_print = None

# %% Logos and printed names

home_logo, _ = lab.get_team_badge_and_colour(home_team)
away_logo, _ = lab.get_team_badge_and_colour(away_team)

if home_team_print is None:
    home_team_print = home_team

if away_team_print is None:
    away_team_print = away_team

# %% Get data

# Get match data
understat = UnderstatClient()
match_data = understat.league(league=league).get_match_data(season=year)

# Format match data
match_df = pd.DataFrame(match_data).set_index('id')

# Get ID for chosen match
selected_match = match_df[
    (match_df['h'].apply(lambda x: x['title']) == home_team) & (match_df['a'].apply(lambda x: x['title']) == away_team)]

# Get shot data
shot_data = understat.match(match=selected_match.index[0]).get_shot_data()

# Format shot data
shots_df = (pd.concat([pd.DataFrame(shot_data['h']), pd.DataFrame(shot_data['a'])]).set_index('id')
            .astype(
    {'minute': 'float', 'X': 'float', 'Y': 'float', 'xG': 'float', 'h_goals': 'float', 'a_goals': 'float'}))

# Get player data
player_data = understat.match(match=selected_match.index[0]).get_roster_data()

# %% Process data

for idx, shot in shots_df.iterrows():
    if shot['result'] == 'OwnGoal':
        shots_df.loc[idx, 'X'] = 1 - shot['X']
        shots_df.loc[idx, 'Y'] = 1 - shot['Y']

    if len(shot['player'].split(' ')) == 1:
        shots_df.loc[idx, 'player_initials'] = shot['player'].split(' ')[0][0:2]
    else:
        shots_df.loc[idx, 'player_initials'] = shot['player'].split(' ')[0][0].upper() + shot['player'].split(' ')[1][0].upper()

# %% Calculate shot stats

# Home team stats
home_shots = len((shots_df[(shots_df['h_a'] == 'h') & (shots_df['result'] != 'OwnGoal')]))
home_xg_shot = round(
    protected_divide(float(selected_match['xG'].apply(lambda x: x['h'])[0]), len(shots_df[shots_df['h_a'] == 'h'])), 2)
home_goal_shot = round(
    protected_divide(int(selected_match['goals'].apply(lambda x: x['h'])[0]), len(shots_df[shots_df['h_a'] == 'h'])), 2)
home_xg_perf = round(
    int(selected_match['goals'].apply(lambda x: x['h'])[0]) - float(selected_match['xG'].apply(lambda x: x['h'])[0]), 2)
if len(shots_df[(shots_df['h_a'] == 'h') & (shots_df['result'] == 'Goal')]) == 0:
    home_low_xg_goal = '-'
else:
    home_low_xg_goal = round(min(shots_df[(shots_df['h_a'] == 'h') & (shots_df['result'] == 'Goal')]['xG']), 2)
if len(shots_df[(shots_df['h_a'] == 'h') & (shots_df['result'] != 'Goal')]) == 0:
    home_high_xg_miss = '-'
else:
    home_high_xg_miss = round(max(shots_df[(shots_df['h_a'] == 'h') & (shots_df['result'] != 'Goal')]['xG']), 2)

# Away team stats
away_shots = len((shots_df[(shots_df['h_a'] == 'a') & (shots_df['result'] != 'OwnGoal')]))
away_xg_shot = round(
    protected_divide(float(selected_match['xG'].apply(lambda x: x['a'])[0]), len(shots_df[shots_df['h_a'] == 'a'])), 2)
away_goal_shot = round(
    protected_divide(int(selected_match['goals'].apply(lambda x: x['a'])[0]), len(shots_df[shots_df['h_a'] == 'a'])), 2)
away_xg_perf = round(
    int(selected_match['goals'].apply(lambda x: x['a'])[0]) - float(selected_match['xG'].apply(lambda x: x['a'])[0]), 2)
if len(shots_df[(shots_df['h_a'] == 'a') & (shots_df['result'] == 'Goal')]) == 0:
    away_low_xg_goal = '-'
else:
    away_low_xg_goal = round(min(shots_df[(shots_df['h_a'] == 'a') & (shots_df['result'] == 'Goal')]['xG']), 2)
if len(shots_df[(shots_df['h_a'] == 'a') & (shots_df['result'] != 'Goal')]) == 0:
    away_high_xg_miss = '-'
else:
    away_high_xg_miss = round(max(shots_df[(shots_df['h_a'] == 'a') & (shots_df['result'] != 'Goal')]['xG']), 2)

if home_xg_perf > 0:
    h_sign = '+'
else:
    h_sign = ''
if away_xg_perf > 0:
    a_sign = '+'
else:
    a_sign = ''

# %% Plot shots

# Overwrite rcparams
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'

# Plot pitch
pitch = VerticalPitch(half=True, pitch_color='#313332', line_color='white', linewidth=1, pitch_type = 'opta', stripe=False)
fig, ax = pitch.grid(nrows=1, ncols=2, title_height=0.03, grid_height=0.51, endnote_height=0, axis=False)
fig.set_size_inches(12, 7)
fig.set_facecolor('#313332')

# Determine pitch axis limits
min_x = PITCH_LENGTH_X * shots_df['X'].min()
min_y = PITCH_WIDTH_Y * min(shots_df['Y'].min(), shots_df['Y'].max())
plot_xlim = PITCH_LENGTH_X * 0.625
plot_ylim = PITCH_WIDTH_Y * 1/12

# Apply pitch axis limits
ax['pitch'][0].set_xlim((plot_ylim, PITCH_WIDTH_Y - plot_ylim))
ax['pitch'][0].set_ylim((plot_xlim, PITCH_LENGTH_X))
ax['pitch'][1].set_xlim((plot_ylim, PITCH_WIDTH_Y - plot_ylim))
ax['pitch'][1].set_ylim((plot_xlim, PITCH_LENGTH_X))

# Show pitch borders
for axis in ['left', 'right', 'bottom']:
    ax['pitch'][0].spines[axis].set_visible(True)
    ax['pitch'][0].spines[axis].set_color('grey')
    ax['pitch'][1].spines[axis].set_visible(True)
    ax['pitch'][1].spines[axis].set_color('grey')

# Plot each shot
for _, shot in shots_df.iterrows():

    # Determine pitch to plot on
    pitch_num = None
    if shot['h_a'] == 'h':
        pitch_num = 0
    elif shot['h_a'] == 'a':
        pitch_num = 1

    # Marker based on type of shot
    if shot['shotType'] == 'Head':
        marker = 'o'
        s = 250
        s_delta = 150
    elif shot['situation'] in ['DirectFreeKick', 'Penalty']:
        marker = 's'
        s = 175
        s_delta = 125
    else:
        marker = 'h'
        s = 300
        s_delta = 150

    # Opacity, line colour and line width based on result
    alpha = 1
    lw = 1
    edgecolors = 'w'
    edgecolor_g = 'w'
    fontweight = 'regular'
    zorder = 1
    if shot['result'] == 'Goal':
        lw = 1.5
        alpha = 1
        edgecolors = 'w'
        edgecolor_g = 'w'
        fontweight = 'bold'
        zorder = 4
        s -= 25
        if shot['xG'] <= 0.05:
            edgecolor_g = 'lime'
    elif shot['result'] == 'OwnGoal':
        pitch_num = abs(pitch_num - 1)
        lw = 1.5
        alpha = 1
        edgecolors = 'w'
        fontweight = 'bold'
        zorder = 4
    elif shot['result'] in ['MissedShots', 'BlockedShot']:
        lw = 0.5
        alpha = 1
        edgecolors = 'darkgrey'
        fontweight = 'regular'
        zorder = 1
        if shot['xG'] >= 0.6:
            edgecolors = 'crimson'
            lw = 2
    elif shot['result'] in ['SavedShot', 'ShotOnPost']:
        lw = 1.5
        alpha = 1
        edgecolors = 'darkgrey'
        fontweight = 'regular'
        zorder = 2
        if shot['xG'] >= 0.6:
            edgecolors = 'crimson'

    if shot['xG'] >= 0.7:
        textcolor = 'k'
    else:
        textcolor = 'w'

    # Draw point    
    p1 = ax['pitch'][pitch_num].scatter(PITCH_WIDTH_Y * (1 - shot['Y']), PITCH_LENGTH_X * (shot['X']),
                                        marker=marker, s=s, alpha=alpha, c=shot['xG'], lw=lw, edgecolors=edgecolors,
                                        vmin=-0.04, vmax=1, cmap=plt.cm.inferno, zorder=zorder)
    # Draw cross if goal
    if shot['result'] == 'OwnGoal':
        ax['pitch'][pitch_num].scatter(PITCH_WIDTH_Y * (1 - shot['Y']), PITCH_LENGTH_X * (shot['X']),
                                       marker=marker, s=s, alpha=alpha, c='darkslategrey', lw=lw, edgecolors=edgecolors,
                                       zorder=zorder)

    # Draw double outline if goal
    if shot['result'] == 'Goal':
        ax['pitch'][pitch_num].scatter(PITCH_WIDTH_Y * (1 - shot['Y']), PITCH_LENGTH_X * (shot['X']),
                                       marker=marker, s=s + s_delta, alpha=1, c='#313332', edgecolors=edgecolor_g,
                                       vmin=-0.04, vmax=1, cmap=plt.cm.inferno, zorder=zorder - 1)

    ax['pitch'][pitch_num].text(PITCH_WIDTH_Y * (1 - shot['Y']), PITCH_LENGTH_X * (shot['X']) - 0.1,
                                shot['player_initials'], color=textcolor, fontsize=7, ha='center', va='center',
                                fontweight=fontweight, zorder=zorder)

# Home stats text
fig.text(0.07, 0.27, "Shots:", fontweight="bold", fontsize=10, color='w')
fig.text(0.07, 0.241, "xG/shot:", fontweight="bold", fontsize=10, color='w')
fig.text(0.17, 0.27, "Goals/shot:", fontweight="bold", fontsize=10, color='w')
fig.text(0.17, 0.24, "xG Performance:", fontweight="bold", fontsize=10, color='w')
fig.text(0.34, 0.27, "L. xG Goal:", fontweight="bold", fontsize=10, color='w')
fig.text(0.34, 0.24, "H. xG Miss:", fontweight="bold", fontsize=10, color='w')
fig.text(0.13, 0.27, home_shots, fontweight="regular", fontsize=10, color='w')
fig.text(0.13, 0.24, home_xg_shot, fontweight="regular", fontsize=10, color='w')
fig.text(0.287, 0.27, home_goal_shot, fontweight="regular", fontsize=10, color='w')
fig.text(0.285, 0.24, f"{h_sign}{home_xg_perf}", fontweight="regular", fontsize=10, color='w')
fig.text(0.42, 0.27, home_low_xg_goal, fontweight="regular", fontsize=10, color='w')
fig.text(0.42, 0.24, home_high_xg_miss, fontweight="regular", fontsize=10, color='w')

# Away stats text
fig.text(0.554, 0.27, "Shots:", fontweight="bold", fontsize=10, color='w')
fig.text(0.554, 0.241, "xG/shot:", fontweight="bold", fontsize=10, color='w')
fig.text(0.654, 0.27, "Goals/shot:", fontweight="bold", fontsize=10, color='w')
fig.text(0.654, 0.24, "xG Performance:", fontweight="bold", fontsize=10, color='w')
fig.text(0.824, 0.27, "L. xG Goal:", fontweight="bold", fontsize=10, color='w')
fig.text(0.824, 0.24, "H. xG Miss:", fontweight="bold", fontsize=10, color='w')
fig.text(0.614, 0.27, away_shots, fontweight="regular", fontsize=10, color='w')
fig.text(0.614, 0.24, away_xg_shot, fontweight="regular", fontsize=10, color='w')
fig.text(0.771, 0.27, away_goal_shot, fontweight="regular", fontsize=10, color='w')
fig.text(0.769, 0.24, f"{a_sign}{away_xg_perf}", fontweight="regular", fontsize=10, color='w')
fig.text(0.904, 0.27, away_low_xg_goal, fontweight="regular", fontsize=10, color='w')
fig.text(0.904, 0.24, away_high_xg_miss, fontweight="regular", fontsize=10, color='w')

# Add colorbar
cb_ax = fig.add_axes([0.57, 0.152, 0.35, 0.03])
cbar = fig.colorbar(p1, cax=cb_ax, orientation='horizontal')
cbar.outline.set_edgecolor('w')
cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5)

# Add manual legend
legend_ax = fig.add_axes([0.055, 0.065, 0.5, 0.14])
legend_ax.axis("off")
plt.xlim([0, 5])
plt.ylim([0, 1])

legend_ax.scatter(0.2, 0.8, marker='h', s=300, c='#313332', edgecolors='w')
legend_ax.scatter(0.2, 0.5, marker='o', s=250, c='#313332', edgecolors='w')
legend_ax.scatter(0.2, 0.2, marker='s', s=150, c='#313332', edgecolors='w')
legend_ax.text(0.37, 0.74, "Foot", color="w")
legend_ax.text(0.37, 0.44, "Header", color="w")
legend_ax.text(0.37, 0.14, "Set-Piece", color="w")

legend_ax.scatter(1.3, 0.8, marker='h', s=250, c='indigo', edgecolors='w', lw=1.5, zorder=2)
legend_ax.scatter(1.3, 0.8, marker='h', s=400, c='#313332', edgecolors='w', zorder=1)
legend_ax.scatter(1.3, 0.5, marker='h', s=300, c='indigo', edgecolors='darkgrey', lw=1.5, alpha=1)
legend_ax.scatter(1.3, 0.2, marker='h', s=300, c='indigo', edgecolors='darkgrey', lw=0.5, alpha=1)
legend_ax.text(1.47, 0.74, "Goal", color="w")
legend_ax.text(1.47, 0.44, "Saved or Woodwork", color="w")
legend_ax.text(1.47, 0.14, "Missed or Blocked", color="w")

legend_ax.scatter(3, 0.8, marker='h', s=300, c='darkslategrey', edgecolors='w', lw=1.5, alpha=1)
legend_ax.scatter(3, 0.5, marker='h', s=250, c='indigo', edgecolors='w', lw=1.5, zorder=2)
legend_ax.scatter(3, 0.5, marker='h', s=400, c='#313332', edgecolors='lime', zorder=1)
legend_ax.scatter(3, 0.2, marker='h', s=300, c='y', edgecolors='crimson', lw=1.5, alpha=1)
legend_ax.text(3.17, 0.74, "Own Goal", color="w")
legend_ax.text(3.17, 0.44, "Low xG (<0.05) Goal", color="w")
legend_ax.text(3.17, 0.14, "High xG (>0.60) Miss", color="w")

# Title text
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge'}
title_text = f"{leagues['EPL']} - {year}/{int(year) + 1}"
subtitle_text = f"{home_team_print} {selected_match['goals'].apply(lambda x: x['h'])[0]}-{selected_match['goals'].apply(lambda x: x['a'])[0]} {away_team_print}"
subsubtitle_text = f"Expected Goals: {round(float(selected_match['xG'].apply(lambda x: x['h'])[0]), 2)} - {round(float(selected_match['xG'].apply(lambda x: x['a'])[0]), 2)}"

fig.text(0.5, 0.89, title_text, ha='center', fontweight="bold", fontsize=20, color='w')
fig.text(0.5, 0.835, subtitle_text, ha='center', fontweight="bold", fontsize=18, color='w')
fig.text(0.5, 0.79, subsubtitle_text, ha='center', fontweight="regular", fontsize=14, color='w')

# Add home team Logo
ax = fig.add_axes([0.175, 0.783, 0.15, 0.15])
ax.axis("off")
ax.imshow(home_logo)

# Add away team Logo
ax = fig.add_axes([0.665, 0.783, 0.15, 0.15])
ax.axis("off")
ax.imshow(away_logo)

# Footer text
fig.text(0.5, 0.02, "Created by Jake Kolliari (@_JKDS_). Data provided by Understat.com",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.902, 0.01, 0.06, 0.06])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save image
fig.savefig(f"shot_reports/{league}-{selected_match['datetime'][0][0:10]}-{home_team}-{away_team}", dpi=300)
