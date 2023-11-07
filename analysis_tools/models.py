"""Module containing a variety of predictive and statistical models relevant to the analysis of football data

Functions
---------
get_pass_clusters(events):
    Assign statsbomb or whoscored pass events to a pass cluster

simulate_match_outcome(events, matches, match_id, sim_count=10000):
    Simulate the outcome of a match based on teams xG


"""

import joblib
from sklearn.base import BaseEstimator, TransformerMixin
import os
import numpy as np
import pandas as pd


# Load custom classes that are required for model pipeline (done manually here for ease)
# noinspection PyPep8Naming
class convertYards(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X['x'] = X['x'] * (120 / 100)
        X['y'] = X['y'] * (80 / 100)
        X['endX'] = X['endX'] * (120 / 100)
        X['endY'] = X['endY'] * (80 / 100)
        return X


# noinspection PyPep8Naming
class customScaler(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        self.max_x = 120
        self.max_y = 80
        return self

    def transform(self, X, y=None):
        X['x'] = X['x'] / 120
        X['y'] = X['y'] / 120
        X['endX'] = X['endX'] / 120
        X['endY'] = X['endY'] / 120
        return X


def get_pass_clusters(events, data_mode='whoscored'):
    """ Assign statsbomb or whoscored pass events to a pass cluster

    Function that implements a pass clustering model, that has been trained on over 5,000,000 successful passes across
    EPL, Serie A, Ligue 1, Bundesliga, La Liga and EFLC (2019/20 - 2022/23), to assign passes to a pass cluster. Passes
    are assigned to their most similar cluster based on the start and end position of the pass. The function adds a
    cluster id and cluster centroid (x, y, end x, end y) to each pass.

    Args:
        events (pandas.DataFrame): dataframe of event data.
        data_mode (string, optional): 'whoscored' or 'statsbomb' data. Defaults to 'whoscored'.

    Returns:
        pandas.DataFrame: dataframe of passes with additional 'pass_cluster_id', 'pass_cluster_mean_x',
        'pass_cluster_mean_y', 'pass_cluster_mean_end_x' and 'pass_cluster_mean_end_y' columns.
    """

    # Filter and format data based on data_mode to ensure compatibility with pass cluster model
    if data_mode == 'whoscored':
        passes_out = events[events['eventType'] == 'Pass'].copy()
    elif data_mode == 'statsbomb':
        passes_out = events[events['type_name'] == 'Pass'].copy()
        passes_out['x'] = 100*passes_out['x']/120
        passes_out['y'] = 100*passes_out['y']/80
        passes_out['endX'] = 100*passes_out['end_x'] / 120
        passes_out['endY'] = 100*passes_out['end_y'] / 80
    else:
        raise ValueError("Specify 'whoscored' or 'statsbomb' as data mode")

    # Load pass clustering model
    current_dir = os.getcwd()
    os.chdir(current_dir.split("football-data-analytics")[0] +
             "football-data-analytics/model_directory/pass_cluster_model")
    cluster_model = joblib.load("PassClusterModel65.joblib")
    os.chdir(current_dir)

    # Make cluster predictions and add cluster info
    passes_out['pass_cluster_id'] = cluster_model.predict(passes_out)
    cluster_centers = cluster_model['model'].cluster_centers_ * 120
    passes_out['pass_cluster_mean_x'] = passes_out['pass_cluster_id'].apply(lambda x: cluster_centers[x, 0])
    passes_out['pass_cluster_mean_y'] = passes_out['pass_cluster_id'].apply(lambda x: cluster_centers[x, 1])
    passes_out['pass_cluster_mean_end_x'] = passes_out['pass_cluster_id'].apply(lambda x: cluster_centers[x, 2])
    passes_out['pass_cluster_mean_end_y'] = passes_out['pass_cluster_id'].apply(lambda x: cluster_centers[x, 3])

    # Return data to standard state based on data_mode
    if data_mode == 'whoscored':
        passes_out['pass_cluster_mean_x'] = 100*passes_out['pass_cluster_mean_x']/120
        passes_out['pass_cluster_mean_y'] = 100*passes_out['pass_cluster_mean_y']/80
        passes_out['pass_cluster_mean_end_x'] = 100*passes_out['pass_cluster_mean_end_x']/120
        passes_out['pass_cluster_mean_end_y'] = 100*passes_out['pass_cluster_mean_end_y']/80

    elif data_mode == 'statsbomb':
        passes_out['x'] = 120*passes_out['x']/100
        passes_out['y'] = 80*passes_out['y']/100
        passes_out = passes_out.drop(columns=['endX', 'endY'])

    return passes_out


def simulate_match_outcome(events, matches, match_id, sim_count=10000):
    """ Simulate the outcome of a match based on teams xG

    Function to simulate the outcome of a match by assigning goals to each team based on their chances and xG. Assumes
    that xG represents scoring probability and that all xG events are independent. Matches are simulated a number of
    times, with outcomes used to determine home win, draw and away win probabilites and expected points. Function
    requires statsbomb-style events and matches dataframe, id of match to simulate and number of iterations. Individual
    simulation outcomes are returned. Win probabilities and expected points are added to the matches dataframe

    Args:
        events (pandas.DataFrame): dataframe of statsbomb-style event data.
        matches (pandas.DataFrame): dataframe of statsbomb-style match data.
        match_id (int): numeric identifier of match to simulate
        sim_count (int): number of simulations to run

    Returns:
        pandas.DataFrame: statsbomb-style match dataframe with additional 'home_xg', 'away_xg', 'home_win_probability',
        'away_win_probability', 'draw_probability', 'home_xpoints' and 'away_xpoints' columns
        pandas.DataFrame: dataframe of match simulation results. One row per simulation
    """

    # Initialise lists to store simulated goal scored and outcome
    home_goal_list = []
    away_goal_list = []
    outcome_list = []

    # Retrieve xG events for match to simulate
    match_simulate = matches[matches['match_id'] == match_id]
    match_xg_events = events[(events['match_id'] == match_id) &
                             (events['shot_statsbomb_xg'] == events['shot_statsbomb_xg'])]
    home_xg_list = match_xg_events[match_xg_events['team_name'] == match_simulate['home_team'].values[0]][
        'shot_statsbomb_xg'].values
    away_xg_list = match_xg_events[match_xg_events['team_name'] == match_simulate['away_team'].values[0]][
        'shot_statsbomb_xg'].values

    # Simulate multiple times
    for i in range(sim_count):

        # Initialise simulated goal scored
        home_goals = 0
        away_goals = 0

        # Iterate through home xG events
        if len(home_xg_list) > 0:

            for xg_shot in home_xg_list:
                rand_prob = np.random.random()
                home_goals = home_goals + 1 if rand_prob < xg_shot else home_goals

        # Iterate through away xG events
        if len(away_xg_list) > 0:

            for xg_shot in away_xg_list:
                rand_prob = np.random.random()
                away_goals = away_goals + 1 if rand_prob < xg_shot else away_goals

        # Append goal outcomes to lists
        home_goal_list.append(home_goals)
        away_goal_list.append(away_goals)

        # Define match outcome based on home and away goals
        outcome = 'home' if home_goals > away_goals else 'away' if away_goals > home_goals else 'draw'
        outcome_list.append(outcome)

    # Store all simulated matches within dataframe
    match_simulation_results = pd.DataFrame(zip(home_goal_list, away_goal_list, outcome_list),
                                            columns=['home_goals', 'away_goals', 'outcome'])
    match_simulation_results['home_team'] = match_simulate['home_team'].values[0]
    match_simulation_results['away_team'] = match_simulate['away_team'].values[0]

    # Initialise dictionary to store results
    result_dict = dict()

    # Store win probabilities and xpoints in dictionary
    result_dict['match_id'] = match_id
    result_dict['home_xg'] = home_xg_list.sum()
    result_dict['away_xg'] = away_xg_list.sum()
    result_dict['home_win_probability'] = outcome_list.count('home') / sim_count
    result_dict['away_win_probability'] = outcome_list.count('away') / sim_count
    result_dict['draw_probability'] = outcome_list.count('draw') / sim_count
    result_dict['home_xpoints'] = result_dict['home_win_probability'] * 3 + result_dict['draw_probability'] * 1
    result_dict['away_xpoints'] = result_dict['away_win_probability'] * 3 + result_dict['draw_probability'] * 1

    # Insert win probabilities and xpoints information to dataframe
    if 'home_xpoints' in matches.columns:
        matches_out = matches.copy()
        matches_out.loc[matches['match_id'] == match_id, list(result_dict.keys())[1:]] = list(result_dict.values())[
                                                                                            1:]
    else:
        join_df = pd.DataFrame(result_dict, index=[0])
        matches_out = pd.merge(matches, join_df, left_on='match_id', right_on='match_id', how='left')

    return matches_out, match_simulation_results