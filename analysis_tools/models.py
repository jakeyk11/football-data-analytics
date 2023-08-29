"""Module containing a variety of predictive and statistical models relevant to the analysis of football data

Functions
---------
get_pass_clusters(events):
    Assign statsbomb or whoscored pass events to a pass cluster

"""

import joblib
from sklearn.base import BaseEstimator, TransformerMixin
import os


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
