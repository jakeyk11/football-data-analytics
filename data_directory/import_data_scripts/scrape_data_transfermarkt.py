# Scrape user-specified data from transfermarkt.com
#
# Inputs:   Transfermarkt country code
#           League number of teams to include
#           Starting year of season to include
#           Specification of all competition or league data only
#
# Outputs:  Transfermarkt data, formatted as .pbz2
#
# Jake Kolliari

# %% Imports

import requests
import bs4
import pandas as pd
import numpy as np
import pickle
import bz2

# %% User Inputs

# Input league country (England = GB, Spain = ES, Germany = L, Italy = IT, France = FR, Scotland = SC)
country_code = 'GB'

# Input league number (for example Premier League = 1, Championship = 2, League One = 3, etc.)
league_num = '1'

# Input year that season started
year = '2021'

# Choose whether to obtains stats from all competitions (0 = League comp. only, 1 = All comps.)
all_comps = 0


# %% Function definitions


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


# %% Build URL to league table and send request (as Mozilla browser,
# see https://fcpython.com/blog/introduction-scraping-data-transfermarkt)

url = f"https://www.transfermarkt.co.uk/NULL/startseite/wettbewerb/{country_code}{league_num}/plus/?saison_id={year}"

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 '
                  'Safari/537.36'}
league_res = requests.get(url, headers=headers)
league_soup = bs4.BeautifulSoup(league_res.text, "lxml")

# %% Get team stats

# Initialise team stats list
teamstats = []

for row_id in ["tr.odd", "tr.even"]:
    for team in league_soup.select(row_id):
        team_name = team.a.get("title")
        stats_out = get_team_stats(team)
        stats_out.insert(0, team_name)
        teamstats.append(stats_out)
        
# %% List teams, get URL from each team and obtain player stats of interest in list object

url = f"http://transfermarkt.co.uk/NULL/tabellenachminuten/wettbewerb/{country_code}{league_num}/plus/?saison_id={year}"

league_res = requests.get(url, headers=headers)
league_soup = bs4.BeautifulSoup(league_res.text, "lxml")
teams = league_soup.select("td.no-border-links")

# Initialise stats list (building a list is quicker than building a dataframe in a for loop)
playerstats = []

# Initialise value list
playervalue = []

# Loop through each team in league
for item in teams:
    team_name = item.a.get('title')             # Get team name
    team_url_extension = item.a.get('href')         # Obtain URL extension

    # Adjust URL for player stats page, and get page information
    teamstats_url_extension = team_url_extension.replace('spielplan',
                                                         'leistungsdaten')
    if all_comps == 0:
        url = f"http://transfermarkt.co.uk{teamstats_url_extension}/plus/1?reldata={country_code}{league_num}"
    else:
        url = f"http://transfermarkt.co.uk{teamstats_url_extension}/plus/1?"
    teamstats_res = requests.get(url, headers=headers)
    teamstats_soup = bs4.BeautifulSoup(teamstats_res.text, "lxml")

    # Loop through each odd and even row (corresponding to player), get stats, insert team name and build list of lists
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

    # Loop through each odd and even row (corresponding to player), get value, insert team name and build list of lists
    for player_row in teamvalue_soup.select("tr.odd"):
        value_out = get_player_value(player_row)
        value_out.insert(2, team_name)
        playervalue.append(value_out)
    for player_row in teamvalue_soup.select("tr.even"):
        value_out = get_player_value(player_row)
        value_out.insert(2, team_name)
        playervalue.append(value_out)

# %% Use list objects to build dataframes, and combine

# Create team stats dataframe
team_stats_df = pd.DataFrame(data=teamstats,
                             columns=["Team", "Squad_Count", "Mean_Age", "Foreign_Players",
                                      "Mean_Market_Val", "Tot_Market_Val"])

# Create player stats dataframe
player_stats_df = pd.DataFrame(data=playerstats,
                               columns=["Name", "Position", "Team", "Age",
                                        "In_Squad", "In_XI", "Tot_Mins", "Goals",
                                        "Assists", "Yellows", "Sec_Yellows",
                                        "Reds", "Subs_On", "Subs_Off", "PPG"])

# Create contract and info and market value dataframe
player_value_df = pd.DataFrame(data=playervalue,
                               columns=["Name", "Position", "Team", "Contract_End_DDMM",
                                        "Contract_End_YY", "Market_Value",
                                        "Prev_Market_Value"])

# Combine dataframes, looking for match on player name AND position AND team name
player_info_df = pd.merge(player_stats_df, player_value_df, on=["Name", "Position", "Team"], how="left")
player_info_df = pd.merge(player_info_df, team_stats_df, on="Team", how="left")

# %% Data pre-processing and formatting

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

# %% Save to .csv file for post-processing

# Automatic filename
year_end = str(int(year) + 1)
if all_comps == 0:
    filename = f"transfermarkt_{country_code}{league_num}_{year}-{year_end}.pbz2"
else:
    filename = f"transfermarkt_{country_code}{league_num}_allcomps_{year}-{year_end}.pbz2"

# Store data as compressed pickle file
with bz2.BZ2File(f"../transfermarkt_data/{filename}", "wb") as f:
    pickle.dump(player_info_df, f)
