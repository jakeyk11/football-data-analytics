"""Module containing functions to add custom events to WhoScored-style data

Functions
---------
pre_assist(events):
    Calculate pre-assists from whoscored-style events dataframe, and returns with pre_assist column

progressive_pass(single_event, inplay=True, successful_only=True)
    Identify progressive pass from WhoScored-style pass event.

progressive_carry(single_event, successful_only=True):
    Identify progressive carry from WhoScored-style carry event.

pass_into_box(single_event, inplay=True, successful_only=True):
    Identify successful pass into box from whoscored-style pass event.

carry_into_box(single_event, successful_only=True):
    Identify successful carry into box from whoscored-style carry event.

create_convex_hull(events_df, name='default', min_events=3, include_percent=100, pitch_area = 10000):
    Create a dataframe of convex hull information from statsbomb-style event data.

passes_into_hull(hull_info, events, opp_passes=True, xt_info=False):
    Add pass into hull information to dataframe of convex hulls for whoscored-style event data.

insert_ball_carries(events_df, min_carry_length=3, max_carry_length=60, min_carry_duration=1, max_carry_duration=10):
    Add carry events to whoscored-style events dataframe

get_xthreat(events_df, interpolate=True, pitch_length=105, pitch_width=68):
    Add expected threat metric to whoscored-style events dataframe
"""

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from scipy.interpolate import interp2d
from scipy.spatial import Delaunay
from shapely.geometry.polygon import Polygon


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


def progressive_carry(single_event, successful_only=True):
    """ Identify progressive carry from WhoScored-style carry event.

    Function to identify progressive carries. A carry is considered progressive if the distance between the
    starting point and the end position is: (i) at least 30 meters closer to the opponent’s goal if the starting and
    finishing points are within a team’s own half, (ii) at least 15 meters closer to the opponent’s goal if the
    starting and finishing points are in different halves, (iii) at least 10 meters closer to the opponent’s goal if
    the starting and finishing points are in the opponent’s half. The function takes in a single event and returns a
    boolean (True = successful progressive carry.) This function is best used with the dataframe apply method.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from WhoScored-style event dataframe.
        successful_only (bool, optional): selection of whether to only include successful carries. True by default

    Returns:
        bool: True = progressive carry, nan = non-progressive carry, unsuccessful progressive carry or not a carry
    """

    # Determine if event is pass
    if single_event['eventType'] == 'Carry':

        # Check success (if successful_only = True)
        if successful_only:
            check_success = single_event['outcomeType'] == 'Successful'
        else:
            check_success = True

        # Determine pass start and end position in yards (assuming standard pitch), and determine whether progressive
        x_startpos = 120*single_event['x']/100
        y_startpos = 80*single_event['y']/100
        x_endpos = 120*single_event['endX']/100
        y_endpos = 80*single_event['endY']/100
        delta_goal_dist = (np.sqrt((120 - x_startpos) ** 2 + (40 - y_startpos) ** 2) -
                           np.sqrt((120 - x_endpos) ** 2 + (40 - y_endpos) ** 2))

        # At least 30m closer to the opponent’s goal if the starting and finishing points are within a team’s own half
        if check_success and (x_startpos < 60 and x_endpos < 60) and delta_goal_dist >= 32.8:
            return True

        # At least 15m closer to the opponent’s goal if the starting and finishing points are in different halves
        elif check_success and (x_startpos < 60 and x_endpos >= 60) and delta_goal_dist >= 16.4:
            return True

        # At least 10m closer to the opponent’s goal if the starting and finishing points are in the opponent’s half
        elif check_success and (x_startpos >= 60 and x_endpos >= 60) and delta_goal_dist >= 10.94:
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


def carry_into_box(single_event, successful_only=True):
    """ Identify successful carry into box from whoscored-style pass event.

    Function to identify successful carries that end up in the opposition box. The function takes in a single event,
    and returns a boolean (True = successful carry into the box.) This function is best used with the dataframe apply
    method.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from whoscored-style event dataframe.
        successful_only (bool, optional): selection of whether to only include successful carries. True by default

    Returns:
        bool: True = successful carry into the box, nan = not box carry, unsuccessful carry or not a carry.
    """

    # Determine if event is pass and check pass success
    if single_event['eventType'] == 'Carry':

        # Check success (if successful_only = True)
        if successful_only:
            check_success = single_event['outcomeType'] == 'Successful'
        else:
            check_success = True

        # Determine pass end position, and whether it's a successful pass into box
        x_position = 120 * single_event['endX'] / 100
        y_position = 80 * single_event['endY'] / 100
        if check_success and (x_position >= 102) and (18 <= y_position <= 62):
            return True
        else:
            return float('nan')

    else:
        return float('nan')
    

def create_convex_hull(events_df, name='default', min_events=3, include_events='1std', pitch_area=10000):
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
                                       are furthest from the mean location are removed first. Defaults to 1 std dev.
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

        # Remove (100 - include_percent) or count std of points, starting with furthest from action centroid
        if 'std' in str(include_events):
            num_stds = float(include_events.split('std')[0])
            sqrt_variance = np.sqrt(sum(hull_data['dist_from_mean'] ** 2) / (len(hull_data['dist_from_mean']) - 1))
            reduced_hull_data = hull_data[hull_data['dist_from_mean'] <= sqrt_variance * num_stds]
        else:
            reduced_hull_data = hull_data.head(int(np.ceil(hull_data.shape[0] * include_events / 100)))

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


def passes_into_hull(hull_info, events, opp_passes=True, xt_info=False):
    """ Add pass into hull information to dataframe of convex hulls for whoscored-style event data.

    Function to determine whether one or more passes (passed in as a whoscored-style event dataframe) end within a
    convex hull. The function produces a list of successful and unsucessful passes that end within the hull. This
    information is then used to count passes into the hull, and add the information to the hull information
    dataframe. This function must be used after create_convex_hull.

    Args:
        hull_info (pandas.Series): series of hull information.
        events (pandas.DataFrame): whoscored-style events conaining all passes to be checked.
        opp_passes (bool, optional): selection of whether the passes to be checked are opposition or own team.
        xt_info (bool, optional): selection of whether to include expected threat information. False by default.

    Returns:
        pandas.DataFrame: convex hull information with additional pass columns.
    """

    def in_hull(p, hull):
        """
        Test if points in `p` are in `hull`

        `p` should be a `NxK` coordinates of `N` points in `K` dimensions
        `hull` is either a scipy.spatial.Delaunay object or the `MxK` array of the
        coordinates of `M` points in `K`dimensions for which Delaunay triangulation
        will be computed
        """

        if not isinstance(hull, Delaunay):
            hull = Delaunay(hull)

        return hull.find_simplex(p) >= 0

    # Initialise output
    hull_df = hull_info.copy()
    hull_df['suc_pass_into_hull'] = []
    hull_df['unsuc_pass_into_hull'] = []

    # Ensure only pass events are checked
    events_to_check = events[events['eventType'] == 'Pass']

    # Create polygon object for convex hull that is being assessed
    polygon = Polygon(list(zip(hull_df['hull_reduced_x'], hull_df['hull_reduced_y'])))
    hull_pts = list(zip(hull_df['hull_reduced_x'], hull_df['hull_reduced_y']))

    # Initialise pass counters
    suc_into_hull_count = 0
    suc_into_hull_xt_net = 0
    suc_into_hull_xt_gen = 0
    unsuc_into_hull_count = 0
    unsuc_into_hull_xt_net = 0
    unsuc_into_hull_xt_gen = 0

    # Check each pass individually
    for _, pass_event in events_to_check.iterrows():

        # If the pass being checked is an opposition pass, flip co-ordinates
        if opp_passes is True:
            pass_start_loc_flip = [100 - pass_event['x'], 100 - pass_event['y']]
            pass_end_loc_flip = [100 - pass_event['endX'], 100 - pass_event['endY']]
        else:
            pass_start_loc_flip = [pass_event['x'], pass_event['y']]
            pass_end_loc_flip = [pass_event['endX'], pass_event['endY']]

        # Check point is within polygon
        if in_hull(pass_end_loc_flip, hull_pts):

            # Add successful and unsuccessful passes to columns, and count passes / accumulate obv
            if pass_event['outcomeType'] == 'Successful':
                suc_into_hull_count += 1
                if xt_info:
                    hull_df['suc_pass_into_hull'].append([pass_start_loc_flip, pass_end_loc_flip,
                                                          pass_event['xThreat']])
                    suc_into_hull_xt_net = np.nansum([suc_into_hull_xt_net, pass_event['xThreat']])
                    suc_into_hull_xt_gen = np.nansum([suc_into_hull_xt_gen,
                                                      0 if pass_event['xThreat'] < 0 else pass_event['xThreat']])
                else:
                    hull_df['suc_pass_into_hull'].append([pass_start_loc_flip, pass_end_loc_flip])

            else:
                unsuc_into_hull_count += 1
                if xt_info:
                    hull_df['unsuc_pass_into_hull'].append([pass_start_loc_flip, pass_end_loc_flip,
                                                            pass_event['xThreat']])
                    unsuc_into_hull_xt_net = np.nansum([unsuc_into_hull_xt_net, pass_event['xThreat']])
                    unsuc_into_hull_xt_gen = np.nansum([unsuc_into_hull_xt_gen,
                                                        0 if pass_event['xThreat'] < 0 else pass_event['xThreat']])
                else:
                    hull_df['unsuc_pass_into_hull'].append([pass_start_loc_flip, pass_end_loc_flip])

    hull_df['count_suc_pass_into_hull'] = suc_into_hull_count
    hull_df['count_unsuc_pass_into_hull'] = unsuc_into_hull_count
    hull_df['pct_tot_pass_into_hull'] = round(100 * (suc_into_hull_count + unsuc_into_hull_count) /
                                              len(events_to_check), 2)
    hull_df['hull_pass_prevented_%'] = round(100 * unsuc_into_hull_count /
                                             (suc_into_hull_count + unsuc_into_hull_count), 2)
    if xt_info:
        hull_df['xt_net_suc_pass_into_hull'] = suc_into_hull_xt_net
        hull_df['xt_gen_suc_pass_into_hull'] = suc_into_hull_xt_gen
        hull_df['xt_net_unsuc_pass_into_hull'] = unsuc_into_hull_xt_net
        hull_df['xt_gen_unsuc_pass_into_hull'] = unsuc_into_hull_xt_gen
        hull_df['xt_net_into_hull'] = suc_into_hull_xt_net + suc_into_hull_xt_net
        hull_df['obvtot_into_hull'] = suc_into_hull_xt_gen + unsuc_into_hull_xt_gen

    return hull_df


def insert_ball_carries(events_df, min_carry_length=3, max_carry_length=60, min_carry_duration=1, max_carry_duration=10):
    """ Add carry events to whoscored-style events dataframe

    Function to read a whoscored-style events dataframe (single or multiple matches) and return an event dataframe
    that contains carry information.

    Args:
        events_df (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.
        min_carry_length (float, optional): minimum distance required for event to qualify as carry. 5m by default.
        max_carry_length (float, optional): largest distance in which event can qualify as carry. 60m by default.
        min_carry_duration (float, optional): minimum duration required for event to quality as carry. 2s by default.
        max_carry_duration (float, optional): longest duration in which event can qualify as carry. 10s by default.

    Returns:
        pandas.DataFrame: whoscored-style dataframe of events including carries
    """

    # Initialise output dataframe
    events_out = pd.DataFrame()

    # Carry conditions (convert from metres to opta)
    min_carry_length = 3.0
    max_carry_length = 60.0
    min_carry_duration = 1.0
    max_carry_duration = 10.0

    for match_id in events_df['match_id'].unique():

        match_events = events_df[events_df['match_id'] == match_id].reset_index()
        match_carries = pd.DataFrame()

        for idx, match_event in match_events.iterrows():

            if idx < len(match_events) - 1:
                prev_evt_team = match_event['teamId']
                next_evt_idx = idx + 1
                init_next_evt = match_events.loc[next_evt_idx]
                take_ons = 0
                incorrect_next_evt = True

                while incorrect_next_evt:

                    next_evt = match_events.loc[next_evt_idx]

                    if next_evt['eventType'] == 'TakeOn' and next_evt['outcomeType'] == 'Successful':
                        take_ons += 1
                        incorrect_next_evt = True

                    elif ((next_evt['eventType'] == 'TakeOn' and next_evt['outcomeType'] == 'Unsuccessful')
                          or (next_evt['teamId'] != prev_evt_team and next_evt['eventType'] == 'Challenge' and next_evt[
                                'outcomeType'] == 'Unsuccessful')
                          or (next_evt['eventType'] == 'Foul')):
                        incorrect_next_evt = True

                    else:
                        incorrect_next_evt = False

                    next_evt_idx += 1

                # Apply some conditioning to determine whether carry criteria is satisfied

                same_team = prev_evt_team == next_evt['teamId']
                not_ball_touch = match_event['eventType'] != 'BallTouch'
                dx = 105*(match_event['endX'] - next_evt['x'])/100
                dy = 68*(match_event['endY'] - next_evt['y'])/100
                far_enough = dx ** 2 + dy ** 2 >= min_carry_length ** 2
                not_too_far = dx ** 2 + dy ** 2 <= max_carry_length ** 2
                dt = 60 * (next_evt['cumulative_mins'] - match_event['cumulative_mins'])
                min_time = dt >= min_carry_duration
                same_phase = dt < max_carry_duration
                same_period = match_event['period'] == next_evt['period']

                valid_carry = same_team & not_ball_touch & far_enough & not_too_far & min_time & same_phase &same_period

                if valid_carry:
                    carry = pd.DataFrame()
                    prev = match_event
                    nex = next_evt

                    carry.loc[0, 'eventId'] = prev['eventId'] + 0.5
                    carry['minute'] = np.floor(((init_next_evt['minute'] * 60 + init_next_evt['second']) + (
                                prev['minute'] * 60 + prev['second'])) / (2 * 60))
                    carry['second'] = (((init_next_evt['minute'] * 60 + init_next_evt['second']) +
                                        (prev['minute'] * 60 + prev['second'])) / 2) - (carry['minute'] * 60)
                    carry['teamId'] = nex['teamId']
                    carry['x'] = prev['endX']
                    carry['y'] = prev['endY']
                    carry['expandedMinute'] = np.floor(
                        ((init_next_evt['expandedMinute'] * 60 + init_next_evt['second']) +
                         (prev['expandedMinute'] * 60 + prev['second'])) / (2 * 60))
                    carry['period'] = nex['period']
                    carry['type'] = carry.apply(lambda x: {'value': 99, 'displayName': 'Carry'}, axis=1)
                    carry['outcomeType'] = 'Successful'
                    carry['qualifiers'] = carry.apply(
                        lambda x: {'type': {'value': 999, 'displayName': 'takeOns'}, 'value': str(take_ons)}, axis=1)
                    carry['satisfiedEventsTypes'] = carry.apply(lambda x: [], axis=1)
                    carry['isTouch'] = True
                    carry['playerId'] = nex['playerId']
                    carry['endX'] = nex['x']
                    carry['endY'] = nex['y']
                    carry['blockedX'] = np.nan
                    carry['blockedY'] = np.nan
                    carry['goalMouthZ'] = np.nan
                    carry['goalMouthY'] = np.nan
                    carry['isShot'] = np.nan
                    carry['relatedEventId'] = nex['eventId']
                    carry['relatedPlayerId'] = np.nan
                    carry['isGoal'] = np.nan
                    carry['cardType'] = np.nan
                    carry['isOwnGoal'] = np.nan
                    carry['match_id'] = nex['match_id']
                    carry['eventType'] = 'Carry'
                    carry['cumulative_mins'] = (prev['cumulative_mins'] + init_next_evt['cumulative_mins']) / 2

                    match_carries = pd.concat([match_carries, carry], ignore_index=True, sort=False)

        match_events_and_carries = pd.concat([match_carries, match_events], ignore_index=True, sort=False)
        match_events_and_carries = match_events_and_carries.sort_values(
            ['match_id', 'period', 'cumulative_mins']).reset_index(drop=True)

        # Rebuild events dataframe
        events_out = pd.concat([events_out, match_events_and_carries])

    return events_out


def get_xthreat(events_df, interpolate=True, pitch_length=100, pitch_width=100):
    """ Add expected threat metric to whoscored-style events dataframe

    Function to apply Karun Singh's expected threat model to all successful pass and carry events within a
    whoscored-style events dataframe. This imposes a 12x8 grid of expected threat values on a standard pitch. An
    interpolate parameter can be passed to impose a continous set of expected threat values on the pitch.

    Args:
        events_df (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.
        interpolate (bool, optional): selection of whether to impose a continous set of xT values. True by default.
        pitch_length (float, optional): extent of pitch x coordinate (based on event data). 100 by default.
        pitch_width (float, optional): extent of pitch y coordinate (based on event data). 100 by default.

    Returns:
        pandas.DataFrame: whoscored-style dataframe of events, including expected threat
    """

    # Define function to get cell in which an x, y value falls
    def get_cell_indexes(x_series, y_series, cell_cnt_l, cell_cnt_w, field_length, field_width):
        xi = x_series.divide(field_length).multiply(cell_cnt_l)
        yj = y_series.divide(field_width).multiply(cell_cnt_w)
        xi = xi.astype('int64').clip(0, cell_cnt_l - 1)
        yj = yj.astype('int64').clip(0, cell_cnt_w - 1)
        return xi, yj

    # Initialise output
    events_out = pd.DataFrame()

    # Get Karun Singh expected threat grid
    path = "https://karun.in/blog/data/open_xt_12x8_v1.json"
    xt_grid = pd.read_json(path)
    init_cell_count_w, init_cell_count_l = xt_grid.shape

    # Isolate actions that involve successfully moving the ball (successful carries and passes)
    move_actions = events_df[(events_df['eventType'].isin(['Carry', 'Pass'])) &
                             (events_df['outcomeType'] == 'Successful')]

    # Set-up bilinear interpolator if user chooses to
    if interpolate:
        cell_length = pitch_length / init_cell_count_l
        cell_width = pitch_width / init_cell_count_w
        x = np.arange(0.0, pitch_length, cell_length) + 0.5 * cell_length
        y = np.arange(0.0, pitch_width, cell_width) + 0.5 * cell_width
        interpolator = interp2d(x=x, y=y, z=xt_grid.values, kind='linear', bounds_error=False)
        interp_cell_count_l = int(pitch_length * 10)
        interp_cell_count_w = int(pitch_width * 10)
        xs = np.linspace(0, pitch_length, interp_cell_count_l)
        ys = np.linspace(0, pitch_width, interp_cell_count_w)
        grid = interpolator(xs, ys)
    else:
        grid = xt_grid.values

    # Set cell counts based on use of interpolator
    if interpolate:
        cell_count_l = interp_cell_count_l
        cell_count_w = interp_cell_count_w
    else:
        cell_count_l = init_cell_count_l
        cell_count_w = init_cell_count_w

    # For each match, apply expected threat grid (we go by match to avoid issues with identical event indicies)
    for match_id in move_actions['match_id'].unique():
        match_move_actions = move_actions[move_actions['match_id'] == match_id]

        # Get cell indices of start location of event
        startxc, startyc = get_cell_indexes(match_move_actions['x'], match_move_actions['y'], cell_count_l,
                                            cell_count_w, pitch_length, pitch_width)
        endxc, endyc = get_cell_indexes(match_move_actions['endX'], match_move_actions['endY'], cell_count_l,
                                        cell_count_w, pitch_length, pitch_width)

        # Calculate xt at start and end of eventa
        xt_start = grid[startyc.rsub(cell_count_w - 1), startxc]
        xt_end = grid[endyc.rsub(cell_count_w - 1), endxc]

        # Build dataframe of event index and net xt
        ratings = pd.DataFrame(data=xt_end-xt_start, index=match_move_actions.index, columns=['xThreat'])

        # Merge ratings dataframe to all match events
        match_events_and_ratings = pd.merge(left=events_df[events_df['match_id'] == match_id], right=ratings,
                                            how="left", left_index=True, right_index=True)
        events_out = pd.concat([events_out, match_events_and_ratings], ignore_index=True, sort=False)
        events_out['xThreat_gen'] = events_out['xThreat'].apply(lambda xt: xt if (xt > 0 or xt != xt) else 0)

    return events_out