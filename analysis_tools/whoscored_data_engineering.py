"""Module containing functions to assist with pre-processing and engineering of WhoScored-style data

Functions
---------
get_recipient(events_df):
    Add pass recipient to whoscored-style event data.

add_team_name(events_df, players_df):
    Add team name and opposition team name to event data.

cumulative_match_mins(events):
    Add cumulative minutes to event data and calculate true match minutes

minutes_played(lineups)
    Add total minutes played to player data.

longest_xi(players_df):
    Determine the xi players in each team on the pitch for the longest consistent time.

events_while_playing(events_df, players_df, event_name='Pass', event_team='opposition'):
    Determine number of times an event type occurs whilst players are on the pitch, and add to player dataframe.

create_player_list(lineups, additional_cols=None):
    Create a list of players from whoscored-style lineups dataframe. This requires minutes played information.

group_player_events(events, player_data, group_type='count', agg_columns=None, primary_event_name='Column Name'):
    Aggregate event types per player, and add to player info
    
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


def add_team_name(events_df, players_df):
    """ Add team name and opposition team name to event data.

    Function to add team name and opposition team name to whoscored event data, by extracting playerId and searching
    for team within whoscored player data.

    Args:
        events_df (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.
        players_df (pandas.DataFrame): WhoScored-style dataframe of player information, can be from multiple matches.

    Returns:
        pandas.DataFrame: whoscored-style event dataframe with additional 'team_name' and 'opp_team_name' column.
    """

    # Initialise output dataframes
    events_out = pd.DataFrame()

    # Add cumulative time to events data, resetting for each unique match
    for match_id in events_df['match_id'].unique():
        team_name_and_id = players_df[players_df['match_id'] == match_id][['teamId', 'team']].values
        team_dict = dict.fromkeys([team_name_and_id[0][0], team_name_and_id[-1][0]])
        team_dict[team_name_and_id[0][0]] = team_name_and_id[0][1]
        team_dict[team_name_and_id[-1][0]] = team_name_and_id[-1][1]

        match_events = events_df[events_df['match_id'] == match_id].copy()
        match_events['team_name'] = match_events['teamId'].apply(lambda x: team_dict[x] if x == x else np.nan)
        match_events['opp_team_name'] = match_events['teamId'].apply(
            lambda x: "".join(dict((k, v) for k, v in team_dict.items() if k != x).values()) if x == x else np.nan)

        # Rebuild events dataframe
        events_out = pd.concat([events_out, match_events])

    return events_out


def cumulative_match_mins(events_df):
    """ Add cumulative minutes to event data and calculate true match minutes.

    Function to calculate cumulative match minutes, accounting for extra time, and add the information to whoscored
    event data.

    Args:
        events_df (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: whoscored-style event dataframe with additional 'cumulative_mins' column.
        """

    # Initialise output dataframes
    events_out = pd.DataFrame()

    # Add cumulative time to events data, resetting for each unique match
    for match_id in events_df['match_id'].unique():
        match_events = events_df[events_df['match_id'] == match_id].copy()
        match_events['cumulative_mins'] = match_events['minute'] + (1/60) * match_events['second']

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

        # Rebuild events dataframe
        events_out = pd.concat([events_out, match_events])

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

        # Determine total match length from event data, if passed (protect against erroneous mins)
        if events_df is not None:
            match_events = events_df[events_df['match_id'] == match_id]
            match_minutes = match_events['expandedMinute'].max()
            if match_minutes >= 300:
                match_minutes = 95
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


def events_while_playing(events_df, players_df, event_name='Pass', event_team='opposition'):
    """ Determine number of times an event type occurs whilst players are on the pitch, and add to player dataframe.

    Function to calculate the total number of specific event-types that a player either faces or own team completes
    in each game, and add the information to a WhoScored-style dataframe. The user must define the event type to
    aggregate using WhoScored convention, and specify whether to aggregate for the player's own team or the
    opposition. For example, this function could be used to calculate the number of passes the opposition team makes,
    and assign to each player within the lineups dataframe.

    Args:
        events_df (pandas.DataFrame): WhoScored-style dataframe of event data. Events can be from multiple matches.
        players_df (pandas.DataFrame): WhoScored-style dataframe of players, can be from multiple matches.
        event_name (str): WhoScored event type to aggregate data on. Requires WhoScored convention. Defaults to 'Pass'
        event_team (str): aggregate on the player's own team or opposition team. Defaults to opposition.

    Returns:
        pandas.DataFrame: WhoScored-style player dataframe with additional events count column.
    """

    # Initialise output dataframe
    players_df_out = pd.DataFrame()

    # Add event count to lineup data, resetting for each individual match
    for match_id in events_df['match_id'].unique():
        match_events = events_df[events_df['match_id'] == match_id].copy()
        players = players_df[players_df['match_id'] == match_id].copy()

        # For each team calculate team events, and assign to player
        for team in set(match_events['teamId']):
            team_players = players[players['teamId'] == team].copy()

            # Choose whether to include own team or opposition events, and build column name
            if event_team == 'own':
                if event_name == 'Touch':
                    team_events = match_events[(match_events['teamId'] == team) &
                                               (match_events['isTouch'] == True)]
                else:
                    team_events = match_events[(match_events['teamId'] == team) &
                                               (match_events['eventType'] == event_name)]
                col_name = 'team_' + event_name.lower()

            else:
                if event_name == 'Touch':
                    team_events = match_events[(match_events['teamId'] != team) &
                                               (match_events['isTouch'] == True)]
                else:
                    team_events = match_events[(match_events['teamId'] != team) &
                                               (match_events['eventType'] == event_name)]

                col_name = 'opp_' + event_name.lower()

            # For each player, count events whilst they were on the pitch
            for idx, player in team_players.iterrows():
                event_count = len(team_events[(team_events['expandedMinute'] > player['time_on']) &
                                              (team_events['expandedMinute'] < player['time_off'])])
                team_players.loc[idx, col_name] = event_count

            # Rebuild lineups dataframe
            players_df_out = pd.concat([players_df_out, team_players])

    return players_df_out


def create_player_list(lineups, additional_cols=None, pass_extra=None):
    """ Create a list of players from whoscored-style lineups dataframe. This requires minutes played information.

    Function to read a whoscored-style lineups dataframe (single or multiple matches) and return a dataframe of
    players that featured in squads. When multiple matches are passes, the function will determine the position that a
    player most frequently plays. The function will also aggregate player information if columns are passed into the
    additional_cols argument.

    Args:
        lineups (pandas.DataFrame): statsbomb-style dataframe of lineups, including mins played, can be from multiple matches.
        additional_cols (list): list of column names to be aggregated and included in output dataframe.
        pass_extra (list, optional): list of extra columns within lineups to include in output dataframe.

    Returns:
        pandas.DataFrame: players that feature in one or more lineup entries, including most popular position played
    """    

    # Resolve data integrity issues
    lineups.loc[lineups['name'] == 'Vitalii Mykolenko', 'name'] = 'Vitaliy Mykolenko'
    lineups.loc[lineups['name'] == 'Alexander Iwobi', 'name'] = 'Alex Iwobi'
    lineups.loc[lineups['name'] == 'Robert Brady', 'name'] = 'Robbie Brady'

    # Dataframe of player names and team
    if pass_extra is None:
        playerinfo_df = lineups[['name', 'position', 'team']].drop_duplicates()
    else:
        playerinfo_df = lineups[['name', 'position', 'team'] + pass_extra].drop_duplicates()

    # Calculate total playing minutes for each player and add to dataframe
    if additional_cols is None:
        included_cols = lineups.groupby(['name', 'position', 'team'], axis=0).sum(numeric_only=True)['mins_played']
    else:
        included_cols = lineups.groupby(['name', 'position', 'team'], axis=0).sum(numeric_only=True)[['mins_played']
                                                                                                     + additional_cols]

    playerinfo_df = playerinfo_df.merge(included_cols, left_on=['name', 'position', 'team'], right_index=True)
    
    # Sum minutes played in each position
    playerinfo_df['tot_mins_played'] = playerinfo_df.groupby(['name', 'team'])['mins_played'].transform('sum')
    if additional_cols is not None:
        for col in additional_cols:
            playerinfo_df['tot_' + col] = playerinfo_df.groupby(['name', 'team'])[col].transform('sum')

    # Order player entries by minutes played, ensuring most popular position is at the top.
    playerinfo_df.sort_values('mins_played', ascending=False, inplace=True)
    
    # Remove duplicates, leaving only the player in their most popular position
    playerinfo_df = playerinfo_df[~playerinfo_df[['name','team']].duplicated(keep='first')]
    
    # Rename columns 
    playerinfo_df['mins_played'] = playerinfo_df['tot_mins_played']
    playerinfo_df.drop('tot_mins_played', axis=1, inplace=True)
    if additional_cols is not None:
        for col in additional_cols:
            playerinfo_df[col] = playerinfo_df['tot_' + col]
            playerinfo_df.drop('tot_' + col, axis=1, inplace=True)
    
    # Add position type
    playerinfo_df['pos_type'] = playerinfo_df['position'].apply(lambda x: 'DEF' if x in ['DC', 'DL', 'DR', 'DMR', 'DML'] else 
                                                                ('MID' if x in ['AML', 'AMR', 'AMC', 'DM', 'DMC', 'MC', 'ML', 'MR'] else 
                                                                 ('FWD' if x in ['FW', 'FWL', 'FWR'] else 
                                                                  'GK' if x in ['GK'] else 'SUB')))
 
    return playerinfo_df


def group_player_events(events, player_data, group_type='count', agg_columns=None, col_names='Column Name'):
    """ Aggregate event types per player, and add to player information dataframe

    Function to read a whoscored-style events dataframe (single or multiple matches) and return a dataframe of
    aggregated information per player. Aggregation may be an event count or an event sum, based on the group_type
    input.

    Args:
        events (pandas.DataFrame): whoscored-style dataframe of event data. Events can be from multiple matches.
        player_data (pandas.DataFrame): whoscored-style dataframe of player information. Must include a 'name' column.
        group_type (string, optional): aggregation method, can be set to 'sum' or 'count'. 'count' by default.
        agg_columns (list or string, optional): list of columns in event to aggregate, additional to the main
                                                aggregation event.
        col_names (list or string, optional): name of main event type being aggregated (e.g. 'pass'). Used to
                                                        name the aggregated column within player_data dataframe.

    Returns:
        pandas.DataFrame: statsbomb-style dataframe of player information, including aggregated data.
    """

    # Specify agg_columns as list if not assigned
    if agg_columns is None:
        agg_columns = list()
    elif type(agg_columns) == str:
        agg_columns = [agg_columns]

    # Initialise output dataframe
    player_data_out = player_data.copy()

    # Perform aggregation based on grouping type input
    if group_type == 'count':
        grouped_events = events.groupby('playerId', axis=0).count()
        selected_events = grouped_events[agg_columns].copy()
        selected_events.loc[:, col_names] = grouped_events['match_id']
    elif group_type == 'sum':
        grouped_events = events.groupby('playerId', axis=0).sum(numeric_only=True)
        selected_events = grouped_events[agg_columns].copy()
    elif group_type == 'mean':
        grouped_events = events.groupby('playerId', axis=0).mean(numeric_only=True)
        selected_events = grouped_events[agg_columns].copy()
    else:
        selected_events = pd.DataFrame()

    # Merge into player information dataframe
    player_data_out = player_data_out.merge(selected_events, left_on='playerId', right_index=True, how='left')
    if type(col_names) == str:
        col_names = [col_names]
    if agg_columns != list() and group_type in ['sum', 'mean']:
        for idx in np.arange(len(agg_columns)):
            player_data_out = player_data_out.rename(columns={agg_columns[idx]: col_names[idx]})

    # Remove nulls and replace with 0
    player_data_out[col_names] = player_data_out[col_names].fillna(0)

    return player_data_out


