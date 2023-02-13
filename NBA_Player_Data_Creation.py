#%%
# Import Libraries
import pandas as pd
import numpy as np

#%%
# Creates a rolling average for defined columns
def Rolling_Average(df, n_rolls, roll_cols, col_title):
    rolling = df[roll_cols].rolling(n_rolls).mean(skipna=True).shift(1)
    rolling_cols = [f'{col_title}_{col}_{n_rolls}' for col in rolling.columns]
    rolling.columns = rolling_cols
    
    return rolling

#%%
# NOT USED YET
def Hit_Calculation(stat_val, prop_val):
    if np.isnan(prop_val):
        return np.nan
    elif stat_val > prop_val:
        return 1
    elif stat_val < prop_val:
        return 0
    else:
        return 2

#%%
# Import Player Data and Prop Data
NBA_PLAYER_DATA = pd.read_csv('CSVs/NBA_Player_Data.csv', index_col=0)
NBA_PLAYER_PROP = pd.read_csv('CSVs/Player_Prop_Data.csv', index_col=0)

#%%
# Merge the data
merge_data = NBA_PLAYER_DATA.merge(NBA_PLAYER_PROP, on=['Player_Name','GAME_DATE','MATCHUP'], how='inner')



#%%
# Possibly create function to handle this and make better options
merge_data['PTS_Hit'] = (merge_data['PTS'] > merge_data['PTS_PROP']).astype(int)
merge_data['REB_Hit'] = (merge_data['REB'] > merge_data['REB_PROP']).astype(int)
merge_data['AST_Hit'] = (merge_data['AST'] > merge_data['AST_PROP']).astype(int)

FULL_RESULTS = pd.DataFrame()

for player in NBA_PLAYER_DATA['Player_ID'].unique():
# player = MASTER['Player_ID'].unique()[10]
# player_name = MASTER['Player_Name'].unique()[10]
    if (merge_data[merge_data['Player_ID'] == player].empty) != True:
        full_player_gamelog = merge_data[merge_data['Player_ID'] == player]
        home_player_gamelog = merge_data[(merge_data['Player_ID'] == player) & (NBA_PLAYER_DATA['HA'] == 0)]
        away_player_gamelog = merge_data[(merge_data['Player_ID'] == player) & (NBA_PLAYER_DATA['HA'] == 1)]
        
        cols_to_not_roll = ['SEASON_ID', 'Player_ID', 'Game_ID', 'GAME_DATE', 'MATCHUP', 
                            'TEAM', 'TEAM_ID', 'OPP', 'OPP_ID', 'HA', 'Player_Name', 'POS',
                            'POS_CODE']
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
        
        full_rolling_10 = Rolling_Average(full_player_gamelog, 10, cols_to_roll, 'full')
        cols_to_not_roll += list(full_rolling_10.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
        
        full_rolling_20 = Rolling_Average(full_player_gamelog, 20, cols_to_roll, 'full')
        cols_to_not_roll += list(full_rolling_20.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
        
        home_rolling_10 = Rolling_Average(home_player_gamelog, 10, cols_to_roll, 'home')
        cols_to_not_roll += list(home_rolling_10.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
        
        home_rolling_20 = Rolling_Average(home_player_gamelog, 20, cols_to_roll, 'home')
        cols_to_not_roll += list(home_rolling_20.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
        
        away_rolling_10 = Rolling_Average(away_player_gamelog, 10, cols_to_roll, 'away')
        cols_to_not_roll += list(away_rolling_10.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
        
        away_rolling_20 = Rolling_Average(away_player_gamelog, 20, cols_to_roll, 'away')
        cols_to_not_roll += list(away_rolling_20.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
        
        rolls = pd.concat([full_rolling_10, full_rolling_20, home_rolling_10, home_rolling_20,
                           away_rolling_10, away_rolling_20], axis=1)
        
        full_player_gamelog = pd.concat([full_player_gamelog, rolls], axis=1)
        
        # Remove the next game row, so it is not removed when np.nan rows are dropped
        next_game_df = pd.DataFrame(full_player_gamelog.iloc[-1], columns=full_player_gamelog.columns)
        full_player_gamelog = full_player_gamelog[full_player_gamelog['full_PTS_20'].notna()]
        # full_player_gamelog = pd.concat([full_player_gamelog, next_game_df], axis=0)
        
        if FULL_RESULTS.empty:
            FULL_RESULTS = full_player_gamelog
        else:
            FULL_RESULTS = pd.concat([FULL_RESULTS, full_player_gamelog], axis=0)
            
#%%
# Send the Full DataFrame to Excel and CSV files
FULL_RESULTS.to_excel('Excels/THE BIG ONE.xlsx')
FULL_RESULTS.to_csv('CSVs/THE_BIG_ONE.csv')

# %%