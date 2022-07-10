"""Module containing functions to add custom events to StatsBomb-style data

Functions
---------
pre_assist(events, lineups=None)
    Add cumulative minutes to event data and calculate true match minutes.
    
xg_assisted(events)
    Calculate expected goals assisted from statsbomb-style events dataframe, and returns with xg_assisted column.

pass_into_box(single_event, inplay=True)
    Identify successful pass into box from statsbomb-style pass event.

progressive_pass(single_event, inplay=True)
    Identify successful progressive pass from statsbomb-style pass event.

create_convex_hull(events, name='default', include_percent=100)
    Create a dataframe of convex hull information from statsbomb-style event data.
"""

import numpy as np
import pandas
import pandas as pd
from scipy.spatial import ConvexHull


def pre_assist(events):
    """ Calculate pre-assists from statsbomb-style events dataframe, and returns with pre_assist column

    Function to calculate pre-assists from a statsbomb-style event dataframe (from one or multiple matches),
    where a pre-assist is a successful pass made to a player that then goes on to assist with their next pass. The
    events dataframe is returned with an additional pre_assists column.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style event dataframe with additional 'pre_assist' column.
    """

    # Initialise dataframe and new column
    events_out = events.copy()
    events_out['pre_assist'] = float('nan')

    # Loop through each assist event and check who, if anyone, passed to the assister.
    for idx, assist_event in events_out[events_out['pass_goal_assist'] == True].iterrows():

        # Obtain name of assister and numerical identifier of possession phase
        possession_number = assist_event['possession']
        assister = assist_event['player']
        scan_idx = idx - 1
        loop = True

        # Loop through previous events in the same possession phase to find the pre-assist, if there is one
        while loop:
            if events_out.loc[scan_idx, 'possession'] != possession_number:
                loop = False
            if (events_out.loc[scan_idx, 'possession'] == possession_number
                    and events_out.loc[scan_idx, 'pass_recipient'] == assister):
                events_out.loc[scan_idx, 'pre_assist'] = True
                loop = False
            scan_idx -= 1

    return events_out


def xg_assisted(events):
    """ Calculate expected goals assisted from statsbomb-style events dataframe, and returns with xg_assisted column

    Function to calculate expected goals assisted from a statsbomb-style event dataframe (from one or multiple
    matches), where xg assisted is the xg resulting from a shot that occurs after a played has made a successful pass
    to the shooter. The events dataframe is returned with an additional xg_assisted column.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style event dataframe with additional 'xg_assisted' column.
    """

    # Initialise dataframe and new column
    events_out = events.copy()
    events_out['xg_assisted'] = float('NaN')

    # Create assisted xG column
    for idx, assist_event in events_out[events_out['pass_shot_assist'] == True].iterrows():
        events_out.loc[idx, 'xg_assisted'] = events_out[events_out['id'] ==
                                                        assist_event['pass_assisted_shot_id']][
            'shot_statsbomb_xg'].values

    return events_out


def pass_into_box(single_event, inplay=True):
    """ Identify successful pass into box from statsbomb-style pass event.

    Function to identify successful passes that end up in the opposition box. The function takes in a single event,
    and returns a boolean (True = successful pass into the box.) This function is best used with the dataframe apply
    method.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from statsbomb-style event dataframe.
        inplay (bool): selection of whether to include 'in-play' events only (set to True).

    Returns:
        bool: True = successful pass into the box, nan = not box pass, unsuccessful pass or not a pass.
    """

    # Determine if event is pass and check pass success
    if single_event['type'] == 'Pass':
        check_success = single_event['pass_outcome'] != single_event['pass_outcome']

        # Check pass made in-play (if inplay = True)
        if inplay:
            check_inplay = not single_event['pass_type'] in ['Corner', 'Free Kick', 'Throw-in', 'Kick Off']
        else:
            check_inplay = True

        # Determine pass end position, and whether it's a successful pass into box
        x_position = single_event['pass_end_location'][0]
        y_position = single_event['pass_end_location'][1]
        if (check_success and check_inplay) and (x_position >= 102) and (18 <= y_position <= 62):
            return True
        else:
            return float('nan')

    else:
        return float('nan')


def progressive_pass(single_event, inplay=True):
    """ Identify successful progressive pass from statsbomb-style pass event.

    Function to identify successful progressive passes. A pass is considered progressive if the distance between the
    starting point and the next touch is: (i) at least 30 meters closer to the opponent’s goal if the starting and
    finishing points are within a team’s own half, (ii) at least 15 meters closer to the opponent’s goal if the
    starting and finishing points are in different halves, (iii) at least 10 meters closer to the opponent’s goal if
    the starting and finishing points are in the opponent’s half. The function takes in a single event and returns a
    boolean (True = successful progressive pass.) This function is best used with the dataframe apply method.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from statsbomb-style event dataframe.
        inplay (bool): selection of whether to include 'in-play' events only (set to True).

    Returns:
        bool: True = successful progressive pass, nan = non-progressive, unsuccessful pass or not a pass.
    """

    # Determine if event is pass and check pass success
    if single_event['type'] == 'Pass':
        check_success = single_event['pass_outcome'] != single_event['pass_outcome']

        # Check pass made in-play (if inplay = True)
        if inplay:
            check_inplay = not single_event['pass_type'] in ['Corner', 'Free Kick', 'Throw-in', 'Kick Off']
        else:
            check_inplay = True

        # Determine pass start and end position, and determine whether progressive
        x_startpos = single_event['location'][0]
        y_startpos = single_event['location'][1]
        x_endpos = single_event['pass_end_location'][0]
        y_endpos = single_event['pass_end_location'][1]
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


def create_convex_hull(events, name='default', include_percent=100):
    """ Create a dataframe of convex hull information from statsbomb-style event data.

    Function to create convex hull information from a dataframe of statsbomb-style event data, where each event has a
    'location' entry. A convex hull object is created, which is defined as the smallest convex polygon that encloses
    all the locations in the set of events. The outermost event locations may be omitted in order to produce a convex
    hull that better represents the most common event locations. The function returns a dataframe of convex hull
    information, including hull points, area and perimeter.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        name (string): identifier for convex hull, used as the dataframe index.
        include_percent (float, optional): percentage of event locations to include in convex hull. Event locations that
                                       are furthest from the mean location are removed first. Defaults to 100%.

    Returns:
        pandas.DataFrame: convex hull information

    """
    # Initialise output and prepare for storage of lists (objects)
    hull_df = pd.DataFrame(columns=['hull_x', 'hull_y', 'hull_reduced_x', 'hull_reduced_y', 'hull_area',
                                    'hull_perimeter', 'hull_area_%'], index=[name])
    hull_df['hull_x'] = hull_df['hull_x'].astype('object')
    hull_df['hull_y'] = hull_df['hull_y'].astype('object')
    hull_df['hull_reduced_x'] = hull_df['hull_reduced_x'].astype('object')
    hull_df['hull_reduced_y'] = hull_df['hull_reduced_y'].astype('object')

    # Create dataframe that sorts events by distance from mean event position
    hull_data = pd.DataFrame(events['location'].to_list(), columns=['x_position', 'y_position'])
    hull_data['x_from_mean'] = hull_data['x_position'] - hull_data['x_position'].mean()
    hull_data['y_from_mean'] = hull_data['y_position'] - hull_data['y_position'].mean()
    hull_data['dist_from_mean'] = np.sqrt(hull_data['x_from_mean']**2 + hull_data['y_from_mean']**2)
    hull_data.sort_values('dist_from_mean', inplace=True)

    # Remove (100 - include_percent) of points, starting with furthest from action centroid
    reduced_hull_data = hull_data.head(int(np.ceil(hull_data.shape[0] * include_percent / 100)))

    # Build list of hull points and a convex hull dataframe
    hull_pts = list(zip(reduced_hull_data['x_position'], reduced_hull_data['y_position']))
    hull_df.loc[name, 'hull_x'] = list(hull_data['x_position'].values)
    hull_df.loc[name, 'hull_reduced_x'] = list(reduced_hull_data['x_position'].values)
    hull_df.loc[name, 'hull_y'] = list(hull_data['y_position'].values)
    hull_df.loc[name, 'hull_reduced_y'] = list(reduced_hull_data['y_position'].values)

    # Calculate and store convex hull area and perimeter
    hull_df.loc[name, 'hull_area'] = ConvexHull(hull_pts).volume
    hull_df.loc[name, 'hull_perimeter'] = ConvexHull(hull_pts).area
    hull_df.loc[name, 'hull_area_%'] = 100 * hull_df.loc[name, 'hull_area'] / (120 * 80)

    return hull_df


