"""Module containing functions to assist with pre-processing and engineering of StatsBomb-style data

Functions
---------
cumulative_match_mins(events, lineups=None)
    Add cumulative minutes to event data and calculate true match minutes.
    
events_while_playing(events, lineups, event_name='Pass', event_team='opposition')
    Determine number of times an event type occurs whilst players are on the pitch, and add to lineups dataframe.

add_player_nickname(events, lineups)
    Add player nicknames to statsbomb-style event data, using statsbomb-style lineups dataframe

create_player_list(lineups, include_mins=False)
    Create a list of players from statsbomb-style lineups dataframe.

group_player_events(events, player_data, group_type='count', event_types=None, primary_event_name='Column Name'):
    Aggregate event types per player, and add to player information dataframe.

find_offensive_actions(events)
    Return dataframe of in-play offensive actions from event data

find_defensive_actions(events)
    Return dataframe of in-play defensive actions from event data.
"""

import numpy as np
import pandas
import pandas as pd


def cumulative_match_mins(events, lineups=None):
    """ Add cumulative minutes to event data and calculate true match minutes.

    Function to calculate cumulative match minutes, accounting for extra time, and add the information to statsbomb
    event data. If passed a lineups dataframe, the function will use cumulative minutes calculations to determine the
    number of minutes played by each player in each match, again adding the information to the lineups dataframe.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        lineups (pandas.DataFrame, optional): statsbomb-style dataframe of lineups, can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style event dataframe with additional 'cumulative_mins' column.
        pandas.DataFrame: statsbomb-style lineup dataframe with additional time columns. Empty if lineups isn't passed.
        """

    # Nested function to calculate and format time played from match duration and line-up dataframe
    def time_played(match_lineup, match_minutes):
        time_on = match_lineup['time_on']
        time_off = match_lineup['time_off']
        if not match_lineup['positions']:
            time_on = 0
            time_off = 0
        if time_on != time_on:
            time_on = 0
        if time_off != time_off:
            time_off = match_minutes
        mins_played = time_off - time_on
        return [time_on, time_off, mins_played]

    # Initialise output dataframes
    events_out = pd.DataFrame()
    lineups_out = pd.DataFrame()

    # Add cumulative time to events data, resetting for each unique match
    for match_id in events['match_id'].unique():
        match_events = events[events['match_id'] == match_id]
        match_events.loc[:, 'cumulative_mins'] = (match_events.loc[:, 'minute'] +
                                                  (1 / 60) * match_events.loc[:, 'second'])

        # Add time increment to cumulative minutes based on period of game.
        for period in np.arange(1, match_events['period'].max() + 1, 1):
            if period > 1:
                t_delta = match_events[match_events['period'] == period - 1]['cumulative_mins'].max() - \
                          match_events[match_events['period'] == period]['cumulative_mins'].min()
            elif period == 1 or period == 5:
                t_delta = 0
            else:
                t_delta = 0
            match_events.loc[match_events['period'] == period, 'cumulative_mins'] += t_delta

        # Calculate total game time and rebuild events dataframe
        total_mins = match_events['cumulative_mins'].max()
        events_out = pd.concat([events_out, match_events])

        # Obtain corresponding match lineups, if lineups is passed as an input.
        if lineups is not None:
            lineup = lineups[lineups['match_id'] == match_id]

            # Add time on and time off to each player in the lineup by obtaining substitute info from match events
            for _, sub in match_events[match_events['type'] == 'Substitution'].iterrows():
                lineup.loc[lineup['player_name'] == sub['substitution_replacement'], 'time_on'] = sub['cumulative_mins']
                lineup.loc[lineup['player_name'] == sub['player'], 'time_off'] = sub['cumulative_mins']

            # Apply time_played function to reformat time on and time off, and calculate minutes played
            lineup[['time_on', 'time_off', 'mins_played']] = lineup.apply(time_played, axis=1, result_type="expand",
                                                                          match_minutes=total_mins)
            # Rebuild lineups dataframe
            lineups_out = pd.concat([lineups_out, lineup])

        else:
            lineups_out = pd.DataFrame()

    return events_out, lineups_out


def events_while_playing(events, lineups, event_name='Pass', event_team='opposition'):
    """ Determine number of times an event type occurs whilst players are on the pitch, and add to lineups dataframe.

    Function to calculate the total number of specific event-types that a player either faces or own team completes
    in each game, and add the information to a statsbomb-style dataframe. The user must define the event type to
    aggregate using statsbomb convention, and specify whether to aggregate for the player's own team or the
    opposition. For example, this function could be used to calculate the number of passes the opposition team makes,
    and assign to each player within the lineups dataframe.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        lineups (pandas.DataFrame): statsbomb-style dataframe of lineups, can be from multiple matches.
        event_name (str): statsbomb event type to aggregate data on. Requires statsbomb convention. Defaults to 'Pass'
        event_team (str): aggregate on the player's own team or opposition team. Defaults to opposition.

    Returns:
        pandas.DataFrame: statsbomb-style lineup dataframe with additional events count column.
    """

    # Initialise output dataframe
    lineups_out = pd.DataFrame()

    # Add event count to lineup data, resetting for each individual match
    for match_id in events['match_id'].unique():
        match_events = events[events['match_id'] == match_id]
        lineup = lineups[lineups['match_id'] == match_id]

        # For each team calculate team events, and assign to player
        for team in set(match_events['team']):
            team_lineup = lineup[lineup['team_name'] == team]

            # Choose whether to include own team or opposition events, and build column name
            if event_team == 'own':
                team_events = match_events[(match_events['possession_team'] == team) &
                                           (match_events['type'] == event_name)]
                col_name = 'team_' + event_name.lower()

            else:
                team_events = match_events[(match_events['possession_team'] != team) &
                                           (match_events['type'] == event_name)]
                col_name = 'opp_' + event_name.lower()

            # For each player, count events whilst they were on the pitch
            for idx, player in team_lineup.iterrows():
                event_count = len(team_events[(team_events['cumulative_mins'] > player['time_on']) &
                                              (team_events['cumulative_mins'] < player['time_off'])])
                lineup.loc[idx, col_name] = event_count

        # Rebuild lineups dataframe
        lineups_out = pd.concat([lineups_out, lineup])

    return lineups_out


def add_player_nickname(events, lineups):
    """ Add player nicknames to statsbomb-style event data, using statsbomb-style lineups dataframe

    Function to read in statsbomb-style lineups dataframe, match player nicknames to player names and then add player
    nicknames to statsbomb event data. Also removes None values from lineups player_nickname column, allowing it to
    be used for text visualisation.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        lineups (pandas.DataFrame): statsbomb-style dataframe of lineups, can be from multiple matches.
    Returns:
        pandas.DataFrame: statsbomb-style dataframe of event data, with additional player nickname column.
        pandas.DataFrame: statsbomb-style dataframe of lineup data, with complete player nickname column.
    """

    # Initialise dataframes
    events_out = events.copy()
    lineups_out = lineups.copy()

    # Fill missing lineup nicknames
    lineups_out['player_nickname'] = lineups_out.apply(lambda row: (row['player_name'] if row['player_nickname'] is None
                                                                    else row['player_nickname']), axis=1)

    # Create dataframe that matches player nicknames to player names
    names_df = lineups_out[['player_name', 'player_nickname']].drop_duplicates()

    # Find all player names in lineups dataframe, and match to nicknames
    events_out = events_out.merge(names_df, left_on='player', right_on='player_name',
                                  how='left').drop('player_name', axis=1)

    return events_out, lineups_out


def create_player_list(lineups, additional_cols=None):
    """ Create a list of players from statsbomb-style lineups dataframe

    Function to read a statsbomb-style lineups dataframe (single or multiple matches) and return a dataframe of
    players that featured in squad. The function will also aggregate minutes played by each player if minutes_played
    argument is set to True.

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
    playerinfo_df = lineups[['player_name', 'player_nickname']].drop_duplicates()

    # If include_mins = True, calculate total playing minutes for each player and add to dataframe
    included_cols = lineups.groupby('player_name', axis=0).sum()[additional_cols]
    playerinfo_df = playerinfo_df.merge(included_cols, left_on='player_name', right_index=True)

    return playerinfo_df


def group_player_events(events, player_data, group_type='count', event_types=None, primary_event_name='Column Name'):
    """ Aggregate event types per player, and add to player information dataframe

    Function to read a statsbomb-style events dataframe (single or multiple matches) and return a dataframe of
    aggregated information per player. Aggregation may be an event count or an event sum, based on the group_type
    input.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        player_data (pandas.DataFrame): statsbomb-style dataframe of player information. Must include a 'player_name'
                                        column.
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
        grouped_events = events.groupby('player', axis=0).count()
        selected_events = grouped_events[event_types]
        selected_events.loc[:, primary_event_name] = grouped_events['match_id']
    elif group_type == 'sum':
        grouped_events = events.groupby('player', axis=0).sum()
        selected_events = grouped_events[event_types]
    else:
        selected_events = pd.DataFrame()

    # Merge into player information dataframe
    player_data_out = player_data_out.merge(selected_events, left_on='player_name', right_index=True, how='outer')
    return player_data_out


def find_offensive_actions(events):
    """ Return dataframe of in-play offensive actions from event data.

    Function to find all in-play offensive actions within a statsbomb-style events dataframe (single of multiple
    matches), and return as a new dataframe.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style dataframe of offensive actions.
    """

    # Define and filter offensive events
    offensive_actions = ['Carry', 'Dribble', 'Foul Won', 'Pass', 'Shot']
    offensive_action_df = events[events['type'].isin(offensive_actions)].reset_index(drop=True)

    # Remove defensive foul won
    offensive_action_df = offensive_action_df.drop(offensive_action_df[offensive_action_df['foul_won_defensive']
                                                                       == True].index)

    # Remove unsuccessful pass
    offensive_action_df = offensive_action_df.drop(offensive_action_df[offensive_action_df['pass_outcome'] ==
                                                                       offensive_action_df['pass_outcome']].index)

    # Remove passes from set pieces
    offensive_action_df = offensive_action_df.drop(offensive_action_df[offensive_action_df['pass_type']
                                                   .isin(['Corner', 'Free Kick', 'Throw-in'])].index)

    # Remove shots from set pieces
    offensive_action_df = offensive_action_df.drop(offensive_action_df[(offensive_action_df['shot_type'] != 'Open Play')
                                                                       & (offensive_action_df['type'] == 'Shot')].index)

    return offensive_action_df


def find_defensive_actions(events):
    """ Return dataframe of in-play defensive actions from event data.

    Function to find all in-play defensive actions within a statsbomb-style events dataframe (single of multiple
    matches), and return as a new dataframe.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style dataframe of defensive actions.
    """

    # Define and filter offensive events
    defensive_actions = ['Ball Recovery', 'Block', 'Clearance', 'Interception', 'Pressure', 'Duel', '50/50', 'Foul Won']
    defensive_action_df = events[events['type'].isin(defensive_actions)].reset_index(drop=True)

    # Remove offensive team block
    defensive_action_df = defensive_action_df.drop(defensive_action_df[defensive_action_df['block_offensive']
                                                                       == True].index)

    # Remove offensive foul won
    defensive_action_df = defensive_action_df.drop(defensive_action_df[(defensive_action_df['foul_won_defensive'] !=
                                                                        True) & (defensive_action_df['type'] ==
                                                                                 'Foul Won')].index)

    return defensive_action_df
