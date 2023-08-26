# %% Points Model

# %% Imports

import pandas as pd
import bz2
import os
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import numpy as np
import matplotlib as mpl
from PIL import Image
import matplotlib.patheffects as path_effects

# %% Add custom tools to path

root_folder = os.path.abspath(os.path.dirname(
    (os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_folder)

import analysis_tools.whoscored_custom_events as wce
import analysis_tools.whoscored_data_engineering as wde
import analysis_tools.logos_and_badges as lab

# %% User inputs

# Data to use
data_grab = [
            ['EFLC', '2018'],
            ['EFLC', '2019'],
            ['EFLC', '2020'],
            ['EFLC', '2021'],
            ['EFLC', '2022']
            ]

# Decide whether to brighten competition logo
logo_brighten = False

# %% Import data

# Initialise storage dataframes
events_df = pd.DataFrame()
players_df = pd.DataFrame()
leaguetable_df = pd.DataFrame()
match_dict = dict.fromkeys([f"{data[0]} {data[1]}" for data in data_grab])

for data in data_grab:
    league = data[0]
    year = data[1]
    league_events = pd.DataFrame()
    league_players = pd.DataFrame()
        
    file_path_evts = f"../../data_directory/whoscored_data/{data[1]}_{str(int(data[1].replace('20','', 1)) + 1)}/{data[0]}"
    files = os.listdir(file_path_evts)
    
    # Load event data match by match
    for file in files:
        if file == 'event-types.pbz2':
            event_types = bz2.BZ2File(f"{file_path_evts}/{file}", 'rb')
            event_types = pickle.load(event_types)
        elif '-eventdata-' in file:
            match_events = bz2.BZ2File(f"{file_path_evts}/{file}", 'rb')
            match_events = pickle.load(match_events)
            league_events = pd.concat([league_events, match_events])
        elif '-playerdata-' in file:
            match_players = bz2.BZ2File(f"{file_path_evts}/{file}", 'rb')
            match_players = pickle.load(match_players)
            league_players = pd.concat([league_players, match_players])
        else:
            pass
        
    # Add match ids to match dictionary
    match_dict[f"{data[0]} {data[1]}"] = set(league_events['match_id'].tolist())
    
    # Append league data to combined dataset
    events_df = pd.concat([events_df, league_events])
    players_df = pd.concat([players_df, league_players])
    
    # Load league table data
    file_path_league = f"../../data_directory/leaguetable_data/{data[1]}_{str(int(data[1].replace('20','', 1)) + 1)}"
    file = f"{data[0]}-table-{data[1]}.pbz2"
    league_table = bz2.BZ2File(f"{file_path_league}/{file}", 'rb')
    league_table = pickle.load(league_table)
    league_table['league'] = data[0]
    league_table['year'] = data[1]
    leaguetable_df = pd.concat([leaguetable_df, league_table])

    print(f"{league}, {year} data import complete")

# %% Get competition logo

comp_logo = lab.get_competition_logo(data_grab[-1][0], data_grab[-1][1], logo_brighten=logo_brighten) 

# %% Process event data

events_df['box_entry_attempt'] = events_df.apply(wce.box_entry, successful_only=False, axis=1)
events_df['box_entry_successful'] = events_df.apply(wce.box_entry, successful_only=True, axis=1)

# %% Manual team name replacements

def team_nickname(x):
    
    nicknames = {'Birmingham City': 'Birmingham',
                 'Birmingham City *': 'Birmingham',
                 'Blackburn Rovers': 'Blackburn',
                 'Bolton Wanderers': 'Bolton',
                 'Brighton and Hove Albion': 'Brighton',
                 'Cardiff City': 'Cardiff',
                 'Charlton Athletic': 'Charlton',
                 'Coventry City': 'Coventry',
                 'Derby County': 'Derby',
                 'Derby County **': 'Derby',
                 'Huddersfield Town': 'Huddersfield',
                 'Hull City': 'Hull',
                 'Ipswich Town': 'Ipswich',
                 'Leeds United': 'Leeds',
                 'Leicester City': 'Leicester',
                 'Luton Town': 'Luton',
                 'Manchester City': 'Man City',
                 'Manchester United': 'Man Utd',
                 'Newcastle United': 'Newcastle',
                 'Norwich City': 'Norwich',
                 'Peterborough United': 'Peterborough',
                 'Preston North End': 'Preston',
                 'Queens Park Rangers': 'QPR',
                 'Reading *': 'Reading',
                 'Sheffield Wednesday': 'Sheff Wed',
                 'Sheffield Wednesday *': 'Sheff Wed',
                 'Sheffield United': 'Sheff Utd',
                 'Stoke City': 'Stoke',
                 'Swansea City': 'Swansea',
                 'Tottenham Hotspur': 'Tottenham',
                 'Rotherham United': 'Rotherham',
                 'West Bromwich Albion': 'West Brom',
                 'West Ham United': 'West Ham',
                 'Wigan Athletic': 'Wigan',
                 'Wigan Athletic *': 'Wigan',
                 'Wigan Athletic **': 'Wigan',
                 'Wolverhampton Wanderers': 'Wolves',
                 'Wycombe Wanderers': 'Wycombe'}
                 
    return nicknames[x] if x in nicknames else x

leaguetable_df['team_name_short'] = leaguetable_df['team'].apply(team_nickname)
leaguetable_df.reset_index(inplace=True, drop = True)

# %% Calculate team metrics within each season

leaguetable_analyse_df = leaguetable_df.copy()

for idx, league_entry in leaguetable_analyse_df.iterrows():
    
    # Get team matches and events for given season
    league_match_ids = match_dict[f"{league_entry['league']} {league_entry['year']}"]
    team_id = players_df[players_df['team']==league_entry['team_name_short']]['teamId'].values[0]
    team_match_ids = set(events_df[(events_df['match_id'].isin(league_match_ids)) & (events_df['teamId']==team_id)]['match_id'])
    rel_events = events_df[events_df['match_id'].isin(team_match_ids)]
    rel_team_events = rel_events[rel_events['teamId']==team_id]
    rel_opp_events = rel_events[rel_events['teamId']!=team_id]

    # Mins played (use 96 if a null is retured against mins played)
    mp = 0
    for match in team_match_ids:
        if rel_events[rel_events['match_id']==match]['cumulative_mins'].max() == rel_events[rel_events['match_id']==match]['cumulative_mins'].max():
            mp += np.nanmax(rel_events[rel_events['match_id']==match]['cumulative_mins'])
        else:
            mp+=96
            
    # Passes for and against
    passes_for = rel_team_events[rel_team_events['eventType'].isin(['Pass', 'OffsidePass'])]
    passes_against = rel_opp_events[rel_opp_events['eventType'].isin(['Pass', 'OffsidePass'])]
    passes_for_high_33 = passes_for[passes_for['x']>=200/3]
    passes_against_high_33 = passes_against[passes_against['x']>=100/3]
    passes_against_high_60 = passes_against[passes_against['x']<=60]
    
    leaguetable_analyse_df.loc[idx, 'Minutes Played'] = mp
    leaguetable_analyse_df.loc[idx, 'Passes For'] = len(passes_for)
    leaguetable_analyse_df.loc[idx, 'Passes Against'] = len(passes_against)
    leaguetable_analyse_df.loc[idx, 'Passes For Final Third'] = len(passes_for_high_33)
    leaguetable_analyse_df.loc[idx, 'Passes Against Final Third'] = len(passes_against_high_33)
    leaguetable_analyse_df.loc[idx, 'Passes Against Highest 60%'] = len(passes_against_high_60)
    
    # Defensive actions
    def_actions = wce.find_defensive_actions(rel_team_events)
    def_actions_opp = wce.find_defensive_actions(rel_opp_events)
    def_actions_high_33 = def_actions[def_actions['x']>=200/3]
    def_actions_high_60 = def_actions[def_actions['x']>=40]
    
    leaguetable_analyse_df.loc[idx, 'Defensive Actions'] = len(def_actions)
    leaguetable_analyse_df.loc[idx, 'Final Third Defensive Actions'] = len(def_actions_high_33)
    leaguetable_analyse_df.loc[idx, 'High 60 Defensive Actions'] = len(def_actions_high_60)
    
    # Box entries for and against
    box_entry_attempts_for = rel_team_events[rel_team_events['box_entry_attempt']==True]
    box_entry_success_for = rel_team_events[rel_team_events['box_entry_successful']==True]
    box_entry_attempts_against = rel_opp_events[rel_opp_events['box_entry_attempt']==True]
    box_entry_success_against = rel_opp_events[rel_opp_events['box_entry_successful']==True]
    
    leaguetable_analyse_df.loc[idx, 'Attempted Box Entries For'] = len(box_entry_attempts_for)
    leaguetable_analyse_df.loc[idx, 'Successful Box Entries For'] = len(box_entry_success_for)
    leaguetable_analyse_df.loc[idx, 'Attempted Box Entries Against'] = len(box_entry_attempts_against)
    leaguetable_analyse_df.loc[idx, 'Successful Box Entries Against'] = len(box_entry_success_against)
    
    # Offensive Build-up
    threat_gen_events_for = rel_team_events[rel_team_events['xThreat']==rel_team_events['xThreat']] 
    threat_gen_events_for_ip = threat_gen_events_for[(~threat_gen_events_for['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 212 in x) else False))] 
    threat_gen_long_ball_for_ip = threat_gen_events_for_ip[threat_gen_events_for_ip['satisfiedEventsTypes'].apply(lambda x: True if (127 in x or 128 in x) else False)]
    threat_gen_cross_for_ip = threat_gen_events_for_ip[threat_gen_events_for_ip['satisfiedEventsTypes'].apply(lambda x: True if (125 in x or 126 in x or 59 in x) else False)]   
    threat_gen_carry_for_ip = threat_gen_events_for_ip[threat_gen_events_for_ip['eventType']=='Carry']

    leaguetable_analyse_df.loc[idx, 'In-Play Threat Creating Actions For'] = len(threat_gen_events_for_ip)
    leaguetable_analyse_df.loc[idx, 'In-Play xT For'] = threat_gen_events_for_ip['xThreat_gen'].sum()
    leaguetable_analyse_df.loc[idx, 'In-Play Long Ball xT For'] = threat_gen_long_ball_for_ip['xThreat_gen'].sum()
    leaguetable_analyse_df.loc[idx, 'In-Play Cross xT For'] = threat_gen_cross_for_ip['xThreat_gen'].sum()
    leaguetable_analyse_df.loc[idx, 'In-Play Carry xT For'] = threat_gen_carry_for_ip['xThreat_gen'].sum()

    # Opposition Build-Up    
    threat_gen_events_against = rel_opp_events[rel_opp_events['xThreat']==rel_opp_events['xThreat']] 
    threat_gen_events_against_ip = threat_gen_events_against[(~threat_gen_events_against['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 212 in x) else False))] 
    threat_gen_long_ball_against_ip = threat_gen_events_against_ip[threat_gen_events_against_ip['satisfiedEventsTypes'].apply(lambda x: True if (127 in x or 128 in x) else False)]
    threat_gen_cross_against_ip = threat_gen_events_against_ip[threat_gen_events_against_ip['satisfiedEventsTypes'].apply(lambda x: True if (125 in x or 126 in x or 59 in x) else False)]   
    threat_gen_carry_against_ip = threat_gen_events_against_ip[threat_gen_events_against_ip['eventType']=='Carry']
    
    leaguetable_analyse_df.loc[idx, 'In-Play Threat Creating Actions Against'] = len(threat_gen_events_against_ip)    
    leaguetable_analyse_df.loc[idx, 'In-Play xT Against'] = threat_gen_events_against_ip['xThreat_gen'].sum()
    leaguetable_analyse_df.loc[idx, 'In-Play Long Ball xT Against'] = threat_gen_long_ball_against_ip['xThreat_gen'].sum()
    leaguetable_analyse_df.loc[idx, 'In-Play Cross xT Against'] = threat_gen_cross_against_ip['xThreat_gen'].sum()
    leaguetable_analyse_df.loc[idx, 'In-Play Carry xT Against'] = threat_gen_carry_against_ip['xThreat_gen'].sum()

    # Shots and big chances for
    shots_for = rel_team_events[(rel_team_events['eventType'].isin(['MissedShots', 'SavedShot', 'ShotOnPost', 'Goal'])) & (~rel_team_events['satisfiedEventsTypes'].apply(lambda x: True if( 5 in x or 6 in x) else False))].copy()
    shots_for['shot_distance'] = shots_for[['x','y']].apply(lambda a: np.sqrt((120*((100-a[0])/100))**2 + (80*((50-a[1])/100))**2),axis = 1)        
    big_chances_for = rel_team_events[rel_team_events['satisfiedEventsTypes'].apply(lambda x: True if 203 in x and not (31 in x or 34 in x or 212 in x) else False)]

    leaguetable_analyse_df.loc[idx, 'In-Play Shots For'] = len(shots_for)
    leaguetable_analyse_df.loc[idx, 'In-Play Shot For Mean Distance'] = shots_for['shot_distance'].mean()
    leaguetable_analyse_df.loc[idx, 'Big Chances For'] = len(big_chances_for)
  
    # Shots and big chances against
    shots_against = rel_opp_events[(rel_opp_events['eventType'].isin(['MissedShots', 'SavedShot', 'ShotOnPost', 'Goal'])) & (~rel_opp_events['satisfiedEventsTypes'].apply(lambda x: True if( 5 in x or 6 in x) else False))].copy()
    shots_against['shot_distance'] = shots_against[['x','y']].apply(lambda a: np.sqrt((120*((100-a[0])/100))**2 + (80*((50-a[1])/100))**2),axis = 1)        
    big_chances_against = rel_opp_events[rel_opp_events['satisfiedEventsTypes'].apply(lambda x: True if 203 in x and not (31 in x or 34 in x or 212 in x) else False)]

    leaguetable_analyse_df.loc[idx, 'In-Play Shots Against'] = len(shots_against)
    leaguetable_analyse_df.loc[idx, 'In-Play Shot Against Mean Distance'] = shots_against['shot_distance'].mean()
    leaguetable_analyse_df.loc[idx, 'Big Chances Against'] = len(big_chances_against)
    
    # Offensive set piece performance
    set_pieces = rel_team_events[rel_team_events['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 6 in x or 5 in x) else False)]
    set_pieces = set_pieces[(set_pieces['eventType']=='Pass') |
                            (set_pieces['eventType']=='SavedShot') |
                            ((set_pieces['eventType']=='MissedShots') & (set_pieces['blockedX']=='blockedX'))]
    set_pieces = wce.get_pass_outcome(set_pieces, rel_events, t=5)
    good_set_pieces = set_pieces[set_pieces['pass_outcome'].isin(['Goal', 'Shot', 'Key Pass'])]
    
    leaguetable_analyse_df.loc[idx, 'Indirect Set Pieces For'] = len(set_pieces)
    leaguetable_analyse_df.loc[idx, 'Indirect Set Piece Chances For'] = len(good_set_pieces)
    
    # Defensive set piece performance
    opp_set_pieces = rel_opp_events[rel_opp_events['satisfiedEventsTypes'].apply(lambda x: True if (31 in x or 34 in x or 6 in x or 5 in x) else False)]
    opp_set_pieces = opp_set_pieces[(opp_set_pieces['eventType']=='Pass') |
                                    (opp_set_pieces['eventType']=='SavedShot') |
                                    ((opp_set_pieces['eventType']=='MissedShots') & (opp_set_pieces['blockedX']=='blockedX'))]
    opp_set_pieces = wce.get_pass_outcome(opp_set_pieces, rel_events, t=5)
    opp_good_set_pieces = opp_set_pieces[opp_set_pieces['pass_outcome'].isin(['Goal', 'Shot', 'Key Pass'])]
    
    leaguetable_analyse_df.loc[idx, 'Indirect Set Pieces Against'] = len(opp_set_pieces)
    leaguetable_analyse_df.loc[idx, 'Indirect Set Piece Chances Against'] = len(opp_good_set_pieces)
    
    # Offensive cross performance
    crosses = passes_for[passes_for['satisfiedEventsTypes'].apply(lambda x: True if (125 in x or 126 in x or 59 in x) and not(31 in x or 34 in x or 212 in x) else False)]   
    crosses = wce.get_pass_outcome(crosses, rel_events, t=5)
    good_crosses = crosses[crosses['pass_outcome'].isin(['Goal', 'Shot', 'Key Pass'])]
    
    leaguetable_analyse_df.loc[idx, 'In-Play Crosses For'] = len(crosses)
    leaguetable_analyse_df.loc[idx, 'In-Play Chance-creating Crosses For'] = len(good_crosses)
    
    # Defensive cross performance
    opp_crosses = passes_against[passes_against['satisfiedEventsTypes'].apply(lambda x: True if (125 in x or 126 in x or 59 in x) and not(31 in x or 34 in x or 212 in x) else False)]   
    opp_crosses = wce.get_pass_outcome(opp_crosses, rel_events, t=5)
    opp_good_crosses = opp_crosses[opp_crosses['pass_outcome'].isin(['Goal', 'Shot', 'Key Pass'])]
    
    leaguetable_analyse_df.loc[idx, 'In-Play Crosses Against'] = len(opp_crosses)
    leaguetable_analyse_df.loc[idx, 'In-Play Chance-creating Crosses Against'] = len(opp_good_crosses)
    
    # Transition - ball wins
    recoveries = rel_team_events[(rel_team_events['eventType']=='BallRecovery') & (rel_team_events['outcomeType']=='Successful')]
    interceptions = rel_team_events[(rel_team_events['eventType']=='Interception') & (rel_team_events['outcomeType']=='Successful')]
    tackles = rel_team_events[(rel_team_events['eventType']=='Tackle') & (rel_team_events['outcomeType']=='Successful')]
    pass_blocks = rel_team_events[(rel_team_events['eventType']=='BlockedPass') & (rel_team_events['outcomeType']=='Successful') ]
    ball_wins = pd.concat([recoveries, interceptions, tackles, pass_blocks], axis=0)
    ball_wins_high_33 = ball_wins[ball_wins['x']>=200/3]
    
    opp_recoveries = rel_opp_events[(rel_opp_events['eventType']=='BallRecovery') & (rel_opp_events['outcomeType']=='Successful')]
    opp_interceptions = rel_opp_events[(rel_opp_events['eventType']=='Interception') & (rel_opp_events['outcomeType']=='Successful')]
    opp_tackles = rel_opp_events[(rel_opp_events['eventType']=='Tackle') & (rel_opp_events['outcomeType']=='Successful')]
    opp_pass_blocks = rel_opp_events[(rel_opp_events['eventType']=='BlockedPass') & (rel_opp_events['outcomeType']=='Successful') ]
    opp_ball_wins = pd.concat([opp_recoveries, opp_interceptions, opp_tackles, opp_pass_blocks], axis=0)
    
    leaguetable_analyse_df.loc[idx, 'Ball Wins'] = len(ball_wins)
    leaguetable_analyse_df.loc[idx, 'Final Third Ball Wins'] = len(ball_wins_high_33)
    leaguetable_analyse_df.loc[idx, 'Opp Ball Wins'] = len(opp_ball_wins)
    
    # Transition - ball losses
    bad_touches = rel_team_events[(rel_team_events['eventType']=='BallTouch') & (rel_team_events['outcomeType']=='Unsuccessful')]
    bad_pass = rel_team_events[(rel_team_events['eventType']=='Pass') & (rel_team_events['outcomeType']=='Unsuccessful')]
    bad_takeon = rel_team_events[(rel_team_events['eventType']=='TakeOn') & (rel_team_events['outcomeType']=='Unsuccessful')]
    disspossessed = rel_team_events[rel_team_events['eventType']=='Disspossessed']
    ball_losses = pd.concat([bad_touches, bad_pass, bad_takeon, disspossessed], axis=0)

    opp_bad_touches = rel_opp_events[(rel_opp_events['eventType']=='BallTouch') & (rel_opp_events['outcomeType']=='Unsuccessful')]
    opp_bad_pass = rel_opp_events[(rel_opp_events['eventType']=='Pass') & (rel_opp_events['outcomeType']=='Unsuccessful')]
    opp_bad_takeon = rel_opp_events[(rel_opp_events['eventType']=='TakeOn') & (rel_opp_events['outcomeType']=='Unsuccessful')]
    opp_disspossessed = rel_opp_events[rel_opp_events['eventType']=='Disspossessed']
    opp_ball_losses = pd.concat([opp_bad_touches, opp_bad_pass, opp_bad_takeon, opp_disspossessed], axis=0)

    leaguetable_analyse_df.loc[idx, 'Ball Losses'] = len(ball_losses)    
    leaguetable_analyse_df.loc[idx, 'Opp Ball Losses'] = len(opp_ball_losses)

# %% Generate metrics
    
metric_df = pd.DataFrame()
metric_df['Team'] = leaguetable_analyse_df['team']

# Use actual points as opposed to registered points, to discount deductions
metric_df['Points'] = 3*leaguetable_analyse_df['wins'] + leaguetable_analyse_df['draws']
   
style_df = metric_df.copy()

style_df['Passes / 90'] = 90*leaguetable_analyse_df['Passes For']/leaguetable_analyse_df['Minutes Played']
style_df['Opp passes / 90'] = 90*leaguetable_analyse_df['Passes Against']/leaguetable_analyse_df['Minutes Played']
style_df['Passes / Ball Loss'] = leaguetable_analyse_df['Passes For']/leaguetable_analyse_df['Ball Losses']
style_df['Opp Passes / Opp Ball Loss'] = leaguetable_analyse_df['Passes Against']/leaguetable_analyse_df['Opp Ball Losses']
style_df['xT / IP Offensive Action'] = leaguetable_analyse_df['In-Play xT For']/leaguetable_analyse_df['In-Play Threat Creating Actions For']
style_df['Opp xT / IP Offensive Action'] = leaguetable_analyse_df['In-Play xT Against']/leaguetable_analyse_df['In-Play Threat Creating Actions Against']
style_df['IP Box Entries For / 100 Passes'] = 100 * leaguetable_analyse_df['Successful Box Entries For'] / leaguetable_analyse_df['Passes For']
style_df['IP Box Entries Against / 100 Opp Passes'] = 100 * leaguetable_analyse_df['Successful Box Entries Against'] / leaguetable_analyse_df['Passes Against']

threat_df = metric_df.copy()

threat_df['xT For / 90'] = 90*leaguetable_analyse_df['In-Play xT For']/leaguetable_analyse_df['Minutes Played']
threat_df['xT For / Ball Loss'] = leaguetable_analyse_df['In-Play xT For']/leaguetable_analyse_df['Ball Losses']
threat_df['Pct xT For by Ball Carries'] = 100*(leaguetable_analyse_df['In-Play Carry xT For']/leaguetable_analyse_df['In-Play xT For'])
threat_df['Pct xT For by Crosses'] = 100*(leaguetable_analyse_df['In-Play Cross xT For']/leaguetable_analyse_df['In-Play xT For'])
threat_df['Pct xT For by Long Passes'] = 100*(leaguetable_analyse_df['In-Play Long Ball xT For']/leaguetable_analyse_df['In-Play xT For'])
threat_df['xT Against / 90'] = 90*leaguetable_analyse_df['In-Play xT Against']/leaguetable_analyse_df['Minutes Played']
threat_df['xT Against / Opp Ball Loss'] = leaguetable_analyse_df['In-Play xT Against']/leaguetable_analyse_df['Opp Ball Losses']
threat_df['Pct xT Against by Ball Carries'] = 100*(leaguetable_analyse_df['In-Play Carry xT Against']/leaguetable_analyse_df['In-Play xT Against'])
threat_df['Pct xT Against by Crosses'] = 100*(leaguetable_analyse_df['In-Play Cross xT Against']/leaguetable_analyse_df['In-Play xT Against'])
threat_df['Pct xT Against by Long Passes'] = 100*(leaguetable_analyse_df['In-Play Long Ball xT Against']/leaguetable_analyse_df['In-Play xT Against'])

chance_df = metric_df.copy()

chance_df['Big Chances For / 100 Passes'] = 100*leaguetable_analyse_df['Big Chances For']/leaguetable_analyse_df['Passes For']
chance_df['Big Chances For / Ball Loss'] = leaguetable_analyse_df['Big Chances For']/leaguetable_analyse_df['Ball Losses']
chance_df['Big Chances Against / 100 Opp Passes'] = 100*leaguetable_analyse_df['Big Chances Against']/leaguetable_analyse_df['Passes Against']
chance_df['Big Chances Against / Opp Ball Loss'] = leaguetable_analyse_df['Big Chances Against']/leaguetable_analyse_df['Opp Ball Losses']
chance_df['Pct Crosses For result in Chance'] = 100*leaguetable_analyse_df['In-Play Chance-creating Crosses For']/leaguetable_analyse_df['In-Play Crosses For']
chance_df['Pct Set Pieces For result in Chance'] = 100*leaguetable_analyse_df['Indirect Set Piece Chances For']/leaguetable_analyse_df['Indirect Set Pieces For']

defensive_df = metric_df.copy()

defensive_df['Defensive Actions / 100 Opp Passes'] = 100*leaguetable_analyse_df['Defensive Actions'] / leaguetable_analyse_df['Passes Against']
defensive_df['High Def Actions / 100 Opp Passes own 3rd'] = 100*leaguetable_analyse_df['Final Third Defensive Actions'] / leaguetable_analyse_df['Passes Against Final Third']
defensive_df['Ball Wins / 100 Opp Passes'] = 100*leaguetable_analyse_df['Ball Wins'] / leaguetable_analyse_df['Passes Against']
defensive_df['High Ball Wins / 100 Opp Passes own 3rd'] = 100*leaguetable_analyse_df['Final Third Ball Wins'] / leaguetable_analyse_df['Passes Against Final Third']
defensive_df['PPDA Highest 60% Pitch'] = leaguetable_analyse_df['Passes Against Highest 60%']/leaguetable_analyse_df['High 60 Defensive Actions']
defensive_df['Pct Crosses Against result in Chance'] = 100*leaguetable_analyse_df['In-Play Chance-creating Crosses Against']/leaguetable_analyse_df['In-Play Crosses Against']
defensive_df['Pct Set Pieces Against result in Chance'] = 100*leaguetable_analyse_df['Indirect Set Piece Chances Against']/leaguetable_analyse_df['Indirect Set Pieces Against']

shots_df = metric_df.copy()

shots_df['Goal Difference'] = leaguetable_analyse_df['goals_for'] - leaguetable_analyse_df['goals_against']
shots_df['IP Shots For / 100 Passes'] = 100*leaguetable_analyse_df['In-Play Shots For']/leaguetable_analyse_df['Passes For']
shots_df['IP Shots Against / 100 Opp Passes'] = 100*leaguetable_analyse_df['In-Play Shots Against']/leaguetable_analyse_df['Passes Against']
shots_df['IP Shots For Mean Distance'] = leaguetable_analyse_df['In-Play Shot For Mean Distance']
shots_df['IP Shots Against Mean Distance'] = leaguetable_analyse_df['In-Play Shot Against Mean Distance']

all_metric_df = pd.concat([style_df, threat_df, chance_df, defensive_df, shots_df], axis=1)
all_metric_df = all_metric_df.loc[:,~all_metric_df.columns.duplicated()]

# %% PLOT 1 - Correlation matrix

# Construct plot
fig, ax = plt.subplots(nrows = 1, ncols=1, figsize=[12,10])
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Overwrite rcparams and custom colorbar
mpl.rcParams['xtick.color'] = 'w'
mpl.rcParams['ytick.color'] = 'w'
CustomCmap = mpl.colors.LinearSegmentedColormap.from_list("", ["violet","#313332","palegreen"])

# Plot correlation matrix
plot_df = all_metric_df
correlations = plot_df.corr(numeric_only=True)
hm = sns.heatmap(correlations, annot = True, cmap = CustomCmap, vmin=-1, vmax=1, fmt='.2f', cbar=False, annot_kws={"size": 6})

# Add and position colorbar
legend_ax = fig.add_axes([0.015, 0.01, 0.28, 0.09])
plt.xlim([0, 8])
plt.ylim([-0.5, 1])
legend_ax.axis("off")

for idx, r in enumerate(np.linspace(-1,1,7)):
    if idx%2 == 0:
        ypos = 0.38
    else:
        ypos= 0.62
    if idx == 0 or idx == 6:
        text_color = "#313332"
    else:
        text_color = "w"
    xpos = idx/1.4 + 1.5
    color = CustomCmap(int(255*idx/6))
    legend_ax.scatter(xpos, ypos, marker='H', s=550, color=color, edgecolors='w')
    legend_ax.text(xpos, ypos, round(r,2), color=text_color, fontsize=8, fontweight = "bold", ha = "center", va = "center")

legend_ax.text(3.7, -0.2, "Correlation Score, r", color='w', fontweight = "bold", ha = "center", va = "center")

# Create title
leagues = {'EPL': 'Premier League', 'La_Liga': 'La Liga', 'Bundesliga': 'Bundesliga', 'Serie_A': 'Serie A',
           'Ligue_1': 'Ligue 1', 'RFPL': 'Russian Premier Leauge', 'EFLC': 'EFL Championship', 'World_Cup': 'World Cup',
           'EFL1': 'EFL League One', 'EFL2': 'EFL League Two'}

title_text = f"{leagues[data_grab[-1][0]]} Last {len(data_grab)} Seasons − Features of Successful Teams"
subtitle_text = "Correlation between Team Metrics over a Season and Points Accumulated in that Season"
subsubtitle_text = "Correlation Matrix showing Correlation between Metric Pairs"

fig.text(0.105, 0.94, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.105, 0.914, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.105, 0.889, subsubtitle_text, fontweight="regular", fontsize=10, color='w')

ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize = 7)
ax.set_yticklabels(ax.get_ymajorticklabels(), fontsize = 7)
ax.set_position([0.2, 0.28, 0.75, 0.57])

# Add competition Logo
ax2 = fig.add_axes([0.012, 0.875, 0.1, 0.1])
ax2.axis("off")
ax2.imshow(comp_logo)

# Create footer
fig.text(0.5, 0.024, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.93, 0.006, 0.05, 0.05])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)

# Save image to file 
fig.savefig(f"team_metric_pts_correlation/{data_grab[-1][0]}-{data_grab[0][1]}-to-{data_grab[-1][1]}-metric-correlation-matrix", dpi=300)

# %% Bar plot

#points_corr_df = correlations['Points'].sort_values(ascending = False)[1:]

points_corr_pos_df = points_corr_df[points_corr_df>=0]
points_corr_neg_df = points_corr_df[points_corr_df<0]
empty_df = pd.Series(index = [""], data=[0])
plot_df = pd.concat([points_corr_pos_df, empty_df, points_corr_neg_df, empty_df])

# Set-up bar plot
fig, ax = plt.subplots(figsize=(10, 10))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)

# Define colour scale
color_scale = 255*((plot_df - (-1))/(1 - (-1)))
color_scale = [int(color) for color in color_scale.values.tolist()]

# Plot data
ax.barh(plot_df.index, plot_df, color=CustomCmap(color_scale), edgecolor='grey', lw=0.2)
ax.plot([0, 0], [len(plot_df), -2], color = 'w', lw = 0.5)

# Draw line through artificial y=0
xlim = ax.set_xlim([-1.05, 1.05])
ax.plot([-0.8, 0.8], [len(points_corr_pos_df), len(points_corr_pos_df)], color = 'w', lw = 0.5)

# Define axes
ax.set_xlabel("Correlation Score, r [-1, 1]", labelpad = 10, fontweight="bold", fontsize=12, color='w')
ax.set_ylim(-0.5, len(plot_df)-0.5)
ax.spines['bottom'].set_color('w')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['left'].set_visible(False)
ax.set_axisbelow(True)
ax.grid(color='gray', alpha = 0.2)
ax.set_yticks([])
plt.gca().invert_yaxis()

# Add axes labels and badges
path_eff = [path_effects.Stroke(linewidth=3, foreground='#313332'), path_effects.Normal()]
for idx, plot_pos in enumerate(np.arange(0.3, len(plot_df))):
    #if idx not in [len(pos),2*n_players+1]:
        metric = plot_df.index[idx]
        if plot_df[idx] > 0:
            if plot_df[idx] > 0.1:
                ax.text(plot_df[idx], plot_pos, "+" + str(round(plot_df[idx],2))+ " ", fontsize = 8, color = 'w', va = "bottom", ha = "right", path_effects = path_eff)
            ax.text(-0.02, plot_pos, metric, fontsize = 8, color = 'w', va = "bottom", ha = "right")
        else:
            if plot_df[idx] < -0.1:
                ax.text(plot_df[idx], plot_pos, " " + str(round(plot_df[idx],2)), fontsize = 8, color = 'w', va = "bottom", ha = "left", path_effects = path_eff)
            ax.text(0.02, plot_pos, metric, fontsize = 8, color = 'w', va = "bottom", ha = "left")


# Create title
title_text = f"{leagues[data_grab[-1][0]]} Last {len(data_grab)} Seasons − Features of Successful Teams"
subtitle_text = "Correlation between Team Metrics over a Season and Points Accumulated in that Season"
subsubtitle_text = "Bar Chart showing Correlation between each Metric and Total Points"
fig.text(0.115, 0.94, title_text, fontweight="bold", fontsize=15, color='w')
fig.text(0.115, 0.914, subtitle_text, fontweight="bold", fontsize=12, color='w')
fig.text(0.115, 0.89, subsubtitle_text, fontweight="regular", fontsize=10, color='w')

# Add competition Logo
ax2 = fig.add_axes([0.012, 0.875, 0.1, 0.1])
ax2.axis("off")
ax2.imshow(comp_logo)

# Create footer
fig.text(0.5, 0.024, "Created by Jake Kolliari (@_JKDS_). Data provided by Opta.",
         fontstyle="italic", ha="center", fontsize=9, color="white")

# Add twitter logo
ax = fig.add_axes([0.93, 0.006, 0.05, 0.05])
ax.axis("off")
badge = Image.open('..\..\data_directory\misc_data\images\JK Twitter Logo.png')
ax.imshow(badge)    

# Tight layout
fig.tight_layout(rect=[0.07, 0.04, 0.93, 0.86])

# Save image to file 
fig.savefig(f"team_metric_pts_correlation/{data_grab[-1][0]}-{data_grab[0][1]}-to-{data_grab[-1][1]}-metric-correlation-with-points", dpi=300)

# %% Scatter of specific metric

fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (8,8))
fig.set_facecolor('#313332')
ax.patch.set_alpha(0)
y_plot = 'Pct xT Against by Crosses'

# Add line
sns.scatterplot(all_metric_df, y = y_plot, x = 'Points', color = 'grey', s=50, ax=ax, zorder = 2)
reg = sns.regplot(all_metric_df, y = y_plot, x = 'Points', scatter = False, line_kws={"color": "w", "lw":1, "ls" :'--'}, scatter_kws={"color": "grey", "s":50, "zorder":2}, ax=ax)

# Format
ax.grid(lw = 0.5, color= 'w', ls = ':')
ax.spines['top'].set_visible(False) 
ax.spines['right'].set_visible(False) 
ax.spines['bottom'].set_color("w") 
ax.spines['left'].set_color("w")
ax.xaxis.label.set_color('w')
ax.yaxis.label.set_color('w')

# Save image to file 
fig.savefig(f"team_metric_pts_correlation/{data_grab[-1][0]}-{data_grab[0][1]}-to-{data_grab[-1][1]}-{y_plot.replace(' / ', ' ').replace(' ','-').lower()}-vs-points", dpi=300)

# %% Compare two different leagues

# Run the script for one league and manually save points_corr_df to league_1_corr_df, run the script again and save points_corr_df to league_2_corr_df
#league_1_corr_df = None
#league_2_corr_df = None

# %% Plot to compare two leauges

league_1_name = 'EFLC'
league_2_name = 'EPL'

if league_1_corr_df is not None and league_2_corr_df is not None:
    delta_corr_df = pd.merge(league_1_corr_df, league_2_corr_df, left_index=True, right_index=True, suffixes=('_'+league_1_name, '_'+league_2_name))
    delta_corr_df['Corr_Increase'] = abs(delta_corr_df['Points_' + league_1_name]) - abs(delta_corr_df['Points_' + league_2_name])