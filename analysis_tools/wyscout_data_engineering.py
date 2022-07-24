"""Module containing functions to assist with pre-processing and engineering of Wyscout-style data

Functions
---------
format_wyscout_data(tournament='England', data_folder="../../data_directory/wyscout_data")
    Load Wyscout json files with matches, events, players and competitions."""

import bz2
import pickle
from collections import defaultdict
import pandas as pd


def format_wyscout_data(tournament='England', data_folder="../../data_directory/wyscout_data"):
    """ Load Wyscout json files with matches, events, players and competitions.

    Function to load and format Wyscout json files (location defined by folder input) for a user-defined tournament.

    Args:
        tournament (list, optional): List of tournaments to load.
        data_folder (str, optional): Location of data, relative to script in which function is called..

    Returns:
        pandas.DataFrame: wyscout-style event dataframe, containing all events from selected competition.
        pandas.DataFrame: wyscout-style matches dataframe, containing all match information from selected competition.
        defaultdict: wyscout-style event dictionary, containing events per match.
        pandas.DataFrame: wyscout-style player dataframe, containing player info for all players in av. Wyscout data.
        pandas.DataFrame: wyscout-style competition dataframe, containing comp info for all comps in av. Wyscout data.
        pandas.DataFrame: wyscout-style team dataframe, containing team info for all teams in av. Wyscout data.
    """

    if isinstance(tournament, str):
        tournament = [tournament]

    events, matches = pd.DataFrame(), pd.DataFrame()

    for idx, data_selection in enumerate(tournament):
        
        # Load in the Wyscout matches and event data
        events_temp = bz2.BZ2File(f"{data_folder}/events/events_{data_selection}.pbz2", 'rb')
        events_temp = pd.DataFrame(pickle.load(events_temp))
        matches_temp = bz2.BZ2File(f"{data_folder}/matches/matches_{data_selection}.pbz2", 'rb')
        matches_temp = pd.DataFrame(pickle.load(matches_temp))

        if idx == 0:
            events = events_temp
            matches = matches_temp
        else:
            events = events.append(events_temp)
            matches = matches.append(matches_temp)

    # Produce a dictionary of lists: top level dictionary of matches with sub-list of events
    match_id2events = defaultdict(list)
    for _, event in events.iterrows():
        match_id = event['matchId']
        match_id2events[match_id].append(event)

    # Produce a dictionary of dictionaries: top level dictionary of matches with sub-dictionary of match info
    match_id2match = defaultdict(dict)
    for _, match in matches.iterrows():
        match_id = match['wyId']
        match_id2match[match_id] = match

    # Load in the Wyscout player data
    players = bz2.BZ2File(f"{data_folder}/players.pbz2", 'rb')
    players = pickle.load(players)

    # Produce a dictionary of dictionaries: top level dictionary of players with sub-dictionary of player info
    player_id2player = defaultdict(dict)
    for player in players:
        player_id = player['wyId']
        player_id2player[player_id] = player

    # Load in the Wyscout competition data
    competitions = bz2.BZ2File(f"{data_folder}/competitions.pbz2", 'rb')
    competitions = pickle.load(competitions)

    # Produce a dictionary: top level dictionary of competitions with sub-dictionary of competition info
    competition_id2competition = defaultdict(dict)
    for competition in competitions:
        competition_id = competition['wyId']
        competition_id2competition[competition_id] = competition

    # Load in the Wyscout teams data
    teams = bz2.BZ2File(f"{data_folder}/teams.pbz2", 'rb')
    teams = pickle.load(teams)

    # Produce a list of dictionaries: top level dictionary of teams with sub-dictionary of team info
    team_id2team = defaultdict(dict)
    for team in teams:
        team_id = team['wyId']
        team_id2team[team_id] = team

    # Convert to dataframes
    match_id2match = pd.DataFrame(match_id2match).transpose()
    player_id2player = pd.DataFrame(player_id2player).transpose()
    competition_id2competition = pd.DataFrame(competition_id2competition).transpose()
    team_id2team = pd.DataFrame(team_id2team).transpose()

    return match_id2match, events, match_id2events, player_id2player, competition_id2competition, team_id2team
