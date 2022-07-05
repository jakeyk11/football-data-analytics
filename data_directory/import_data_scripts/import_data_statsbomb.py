# Import user-specified data from Statsbomb
#
# Inputs:   Competition name (Statsbomb convention)
#           Competition year (Statsbomb convention)
#
# Outputs:  Statsbomb data, formatted as .pbz2
#
# Jake Kolliari

#%% Imports

from statsbombpy import sb
import pandas as pd
import pickle
import bz2

#%% User inputs

# Input competition name (Statsbomb convention)
competition = 'FIFA World Cup'

# Input competition year or years(s)
year = '2018'

#%% Read in data

# Initialise dataframes of interest. We want to collect all events and all line-up information
events = pd.DataFrame()
lineups = pd.DataFrame()

# Get Statsbomb comps and find IDs of user-selected competition
comps = sb.competitions()
comp_id = comps[(comps['competition_name'] == competition) &
                (comps['season_name'] == year)][['competition_id', 'season_id']].values[0]

# Use competition IDs to get all match IDs
matches = sb.matches(competition_id=comp_id[0], season_id=comp_id[1])

#%% Format data

# Use match IDs to build single dataframes of competition events and lineups
for _, match in matches.iterrows():
    
    # For each match sort match events by time in match
    match_events = sb.events(match_id=match['match_id']).sort_values(['period', 'timestamp'], axis=0)
    
    # For each match build a dataframe of lineups
    lineup = sb.lineups(match_id=match['match_id'])
    t1_lineup = list(lineup.values())[0].assign(team_name=list(lineup.keys())[0])
    t2_lineup = list(lineup.values())[1].assign(team_name=list(lineup.keys())[1])
    lineup = t1_lineup.append(t2_lineup).reset_index(drop=True).assign(match_id=match['match_id'])

    # Build up dataframe of all events and all lineup information.
    events = events.append(match_events).reset_index(drop=True)
    lineups = lineups.append(lineup)

# Reset index
events.reset_index(inplace=True, drop=True)
lineups.reset_index(inplace=True, drop=True)

#%% Store data

comp_string = competition.replace(" ", "-").lower()

# Store data as compressed pickle file
with bz2.BZ2File(f"../statsbomb_data/{comp_string}-{year}-eventdata.pbz2", "wb") as f:
    pickle.dump(events, f)
with bz2.BZ2File(f"../statsbomb_data/{comp_string}-{year}-lineupdata.pbz2", "wb") as f:
    pickle.dump(lineups, f)
