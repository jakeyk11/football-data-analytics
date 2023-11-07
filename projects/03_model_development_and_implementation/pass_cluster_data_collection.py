''' Load data for pass clustering '''

# %% Imports

import pandas as pd
import numpy as np
import os
import bz2
import pickle

# %% Select data to load

data_to_load = [['EPL', '2022'],
                ['La_Liga', '2022'],
                ['Ligue_1', '2022'],
                ['Bundesliga', '2022'],
                ['Serie_A', '2022'],
                ['EFLC', '2022'],
                ['EPL', '2021'],
                ['La_Liga', '2021'],
                ['Ligue_1', '2021'],
                ['Bundesliga', '2021'],
                ['Serie_A', '2021'],
                ['EFLC', '2021'],
                ['EPL', '2020'],
                ['La_Liga', '2020'],
                ['Ligue_1', '2020'],
                ['Bundesliga', '2020'],
                ['Serie_A', '2020'],
                ['EFLC', '2020'],
                ]

# Initialise storage dataframes
passes_df = pd.DataFrame()

for data in data_to_load:
    league = data[0]
    year = data[1]
    league_passes = pd.DataFrame()
        
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
            match_passes = match_events[(match_events['outcomeType'] == 'Successful') &
                                        (match_events['eventType'] == 'Pass') & 
                                        (match_events['satisfiedEventsTypes'].apply(lambda x: not (31 in x or 34 in x or 212 in x)))]
            
            
            league_passes = pd.concat([league_passes, match_passes])

    # Append league data to combined dataset
    passes_df = pd.concat([passes_df, league_passes])

    print(f"{league}, {year} passes loaded")

# %% Store data in random order in a group of compressed bz2 files

passes_df_out = passes_df.sample(frac=1).reset_index(drop=True)
num_files = 100
n_passes = len(passes_df_out)
sample_size = int(np.floor(n_passes/num_files))
for idx in np.arange(0,num_files):
    print(f"Isolating sample {idx}")
    pass_sample_df = passes_df_out.iloc[sample_size*idx:sample_size*(idx+1)]
    print(f"Saving sample {idx}")
    with bz2.BZ2File(f"pass_data_{idx}.pbz2", "wb") as f:
        pickle.dump(pass_sample_df, f)
    print("Save complete")
