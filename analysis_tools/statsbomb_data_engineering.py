"""Module containing functions to assist with pre-processing and engineering of StatsBomb-style data

Functions
---------
cumulative_match_mins(events)
    Add cumulative minutes to event data and calculate true match minutes.

get_playtime_and_position(events, lineups)
    Add time played and position played information to lineups dataframe.

longest_xi(lineups):
    Determine the xi players in each team on the pitch for the longest consistent time.

events_while_playing(events, lineups, event_name='Pass', event_team='opposition')
    Determine number of times an event type occurs whilst players are on the pitch, and add to lineups dataframe.

add_player_nickname(events, lineups)
    Add player nicknames to statsbomb-style event data, using statsbomb-style lineups dataframe

create_player_list(lineups, additional_cols=None, pass_extra=None, group_team=False)
    Create a list of players from statsbomb-style lineups dataframe.

group_player_events(events, player_data, group_type='count', event_types=None, primary_event_name='Column Name'):
    Aggregate event types per player, and add to player information dataframe.

create_team_list(lineups):
    Create a list of teams from statsbomb-style lineups dataframe

group_team_events(events, team_info, group_type='count', agg_columns=None, primary_event_name='Column Name'):
    Aggregate event types per team, and add to team information dataframe.
"""

import numpy as np
import pandas
import pandas as pd


def cumulative_match_mins(events):
    """ Add cumulative minutes to event data and calculate true match minutes.

    Function to calculate cumulative match minutes, accounting for extra time, and add the information to statsbomb
    event data.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style event dataframe with additional 'cumulative_mins' column.
        """

    # Function to format time stamp
    def convert_time(t):
        return 60 * float(t.split(':')[0]) + float(t.split(':')[1]) + (1/60) * float(t.split(':')[2])

    # Initialise output dataframes
    events_out = pd.DataFrame()
    lineups_out = pd.DataFrame()

    # Add cumulative time to events data, resetting for each unique match
    for match_id in events['match_id'].unique():
        match_events = events[events['match_id'] == match_id].copy()
        match_events['cumulative_mins'] = match_events['timestamp'].apply(convert_time)

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


def get_playtime_and_position(events, lineups):
    """ Add time played and position played information to lineups dataframe.

    Function to calculate the total time (including added time) that a player spends on the pitch, and the position
    in which they played. This information is obtained by scanning a Statsbomb style event dataframe for starting
    xis, substitutions, tactical changes and red cards. The information is then added to a statsbomb style lineups
    dataframe. Both events and lineups can be from one or multiple matchee.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        lineups (pandas.DataFrame, optional): statsbomb-style dataframe of lineups, can be from multiple matches.

    Returns:
        pandas.DataFrame: statsbomb-style lineup dataframe with additional time and position columns.
        """

    # Initialise output dataframes
    lineups_out = lineups
    lineups_out['position'] = 'Sub'

    # Isolate each match, calculate duration and find starting xi, substitutions, tactical changes and red cards
    for match_id in events['match_id'].unique():
        match_duration = events[events['match_id'] == match_id]['cumulative_mins'].max()
        player_changes = events[(events['match_id'] == match_id) &
                                (events['type'].isin(['Starting XI', 'Substitution',
                                                      'Tactical Shift', 'Bad Behaviour']))]
        # Isolate each team
        for team in player_changes['team'].unique():
            # Loop through starting xis, adding positions and time played to lineups dataframe
            for player in player_changes[(player_changes['team'] == team) &
                                         (player_changes['type'] == 'Starting XI')]['tactics'].values[0]['lineup']:
                lineups_out.at[lineups_out[(lineups_out['player_id'] == player['player']['id'])
                                           & (lineups_out['match_id'] == match_id)].index.values[0],
                               'position'] = ''.join(s[0] for s in player['position']['name'].split())
                lineups_out.at[lineups_out[(lineups_out['player_id'] == player['player']['id']) &
                                           (lineups_out['match_id'] == match_id)].index.values[0], 'time_on'] = 0
                lineups_out.at[lineups_out[(lineups_out['player_id'] == player['player']['id']) &
                                           (lineups_out['match_id'] == match_id)].index.values[0],
                               'time_off'] = match_duration
            # Loop through substitutions, and update minutes played information
            for _, substitution in player_changes[(player_changes['team'] == team) &
                                                  (player_changes['type'] == 'Substitution')].iterrows():
                lineups_out.at[lineups_out[(lineups_out['player_name'] == substitution['substitution_replacement']) &
                                           (lineups_out['match_id'] == match_id)].index.values[0],
                               'position'] = ''.join(s[0] for s in substitution['position'].split())
                lineups_out.at[lineups_out[(lineups_out['player_id'] == substitution['player_id']) &
                                           (lineups_out['match_id'] == match_id)].index.values[0],
                               'time_off'] = substitution['cumulative_mins']
                lineups_out.at[lineups_out[(lineups_out['player_name'] == substitution['substitution_replacement'])
                                           & (lineups_out['match_id'] == match_id)].index.values[0],
                               'time_on'] = substitution['cumulative_mins']
                lineups_out.at[lineups_out[(lineups_out['player_name'] == substitution['substitution_replacement'])
                                           & (lineups_out['match_id'] == match_id)].index.values[0],
                               'time_off'] = match_duration
            # Loop through red cards, and update minutes played information
            for _, sent_off in player_changes[(player_changes['team'] == team) &
                                              (player_changes['bad_behaviour_card'].isin(
                                                  ['Red Card', 'Second Yellow']))].iterrows():
                lineups_out.at[lineups_out[(lineups_out['player_id'] == sent_off['player_id']) &
                                           (lineups_out['match_id'] == match_id)].index.values[0],
                               'time_off'] = sent_off['cumulative_mins']

    lineups_out['mins_played'] = lineups_out['time_off'] - lineups_out['time_on']
    lineups_out.loc[lineups_out['mins_played'] != lineups_out['mins_played'], 'mins_played'] = 0

    return lineups_out


def longest_xi(lineups):
    """ Determine the xi players in each team on the pitch for the longest consistent time.

    Determine the xi players in each team that stay on the pitch for the longest time together, and add information
    to the Statsbomb line-ups dataframe. It is intended that this function is used after playtime has been calculated.

    Args:
        lineups (pandas.DataFrame): Statsbomb-style dataframe of player information, can be from multiple matches.

    Returns:
        pandas.DataFrame: WhoScored-style player dataframe with additional longest_xi column."""

    # Initialise output dataframes
    lineups_out = pd.DataFrame()

    # Add cumulative time to events data, resetting for each unique match
    for match_id in lineups['match_id'].unique():
        lineups = lineups[lineups['match_id'] == match_id]
        lineups['longest_xi'] = np.nan

        # Determine match length and initialise list of sub minutes.
        match_end = lineups['time_off'].max()
        sub_mins = [[], []]

        # Determine the longest same xi for each team individually
        for idx, team in enumerate(lineups['team_name'].unique()):
            team_lineup_df = lineups[lineups['team_name'] == team]

            # Get minutes players are subbed off
            for _, player in team_lineup_df.iterrows():
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
            for playerid, player in team_lineup_df.iterrows():
                if player['time_on'] <= same_team_mins[0] and player['time_off'] >= same_team_mins[1]:
                    lineups.loc[playerid, 'longest_xi'] = True

        # Rebuild player dataframe
        lineups_out = pd.concat([lineups_out, lineups])

    return lineups_out


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
        match_events = events[events['match_id'] == match_id].copy()
        lineup = lineups[lineups['match_id'] == match_id].copy()

        # For each team calculate team events, and assign to player
        for team in set(match_events['team']):
            team_lineup = lineup[lineup['team_name'] == team]

            # Choose whether to include own team or opposition events, and build column name
            if event_team == 'own':
                if event_name == 'Touch':
                    team_events = match_events[(match_events['team'] == team) &
                                               (match_events['istouch'] == match_events['istouch'])]
                elif event_name == 'Possession':
                    team_events = match_events[match_events['possession_team'] == team]
                else:
                    team_events = match_events[(match_events['team'] == team) &
                                               (match_events['type'] == event_name)]
                col_name = 'team_' + event_name.lower()

            else:
                if event_name == 'Touch':
                    team_events = match_events[(match_events['team'] != team) &
                                               (match_events['istouch'] == match_events['istouch'])]
                elif event_name == 'Possession':
                    team_events = match_events[match_events['possession_team'] != team]
                else:
                    team_events = match_events[(match_events['team'] != team) &
                                               (match_events['type'] == event_name)]

                col_name = 'opp_' + event_name.lower()

            # For each player, count events whilst they were on the pitch
            for idx, player in team_lineup.iterrows():
                if event_name == 'Possession':
                    event_count = len(set(team_events[(team_events['cumulative_mins'] >= player['time_on']) &
                                                      (team_events['cumulative_mins'] <= player['time_off'])]
                                          ['possession']))
                else:
                    event_count = len(team_events[(team_events['cumulative_mins'] >= player['time_on']) &
                                                  (team_events['cumulative_mins'] <= player['time_off'])])
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


def create_player_list(lineups, additional_cols=None, pass_extra=None, group_team=False):
    """ Create a list of players from statsbomb-style lineups dataframe

    Function to read a statsbomb-style lineups dataframe (single or multiple matches) and return a dataframe of
    players that featured in squads. When multiple matches are passes, the function will determine the position that a
    player most frequently plays. The function will also aggregate player information if columns are passed into the
    additional_cols argument.

    Args:
        lineups (pandas.DataFrame): statsbomb-style dataframe of lineups, can be from multiple matches.
        additional_cols (list, optional): list of column names to be aggregated and included in output dataframe.
        pass_extra (list, optional): list of extra columns within lineups to include in output dataframe.
        group_team (bool, optional): decide whether to group player if played for multiple teams (transfer)

    Returns:
        pandas.DataFrame: players that feature in one or more lineup entries, may include total minutes played.
    """

    # Nested function to group and categorise positions
    def group_positions(position):
        if position in ['G']:
            position_group = 'Goalkeeper'
        elif position in ['CB', 'LCB', 'RCB']:
            position_group = 'Centre Back'
        elif position in ['LB', 'RB']:
            position_group = 'Full-back'
        elif position in ['LWB', 'RWB']:
            position_group = 'Wing-back'
        elif position in ['CDM', 'LDM', 'RDM']:
            position_group = 'Defensive Midfielder'
        elif position in ['CM', 'LCM', 'RCM']:
            position_group = 'Centre Midfielder'
        elif position in ['CAM', 'LAM', 'RAM']:
            position_group = 'Attacking Midfielder'
        elif position in ['LM', 'RM']:
            position_group = 'Wide Midfielder'
        elif position in ['LW', 'RW']:
            position_group = 'Winger'
        elif position in ['CF', 'LCF', 'RCF']:
            position_group = 'Centre Forward'
        elif position in ['Sub']:
            position_group = 'Substitute'
        else:
            position_group = 'Unknown'
        if position_group in ['Goalkeeper']:
            position_category = 'Goalkeeper'
        elif position_group in ['Centre Back', 'Full-back', 'Wing-back']:
            position_category = 'Defender'
        elif position_group in ['Defensive Midfielder', 'Centre Midfielder', 'Attacking Midfielder', 'Wide Midfielder']:
            position_category = 'Midfielder'
        elif position_group in ['Winger', 'Centre Forward']:
            position_category = 'Forward'
        else:
            position_category = position_group

        return position_group, position_category

    # Dataframe of player names and team
    if pass_extra is None:
        playerinfo_df = lineups[['player_id', 'player_name', 'player_nickname', 'position', 'country',
                                 'team_name']].drop_duplicates()
    else:
        playerinfo_df = lineups[['player_id', 'player_name', 'player_nickname', 'position', 'country',
                                 'team_name'] + pass_extra].drop_duplicates()

    # Calculate total playing minutes and other aggregated columns for each player and add to dataframe
    if additional_cols is None:
        included_cols = lineups.groupby(['player_id', 'position', 'team_name'], axis=0).sum()['mins_played']
    else:
        included_cols = lineups.groupby(['player_id', 'position', 'team_name'], axis=0).sum()[['mins_played']
                                                                                              + additional_cols]

    playerinfo_df = playerinfo_df.merge(included_cols, left_on=['player_id', 'position', 'team_name'], right_index=True)

    # Group by player and team (to avoid removing transfers) and drop duplicates due to different positions
    playerinfo_df.sort_values('mins_played', ascending=False, inplace=True)
    playerinfo_df[['mins_played'] + additional_cols] = (playerinfo_df.groupby(['player_id', 'team_name'])
                                                        [['mins_played'] + additional_cols].transform('sum'))
    playerinfo_df.drop_duplicates(subset=['player_id', 'team_name'], keep='first', inplace=True)

    # Remove duplicate teams if required
    if group_team:
        playerinfo_df.sort_values('mins_played', ascending=False, inplace=True)
        playerinfo_df[['mins_played'] + additional_cols] = (playerinfo_df.groupby(['player_id'])
                                                            [['mins_played'] + additional_cols].transform('sum'))
        playerinfo_df.drop_duplicates(subset=['player_id'], keep='first', inplace=True)

    # Add position info
    playerinfo_df['position_group'], playerinfo_df['position_category'] = zip(*playerinfo_df['position'].
                                                                              apply(group_positions))

    return playerinfo_df.set_index('player_id')


def group_player_events(events, player_data, group_type='count', agg_columns=None, primary_event_name='Column Name'):
    """ Aggregate event types per player, and add to player information dataframe

    Function to read a statsbomb-style events dataframe (single or multiple matches) and return a dataframe of
    aggregated information per player. Aggregation may be an event count or an event sum, based on the group_type
    input.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        player_data (pandas.DataFrame): statsbomb-style dataframe of player information. Must include a 'player_id'
                                        column.
        group_type (string, optional): aggregation method, can be set to 'sum' or 'count'. 'count' by default.
        agg_columns (list, optional): list of columns in event to aggregate, for sum or mean aggregation.
        primary_event_name (string, optional): name of main event type being aggregated (e.g. 'pass'). Used to name the
                                           aggregated column within player_data dataframe.

    Returns:
        pandas.DataFrame: statsbomb-style dataframe of player information, including aggregated data.
    """

    # Specify agg_columns as list if not assigned
    if agg_columns is None:
        agg_columns = list()

    # Initialise output dataframe
    player_data_out = player_data.copy()

    # Perform aggregation based on grouping type input
    if group_type == 'count':
        grouped_events = events.groupby('player_id', axis=0).count()
        selected_events = grouped_events[agg_columns].copy()
        selected_events.loc[:, primary_event_name] = grouped_events['match_id']
    elif group_type == 'sum':
        grouped_events = events.groupby('player_id', axis=0).sum()
        selected_events = grouped_events[agg_columns].copy()
    elif group_type == 'mean':
        grouped_events = events.groupby('player_id', axis=0).mean()
        selected_events = grouped_events[agg_columns].copy()
    else:
        selected_events = pd.DataFrame()

    # Merge into player information dataframe
    player_data_out = player_data_out.merge(selected_events, left_on='player_id', right_index=True, how='outer')
    return player_data_out


def create_team_list(lineups):
    """ Create a list of teams from statsbomb-style lineups dataframe

    Function to read a statsbomb-style lineups dataframe (single or multiple matches) and return a dataframe of
    teams that featured, number of games played and total minutes played.

    Args:
        lineups (pandas.DataFrame): statsbomb-style dataframe of lineups, can be from multiple matches.

    Returns:
        pandas.DataFrame: teams that feature in one or more lineup entries, including total minutes played.
    """

    teaminfo_df = lineups[['team_name', 'match_id']].drop_duplicates()

    included_cols_max = lineups.groupby(['team_name', 'match_id'], axis=0).max()['mins_played']

    teaminfo_df = teaminfo_df.merge(included_cols_max, left_on=['team_name', 'match_id'], right_index=True)
    teaminfo_df['matches_played'] = 1

    teaminfo_df = teaminfo_df.groupby(['team_name']).sum()[['mins_played', 'matches_played']]

    return teaminfo_df


def group_team_events(events, team_info, group_type='count', agg_columns=None, primary_event_name='Column Name'):
    """ Aggregate event types per team, and add to team information dataframe

    Function to read a statsbomb-style events dataframe (single or multiple matches) and return a dataframe of
    aggregated information per team. Aggregation may be an event count or an event sum, based on the group_type
    input.

    Args:
        events (pandas.DataFrame): statsbomb-style dataframe of event data. Events can be from multiple matches.
        team_info (pandas.DataFrame): statsbomb-style dataframe of team information. Must include a 'team' column.
        group_type (string, optional): aggregation method, can be set to 'sum' or 'count'. 'count' by default.
        agg_columns (list, optional): list of columns in event to aggregate, for sum or mean aggregation.
        primary_event_name (string, optional): name of main event type being aggregated (e.g. 'pass'). Used to name the
                                           aggregated column within player_data dataframe.

    Returns:
        pandas.DataFrame: statsbomb-style dataframe of team information, including aggregated data.
    """

    # Specify agg_columns as list if not assigned
    if agg_columns is None:
        agg_columns = list()

    # Initialise output dataframe
    team_info_out = team_info.copy()

    # Perform aggregation based on grouping type input
    if group_type == 'count':
        grouped_events = events.groupby('team', axis=0).count()
        selected_events = grouped_events[agg_columns].copy()
        selected_events.loc[:, primary_event_name] = grouped_events['match_id']
    elif group_type == 'sum':
        grouped_events = events.groupby('team', axis=0).sum()
        selected_events = grouped_events[agg_columns].copy()
    elif group_type == 'mean':
        grouped_events = events.groupby('team', axis=0).mean()
        selected_events = grouped_events[agg_columns].copy()
    else:
        selected_events = pd.DataFrame()

    # Merge into player information dataframe
    team_info_out = team_info_out.merge(selected_events, left_on='team_name', right_index=True, how='outer')
    return team_info_out
