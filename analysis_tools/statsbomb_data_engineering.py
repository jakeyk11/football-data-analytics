"""Module containing functions to assist with pre-processing and engineering of StatsBomb-style data

Functions
---------
add_cumulative_mins(events)
    Add cumulative minutes to event data and calculate true match minutes.

process_lineups(lineups, events, tactics):
    Process and format statsbomb-style lineup information.

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

create_league_table(matches, xmetrics=False):
    Create a league table from statsbomb-style matches dataframe
"""

import numpy as np
import pandas as pd
import datetime


def add_cumulative_mins(events):
    """ Add cumulative match minutes to event data

    Function to calculate cumulative match minutes, accounting for added time, extra time and period transitions.
    This adds a new column 'cumulative_mins' to the event dataframe.

    Args:
        events (pandas.DataFrame): dataframe of event data. Events can be from multiple matches or just one.

    Returns:
        pandas.DataFrame: event dataframe with additional 'cumulative_mins' column.
    """

    # Function to convert time stamp to mins
    def convert_time(t):
        if isinstance(t, datetime.time):
            t_out = 60 * t.hour + t.minute + (1 / 60) * t.second

        else:
            t_out = 0
        return t_out

    # Initialise output dataframe
    events_out = pd.DataFrame()

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

        # Combine individual matches if events for multiple matches have been passed
        events_out = pd.concat([events_out, match_events])

    return events_out


def process_lineups(lineups, events, tactics):
    """ Process and format statsbomb-style lineup information

    Function to proces statsbomb-style lineup dataframe, including the addition of the positions and formations that
    each player played in and for how long (cumulatively). This function only works with lineupss and tactics dataframes
    that have been generated with the mplsoccer parser. This function generates 2 lineup dataframes, the first of which
    is consistent with the default statsbomb output, but includes starting formation, position breakdowns and cumulative
    minutes played by each player. The starting xi and longest xi are also tagged. The second dataframe is a custom
    lineup dataframe that includes information on tactical changes and breaks down minutes played by each player in a
    specific position and/or system. The starting xi, longest xi and longest tactic are also tagged. The fucntion will
    construct output dataframes for one or multiple matches.

    Args:
        lineups (pandas.DataFrame): statsbomb-style dataframe of lineup data, parsed using mplsoccer
        events (pandas.DataFrame): statsbomb-style dataframe of event data, parsed using mplsoccer
        tactics (pandas.DataFrame): statsbomb-style dataframe of tactic data, parsed using mplsoccer

    Returns:
        pandas.DataFrame: core lineup dataframe, focusing on general and positional involvement
        pandas.DataFrame: custom lineup dataframe, focusing on positional and tactical involvement
    """

    def group_positions(position):
        """ Define positions and position groups based on Statsbomb style position name

        Args:
            position (string): position name

        Returns:
            position_group (string): grouped position e.g. full back, center midfielder, winger
            position_category (string): cateogorised position e.g. Goalkeeper, defender, midfielder, forward
        """

        if position in ['Goalkeeper']:
            position_group = 'Goalkeeper'
        elif position in ['Left Back', 'Right Back']:
            position_group = 'Full Back'
        elif position in ['Left Center Back', 'Center Back', 'Right Center Back']:
            position_group = 'Center Back'
        elif position in ['Left Wing Back', 'Right Wing Back']:
            position_group = 'Wing Back'
        elif position in ['Left Defensive Midfield', 'Center Defensive Midfield', 'Right Defensive Midfield']:
            position_group = 'Defensive Midfielder'
        elif position in ['Left Center Midfield', 'Center Midfield', 'Right Center Midfield']:
            position_group = 'Center Midfielder'
        elif position in ['Left Midfield', 'Right Midfield']:
            position_group = 'Wide Midfielder'
        elif position in ['Left Attacking Midfield', 'Center Attacking Midfield', 'Right Attacking Midfield']:
            position_group = 'Attacking Midfielder'
        elif position in ['Left Wing', 'Right Wing']:
            position_group = 'Winger'
        elif position in ['Left Center Forward', 'Center Forward', 'Right Center Forward', 'Striker',
                          'Secondary Striker']:
            position_group = 'Center Forward'
        elif position in ['Substitute']:
            position_group = 'Substitute'
        else:
            position_group = 'Unknown'

        if position_group in ['Goalkeeper']:
            position_category = 'Goalkeeper'
        elif position_group in ['Center Back', 'Full Back', 'Wing Back']:
            position_category = 'Defender'
        elif position_group in ['Defensive Midfielder', 'Center Midfielder', 'Attacking Midfielder', 'Wide Midfielder']:
            position_category = 'Midfielder'
        elif position_group in ['Centre Forward']:
            position_category = 'Forward'
        else:
            position_category = position_group

        return position_group, position_category

    # Initialise output dataframes
    lineups_out = pd.DataFrame()
    lineups_dense_out = pd.DataFrame()

    # Iterate through each match found within events dataframe
    for match_id in events['match_id'].unique():

        # Get lineups for match
        match_lineups = pd.DataFrame()
        match_start_lineups = lineups[lineups['match_id'] == match_id].copy()
        match_events = events[events['match_id'] == match_id]
        match_tactics = tactics[tactics['match_id'] == match_id]

        # Determine match duration by looking at maximum time
        match_duration = match_events['cumulative_mins'].max()

        # Get starting xis and add position/formation information to match lineups
        starting_xis = match_events[match_events['type_name'] == 'Starting XI']
        starting_xi_players = match_tactics[match_tactics['id'].isin(starting_xis['id'])]
        match_start_lineups = match_start_lineups.merge(starting_xi_players[['player_id', 'position_name']], how="left",
                                                        on='player_id')
        starting_formations = starting_xis[['team_id', 'tactics_formation']]
        match_start_lineups = match_start_lineups.merge(starting_formations, how="left", on='team_id')

        # Set identifier for start lineups
        match_start_lineups['tactical_setup_id'] = 0
        match_start_lineups['player_setup_id'] = 0

        # Fill time on information for starting xi and position information for subs
        match_start_lineups.loc[
            match_start_lineups['position_name'] == match_start_lineups['position_name'], 'time_on'] = 0
        match_start_lineups.loc[match_start_lineups['position_name'] != match_start_lineups[
            'position_name'], 'position_name'] = 'Substitute'

        # Look at each team tactical changes individually
        for team_id in events[events['match_id'] == match_id]['team_id'].unique():

            # Initialise counters
            idx = 0
            tactic_change_idx = 0
            player_change_idx = 0

            # Get team starting lineups
            team_lineups = match_start_lineups[match_start_lineups['team_id'] == team_id].copy()

            # Get team tactical events (if they exist)
            if len(match_events[match_events['type_name'] == 'Substitution']) != 0:
                team_sub_events = match_events[
                    (match_events['team_id'] == team_id) & (match_events['type_name'] == 'Substitution')]
            else:
                team_sub_events = pd.DataFrame()

            if len(match_events[match_events['type_name'] == 'Tactical Shift']) != 0:
                team_tactical_shift_events = match_events[
                    (match_events['team_id'] == team_id) & (match_events['type_name'] == 'Tactical Shift')]
            else:
                team_tactical_shift_events = pd.DataFrame()

            if 'bad_behaviour_card_name' in match_events.columns:
                team_bad_behaviour_events = match_events[(match_events['team_id'] == team_id) & (
                    match_events['bad_behaviour_card_name'].isin(['Red Card', 'Second Yellow']))]
            else:
                team_bad_behaviour_events = pd.DataFrame()

            if 'foul_committed_card_name' in match_events.columns:
                team_foulcard_events = match_events[(match_events['team_id'] == team_id) & (
                    match_events['foul_committed_card_name'].isin(['Red Card', 'Second Yellow']))]
            else:
                team_foulcard_events = pd.DataFrame()

            team_tactical_events = pd.concat(
                [team_sub_events, team_tactical_shift_events, team_bad_behaviour_events, team_foulcard_events],
                ignore_index=False).sort_index()

            # Tag end of time of starting lineup (first time something changes)
            if len(team_tactical_events) >= 1:
                team_lineups.loc[(team_lineups['position_name'] != 'Substitute'), 'time_off'] = team_tactical_events[
                    'cumulative_mins'].min()
            else:
                team_lineups.loc[(team_lineups['position_name'] != 'Substitute'), 'time_off'] = match_duration

            # Store latest lineup as previous lineup (which will be updated later)
            prev_lineup = team_lineups[(team_lineups['position_name'] != 'Substitute')]

            # Iterate through tactical events
            for _, team_tactical_event in team_tactical_events.iterrows():

                # Tactical shifts
                if team_tactical_event['type_name'] == 'Tactical Shift':

                    # Iterate tactical change id
                    tactic_change_idx += 1

                    # Get xi
                    current_xi = match_tactics[match_tactics['id'] == team_tactical_event['id']].sort_values(
                        'player_id')
                    current_xi = current_xi[current_xi['player_id'].isin(prev_lineup['player_id'])]

                    # Copy prev lineup players based on new xi, and store new positions, formation and sub times
                    lineup_entry = prev_lineup[
                        prev_lineup['player_id'].isin(current_xi['player_id'])].copy().sort_values('player_id')
                    lineup_entry['tactics_formation'] = team_tactical_event['tactics_formation']
                    lineup_entry['position_name'] = current_xi['position_name'].tolist()
                    lineup_entry['time_on'] = team_tactical_event['cumulative_mins']
                    lineup_entry['time_off'] = match_duration if idx == len(team_tactical_events) - 1 else \
                    team_tactical_events.iloc[idx + 1, :]['cumulative_mins']

                # Subs
                elif team_tactical_event['type_name'] == 'Substitution':

                    # Iterate tactical change and player change id
                    player_change_idx += 1
                    tactic_change_idx += 1

                    # Copy prev lineup players and replace info for subbed player(s)
                    lineup_entry = prev_lineup.sort_values('player_id')
                    subbed_in = team_lineups[
                        team_lineups['player_id'] == team_tactical_event['substitution_replacement_id']].tail(1)
                    subbed_out = lineup_entry[lineup_entry['player_id'] == team_tactical_event['player_id']]
                    subbed_in['position_name'] = subbed_out['position_name'].values[0]
                    subbed_in['tactics_formation'] = subbed_out['tactics_formation'].values[0]
                    lineup_entry = pd.concat([lineup_entry, subbed_in], ignore_index=True)
                    lineup_entry['time_on'] = team_tactical_event['cumulative_mins']
                    lineup_entry['time_off'] = (match_duration if idx == len(team_tactical_events) - 1 else
                                                team_tactical_events.iloc[idx + 1, :]['cumulative_mins'])
                    lineup_entry = lineup_entry[lineup_entry['player_id'] != team_tactical_event['player_id']]

                # Red card or second yellow
                elif team_tactical_event['type_name'] in ['Bad Behaviour', 'Foul Committed']:

                    # Iterate tactical change and player change id
                    player_change_idx += 1
                    tactic_change_idx += 1

                    # Copy prev lineup players and remove sent off player
                    lineup_entry = prev_lineup.sort_values('player_id')
                    lineup_entry = lineup_entry[lineup_entry['player_id'] != team_tactical_event['player_id']]
                    lineup_entry['time_on'] = team_tactical_event['cumulative_mins']
                    lineup_entry['time_off'] = (match_duration if idx == len(team_tactical_events) - 1 else
                                                team_tactical_events.iloc[idx + 1, :]['cumulative_mins'])

                # Add identifier for tactical or lineup change using tags
                lineup_entry['tactical_setup_id'] = tactic_change_idx
                lineup_entry['player_setup_id'] = player_change_idx

                # Register current lineup to previous lineup and add to dataframe
                prev_lineup = lineup_entry.copy()
                team_lineups = pd.concat([team_lineups, lineup_entry], ignore_index=True)
                idx += 1

            # Add time played
            team_lineups['time_played'] = team_lineups['time_off'] - team_lineups['time_on']

            # Tag players in starting xi
            team_lineups['starting_xi'] = team_lineups['player_id'].apply(
                lambda x: 1 if x in list(team_lineups[team_lineups['time_on'] == 0]['player_id']) else np.nan)

            # Tag longest tactical setup
            temp_team_lineups = team_lineups[team_lineups['position_name'] != 'Substitute']
            grouped_tactical_lineups = temp_team_lineups[~temp_team_lineups.duplicated(keep='first',
                                                                                       subset=['player_setup_id',
                                                                                               'tactical_setup_id'])]
            longest_tactical_setup_ids = (grouped_tactical_lineups[grouped_tactical_lineups['time_played'] == np.max(grouped_tactical_lineups['time_played'])][['player_setup_id', 'tactical_setup_id']])

            team_lineups['longest_tactic'] = team_lineups[['player_setup_id', 'tactical_setup_id', 'time_played']].apply(lambda x: 1 if x[0] == longest_tactical_setup_ids['player_setup_id'].values[0] and x[1] == longest_tactical_setup_ids['tactical_setup_id'].values[0] and x[2] == x[2] else np.nan, axis=1)

            # Tag longest xi
            grouped_player_lineups = temp_team_lineups[~temp_team_lineups.duplicated(keep='first', subset=['player_setup_id', 'tactical_setup_id'])].groupby('player_setup_id', as_index=False).sum(numeric_only=True)
            longest_player_setup_id = grouped_player_lineups[grouped_player_lineups['time_played'] == np.max(grouped_player_lineups['time_played'])]['player_setup_id']
            team_lineups['longest_xi'] = team_lineups[['player_setup_id', 'time_played']].apply(lambda x: 1 if x[0] == longest_player_setup_id.values[0] and x[1] == x[1] else np.nan, axis=1)

            # Build match lineup from team lineups
            match_lineups = pd.concat([match_lineups, team_lineups], ignore_index=True)

        # Condense lineup dataframe to avoid duplicating full xis for substitutes
        match_lineups = match_lineups.sort_values(['match_id', 'team_id', 'player_id',
                                                   'time_on']).reset_index(drop=True)
        match_lineups = pd.concat([match_lineups.groupby(['player_id', 'player_name', 'player_nickname', 'birth_date',
                                                          'player_gender', 'player_height', 'player_weight',
                                                          'jersey_number', 'match_id', 'competition', 'season',
                                                          'team_id', 'team_name', 'country_id', 'country_name',
                                                          'position_name', 'tactics_formation'], dropna=False, as_index=False).min().drop(columns=['time_off', 'time_played']),
                                   match_lineups.groupby(['player_id', 'player_name', 'player_nickname', 'birth_date',
                                                          'player_gender', 'player_height', 'player_weight',
                                                          'jersey_number', 'match_id', 'competition', 'season',
                                                          'team_id', 'team_name', 'country_id', 'country_name',
                                                          'position_name', 'tactics_formation'], dropna=False, as_index=False).max()['time_off']], axis=1)
        match_lineups['time_played'] = match_lineups['time_off'] - match_lineups['time_on']

        # Further condense to revert to standard lineups dataframe (using players most common position)
        match_lineups_condensed = pd.concat([match_lineups.groupby(['player_id', 'player_name', 'player_nickname',
                                                                    'birth_date', 'player_gender', 'player_height',
                                                                    'player_weight', 'jersey_number', 'match_id',
                                                                    'competition', 'season', 'team_id', 'team_name',
                                                                    'country_id', 'country_name'], dropna=False, as_index=False).
                                            min().drop(columns=['time_off', 'longest_tactic', 'tactics_formation',
                                                                'position_name', 'tactical_setup_id', 'player_setup_id',
                                                                'time_played']),
                                             match_lineups.groupby(['player_id', 'player_name', 'player_nickname',
                                                                    'birth_date', 'player_gender', 'player_height',
                                                                    'player_weight', 'jersey_number', 'match_id',
                                                                    'competition', 'season', 'team_id', 'team_name',
                                                                    'country_id', 'country_name'],dropna=False, as_index=False).max()['time_off']], axis=1)

        match_lineups_condensed['time_played'] = match_lineups_condensed['time_off']-match_lineups_condensed['time_on']

        # Add longest positions per player to condensed version
        player_pos_grouped = match_lineups.groupby(['player_id','position_name'],
                                                   as_index=False).sum(numeric_only=True).sort_values(['player_id', 'time_played'], ascending=False)
        player_pos_grouped = player_pos_grouped[~player_pos_grouped.duplicated(keep='first', subset=['player_id']
                                                                               )][['player_id', 'position_name']]
        match_lineups_condensed['position_name'] = match_lineups_condensed.merge(player_pos_grouped, how='left',
                                                                                 on='player_id')['position_name']

        # Add longest formation to condensed version
        team_form_grouped = match_lineups.groupby(['player_id', 'team_id', 'tactics_formation'], as_index=False
                                                  ).sum(numeric_only=True).sort_values(['team_id', 'time_played'],
                                                                                       ascending=False)
        team_form_grouped = team_form_grouped[~team_form_grouped.duplicated(keep='first',
                                                                            subset=['team_id'])][['team_id', 'tactics_formation']]
        match_lineups_condensed['tactics_formation'] = match_lineups_condensed.merge(team_form_grouped,
                                                                                     how='left', on='team_id'
                                                                                     )['tactics_formation']

        # Add abbreviated position names to dataframes
        match_lineups['position_group'], match_lineups['position_category'] = zip(
            *match_lineups['position_name'].apply(group_positions))
        match_lineups_condensed['position_group'], match_lineups_condensed['position_category'] = zip(
            *match_lineups_condensed['position_name'].apply(group_positions))

        # Sort and order dataframes
        match_lineups.sort_values(['match_id', 'team_name', 'time_on'], inplace=True)
        match_lineups_condensed.sort_values(['match_id', 'team_name', 'time_on'], inplace=True)
        match_lineups = match_lineups[
            list(match_lineups.columns[0:16]) + ['position_group', 'position_category', 'tactics_formation', 'time_on',
                                                 'time_off', 'time_played', 'starting_xi', 'longest_xi',
                                                 'longest_tactic']]
        match_lineups_condensed = match_lineups_condensed[
            list(match_lineups_condensed.columns[0:15]) + ['position_name', 'position_group', 'position_category',
                                                           'tactics_formation', 'time_on', 'time_off', 'time_played',
                                                           'starting_xi', 'longest_xi']]

        # Build multi-match dataframes
        lineups_out = pd.concat([lineups_out, match_lineups_condensed], ignore_index=True)
        lineups_dense_out = pd.concat([lineups_dense_out, match_lineups], ignore_index=True)

    # Reset index
    lineups_out = lineups_out.reset_index(drop=True)
    lineups_dense_out = lineups_dense_out.reset_index(drop=True)

    return lineups_out, lineups_dense_out


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
        for team in set(match_events['team_name']):
            team_lineup = lineup[lineup['team_name'] == team]

            # Choose whether to include own team or opposition events, and build column name
            if event_team == 'own':
                if event_name == 'Touch':
                    team_events = match_events[(match_events['team_name'] == team) &
                                               (match_events['touch_type'] == match_events['touch_type'])]
                elif event_name == 'Possession':
                    team_events = match_events[match_events['possession_team_name'] == team]
                else:
                    team_events = match_events[(match_events['team_name'] == team) &
                                               (match_events['type_name'] == event_name)]
                col_name = 'team_' + event_name.lower()

            else:
                if event_name == 'Touch':
                    team_events = match_events[(match_events['team_name'] != team) &
                                               (match_events['touch_type'] == match_events['touch_type'])]
                elif event_name == 'Possession':
                    team_events = match_events[match_events['possession_team_name'] != team]
                else:
                    team_events = match_events[(match_events['team_name'] != team) &
                                               (match_events['type_name'] == event_name)]

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


def create_player_list(lineups, additional_cols=None, pass_extra=None, group_position=True, group_team=False,
                       group_comp=True):
    """ Create a list of players from statsbomb-style lineups dataframe

    Function to read a statsbomb-style lineups dataframe (single or multiple matches) and return a dataframe of
    players that featured in squads. When multiple matches are passes, the function will determine the position that a
    player most frequently plays. The function will also aggregate player information if columns are passed into the
    additional_cols argument.

    Args:
        lineups (pandas.DataFrame): statsbomb-style dataframe of lineups, can be from multiple matches.
        additional_cols (list, optional): list of column names to be aggregated and included in output dataframe.
        pass_extra (list, optional): list of extra columns within lineups to include in output dataframe.
        group_position (bool, optional): decide whether to group player minutes in different positions (transfer). True
        by default.
        group_team (bool, optional): decide whether to group player if played for multiple teams (transfer). False by
        default.
        group_comp (bool, optional): decide whether to group players over multiple competitions/seasons. True by default

    Returns:
        pandas.DataFrame: players that feature in one or more lineup entries, may include total minutes played.
    """

    # Dataframe of player names and team
    if pass_extra is None:
        playerinfo_df = lineups[['player_id', 'player_name', 'player_nickname', 'position_name', 'position_group',
                                 'position_category', 'country_name', 'team_name', 'competition',
                                 'season']].drop_duplicates()
    else:
        playerinfo_df = lineups[['player_id', 'player_name', 'player_nickname', 'position_name', 'position_group',
                                 'position_category', 'country_name', 'team_name', 'competition', 'season']
                                + pass_extra].drop_duplicates()

    # Calculate total playing minutes and other aggregated columns for each player and add to dataframe
    if additional_cols is None:
        included_cols = lineups.groupby(['player_id', 'position_name', 'position_group', 'position_category',
                                         'team_name', 'competition',
                                         'season'], axis=0).sum(numeric_only=True)['time_played']
    else:
        included_cols = lineups.groupby(['player_id', 'position_name', 'position_group', 'position_category',
                                         'team_name', 'competition',
                                         'season'], axis=0).sum(numeric_only=True)[['time_played'] + additional_cols]

    playerinfo_df = playerinfo_df.merge(included_cols, left_on=['player_id', 'position_name', 'position_group',
                                                                'position_category', 'team_name', 'competition',
                                                                'season'], right_index=True)

    # Group players minutes in different positions (if group_position is True). Keep most common position per player
    if group_position:
        playerinfo_df.sort_values('time_played', ascending=False, inplace=True)
        if additional_cols is None:
            playerinfo_df['time_played'] = (playerinfo_df.groupby(['player_id', 'team_name', 'competition', 'season'])
                                            ['time_played'].transform('sum'))
        else:
            playerinfo_df[['time_played'] + additional_cols] = (playerinfo_df.groupby(['player_id', 'team_name',
                                                                                       'competition', 'season'])
                                                                [['time_played'] + additional_cols].transform('sum'))
        playerinfo_df.drop_duplicates(subset=['player_id', 'team_name', 'competition', 'season'], keep='first',
                                      inplace=True)

    # Group players minutes for different team / remove transfers (if group_team is True). Keep most common team
    if group_team:
        playerinfo_df.sort_values('time_played', ascending=False, inplace=True)
        if additional_cols is None:
            playerinfo_df['time_played'] = (playerinfo_df.groupby(['player_id', 'competition', 'season'])
                                            ['time_played'].transform('sum'))
        else:
            playerinfo_df[['time_played'] + additional_cols] = (playerinfo_df.groupby(['player_id', 'competition',
                                                                                       'season'])
                                                            [['time_played'] + additional_cols].transform('sum'))
        playerinfo_df.drop_duplicates(subset=['player_id', 'competition', 'season'], keep='first', inplace=True)

    # Group players minutes over different competitions (if group_comp is True).
    if group_comp:
        if additional_cols is None:
            playerinfo_df['time_played'] = (playerinfo_df.groupby(['player_id'])['time_played'].transform('sum'))
        else:
            playerinfo_df[['time_played'] + additional_cols] = (playerinfo_df.groupby(['player_id'])
                                                                [['time_played'] + additional_cols].transform('sum'))
        playerinfo_df.drop_duplicates(subset=['player_id'], keep='first', inplace=True)
        playerinfo_df = playerinfo_df.drop(columns=['competition', 'season'])

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

    # Drop column if one with identical name exists
    if primary_event_name in player_data_out.columns:
        player_data_out = player_data_out.drop(primary_event_name, axis=1)

    # Perform aggregation based on grouping type input
    if group_type == 'count':
        grouped_events = events.groupby('player_id', axis=0).count()
        selected_events = grouped_events[agg_columns].copy()
        selected_events.loc[:, primary_event_name] = grouped_events['match_id']
    elif group_type == 'sum':
        grouped_events = events.groupby('player_id', axis=0).sum(numeric_only=True)
        selected_events = grouped_events[agg_columns].copy()
    elif group_type == 'mean':
        grouped_events = events.groupby('player_id', axis=0).mean(numeric_only=True)
        selected_events = grouped_events[agg_columns].copy()
    else:
        selected_events = pd.DataFrame()

    # Merge into player information dataframe
    player_data_out = player_data_out.merge(selected_events, left_on='player_id', right_index=True, how='left')
    if agg_columns != list() and group_type in ['sum', 'mean']:
        player_data_out = player_data_out.rename(columns={agg_columns: primary_event_name})
        
    # Remove nulls and replace with 0
    player_data_out[primary_event_name] = player_data_out[primary_event_name].fillna(0)
    
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

    included_cols_max = lineups.groupby(['team_name', 'match_id'], axis=0).max()['time_played']

    teaminfo_df = teaminfo_df.merge(included_cols_max, left_on=['team_name', 'match_id'], right_index=True)
    teaminfo_df['matches_played'] = 1

    teaminfo_df = teaminfo_df.groupby(['team_name']).sum()[['time_played', 'matches_played']]

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
        grouped_events = events.groupby('team_name', axis=0).count()
        selected_events = grouped_events[agg_columns].copy()
        selected_events.loc[:, primary_event_name] = grouped_events['match_id']
    elif group_type == 'sum':
        grouped_events = events.groupby('team_name', axis=0).sum(numeric_only=True)
        selected_events = grouped_events[agg_columns].copy()
    elif group_type == 'mean':
        grouped_events = events.groupby('team_name', axis=0).mean(numeric_only=True)
        selected_events = grouped_events[agg_columns].copy()
    else:
        selected_events = pd.DataFrame()

    # Merge into player information dataframe
    team_info_out = team_info_out.merge(selected_events, left_on='team_name', right_index=True, how='left')
    if agg_columns != list() and group_type in ['sum', 'mean']:
        team_info_out = team_info_out.rename(columns={agg_columns: primary_event_name})

    # Remove nulls and replace with 0
    team_info_out[primary_event_name] = team_info_out[primary_event_name].fillna(0)

    return team_info_out


def create_league_table(matches, xmetrics=False):
    """ Create a league table from statsbomb-style matches dataframe

    Function to read a statsbomb-style matches dataframe and return a dataframe that represents the league table. An
    expected league table can be returned provided expected points modelling has been undertaken and the user specifies
    type = 'expected'.

    Args:
        matches (pandas.DataFrame): statsbomb-style dataframe of matches
        xmetrics (bool, optional): include expected metrics in league table. Defaults to False.
    Returns:
        pandas.DataFrame: league table
    """

    # Initialise output dataframe
    leaguetable = pd.DataFrame()
    matches_out = matches.copy()

    # Add teams to league table
    leaguetable['team'] = sorted(list(set(matches_out['home_team'].values.tolist() +
                                          matches_out['away_team'].values.tolist())))

    # Calculate home and away points based on matches dataframe
    matches_out['home_points'] = (matches_out[['home_score', 'away_score']]
                                  .apply(lambda x: 3 if x[0] > x[1] else 1 if x[0] == x[1] else 0, axis=1))
    matches_out['away_points'] = (matches_out[['home_score', 'away_score']]
                                  .apply(lambda x: 3 if x[0] < x[1] else 1 if x[0] == x[1] else 0, axis=1))

    # Add information to league table dataframe
    leaguetable['matches_played'] = (matches_out.groupby('home_team').count()['match_id'] +
                                     matches_out.groupby('away_team').count()['match_id']).values
    leaguetable['points'] = (matches_out.groupby('home_team').sum(numeric_only=True)['home_points'] +
                             matches_out.groupby('away_team').sum(numeric_only=True)['away_points']).values
    leaguetable['goals_for'] = (matches_out.groupby('home_team').sum(numeric_only=True)['home_score'] +
                                matches_out.groupby('away_team').sum(numeric_only=True)['away_score']).values
    leaguetable['goals_against'] = (matches_out.groupby('home_team').sum(numeric_only=True)['away_score'] +
                                    matches_out.groupby('away_team').sum(numeric_only=True)['home_score']).values
    leaguetable['goal_difference'] = leaguetable['goals_for'] - leaguetable['goals_against']
    leaguetable['position'] = (leaguetable[['points', 'goal_difference', 'goals_for']].apply(tuple, axis=1)
                               .rank(method='min', ascending=False).astype(int))

    # Add expected information to league table dataframe if parameter is passed
    if xmetrics:

        leaguetable['xg_for'] = (matches_out.groupby('home_team').sum(numeric_only=True)['home_xg'] +
                                 matches_out.groupby('away_team').sum(numeric_only=True)['away_xg']).values
        leaguetable['xg_against'] = (matches_out.groupby('home_team').sum(numeric_only=True)['away_xg'] +
                                     matches_out.groupby('away_team').sum(numeric_only=True)['home_xg']).values
        leaguetable['xg_difference'] = leaguetable['xg_for'] - leaguetable['xg_against']
        leaguetable['expected_points'] = (matches_out.groupby('home_team').sum(numeric_only=True)['home_xpoints'] +
                                          matches_out.groupby('away_team').sum(numeric_only=True)['away_xpoints']).values
        leaguetable['expected_position'] = (leaguetable[['expected_points', 'xg_difference', 'xg_for']]
                                            .apply(tuple, axis=1).rank(method='min', ascending=False).astype(int))
        leaguetable = leaguetable.sort_values('expected_position')

    else:
        leaguetable = leaguetable.sort_values('position')

    return leaguetable
