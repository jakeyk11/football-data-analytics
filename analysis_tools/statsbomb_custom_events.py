"""Module containing functions to add custom events to StatsBomb-style data

Functions
---------
pre_assist(events, lineups=None)
    Add cumulative minutes to event data and calculate true match minutes.

xg_assisted(events)
    Calculate expected goals assisted from statsbomb-style events dataframe, and returns with xg_assisted column.

istouch(single_event, inplay=True)
    Determine whether a statsbomb-style event involves the player touching the ball.

pass_into_box(single_event, inplay=True)
    Identify successful pass into box from statsbomb-style pass event.

progressive_pass(single_event, inplay=True)
    Identify successful progressive pass from statsbomb-style pass event.

create_convex_hull(events, name='default', include_percent=100)
    Create a dataframe of convex hull information from statsbomb-style event data.

passes_into_hull(hull_info, events, opp_passes=True):
    Add pass into hull information to dataframe of convex hulls for statsbomb-style event data.

defensive_line_positions(events, team, include_events='1std'):
    Calculate the positions of various defensive lines

long_ball_retention(events, player_name, player_team):
    Analyse player ability to retain the ball after a long ball is played to them.
"""

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from scipy.spatial import Delaunay
from shapely.geometry.polygon import Polygon
import analysis_tools.statsbomb_data_engineering as sde


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
    events_out['xg_assisted'] = float('nan')

    # Create assisted xG column
    for idx, assist_event in events_out[events_out['pass_shot_assist'] == True].iterrows():
        events_out.loc[idx, 'xg_assisted'] = events_out[events_out['id'] ==
                                                        assist_event['pass_assisted_shot_id']][
            'shot_statsbomb_xg'].values

    return events_out


def istouch(single_event, inplay=True):
    """Determine whether a statsbomb-style event involves the player touching the ball.

    Function to identify events that involve the player touching the ball. The function takes in a single event,
    and returns a string that defines whether the player touches the ball and whether the touch was a defensive or
    defensive actions. This function is best used with the dataframe apply.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from statsbomb-style event dataframe.
        inplay (bool, optional): selection of whether to include 'in-play' events only. True by default.

    Returns:
        string: Offensive = offensive touch, Defensive = defensive touch, nan = not a touch (or invalid touch).
        bool: Identifies successful touches with True marker
        bool: Identifies touches within the box with True marker
        bool: Identifies touches within the final third with True marker
    """

    # Initialise variables
    touch_type = float(np.nan)
    touch_success = float(np.nan)
    box_touch = float(np.nan)
    final_third_touch = float(np.nan)
    set_piece = False

    # 50 50s won
    if single_event['50_50'] == single_event['50_50']:
        if single_event['team'] == single_event['possession_team']:
            touch_type = 'Offensive'
        else:
            touch_type = 'Defensive'
        if single_event['50_50']['outcome']['name'] in ['Won', 'Success To Team', 'Success To Opposition']:
            touch_success = True

    # Successful ball receipt
    elif single_event['type'] == 'Ball Receipt*' and (single_event['ball_receipt_outcome'] !=
                                                      single_event['ball_receipt_outcome']):
        touch_type = 'Offensive'
        touch_success = True

    # Successful recovery
    elif single_event['type'] == 'Ball Recovery':
        if single_event['ball_recovery_offensive'] == single_event['ball_recovery_offensive']:
            touch_type = 'Offensive'
        else:
            touch_type = 'Defensive'
        if single_event['ball_recovery_recovery_failure'] != single_event['ball_recovery_recovery_failure']:
            touch_success = True

    # Block or deflection
    elif single_event['type'] == 'Block':
        if single_event['block_offensive'] == single_event['block_offensive']:
            touch_type = 'Offensive'
        else:
            touch_type = 'Defensive'
        touch_success = True

    # Carry
    elif single_event['type'] == 'Carry':
        touch_type = 'Offensive'
        touch_success = True

    # Clearance
    elif single_event['type'] == 'Clearance':
        touch_type = 'Defensive'
        touch_success = True

    # Dribble
    elif single_event['type'] == 'Dribble' and single_event['dribble_no_touch'] != single_event['dribble_no_touch']:
        touch_type = 'Offensive'
        if single_event['dribble_outcome'] == 'Complete':
            touch_success = True

    # Duel
    elif single_event['duel_type'] == 'Tackle':
        touch_type = 'Defensive'
        if single_event['duel_outcome'] in ['Won', 'Success', 'Success In Play', 'Success Out']:
            touch_success = True

    # Interception
    elif single_event['type'] == 'Interception' and single_event['interception_outcome'] != 'Lost':
        touch_type = 'Defensive'
        if single_event['interception_outcome'] in ['Won', 'Success', 'Success In Play', 'Success Out']:
            touch_success = True

    # Miscontrol
    elif single_event['type'] == 'Miscontrol':
        touch_type = 'Offensive'

    # Pass
    elif single_event['type'] == 'Pass' and single_event['pass_body_part'] != 'No Touch':
        touch_type = 'Offensive'
        if single_event['pass_type'] in ['Corner', 'Free Kick', 'Goal Kick', 'Kick Off', 'Throw-in']:
            set_piece = True
        else:
            set_piece = False
        if single_event['pass_outcome'] != single_event['pass_outcome']:
            touch_success = True

    # Shot
    elif single_event['type'] == 'Shot':
        touch_type = 'Offensive'
        if single_event['shot_type'] == 'Open Play':
            set_piece = False
        else:
            set_piece = True
        if single_event['shot_outcome'] in ['Saved', 'Goal', 'Saved To Post']:
            touch_success = True

    # In box
    if single_event['location'] == single_event['location']:
        x_position = single_event['location'][0]
        y_position = single_event['location'][1]
        if (x_position >= 102) and (18 <= y_position <= 62):
            box_touch = True
        if x_position >= 80:
            final_third_touch = True

    # Include or exclude set pieces
    if inplay:
        if not set_piece:
            return touch_type, touch_success, box_touch, final_third_touch
    else:
        return touch_type, touch_success, box_touch, final_third_touch


def pass_into_box(single_event, inplay=True, successful_only=True):
    """ Identify successful pass into box from statsbomb-style pass event.

    Function to identify successful passes that end up in the opposition box. The function takes in a single event,
    and returns a boolean (True = successful pass into the box.) This function is best used with the dataframe apply
    method.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from statsbomb-style event dataframe.
        inplay (bool, optional): selection of whether to include 'in-play' events only. True by default.
        successful_only (bool, optional): selection of whether to only include successful passes. True by default
    Returns:
        bool: True = successful pass into the box, nan = not box pass, unsuccessful pass or not a pass.
    """

    # Determine if event is pass and check pass success
    if single_event['type'] == 'Pass':

        # Check success (if successful_only = True)
        if successful_only:
            check_success = single_event['pass_outcome'] != single_event['pass_outcome']
        else:
            check_success = True

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


def create_convex_hull(events, name='default', include_events='1std', min_events=3, pitch_area=9600):
    """ Create a dataframe of convex hull information from statsbomb-style event data.

    Function to create convex hull information from a dataframe of statsbomb-style event data, where each event has a
    'location' entry. A convex hull object is created, which is defined as the smallest convex polygon that encloses
    all the locations in the set of events. The outermost event locations may be omitted in order to produce a convex
    hull that better represents the most common event locations. The function returns a dataframe of convex hull
    information, including hull points, area and perimeter.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        name (string): identifier for convex hull, used as the dataframe index.
        min_events (int, optional): minimum number of events required to produce convex hull. 3 by default.
        include_events (float, optional): percentage of event locations, or number of standard deviations from mean, to
        include. Event locations that are furthest from the mean location are removed first. Defaults to 1 standard dev.
        pitch_area (float, optional): total area of the pitch, used to calculate percentages. 9600 by default.

    Returns:
        pandas.DataFrame: convex hull information

    """

    # Initialise output
    hull_df = None

    if len(events) >= min_events:

        # Initialise output and prepare for storage of lists (objects)
        hull_df = pd.DataFrame(columns=['hull_x', 'hull_y', 'hull_reduced_x', 'hull_reduced_y', 'hull_centre',
                                        'hull_area', 'hull_perimeter', 'hull_area_%'], index=[name])
        hull_df['hull_x'] = hull_df['hull_x'].astype('object')
        hull_df['hull_y'] = hull_df['hull_y'].astype('object')
        hull_df['hull_reduced_x'] = hull_df['hull_reduced_x'].astype('object')
        hull_df['hull_reduced_y'] = hull_df['hull_reduced_y'].astype('object')

        # Create dataframe that sorts events by distance from mean event position
        hull_data = pd.DataFrame()
        hull_data['x_position'] = events['location'].apply(lambda x: x[0])
        hull_data['y_position'] = events['location'].apply(lambda x: x[1])
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
        hull_df.at[name, 'hull_centre'] = (reduced_hull_data['x_position'].mean(),
                                           reduced_hull_data['y_position'].mean())
        hull_df.at[name, 'hull_area'] = ConvexHull(hull_pts).volume
        hull_df.at[name, 'hull_perimeter'] = ConvexHull(hull_pts).area
        hull_df.at[name, 'hull_area_%'] = round(100 * hull_df.loc[name, 'hull_area'] / pitch_area,2)

    return hull_df


def passes_into_hull(hull_info, events, opp_passes=True, obv_info=False):
    """ Add pass into hull information to dataframe of convex hulls for statsbomb-style event data.

    Function to determine whether one or more passes (passed in as a Statsbomb-style event dataframe) end or pass
    through a convex hull. The function produce a list of successful and unsucessful passes that end within the hull,
    and a list of successful and unsuccessful ground passes that pass through the hull. This information is then used
    to count pass into/through the hull, and add the information to the hull information dataframe. This function
    must be used after create_convex_hull.

    Args:
        hull_info (pandas.Series): series of hull information.
        events (pandas.DataFrame): statsbomb-style events conaining all passes to be checked.
        opp_passes (bool, optional): selection of whether the passes to be checked are opposition or own team.
        obv_info (bool, optional): selection of whether to include obv information. False by default.

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
    events_to_check = events[events['type'] == 'Pass']

    # Create polygon object for convex hull that is being assessed
    polygon = Polygon(list(zip(hull_df['hull_reduced_x'], hull_df['hull_reduced_y'])))
    hull_pts = list(zip(hull_df['hull_reduced_x'], hull_df['hull_reduced_y']))

    # Initialise pass counters
    suc_into_hull_count = 0
    suc_into_hull_obvfor = 0
    suc_into_hull_obvagainst = 0
    suc_into_hull_obvtot = 0
    unsuc_into_hull_count = 0
    unsuc_into_hull_obvfor = 0
    unsuc_into_hull_obvagainst = 0
    unsuc_into_hull_obvtot = 0

    # Check each pass individually
    for _, pass_event in events_to_check.iterrows():

        # If the pass being checked is an opposition pass, flip co-ordinates
        if opp_passes is True:
            pass_start_loc_flip = list(np.subtract([120, 80], pass_event['location']))
            pass_end_loc_flip = list(np.subtract([120, 80], pass_event['pass_end_location']))
        else:
            pass_start_loc_flip = pass_event['location']
            pass_end_loc_flip = pass_event['pass_end_location']

        # Check point is within polygon
        if in_hull(pass_end_loc_flip, hull_pts):

            # Add successful and unsuccessful passes to columns, and count passes / accumulate obv
            if pass_event['pass_outcome'] != pass_event['pass_outcome']:
                suc_into_hull_count += 1
                if obv_info:
                    hull_df['suc_pass_into_hull'].append([pass_start_loc_flip, pass_end_loc_flip,
                                                          pass_event['obv_against_net'], pass_event['obv_for_net']])
                    suc_into_hull_obvfor = np.nansum([suc_into_hull_obvfor, pass_event['obv_for_net']])
                    suc_into_hull_obvagainst = np.nansum([suc_into_hull_obvagainst, pass_event['obv_against_net']])
                    suc_into_hull_obvtot = np.nansum([suc_into_hull_obvtot, pass_event['obv_total_net']])
                else:
                    hull_df['suc_pass_into_hull'].append([pass_start_loc_flip, pass_end_loc_flip])

            else:
                unsuc_into_hull_count += 1
                if obv_info:
                    hull_df['unsuc_pass_into_hull'].append([pass_start_loc_flip, pass_end_loc_flip,
                                                            pass_event['obv_against_net'], pass_event['obv_for_net']])
                    unsuc_into_hull_obvfor = np.nansum([unsuc_into_hull_obvfor, pass_event['obv_for_net']])
                    unsuc_into_hull_obvagainst = np.nansum([unsuc_into_hull_obvagainst, pass_event['obv_against_net']])
                    unsuc_into_hull_obvtot = np.nansum([unsuc_into_hull_obvtot, pass_event['obv_total_net']])
                else:
                    hull_df['unsuc_pass_into_hull'].append([pass_start_loc_flip, pass_end_loc_flip])

    hull_df['count_suc_pass_into_hull'] = suc_into_hull_count
    hull_df['count_unsuc_pass_into_hull'] = unsuc_into_hull_count
    hull_df['pct_tot_pass_into_hull'] = round(100 * (suc_into_hull_count + unsuc_into_hull_count) /
                                              len(events_to_check), 2)
    hull_df['hull_pass_prevented_%'] = round(100 * unsuc_into_hull_count /
                                             (suc_into_hull_count + unsuc_into_hull_count), 2)
    if obv_info:
        hull_df['obvfor_suc_pass_into_hull'] = suc_into_hull_obvfor
        hull_df['obvagainst_suc_pass_into_hull'] = suc_into_hull_obvagainst
        hull_df['obvtot_suc_pass_into_hull'] = suc_into_hull_obvtot
        hull_df['obvfor_unsuc_pass_into_hull'] = unsuc_into_hull_obvfor
        hull_df['obvagainst_unsuc_pass_into_hull'] = unsuc_into_hull_obvagainst
        hull_df['obvtot_unsuc_pass_into_hull'] = unsuc_into_hull_obvtot
        hull_df['obvfor_into_hull'] = suc_into_hull_obvfor + unsuc_into_hull_obvfor
        hull_df['obvtot_into_hull'] = suc_into_hull_obvtot + unsuc_into_hull_obvtot

    return hull_df


def defensive_line_positions(events, team, include_events='1std'):
    """ Calculate the positions of various defensive lines

    Function to calculate defensive line height, mean pressure height and defensive width using positions of various
    events. Defensive line height is calculated by the mean position of centre back defensive actions and opposition
    offsides. Pressure line height is calculated by the mean position of all pressures completed. Defensive width is
    split into left defensive width and right defensive width, each calculated as the mean position of defensive
    actions completed on that side of the pitch. For all calculations, outliers can be removed by specifying an outer
    percentage or number of standard deviations.

    Args:
        events (pandas.DataFrame): statsbomb-style events dataframe, can be from multiple matches
        team (string): name of team to calculate for
        include_events (float, optional): percentage of event locations, or number of standard deviations from mean, to
        include. Event locations that are furthest from the mean location are removed first. Defaults to 1 standard dev.

    Returns:
        float: Defensive line height. Units are consistent with those used in the input events dataframe
        float: Pressure line height. Units are consistent with those used in the input events dataframe
        float: Left defensive width. Units are consistent with those used in the input events dataframe
        float: Right defensive width. Units are consistent with those used in the input events dataframe
        """

    # Initialise outputs
    def_line_event_heights = []
    left_def_widths = []
    right_def_widths = []
    pressure_heights = []

    # Initialise loop outputs in case of no assignment
    def_line_event_height = []
    left_def_width = []
    right_def_width = []
    pressure_height = []

    # Loop through each match. It is important to isolate matches for offside calculations.
    for match_id in events['match_id'].unique():
        match_events = events[events['match_id'] == match_id]

        # Get defensive actions and calculate defensive action positions
        defensive_actions_df = sde.find_defensive_actions(match_events)
        cb_actions = defensive_actions_df[(defensive_actions_df['team'] == team) &
                                                (defensive_actions_df['position'] == 'Center Back')]
        left_def_actions = defensive_actions_df[(defensive_actions_df['team'] == team) &
                                                (defensive_actions_df['position'].isin(['Left Back', 'Left Midfield',
                                                                                        'Left Wing Back',
                                                                                        'Left Wing']))]
        right_def_actions = defensive_actions_df[(defensive_actions_df['team'] == team) &
                                                 (defensive_actions_df['position'].isin(['Right Back', 'Right Midfield',
                                                                                         'Right Wing Back',
                                                                                        'Right Wing']))]
        pressures = match_events[(match_events['team'] == team) & (match_events['type'] == 'Pressure')]

        # Calculate offsides from opposition team
        general_offsides = match_events[(match_events['team'] != team) & (match_events['type'] == 'Offside')]
        pass_offsides = match_events[(match_events['team'] != team) & (match_events['pass_outcome'] == 'Pass Offside')]

        # Create list of heights of defensive line actions for match
        general_offside_heights = [120 - x[0] for x in general_offsides['location'].values]
        pass_offside_heights = [120 - x[0] for x in pass_offsides['pass_end_location'].values]
        cb_action_heights = [x[0] for x in cb_actions['location'].values]
        def_line_event_height = general_offside_heights + pass_offside_heights + cb_action_heights

        # Create list of heights of pressure actions for match
        pressure_height = [x[0] for x in pressures['location'].values]

        # Create list of widths of left defensive actions for match
        left_def_width = [x[1] for x in left_def_actions['location'].values]

        # Create list of widths of right defensive actions for match
        right_def_width = [x[1] for x in right_def_actions['location'].values]

    def_line_event_heights.append(def_line_event_height)
    pressure_heights.append(pressure_height)
    left_def_widths.append(left_def_width)
    right_def_widths.append(right_def_width)

    # Remove (100 - include_percent) or count std of points, starting with furthest from action centroid
    if 'std' in str(include_events):
        num_stds = float(include_events.split('std')[0])
        sqrt_variance_dh = np.sqrt(sum((def_line_event_heights - np.mean(def_line_event_heights))**2) /
                                   (len(def_line_event_heights) - 1))
        def_line_event_heights = np.array(def_line_event_heights)[abs(def_line_event_heights -
                                                                      np.mean(def_line_event_heights)) <=
                                                                  sqrt_variance_dh * num_stds]
        sqrt_variance_p = np.sqrt(sum((pressure_heights - np.mean(pressure_heights))**2) / (len(pressure_heights) - 1))
        pressure_heights = np.array(pressure_heights)[abs(pressure_heights - np.mean(pressure_heights)) <=
                                                      sqrt_variance_p * num_stds]
        sqrt_variance_lw = np.sqrt(sum((left_def_widths - np.mean(left_def_widths))**2) / (len(left_def_widths) - 1))
        left_def_widths = np.array(left_def_widths)[abs(left_def_widths - np.mean(left_def_widths)) <=
                                                    sqrt_variance_lw * num_stds]
        sqrt_variance_rw = np.sqrt(sum((right_def_widths - np.mean(right_def_widths))**2) / (len(right_def_widths) - 1))
        right_def_widths = np.array(right_def_widths)[abs(right_def_widths - np.mean(right_def_widths)) <=
                                                      sqrt_variance_rw * num_stds]

    else:
        def_line_event_heights = np.sort(def_line_event_heights)[0:int((include_events/100) *
                                                                       len(def_line_event_heights))]
        pressure_heights = np.sort(pressure_heights)[0:int((include_events/100) * len(pressure_heights))]
        left_def_widths = np.sort(left_def_widths)[0:int((include_events/100) * len(left_def_widths))]
        right_def_widths = np.sort(right_def_widths)[0:int((include_events/100) * len(right_def_widths))]

    return np.median(def_line_event_heights), np.median(pressure_heights), \
        np.median(left_def_widths), np.median(right_def_widths)


def long_ball_retention(events, player_name, player_team):
    """ Analyse player ability to retain the ball after a long ball is played to them.

    Function to assess a player's ability to retain the ball after a long ball is played into them. A long ball is
    defined as a Ground pass (by Statsbomb definition) longer than 30m, or a Low or High pass (by Statsbomb
    definition) longer than 20m. High passes are excluded if they result in an aerial duel or head-touch on receipt.
    All passes are excluded if they are played directly into the opposition box. These exclusions are made in order
    to better assess the ability of the player to control long passes.  A dataframe is created containing all long
    balls received, player interim carries, player next action, time to next action, next action success and event
    locations. A long ball receipt is considered successful overall if the player does not immediately miscontrol the
    ball, and player's team still has the ball 10 seconds after the long ball was received. Overall success is added
    to the returned long ball dataframe.

    Args:
        events (pandas.DataFrame): statsbomb-style events dataframe, can be from multiple matches
        player_name (string): full name of player receiving long balls.
        player_team (string): team that player receiving long balls belongs to.

    Returns:
        pandas.DataFrame: Dataframe of player long ball receipt information
    """

    # Add pass into box information
    events_out = events.copy()
    events_out.loc[:, 'pass_into_box'] = events_out.apply(pass_into_box, inplay=False, axis=1)

    # Filter out long balls to player outside the box
    to_player = events_out[events_out['pass_recipient'] == player_name]
    long_ball_to_player = to_player[
        ((to_player['pass_length'] > 21.87) & (to_player['pass_height'].isin(['Low Pass', 'High Pass']))) | (
                    (to_player['pass_length'] > 32.8) & (to_player['pass_height'] == 'Ground Pass'))]
    long_ball_to_player = long_ball_to_player[
        long_ball_to_player['pass_into_box'] != long_ball_to_player['pass_into_box']]

    # Initialise long ball receipt dataframe
    long_ball_received = pd.DataFrame(columns=['match_id', 'match_period', 'long_ball_matchtime', 'pass_x', 'pass_y',
                                               'receipt_x', 'receipt_y', 'receipt_under_pressure', 'receipt_miscontrol',
                                               'initial_carry', 'carry_under_pressure', 'init_carry_endx',
                                               'init_carry_endy', 'next_action', 'next_action_success',
                                               'next_action_endx', 'next_action_endy', 't_next_action',
                                               'long_ball_success'])

    for idx, long_ball_evt in long_ball_to_player.iterrows():

        # Get match, period, time and event index
        evt_match, evt_period, evt_time, evt_index = long_ball_evt[['match_id', 'period', 'cumulative_mins', 'index']]

        # Obtain the following 20s worth of events
        following_evts = events_out[(events_out['match_id'] == evt_match) & (events_out['period'] == evt_period) &
                                (events_out['cumulative_mins'] >= evt_time) & (events_out['cumulative_mins'] <= evt_time + 1/3)
                                & (events_out['index'] >= evt_index)].sort_values('index')

        # Get player ball receipt (first instance)
        ball_receipt = following_evts[(following_evts['type'] == 'Ball Receipt*') &
                                      (following_evts['player'] == player_name)].head(1)

        # Initialise flags
        player_initial_carry = pd.DataFrame()
        player_next_evt = pd.DataFrame()
        player_next_evt_type = np.nan
        player_next_evt_success = np.nan
        player_next_evt_endx = np.nan
        player_next_evt_endy = np.nan
        miscontrol = np.nan
        immed_header = False
        
        # Only continue if a ball receipt event is found
        if len(ball_receipt) == 1:
            receipt_time = ball_receipt['cumulative_mins'].values[0]
            player_next_evt_time = np.nan
            receipt_outcome = ball_receipt['ball_receipt_outcome'].values[0]

            # Only continue if ball receipt event is complete
            if receipt_outcome != receipt_outcome:

                # Check for an event that takes place at the same time as the ball receipt, and an event that takes
                # place after the ball receipt
                player_immed_evt = following_evts[(following_evts['player'] == player_name) &
                                                  (following_evts['cumulative_mins'] == receipt_time) &
                                                  (following_evts['type'] != "Ball Receipt*")].head(1)
                player_next_evt = following_evts[(following_evts['player'] == player_name) &
                                                 (following_evts['cumulative_mins'] > receipt_time)].head(1)

                # If there is an immediate event, flag headers from high balls
                if len(player_immed_evt) == 1:
                    immed_header = True if ((player_immed_evt['pass_body_part'].values[0] == 'Head') and
                                            (long_ball_evt['pass_height'] == 'High')) else False

                    # First time pass and shot
                    if player_immed_evt['type'].values[0] == 'Pass':
                        player_next_evt_type = player_immed_evt['type'].values[0]
                        player_next_evt_success = True if (player_immed_evt['pass_outcome'].values[0] !=
                                                           player_immed_evt['pass_outcome'].values[0]) else False
                        [player_next_evt_endx, player_next_evt_endy] = player_immed_evt['pass_end_location'].values[0]
                        player_next_evt_time = player_immed_evt['cumulative_mins'].values[0]

                    elif player_immed_evt['type'].values[0] == 'Shot':
                        player_next_evt_type = player_immed_evt['type'].values[0]
                        player_next_evt_success = True if (player_immed_evt['shot_outcome'].values[0] in
                                                           ['Saved', 'Goal', 'Saved To Pos']) else False
                        [player_next_evt_endx, player_next_evt_endy] = \
                            player_immed_evt['shot_end_location'].values[0][0:2]
                        player_next_evt_time = player_immed_evt['cumulative_mins'].values[0]

                    # Flag miscontrol
                    elif player_immed_evt['type'].values[0] == 'Miscontrol':
                        miscontrol = True

                    # A carry event is an interim event that should be accounted for
                    elif player_immed_evt['type'].values[0] == 'Carry':
                        player_initial_carry = player_immed_evt

                        # The next event should always exist, but if it doesn't
                        if len(player_next_evt) == 1:

                            # Pass and shot
                            if player_next_evt['type'].values[0] == 'Pass':
                                player_next_evt_type = player_next_evt['type'].values[0]
                                player_next_evt_success = True if (player_next_evt['pass_outcome'].values[0] !=
                                                                   player_next_evt['pass_outcome'].values[0]) else False
                                [player_next_evt_endx, player_next_evt_endy] = \
                                    player_next_evt['pass_end_location'].values[0]
                                player_next_evt_time = player_next_evt['cumulative_mins'].values[0]

                            elif player_next_evt['type'].values[0] == 'Shot':
                                player_next_evt_type = player_next_evt['type'].values[0]
                                player_next_evt_success = True if (player_next_evt['shot_outcome'].values[0] in
                                                                   ['Saved', 'Goal', 'Saved To Pos']) else False
                                [player_next_evt_endx, player_next_evt_endy] = \
                                    player_next_evt['shot_end_location'].values[0][0:2]
                                player_next_evt_time = player_next_evt['cumulative_mins'].values[0]

                            # Free kick win
                            elif player_next_evt['type'].values[0] == 'Foul Won':
                                player_next_evt_type = player_next_evt['type'].values[0]
                                player_next_evt_success = True
                                [player_next_evt_endx, player_next_evt_endy] = player_next_evt['location'].values[0]
                                player_next_evt_time = player_next_evt['cumulative_mins'].values[0]

                            # Dribble
                            elif player_next_evt['type'].values[0] == 'Dribble':
                                player_next_evt_type = player_next_evt['type'].values[0]
                                player_next_evt_success = True if player_next_evt['dribble_outcome'].values[
                                                                      0] == 'Complete' else False
                                [player_next_evt_endx, player_next_evt_endy] = player_next_evt['location'].values[0]
                                player_next_evt_time = player_next_evt['cumulative_mins'].values[0]

                            # Dispossession
                            elif player_next_evt['type'].values[0] == 'Dispossessed':
                                player_next_evt_type = player_next_evt['type'].values[0]
                                player_next_evt_success = False
                                [player_next_evt_endx, player_next_evt_endy] = \
                                    player_initial_carry['carry_end_location'].values[0]
                                player_next_evt_time = player_next_evt['cumulative_mins'].values[0]

                            # Flag miscontrol
                            elif player_next_evt['type'].values[0] == 'Miscontrol':
                                miscontrol = True
                                player_initial_carry = pd.DataFrame()
                                player_next_evt = pd.DataFrame()

                # Account for occasions where there is no interim carry and a pass/shot is made after ball receipt
                elif len(player_immed_evt) == 0 and len(player_next_evt) == 1:

                    # Pass and shot
                    if player_next_evt['type'].values[0] == 'Pass':
                        player_next_evt_type = player_next_evt['type'].values[0]
                        player_next_evt_success = True if (player_next_evt['pass_outcome'].values[0] !=
                                                           player_next_evt['pass_outcome'].values[0]) else False
                        [player_next_evt_endx, player_next_evt_endy] = player_next_evt['pass_end_location'].values[0]
                        player_next_evt_time = player_next_evt['cumulative_mins'].values[0]

                    elif player_next_evt['type'].values[0] == 'Shot':
                        player_next_evt_type = player_next_evt['type'].values[0]
                        player_next_evt_success = True if (player_next_evt['shot_outcome'].values[0] in
                                                           ['Saved', 'Goal', 'Saved To Pos']) else False
                        [player_next_evt_endx, player_next_evt_endy] =\
                            player_next_evt['shot_end_location'].values[0][0:2]
                        player_next_evt_time = player_next_evt['cumulative_mins'].values[0]

                # Check team possession 10 seconds after ball receipt
                possession_team = following_evts[(following_evts['cumulative_mins'] <=
                                                  receipt_time + (1 / 6))].iloc[-1:]['possession_team'].values[0]

                # Build long ball dataframe, provided long ball is not a high ball with first time header
                if not immed_header:

                    long_ball_received.loc[idx, 'match_id'] = str(evt_match)
                    long_ball_received.loc[idx, 'match_period'] = evt_period
                    long_ball_received.loc[idx, 'long_ball_matchtime'] = long_ball_evt['timestamp']
                    long_ball_received.loc[idx, ['pass_x', 'pass_y']] = long_ball_evt['location']
                    long_ball_received.loc[idx, ['receipt_x', 'receipt_y']] = long_ball_evt['pass_end_location']
                    long_ball_received.loc[idx, 'receipt_under_pressure'] = ball_receipt['under_pressure'].values[0]
                    long_ball_received.loc[idx, 'receipt_miscontrol'] = miscontrol
                    if len(player_initial_carry) == 1:
                        long_ball_received.loc[idx, 'initial_carry'] = True
                        long_ball_received.loc[idx, 'carry_under_pressure'] = True if (player_initial_carry
                                                                                       ['under_pressure'].values[0]
                                                                                       == True) else np.nan
                        long_ball_received.loc[idx, ['init_carry_endx', 'init_carry_endy']] =\
                            player_initial_carry['carry_end_location'].values[0]
                    long_ball_received.loc[idx, 'next_action'] = player_next_evt_type
                    long_ball_received.loc[idx, 'next_action_success'] = player_next_evt_success
                    long_ball_received.loc[idx, ['next_action_endx', 'next_action_endy']] = [player_next_evt_endx,
                                                                                             player_next_evt_endy]
                    long_ball_received.loc[idx, 't_next_action'] = 60 * (player_next_evt_time - receipt_time)
                    long_ball_received.loc[idx, 'long_ball_success'] = True if (
                                possession_team == player_team and miscontrol != miscontrol) else np.nan

    return long_ball_received
