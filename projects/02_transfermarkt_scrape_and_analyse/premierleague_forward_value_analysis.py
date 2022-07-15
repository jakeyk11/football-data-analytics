# %% Analysis of transfermarkt data for Premier League players in 2021-22.
#
# Inputs:   Single dataframe of transfermarkt player information as .pbz2 compressed pickle
#           League name string to appear in plot titles
#           URL for logo of league to be plotted
#           Selection of whether to tag player names in plots or not
#           Minimum goal contributions required to feature in plots.
#
# Outputs:  Scouting tool - scatter plot of cost per goal contribution against age, with player more likely to
#           transfer highlighted.
#           Scatter plot of goal contributions vs. market value, with linear regression model fit
#           Assessment of statistical model that predicts market value of a player using simple metrics (age, goals,
#           assists, team position, etc.)
#           Value league table - bar plot of league table, showing squad values and over/underperformance based on
#           value.
#
# Notes: None

# %% Imports

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import collections
import highlight_text as htext
from sklearn.linear_model import LinearRegression
from sklearn import model_selection
from sklearn.preprocessing import StandardScaler
from sklearn import metrics
import requests
from PIL import Image
from io import BytesIO
import pickle
import bz2
import adjustText

# %% User Inputs

# CSV file name corresponding to chosen league
filename = 'transfermarkt_GB1_2021-2022.pbz2'
playerinfo_df = bz2.BZ2File(f"../../data_directory/transfermarkt_data/{filename}", 'rb')
playerinfo_df = pickle.load(playerinfo_df)

# Manual league input for plot titles
league = "Premier League"

# Manual URL containing league logo for plot titles
logo_url = 'https://www.fifplay.com/img/public/premier-league-2-logo.png'

# Turn on or off manual player tags on plots (default off=False)
player_tags = True

# Set minimum number of goal contributions required from a player per season
min_contributions = 10

# %% Process player info and calculate additional parameters

# Player goal contributions
playerinfo_df['Goal_Contributions'] = playerinfo_df['Goals'] + playerinfo_df['Assists']

# Player goal contributions per £1m, and Cost per Goal Contribution (inverse)
playerinfo_df['GC_per_mGBP'] = round(playerinfo_df['Goal_Contributions'] / playerinfo_df['Market_Value'], 2)
playerinfo_df['mGBP_per_GC'] = 1 / playerinfo_df['GC_per_mGBP']

# Player goal contributions per £1m, and Cost per Goal Contribution (inverse)
playerinfo_df['Delta_Value'] = playerinfo_df['Market_Value'] - playerinfo_df['Prev_Market_Value']

# %% Use player information to calculate team totals

# Create basic league table dictionary
team_table = collections.defaultdict()
for i, team in enumerate(playerinfo_df.Team.unique()):
    team_table[team] = i + 1

# Sum and mean player info for each team
teaminfo_sum = playerinfo_df.groupby(["Team"]).sum().reset_index()[["Team", "Goals", "Assists", "Yellows",
                                                                    "Sec_Yellows", "Reds", "Goal_Contributions"]]
teaminfo_mean = playerinfo_df.groupby(["Team"]).mean().reset_index()[["Team", "Mean_Market_Val", "Tot_Market_Val"]]
teaminfo_df = teaminfo_sum.merge(teaminfo_mean, on="Team")

# Use league table dictionary to define league position of each team
teaminfo_df['League_Position'] = teaminfo_df['Team'].apply(lambda x: team_table[x])
teaminfo_df.sort_values("League_Position", ascending=True, inplace=True)

# Rank teams by total squad value, and calculate difference between value rank and league position
teaminfo_df["Value_Rank"] = teaminfo_df["Tot_Market_Val"].rank(method="min", ascending=False)
teaminfo_df['Value_Pos_Delta'] = teaminfo_df['Value_Rank'] - teaminfo_df['League_Position']

# %% Assign team information to player dataframe

# Assign league position of team to each player row
playerinfo_df['Team_Position'] = playerinfo_df['Team'].apply(lambda x: team_table[x])

# Assign goal contributions of team to each player row
playerinfo_df['Team_GC'] = playerinfo_df['Team'].apply(
    lambda x: teaminfo_df[teaminfo_df['Team'] == x]['Goal_Contributions'].item())

# Player goal contributions as a % of team total 
playerinfo_df['Percent_GC'] = 100 * playerinfo_df['Goal_Contributions'] / playerinfo_df['Team_GC']

# %% Define and select forwards only

# Only include forwards (as Goal contribution data has less meaning for Mids and Defenders)
forwards = ['Attacking Midfield', 'Centre-Forward', 'Left Winger', 'Right Winger']
forwardinfo_df = playerinfo_df[playerinfo_df['Position'].isin(forwards)]

# Combine Right and Left Wingers to one position (copy warning supressed after ensuring no impact)
pd.options.mode.chained_assignment = None
forwardinfo_df.loc[forwardinfo_df["Position"].str.contains("Winger"), "Position"] = "Winger"
forwardinfo_df.loc[forwardinfo_df["Position"].str.contains("Striker"), "Position"] = "Centre-Forward"

# Only include forwards that have an estimated market value
forwardinfo_df = forwardinfo_df[forwardinfo_df['Market_Value'].notna()]

# %% Filter forwards dataframe based on user inputs & other parameters

# Only include forwards with at least 20 appearances (includes substitute appearances)
forwardinfo_df = forwardinfo_df[forwardinfo_df['In_XI'] >= 20]

# Only include forwards with more than the min. user-defined contributions
successforward_df = forwardinfo_df[forwardinfo_df['Goal_Contributions'] >= min_contributions]

# %% Define plot formatting parameters

# Overwrite rcParams 
mpl.rcParams['xtick.color'] = "white"
mpl.rcParams['ytick.color'] = "white"
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10

# Define colours
text_color = "w"
subtle_text_color = "#C1CDCD"
background = "#313332"
filler = "grey"
primary = "red"

# %% Use Case 1: Scouting tool - assessing cost per goal contribution against age

# Find players belonging to relegated teams and players with expiring contracts
rel_fwds = successforward_df[successforward_df['Team_Position'] >= 22]
low_contract = successforward_df[successforward_df['Contract_End_YY'] <= 2022]

# Set-up scatter plot showing Goal_Contributions vs. Market_Value
fig, ax = plt.subplots(figsize=(8.5, 8.5))
fig.set_facecolor(background)
ax.patch.set_alpha(0)

# Plot data
ax.grid(ls="dotted", lw="0.5", color="lightgrey", zorder=1)
ax.scatter(successforward_df['Age'], successforward_df['GC_per_mGBP'], s=80, color=filler,
           edgecolors=background, alpha=0.4, lw=0.5, zorder=2)
ax.scatter(rel_fwds['Age'], rel_fwds['GC_per_mGBP'], s=80, color='r',
           edgecolors=background, alpha=1, lw=0.5, zorder=3)
ax.scatter(low_contract['Age'], low_contract['GC_per_mGBP'], s=80, color='r',
           edgecolors=background, alpha=1, lw=0.5, zorder=3)

# Find players of interest and tag (if player_tags=True)
text = list()
if player_tags:
    for player in successforward_df['Name'].values:
        xpos = successforward_df[successforward_df['Name'] == player]['Age']
        ypos = successforward_df[successforward_df['Name'] == player]['GC_per_mGBP']
        if ypos.values[0]/xpos.values[0] >= 0.3: 
            if (player in rel_fwds['Name'].values) or (player in low_contract['Name'].values):
                colour = text_color
            else:
                colour = filler
            tag = player
            text.append(ax.text(xpos.values[0]+0.02, ypos.values[0]+0.02, tag, color=colour, fontsize=8, ha="left",
                                zorder=3))
            
adjustText.adjust_text(text)

# Define axes
ax.set_xlabel("Age (Years)", fontweight="bold", fontsize=14, color=text_color)
ax.set_ylabel("Goal Contributions per £m player value", fontweight="bold", fontsize=14, color=text_color)
x_min = successforward_df['Age'].min() - 2 if (successforward_df['Age'].min() % 2) == 0 else successforward_df[
                                                                                                 'Age'].min() - 1
x_max = successforward_df['Age'].max() + 1
ax.set_xlim(x_min, x_max)
plt.xticks(np.arange(x_min, x_max + 1, 2))

# Create title
title_text = f"{league} {filename.split('_')[2].replace('.pbz2', '')}"
subtitle_text = "A view of Goal Contributions per £m player value"
subsubtitle_text = "Players with increased transfer probability <highlighted>"
side_text = f"Only players with {min_contributions} or\nmore goal contributions\nare shown. Players of\ninterest are tagged, with\nincreased transfer prob.\ndefined as player whose\ncontract expires this year\nor player whose club got\nrelegated this year."
fig.text(0.15, 0.95, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.15, 0.915, subtitle_text, fontweight="regular", fontsize=14, color='w')
htext.fig_text(0.15, 0.895, s=subsubtitle_text, fontweight="regular", fontsize=12,
               color=text_color, highlight_textprops=[{"color": 'r', "fontweight": 'bold'}])
fig.text(0.76, 0.865, side_text, fontweight="regular", fontsize=8, color='w')

# Add Championship Logo
ax2 = fig.add_axes([0.04, 0.87, 0.1, 0.1])
ax2.axis("off")
response = requests.get(logo_url)
img = Image.open(BytesIO(response.content))
ax2.imshow(img)

# Create footer
fig.text(0.28, 0.02, "Created by Jake Kolliari. Data provided by Transfermarkt.co.uk",
         fontstyle="italic", fontsize=9, color=text_color)  # Credit text

plt.tight_layout(rect=[0.03, 0.06, 0.95, 0.86])

# %% Use Case 2: Create a simple set of linear regression models for visualisation of Goal Contributions vs. Market
# Value

# Break down into seperate df's by position
Wing_df = forwardinfo_df[forwardinfo_df['Position'] == 'Winger']
CF_df = forwardinfo_df[forwardinfo_df['Position'] == 'Centre-Forward']
CAM_df = forwardinfo_df[forwardinfo_df['Position'] == 'Attacking Midfield']

y_W = Wing_df['Market_Value']
X_W = Wing_df[['Goal_Contributions']]
y_CF = CF_df['Market_Value']
X_CF = CF_df[['Goal_Contributions']]
y_CAM = CAM_df['Market_Value']
X_CAM = CAM_df[['Goal_Contributions']]

# Fit models
W_LinModel = LinearRegression(fit_intercept=False)
CF_LinModel = LinearRegression(fit_intercept=False)
CAM_LinModel = LinearRegression(fit_intercept=False)
W_LinModel.fit(X_W, y_W)
CF_LinModel.fit(X_CF, y_CF)
CAM_LinModel.fit(X_CAM, y_CAM)

# Predictions and metrics
X = np.linspace(0, 60, 35).reshape(-1, 1)
yPred_W = W_LinModel.predict(X)
yPred_CF = CF_LinModel.predict(X)
yPred_CAM = CAM_LinModel.predict(X)

# Set-up scatter plot showing Goal_Contributions vs. Market_Value
fig, ax = plt.subplots(figsize=(8.5, 8.5))
fig.set_facecolor(background)
ax.patch.set_alpha(0)

# Plot data and models
ax.grid(ls="dotted", lw="0.5", color="lightgrey", zorder=1)
ax.scatter(X_W, y_W, s=80, color='y', edgecolors=background, alpha=0.4,
           lw=0.5, zorder=2)
ax.scatter(X_CF, y_CF, s=80, color='r', edgecolors=background, alpha=0.4,
           lw=0.5, zorder=3)
ax.scatter(X_CAM, y_CAM, s=80, color='m', edgecolors=background, alpha=0.4,
           lw=0.5, zorder=4)
ax.plot(X, yPred_W, color='y', zorder=5)
ax.plot(X, yPred_CF, color='r', zorder=5)
ax.plot(X, yPred_CAM, color='m', zorder=5)

# Define axes
ax.set_xlabel("Goal Contributions", fontweight="bold", fontsize=14, color=text_color)
ax.set_ylabel("Market Value (£m)", fontweight="bold", fontsize=14, color=text_color)
xlim = successforward_df['Goal_Contributions'].max() + 1
ylim = np.ceil(successforward_df['Market_Value'].max()) + 0.5
ax.set_xlim(0, xlim)
ax.set_ylim(0, ylim)

# Create title
title_text = f"{league} {filename.split('_')[2].replace('.pbz2', '')}"
subtitle_text = "Goal Contributions vs. Market Value for <Attacking Midfielders>,\n   <Wingers> and <Centre Forwards>"
fig.text(0.15, 0.95, title_text, fontweight="bold", fontsize=16, color='w')
htext.fig_text(0.15, 0.93, s=subtitle_text, fontweight="regular", fontsize=14,
               color=text_color, highlight_textprops=[{"color": 'm', "fontweight": 'bold'},
                                                      {"color": 'y', "fontweight": 'bold'},
                                                      {"color": 'r', "fontweight": 'bold'}])

# Find players of interest and tag (if player_tags=True)
text = list()
if player_tags:
    for player in successforward_df['Name'].values:
        xpos = playerinfo_df[playerinfo_df['Name'] == player]['Goal_Contributions']
        ypos = playerinfo_df[playerinfo_df['Name'] == player]['Market_Value']
        if xpos.values[0] >= np.percentile(forwardinfo_df['Goal_Contributions'],
                                           80) or ypos.values[0] >= np.percentile(forwardinfo_df['Market_Value'], 80):
            tag = player
            text.append(ax.text(xpos.values[0]+0.02, ypos.values[0]+0.02, tag, color=subtle_text_color, fontsize=8,
                                ha="left", zorder=6))
            
adjustText.adjust_text(text)

# Add Championship Logo
ax2 = fig.add_axes([0.04, 0.87, 0.1, 0.1])
ax2.axis("off")
response = requests.get(logo_url)
img = Image.open(BytesIO(response.content))
ax2.imshow(img)

# Create footer
fig.text(0.28, 0.02, "Created by Jake Kolliari. Data provided by Transfermarkt.co.uk",
         fontstyle="italic", fontsize=9, color=text_color)

fig.tight_layout(rect=[0.03, 0.06, 0.95, 0.86])

# %% Use Case 3: Can we predict market value using simple metrics? Create a full model that models market value

# Encode categorical position
forwardInfo_modeldf = pd.get_dummies(data=forwardinfo_df, columns=['Position'])

y = forwardInfo_modeldf['Market_Value']
X = forwardInfo_modeldf[['Goals', 'Assists', 'Team_Position', 'In_XI', 'Age',
                         'Position_Attacking Midfield', 'Position_Centre-Forward',
                         'Position_Winger']]

# Scale/normalise data
scaler = StandardScaler()
scaler.fit(X)
X_scaled = pd.DataFrame(scaler.transform(X), columns=X.columns)

# Create test and train data
X_train, X_test, y_train, y_test = model_selection.train_test_split(X_scaled, y, test_size=0.2)

# Fit model to training data
dValue_LinModel = LinearRegression()
dValue_LinModel.fit(X_train, y_train)

# Predict on test data and evaluate
test_predictions = dValue_LinModel.predict(X_test)
explained_variance = metrics.explained_variance_score(y_test, test_predictions)
mean_absolute_error = metrics.mean_absolute_error(y_test, test_predictions)
mse = metrics.mean_squared_error(y_test, test_predictions)
r2 = metrics.r2_score(y_test, test_predictions)

# Very low R2 results suggests, on first look, it is difficult to approximate player change in market value
# based on goals, assists, position, appearances etc. using a linear regression model. Further work required
# to conclude with certainty.

# %% Use Case 4: Bar chart of team position against team value

teaminfo_df["Team_Pos_Str"] = teaminfo_df["Team"] + ': ' + teaminfo_df["League_Position"].astype(str)

# Set-up bar plot showing team position vs. total value
fig, ax = plt.subplots(figsize=(8.5, 8.5))
fig.set_facecolor(background)
ax.patch.set_alpha(0)

# Define and add colour
my_cmap = plt.get_cmap("seismic_r")
color_scale = (teaminfo_df['Value_Pos_Delta'] +
               teaminfo_df['League_Position'].max())/(2*teaminfo_df['League_Position'].max())

# Plot data
ax.barh(teaminfo_df["Team_Pos_Str"], teaminfo_df["Tot_Market_Val"], color=my_cmap(color_scale))

# Create title
title_text = f"{league} {filename.split('_')[2].replace('.pbz2', '')}"
subtitle_text = "League Table (exc. Points Deductions) including Squad Values"
subsubtitle_text = "Coloured by <Value Under-performance> / <Value Over-performance>"
fig.text(0.15, 0.95, title_text, fontweight="bold", fontsize=16, color='w')
fig.text(0.15, 0.92, subtitle_text, fontweight="regular", fontsize=14, color='w')
htext.fig_text(0.15, 0.905, s=subsubtitle_text, fontweight="regular", fontsize=12,
               color=text_color, highlight_textprops=[{"color": 'lightcoral', "fontweight": 'bold'},
                                                      {"color": 'cornflowerblue', "fontweight": 'bold'}])

# Define axes
ax.set_xlabel("Squad Value (£m)", fontweight="bold", fontsize=14, color=text_color)
ax.set_ylim(-0.5, teaminfo_df['League_Position'].max()-0.5)
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_color('w')
plt.gca().invert_yaxis()

# Add axes labels
for idx, plot_pos in enumerate(np.arange(0.2, teaminfo_df['League_Position'].max())):
    if idx == teaminfo_df['League_Position'].max()-1 or idx == 0:
        value_str = "Value Rank = "
    else:
        value_str = ""
    text_team = teaminfo_df[teaminfo_df['League_Position'] == idx+1]
    ax.text(text_team['Tot_Market_Val']+1, plot_pos, value_str + str(int(text_team['Value_Rank'].values[0])), color='w')

# Add Championship Logo
ax2 = fig.add_axes([0.04, 0.87, 0.1, 0.1])
ax2.axis("off")
response = requests.get(logo_url)
img = Image.open(BytesIO(response.content))
ax2.imshow(img)

# Create footer
fig.text(0.28, 0.02, "Created by Jake Kolliari. Data provided by Transfermarkt.co.uk",
         fontstyle="italic", fontsize=9, color=text_color)

fig.tight_layout(rect=[0.03, 0.06, 0.95, 0.86])
