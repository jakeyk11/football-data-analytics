"""Module containing functions to assist with pre-processing and engineering of WhoScored-style data

Functions
---------
get_recipient(events_df):
    Add pass recipient to whoscored-style event data.

minutes_played(lineups)
    Add total minutes played to player data.

longest_xi(players_df):
    Determine the xi players in each team on the pitch for the longest consistent time.

create_player_list(lineups, additional_cols=None):
    Create a list of players from whoscored-style lineups dataframe

find_offensive_actions(events_df):
    Return dataframe of in-play offensive actions from event data.

find_defensive_actions(events_df):
    Return dataframe of in-play defensive actions from event data.
"""

import pandas as pd
import numpy as np


def get_recipient(events_df):
    """ Add pass recipient to whoscored-style event data.

    Determine the pass recipient from who-scored style event data, and add information to the event dataframe.

    Args:
        events_df (pandas.DataFrame, optional): WhoScored-style event dataframe

    Returns:
        pandas.DataFrame: WhoScored-style event dataframe with additional pass recipient column
        """

    # Initialise output dataframe
    events_out = events_df.copy()

    # Shift dataframe to calculate pass recipient
    events_out["pass_recipient"] = events_out["playerId"].shift(-1)

    return events_out


def minutes_played(players_df, events_df=None):
    """ Add total minutes played to WhoScored player data.

    Determine the total number of minutes each player played in each match, and add information to the WhoScored
    player dataframe. Requires an event data argument corresponding to each match to determine match lengths and
    calculate minutes played accurately. If not passed a total match length of 95 minutes will be assumed.

    Args:
        players_df (pandas.DataFrame): WhoScored-style dataframe of player information, can be from multiple matches.
        events_df (pandas.DataFrame, optional): WhoScored-style event dataframe, used to calculate total match minutes. None by default.

    Returns:
        pandas.DataFrame: WhoScored-style player dataframe with additional time columns.
        """

    # Nested function to calculate and format time played from match duration and line-up dataframe
    def time_played(player, total_mins):
        if player['isFirstEleven'] is True:
            time_on = 0
            if player['subbedOutExpandedMinute'] != player['subbedOutExpandedMinute']:
                time_off = total_mins
            else:
                time_off = player['subbedOutExpandedMinute']
        elif player['subbedInExpandedMinute'] == player['subbedInExpandedMinute']:
            time_on = player['subbedInExpandedMinute']
            if player['subbedOutExpandedMinute'] != player['subbedOutExpandedMinute']:
                time_off = total_mins
            else:
                time_off = player['subbedOutExpandedMinute']
        else:
            time_on = np.nan
            time_off = np.nan
        mins_played = time_off - time_on
        return [time_on, time_off, mins_played]

    # Initialise output dataframes
    players_df_out = pd.DataFrame()

    # Add cumulative time to events data, resetting for each unique match
    for match_id in players_df['match_id'].unique():
        players = players_df[players_df['match_id'] == match_id]

        # Determine total match length from event data, if passed
        if events_df is not None:
            match_events = events_df[events_df['match_id'] == match_id]
            match_minutes = max(match_events['expandedMinute'])
        else:
            match_minutes = 95

        # Apply time_played function to reformat time on and time off, and calculate minutes played
        players[['time_on', 'time_off', 'mins_played']] = players.apply(time_played, axis=1, result_type="expand",
                                                                        total_mins=match_minutes)

        # Rebuild player dataframe
        players_df_out = pd.concat([players_df_out, players])

    return players_df_out


def longest_xi(players_df):
    """ Determine the xi players in each team on the pitch for the longest consistent time.

    Determine the xi players in each team that stay on the pitch for the longest time together, and add information
    to the Whoscored player dataframe. It is intended that this function is used after minutes_played has been called.

    Args:
        players_df (pandas.DataFrame): WhoScored-style dataframe of player information, can be from multiple matches.

    Returns:
        pandas.DataFrame: WhoScored-style player dataframe with additional longest_xi column."""

    # Initialise output dataframes
    players_df_out = pd.DataFrame()

    # Add cumulative time to events data, resetting for each unique match
    for match_id in players_df['match_id'].unique():
        players = players_df[players_df['match_id'] == match_id]
        players['longest_xi'] = np.nan

        # Determine match length and initialise list of sub minutes.
        match_end = max(players_df['time_off'])
        sub_mins = [[], []]

        # Determine the longest same xi for each team individually
        for idx, team in enumerate(players['teamId'].unique()):
            team_player_df = players[players['teamId'] == team]

            # Get minutes players are subbed off
            for _, player in team_player_df.iterrows():
                if player['time_off'] != match_end and player['time_off'] == player['time_off']:
                    sub_mins[idx].append(player['time_off'])

            # Add in match start minute and match end minute, then sort by minute
            sub_mins[idx].insert(0, 0)
            sub_mins[idx].append(int(match_end))
            sub_mins[idx].sort()

            # Longest xi corresponds to the largest time between subs. Get indices of start and end min.
            max_min_diff = 0
            same_team_idxx = 1
            for idxx in np.arange(1, len(sub_mins[idx])):
                min_diff = sub_mins[idx][idxx] - sub_mins[idx][idxx - 1]
                if min_diff > max_min_diff:
                    max_min_diff = min_diff
                    same_team_idxx = idxx
            same_team_mins = [sub_mins[idx][same_team_idxx - 1], sub_mins[idx][same_team_idxx]]

            # Check if players game time includes the longest xi times, and mark if they feature in the longest xi
            for playerid, player in team_player_df.iterrows():
                if player['time_on'] <= same_team_mins[0] and player['time_off'] >= same_team_mins[1]:
                    players.loc[playerid, 'longest_xi'] = True

        # Rebuild player dataframe
        players_df_out = pd.concat([players_df_out, players])

    return players_df_out


def create_player_list(lineups, additional_cols=None):
    """ Create a list of players from whoscored-style lineups dataframe

    Function to read a whoscored-style lineups dataframe (single or multiple matches) and return a dataframe of
    players that featured in squad. The function will also aggregate player information if columns are passed into the
    additional_cols argument.

    Args:
        lineups (pandas.DataFrame): statsbomb-style dataframe of lineups, can be from multiple matches.
        additional_cols (list): list of column names to be aggregated and included in output dataframe.

    Returns:
        pandas.DataFrame: players that feature in one or more lineup entries, may include total minutes played.
    """

    # Specify additional_cols as list if not assigned
    if additional_cols is None:
        additional_cols = list()

    # Dataframe of player names and nicknames
    playerinfo_df = lineups[['name', 'position', 'team']].drop_duplicates()

    # If include_mins = True, calculate total playing minutes for each player and add to dataframe
    included_cols = lineups.groupby('name', axis=0).sum()[additional_cols]
    playerinfo_df = playerinfo_df.merge(included_cols, left_on='name', right_index=True)

    return playerinfo_df


def group_player_events(events, player_data, group_type='count', event_types=None, primary_event_name='Column Name'):
    """ Aggregate event types per player, and add to player information dataframe

    Function to read a whoscored-style events dataframe (single or multiple matches) and return a dataframe of
    aggregated information per player. Aggregation may be an event count or an event sum, based on the group_type
    input.

    Args:
        events (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.
        player_data (pandas.DataFrame): whoscored-style dataframe of player information. Must include a 'name' column.
        group_type (string, optional): aggregation method, can be set to 'sum' or 'count'. 'count' by default.
        event_types (list, optional): list of columns in event to aggregate, additional to the main aggregation event.
        primary_event_name (string, optional): name of main event type being aggregated (e.g. 'pass'). Used to name the
                                           aggregated column within player_data dataframe.

    Returns:
        pandas.DataFrame: statsbomb-style dataframe of player information, including aggregated data.
    """

    # Specify event_types as list if not assigned
    if event_types is None:
        event_types = list()

    # Initialise output dataframe
    player_data_out = player_data.copy()

    # Perform aggregation based on grouping type input
    if group_type == 'count':
        grouped_events = events.groupby('playerId', axis=0).count()
        selected_events = grouped_events[event_types]
        selected_events.loc[:, primary_event_name] = grouped_events['match_id']
    elif group_type == 'sum':
        grouped_events = events.groupby('playerId', axis=0).sum()
        selected_events = grouped_events[event_types]
    else:
        selected_events = pd.DataFrame()

    # Merge into player information dataframe
    player_data_out = player_data_out.merge(selected_events, left_on='playerId', right_index=True, how='outer')
    return player_data_out


def find_offensive_actions(events_df):
    """ Return dataframe of in-play offensive actions from event data.

    Function to find all in-play offensive actions within a whoscored-style events dataframe (single or multiple
    matches), and return as a new dataframe.

    Args:
        events_df (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style dataframe of offensive actions.
    """

    # Define and filter offensive events
    offensive_actions = ['BallTouch', 'TakeOn', 'Pass', 'OffsidePass', 'MissedShots', 'SavedShot', 'Goal']
    offensive_action_df = events_df[events_df['eventType'].isin(offensive_actions)].reset_index(drop=True)

    return offensive_action_df


def find_defensive_actions(events_df):
    """ Return dataframe of in-play defensive actions from event data.

    Function to find all in-play defensive actions within a whscored-style events dataframe (single or multiple
    matches), and return as a new dataframe.

    Args:
        events_df (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: whoscored-style dataframe of defensive actions.
    """

    # Define and filter defensive events
    defensive_actions = ['BallRecovery', 'BlockedPass', 'Challenge', 'Clearance', 'Foul', 'Interception', 'Tackle',
                         'Claim', 'KeeperPickup', 'Punch', 'Save']
    defensive_action_df = events_df[events_df['eventType'].isin(defensive_actions)]

    return defensive_action_df
