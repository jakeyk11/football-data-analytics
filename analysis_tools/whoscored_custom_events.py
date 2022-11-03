"""Module containing functions to add custom events to WhoScored-style data

Functions
---------
def pre_assist(events):
    Calculate pre-assists from whoscored-style events dataframe, and returns with pre_assist column

progressive_pass(single_event, inplay=True, successful_only=True)
    Identify progressive pass from WhoScored-style pass event.

pass_into_box(single_event, inplay=True, successful_only=True):
    Identify successful pass into box from whoscored-style pass event.

create_convex_hull(events_df, name='default', min_events=3, include_percent=100, pitch_area = 10000):
    Create a dataframe of convex hull information from statsbomb-style event data.
"""

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull


def pre_assist(events):
    """ Calculate pre-assists from whoscored-style events dataframe, and returns with pre_assist column

    Function to calculate pre-assists from a whoscored-style event dataframe (from one or multiple matches),
    where a pre-assist is a successful pass made to a player that then goes on to assist with their next pass. The
    events dataframe is returned with an additional pre_assiss column.

    Args:
        events (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style event dataframe with additional 'pre_assist' column.
    """

    # Initialise dataframe and new column
    events_out = events.copy()
    events_out.reset_index(inplace=True)
    events_out['pre_assist'] = float('nan')

    for idx, assist_event in events_out[events_out['satisfiedEventsTypes'].apply(lambda x: 92 in x if x == x else False)].iterrows():

        # Obtain name of assister and numerical identifier of period
        period_number = assist_event['period']
        assist_team = assist_event['teamId']
        assister = assist_event['playerId']
        scan_idx = idx - 1
        loop = True

        # Loop through previous events in the same period to find the pre-assist, if there is one
        while loop:
            if events_out.iloc[scan_idx]['period'] != period_number:
                loop = False
            if events_out.iloc[scan_idx]['teamId'] != assist_team:
                loop = False
            if (events_out.iloc[scan_idx]['period'] == period_number
                    and events_out.iloc[scan_idx]['pass_recipient'] == assister):
                events_out.loc[events_out.index == scan_idx, 'pre_assist'] = True
                loop = False
            scan_idx -= 1

    return events_out


def progressive_pass(single_event, inplay=True, successful_only=True):
    """ Identify progressive pass from WhoScored-style pass event.

    Function to identify progressive passes. A pass is considered progressive if the distance between the
    starting point and the next touch is: (i) at least 30 meters closer to the opponent’s goal if the starting and
    finishing points are within a team’s own half, (ii) at least 15 meters closer to the opponent’s goal if the
    starting and finishing points are in different halves, (iii) at least 10 meters closer to the opponent’s goal if
    the starting and finishing points are in the opponent’s half. The function takes in a single event and returns a
    boolean (True = successful progressive pass.) This function is best used with the dataframe apply method.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from WhoScored-style event dataframe.
        inplay (bool, optional): selection of whether to include 'in-play' events only. True by default.
        successful_only (bool, optional): selection of whether to only include successful passes. True by default

    Returns:
        bool: True = progressive pass, nan = non-progressive pass, unsuccessful progressive pass or not a pass
    """

    # Determine if event is pass
    if single_event['eventType'] == 'Pass':

        # Check success (if successful_only = True)
        if successful_only:
            check_success = single_event['outcomeType'] == 'Successful'
        else:
            check_success = True

        # Check pass made in-play (if inplay = True)
        if inplay:
            check_inplay = not any(item in single_event['satisfiedEventsTypes'] for item in [48, 50, 51, 42, 44, 45, 31, 34])
        else:
            check_inplay = True

        # Determine pass start and end position in yards (assuming standard pitch), and determine whether progressive
        x_startpos = 120*single_event['x']/100
        y_startpos = 80*single_event['y']/100
        x_endpos = 120*single_event['endX']/100
        y_endpos = 80*single_event['endY']/100
        delta_goal_dist = (np.sqrt((120 - x_startpos) ** 2 + (40 - y_startpos) ** 2) -
                           np.sqrt((120 - x_endpos) ** 2 + (40 - y_endpos) ** 2))

        # At least 30m closer to the opponent’s goal if the starting and finishing points are within a team’s own half
        if (check_success and check_inplay) and (x_startpos < 60 and x_endpos < 60) and delta_goal_dist >= 32.8:
            return True

        # At least 15m closer to the opponent’s goal if the starting and finishing points are in different halves
        elif (check_success and check_inplay) and (x_startpos < 60 and x_endpos >= 60) and delta_goal_dist >= 16.4:
            return True

        # At least 10m closer to the opponent’s goal if the starting and finishing points are in the opponent’s half
        elif (check_success and check_inplay) and (x_startpos >= 60 and x_endpos >= 60) and delta_goal_dist >= 10.94:
            return True
        else:
            return float('nan')

    else:
        return float('nan')


def pass_into_box(single_event, inplay=True, successful_only=True):
    """ Identify successful pass into box from whoscored-style pass event.

    Function to identify successful passes that end up in the opposition box. The function takes in a single event,
    and returns a boolean (True = successful pass into the box.) This function is best used with the dataframe apply
    method.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from whoscored-style event dataframe.
        inplay (bool, optional): selection of whether to include 'in-play' events only. True by default.
        successful_only (bool, optional): selection of whether to only include successful passes. True by default

    Returns:
        bool: True = successful pass into the box, nan = not box pass, unsuccessful pass or not a pass.
    """

    # Determine if event is pass and check pass success
    if single_event['eventType'] == 'Pass':

        # Check success (if successful_only = True)
        if successful_only:
            check_success = single_event['outcomeType'] == 'Successful'
        else:
            check_success = True

        # Check pass made in-play (if inplay = True)
        if inplay:
            check_inplay = not any(item in single_event['satisfiedEventsTypes'] for item in [48, 50, 51, 42, 44, 45, 31, 34])
        else:
            check_inplay = True

        # Determine pass end position, and whether it's a successful pass into box
        x_position = 120 * single_event['endX'] / 100
        y_position = 80 * single_event['endY'] / 100
        if (check_success and check_inplay) and (x_position >= 102) and (18 <= y_position <= 62):
            return True
        else:
            return float('nan')

    else:
        return float('nan')


def create_convex_hull(events_df, name='default', min_events=3, include_percent=100, pitch_area=10000):
    """ Create a dataframe of convex hull information from statsbomb-style event data.

    Function to create convex hull information from a dataframe of whoscored-style event data, where each event has a
    'location' entry. A convex hull object is created, which is defined as the smallest convex polygon that encloses
    all the locations in the set of events. The outermost event locations may be omitted in order to produce a convex
    hull that better represents the most common event locations. The function returns a dataframe of convex hull
    information, including hull points, area and perimeter.

    Args:
        events_df (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        name (string): identifier for convex hull, used as the dataframe index.
        min_events (int, optional): minimum number of events required to produce convex hull. 3 by default.
        include_percent (float, optional): percentage of event locations to include in convex hull. Event locations that
                                       are furthest from the mean location are removed first. Defaults to 100%.
        pitch_area (float, optional): total area of the pitch, used to calculate percentages. 10000 by default.

    Returns:
        pandas.DataFrame: convex hull information

    """

    # Initialise output
    hull_df = None

    if len(events_df) >= min_events:

        # Format output and prepare for storage of lists (objects)
        hull_df = pd.DataFrame(columns=['hull_x', 'hull_y', 'hull_reduced_x', 'hull_reduced_y', 'hull_centre',
                                        'hull_area', 'hull_perimeter', 'hull_area_%'], index=[name])
        hull_df['hull_x'] = hull_df['hull_x'].astype('object')
        hull_df['hull_y'] = hull_df['hull_y'].astype('object')
        hull_df['hull_reduced_x'] = hull_df['hull_reduced_x'].astype('object')
        hull_df['hull_reduced_y'] = hull_df['hull_reduced_y'].astype('object')

        # Create dataframe that sorts events by distance from mean event position
        hull_data = pd.DataFrame()
        hull_data['x_position'] = events_df['x']
        hull_data['y_position'] = events_df['y']
        hull_data['x_from_mean'] = hull_data['x_position'] - hull_data['x_position'].mean()
        hull_data['y_from_mean'] = hull_data['y_position'] - hull_data['y_position'].mean()
        hull_data['dist_from_mean'] = np.sqrt(hull_data['x_from_mean']**2 + hull_data['y_from_mean']**2)
        hull_data.sort_values('dist_from_mean', inplace=True)

        # Remove (100 - include_percent) of points, starting with furthest from action centroid
        reduced_hull_data = hull_data.head(int(np.ceil(hull_data.shape[0] * include_percent / 100)))

        # Build list of hull points and a convex hull dataframe
        hull_pts = list(zip(reduced_hull_data['x_position'], reduced_hull_data['y_position']))
        hull_df.at[name, 'hull_x'] = list(hull_data['x_position'].values)
        hull_df.at[name, 'hull_reduced_x'] = list(reduced_hull_data['x_position'].values)
        hull_df.at[name, 'hull_y'] = list(hull_data['y_position'].values)
        hull_df.at[name, 'hull_reduced_y'] = list(reduced_hull_data['y_position'].values)

        # Calculate and store convex hull centre, area and perimeter
        hull_df.at[name, 'hull_centre'] = (reduced_hull_data['x_position'].mean(), reduced_hull_data['y_position'].mean())
        hull_df.at[name, 'hull_area'] = ConvexHull(hull_pts).volume
        hull_df.at[name, 'hull_perimeter'] = ConvexHull(hull_pts).area
        hull_df.at[name, 'hull_area_%'] = 100 * hull_df.loc[name, 'hull_area'] / pitch_area

    return hull_df



