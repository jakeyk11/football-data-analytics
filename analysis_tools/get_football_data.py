"""Module containing functions to import and save football data from a variety of data sources.

Functions
---------
get_statsbomb_data(competition, start_year, save_to_file=False, folderpath=None):
    Import match event and lineup data from Statsbomb for an entire competition.

get_whoscored_data(match_id, save_to_file=False, folderpath=None):
    Scrape match event and player data from WhoScored match centre for a given match.

get_transfermarkt_data(country_code, division_number, start_year, all_comps=False, save_to_file=False, folderpath=None)
    Scrape player information from transfermarkt for an entire league & season.
"""

from statsbombpy import sb
import numpy as np
import pandas as pd
import requests
import bs4
import pickle
import bz2
import re
from selenium import webdriver
import json
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def get_statsbomb_data(competition, start_year, save_to_file=False, folderpath=None):
    """Import match event and lineup data from Statsbomb for an entire competition.

    Function to import match event and lineup information from Statsbomb for all matches within a specified competition.
    Event output is formatted as a single dataframe union of all events across all matches. Lineup output is formatted
    as a single dataframe of lineups for each match within the competition.

    Args:
        competition (string): Competition name, using Statsbomb convention
        start_year (string): Year in which season/competition started, input in YYYY format.
        save_to_file (bool, optional): Selection of whether to save data to pbz2 file.
        folderpath (string, optional):  Path of folder to save data in. Can be a relative file path. None by default.

    Returns:
        pandas.DataFrame: dataframe of match event information
        pandas.DataFrame: dataframe of lineup information
        """

    # Initialise output dataframe
    events = pd.DataFrame()
    lineups = pd.DataFrame()

    # Get Statsbomb comps and find IDs of user-selected competition
    comps = sb.competitions()
    comp_id = comps[(comps['competition_name'] == competition) &
                    (comps['season_name'] == start_year)][['competition_id', 'season_id']].values[0]

    # Use competition IDs to get all match IDs
    matches = sb.matches(competition_id=comp_id[0], season_id=comp_id[1])

    # Use match IDs to build single dataframes of competition events and lineups
    for _, match in matches.iterrows():

        # Sort match events by time in match
        match_events = sb.events(match_id=match['match_id']).sort_values(['period', 'timestamp'], axis=0)

        # Build a dataframe of lineups
        lineup = sb.lineups(match_id=match['match_id'])
        t1_lineup = list(lineup.values())[0].assign(team_name=list(lineup.keys())[0])
        t2_lineup = list(lineup.values())[1].assign(team_name=list(lineup.keys())[1])
        lineup = pd.concat([t1_lineup, t2_lineup]).reset_index(drop=True).assign(match_id=match['match_id'])

        # Build up dataframe of all events and all lineup information.
        events = pd.concat([events, match_events])
        lineups = pd.concat([lineups, lineup])

    # Reset index
    events.reset_index(inplace=True, drop=True)
    lineups.reset_index(inplace=True, drop=True)

    # Store data if user chooses to
    comp_string = competition.replace(" ", "-").lower()
    if save_to_file:
        with bz2.BZ2File(f"{folderpath}/{comp_string}-{start_year}-eventdata.pbz2", "wb") as f:
            pickle.dump(events, f)
        with bz2.BZ2File(f"{folderpath}/{comp_string}-{start_year}-lineupdata.pbz2", "wb") as f:
            pickle.dump(lineups, f)

    return events, lineups


def get_whoscored_data(match_id, get_mappings = False, proxy_servers=None, save_to_file=False, folderpath=None):
    """Scrape match event data and player data from WhoScored match centre for a given match.

    Function to scrape match event and player information from whoscored.com match centre for a single match, based on
    user specification of WhoScored match id (which can be found within the WhoScored match URL). The user may wish to
    scrape WhoScored under a proxy connection - options can be found at https://sslproxies.org/.

    Args:
        match_id (string): Match id, using who-scored convention (found within the WhoScored match URL)
        get_mappings (bool, optional):
        proxy_servers (string, optional): IP addresses:port of proxy servers used to establish site connection (None by default)
        save_to_file (bool, optional): Selection of whether to save data to pbz2 file.
        folderpath (string, optional):  Path of folder to save data in. Can be a relative file path. None by default.

    Returns:
        pandas.DataFrame: dataframe of match event information
        pandas.DataFrame: dataframe of player information
        tuple: contains mapping dicionaries
    """

    # Build WhoScored web url
    website_url = f"https://www.whoscored.com/Matches/{match_id}/Live/"

    # Establish driver options
    driver_options = Options()
    driver_options.add_argument("disable-infobars")
    driver_options.add_argument("--disable-extensions")

    if proxy_servers is not None:
        driver_options.add_argument(f"--proxy-server={proxy_servers}")

    # Set-up driver and open match page
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=driver_options)
    driver.get(website_url)

    # Read html and close driver after short wait
    page_html = driver.page_source
    WebDriverWait(driver, 30)
    driver.close()

    # Extract embedded json from match centre page using regular expression.
    regex_pattern = r'(?<=require\.config\.params\["args"\].=.)[\s\S]*?;'
    match_data_txt = re.findall(regex_pattern, page_html)[0]

    # Add quotations to text for json parser
    match_data_txt = match_data_txt.replace('matchId', '"matchId"')
    match_data_txt = match_data_txt.replace('matchCentreData', '"matchCentreData"')
    match_data_txt = match_data_txt.replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"')
    match_data_txt = match_data_txt.replace('formationIdNameMappings', '"formationIdNameMappings"')
    match_data_txt = match_data_txt.replace('};', '}')

    # Parse json
    match_data_json = json.loads(match_data_txt)

    # If user chooses to, obtain mappings between event types and identifers & formations and identifier
    if get_mappings:
        event_types = match_data_json["matchCentreEventTypeJson"]
        formation_mapping = match_data_json["formationIdNameMappings"]
    else:
        event_types = None
        formation_mapping = None

    # Create team and event dictionaries
    events_dict = match_data_json["matchCentreData"]["events"]
    teams_dict = {match_data_json["matchCentreData"]['home']['teamId']: match_data_json["matchCentreData"]['home']['name'],
                  match_data_json["matchCentreData"]['away']['teamId']: match_data_json["matchCentreData"]['away']['name']}

    # Create players dataframe
    players_home_df = pd.DataFrame(match_data_json["matchCentreData"]['home']['players'])
    players_home_df["teamId"] = match_data_json["matchCentreData"]['home']['teamId']
    players_home_df['team'] = [x for x in teams_dict.values()][0]
    players_away_df = pd.DataFrame(match_data_json["matchCentreData"]['away']['players'])
    players_away_df["teamId"] = match_data_json["matchCentreData"]['away']['teamId']
    players_away_df['team'] = [x for x in teams_dict.values()][1]
    players_df = pd.concat([players_home_df, players_away_df])
    players_df['match_id'] = int(match_id)

    # Create events dataframe and replace identifier with event name
    events_df = pd.DataFrame(events_dict)
    events_df['match_id'] = int(match_id)
    events_df['eventType'] = events_df.apply(lambda row: row['type']['displayName'], axis=1)
    events_df['outcomeType'] = events_df.apply(lambda row: row['outcomeType']['displayName'], axis=1)
    events_df['period'] = events_df.apply(lambda row: row['period']['value'], axis=1)

    # Set index
    events_df.set_index('id', inplace=True)
    players_df.set_index('playerId', inplace=True)

    # Save to file if user chooses to
    if save_to_file:
        with bz2.BZ2File(f"{folderpath}/match-eventdata-{match_id}-{match_data_json['matchCentreData']['home']['name']}-{match_data_json['matchCentreData']['away']['name']}.pbz2", "wb") as f:
            pickle.dump(events_df, f)
        with bz2.BZ2File(f"{folderpath}/match-playerdata-{match_id}-{match_data_json['matchCentreData']['home']['name']}-{match_data_json['matchCentreData']['away']['name']}.pbz2", "wb") as f:
            pickle.dump(players_df, f)

        if get_mappings:
            with bz2.BZ2File(f"{folderpath}/event-types.pbz2", "wb") as f:
                pickle.dump(event_types, f)
            with bz2.BZ2File(f"{folderpath}/formation-mapping.pbz2", "wb") as f:
                pickle.dump(formation_mapping, f)

    return events_df, players_df, tuple([event_types, formation_mapping])


def get_transfermarkt_data(country_code, division_number, start_year, all_comps=False, save_to_file=False, folderpath=None):
    """Scrape player information from transfermarkt for an entire league & season.

    Function to scrape player information from transfermarkt.co.uk for all players within a specified league,
    for a specified season. Player information includes general information (name, age, team, etc.), performance
    information (goals, assists, yellows, etc.), contract information and value information.

    Args:
        country_code (string): League country code, using transfermarkt convention (e.g. England = GB, Spain = ES)
        division_number (string): League number, input as a digit where 1 is the highest division.
        start_year (string): Year in which season started, input in YYYY format.
        all_comps (bool, optional): Selection of whether to include stats from all competitions or domestic competition only. False by default.
        save_to_file (bool, optional): Selection of whether to save data to pbz2 file.
        folderpath (string, optional):  Path of folder to save data in. Can be a relative file path. None by default.

    Returns:
        pandas.DataFrame: dataframe of player information
        """

    # Embedded function definitions

    def get_team_stats(team_stat):
        """ Function to take in team row HTML and extract a list of stats.

        Args:
            team_stat (html object): HTML row corresponding to team.

        Returns:
            list: team stats.
        """

        team_stats = team_stat.find_all('td')
        stats_output = [team_stats[2].text,
                        team_stats[3].text,
                        team_stats[4].text,
                        value_calc(team_stats[5]),
                        value_calc(team_stats[6])]

        return stats_output

    def get_player_stats(player_stat):
        """ Function to take in player row HTML and extract a list of stats.

        Args:
            player_stat (html object): HTML row corresponding to player.

        Returns:
            list: player stats.
        """

        player_stats = player_stat.find_all('td')  # Get all column entries for each player
        stats_output = [player_stats[3].a.get('title'),  # Store player information in list
                        player_stats[4].text,
                        player_stats[5].text,
                        player_stats[7].text,
                        player_stats[8].text,
                        player_stats[17].text.replace("'", "").replace(".", ""),
                        player_stats[9].text,
                        player_stats[10].text,
                        player_stats[11].text,
                        player_stats[12].text,
                        player_stats[13].text,
                        player_stats[14].text,
                        player_stats[15].text,
                        player_stats[16].text.replace(",", ".")]

        return stats_output

    def get_player_value(player_val):
        """ Function to take in player row HTML and extract player value and contract details

        Args:
            player_val (html object): HTML row corresponding to player.

        Returns:
            list: player value and contract information.
        """

        player_value = player_val.find_all('td')
        get_date = date_calc(player_value[7].text)
        get_gbp = value_calc(player_value[10].a)
        get_prev_gbp = prev_value_calc(player_value[10])
        value_output = [player_value[3].a.get('title'),
                        player_value[4].text,
                        get_date[0],
                        get_date[1],
                        get_gbp,
                        get_prev_gbp]

        return value_output

    def value_calc(value_class):
        """ Function to take in transfermarkt value definition and convert to floating point.

        Args:
            value_class (html object): transfermarkt classification of value.

        Returns:
            float: transfermarkt value.
        """

        if not isinstance(value_class, type(None)):
            value_str = value_class.text
            if 'Th.' in value_str:
                value_str = value_str.replace("Th.", "").replace("£", "")
                value = float(value_str) / 1000
            elif 'm' in value_str:
                value_str = value_str.replace("m", "").replace("£", "")
                value = float(value_str)
            else:
                value = np.nan
        else:
            value = np.nan

        return value

    def prev_value_calc(value_class):
        """ Function to take in transfermarkt previous value definition and convert to floating point.

        Args:
            value_class (html object): transfermarkt classification of previous value.

        Returns:
            float: transfermarkt previous value.
        """

        if not isinstance(value_class, type(None)) and (value_class.find('span')):
            value_str = value_class.span['title'].split(':')[1]
            if 'Th.' in value_str:
                value_str = value_str.replace("Th.", "").replace(" £", "")
                value = float(value_str) / 1000
            elif 'm' in value_str:
                value_str = value_str.replace("m", "").replace(" £", "")
                value = float(value_str)
            else:
                value = np.nan
        else:
            value = np.nan

        return value

    def date_calc(date_str):
        """ Function to take in transfermarkt date string and format appropriately.

        Args:
            date_str (string): transfermarkt date definition

        Returns:
            string: day and month
            int: year
        """

        if not date_str == '-':
            day_month_out = date_str.split(',')[0]
            year_out = int(date_str.split(',')[1].replace(" ", ""))
        else:
            day_month_out = np.nan
            year_out = np.nan
        return [day_month_out, year_out]

    # Build URL to league table and send request (as Mozilla browser)
    url = f"https://www.transfermarkt.co.uk/NULL/startseite/wettbewerb/{country_code}{division_number}/plus/?saison_id={start_year}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 '
                      'Safari/537.36'}
    league_res = requests.get(url, headers=headers)
    league_soup = bs4.BeautifulSoup(league_res.text, "lxml")

    # Get team stats
    teamstats = []
    for row_id in ["tr.odd", "tr.even"]:
        for team in league_soup.select(row_id):
            team_name = team.a.get("title")
            stats_out = get_team_stats(team)
            stats_out.insert(0, team_name)
            teamstats.append(stats_out)

    # List teams, get URL from each team and obtain player stats of interest in list object
    url = f"http://transfermarkt.co.uk/NULL/tabellenachminuten/wettbewerb/{country_code}{division_number}/plus/?saison_id={start_year}"
    league_res = requests.get(url, headers=headers)
    league_soup = bs4.BeautifulSoup(league_res.text, "lxml")
    teams = league_soup.select("td.no-border-links")
    playerstats = []
    playervalue = []

    for item in teams:
        team_name = item.a.get('title')  # Get team name
        team_url_extension = item.a.get('href')  # Obtain URL extension

        # Adjust URL for player stats page, and get page information
        teamstats_url_extension = team_url_extension.replace('spielplan',
                                                             'leistungsdaten')
        if not all_comps:
            url = f"http://transfermarkt.co.uk{teamstats_url_extension}/plus/1?reldata={country_code}{division_number}"
        else:
            url = f"http://transfermarkt.co.uk{teamstats_url_extension}/plus/1?"
        teamstats_res = requests.get(url, headers=headers)
        teamstats_soup = bs4.BeautifulSoup(teamstats_res.text, "lxml")

        # Loop through each odd and even row (row = player), get stats, insert team name and build list of lists
        for player_row in teamstats_soup.select("tr.odd"):
            stats_out = get_player_stats(player_row)
            stats_out.insert(2, team_name)
            playerstats.append(stats_out)
        for player_row in teamstats_soup.select("tr.even"):
            stats_out = get_player_stats(player_row)
            stats_out.insert(2, team_name)
            playerstats.append(stats_out)

        # Adjust URL for player value page, and get page information
        teamvalue_url_extension = team_url_extension.replace('spielplan',
                                                             'marktwertanalyse')
        url = f"http://transfermarkt.co.uk{teamvalue_url_extension}"
        teamvalue_res = requests.get(url, headers=headers)
        teamvalue_soup = bs4.BeautifulSoup(teamvalue_res.text, "lxml")

        # Loop through each odd and even row (row = player), get value, insert team name and build list of lists
        for player_row in teamvalue_soup.select("tr.odd"):
            value_out = get_player_value(player_row)
            value_out.insert(2, team_name)
            playervalue.append(value_out)
        for player_row in teamvalue_soup.select("tr.even"):
            value_out = get_player_value(player_row)
            value_out.insert(2, team_name)
            playervalue.append(value_out)

    # Use list objects to build dataframes and combine
    team_stats_df = pd.DataFrame(data=teamstats,
                                 columns=["Team", "Squad_Count", "Mean_Age", "Foreign_Players",
                                          "Mean_Market_Val", "Tot_Market_Val"])
    player_stats_df = pd.DataFrame(data=playerstats,
                                   columns=["Name", "Position", "Team", "Age",
                                            "In_Squad", "In_XI", "Tot_Mins", "Goals",
                                            "Assists", "Yellows", "Sec_Yellows",
                                            "Reds", "Subs_On", "Subs_Off", "PPG"])
    player_value_df = pd.DataFrame(data=playervalue,
                                   columns=["Name", "Position", "Team", "Contract_End_DDMM",
                                            "Contract_End_YY", "Market_Value",
                                            "Prev_Market_Value"])
    player_info_df = pd.merge(player_stats_df, player_value_df, on=["Name", "Position", "Team"], how="left")
    player_info_df = pd.merge(player_info_df, team_stats_df, on="Team", how="left")

    # Replace string values that represent 0, with 0
    player_info_df.replace("-", 0, inplace=True)
    player_info_df.replace("Not used during this season", 0, inplace=True)
    player_info_df.replace("Not in squad during this season", 0, inplace=True)

    # Convert columns of strings to integers
    player_info_df = player_info_df.astype({"Age": "int32", "In_Squad": "int32", "In_XI": "int32",
                                            "Tot_Mins": "int32", "Goals": "int32", "Assists": "int32",
                                            "Yellows": "int32", "Sec_Yellows": "int32",
                                            "Reds": "int32", "Subs_On": "int32", "Subs_Off": "int32",
                                            "PPG": "float"}, copy=False, errors='raise')

    # Save to file if user chooses to
    if save_to_file:
        end_year = str(int(start_year) + 1)
        if not all_comps:
            filename = f"transfermarkt_{country_code}{division_number}_{start_year}-{end_year}.pbz2"
        else:
            filename = f"transfermarkt_{country_code}{division_number}_allcomps_{start_year}-{end_year}.pbz2"

        # Store data as compressed pickle file
        with bz2.BZ2File(f"{folderpath}/{filename}", "wb") as f:
            pickle.dump(player_info_df, f)

    return player_info_df
