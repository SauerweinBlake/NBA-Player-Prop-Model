#%%
# Import Libraries
import pandas as pd
import numpy as np
from nba_api.stats.static.players import find_players_by_full_name, find_players_by_first_name, find_players_by_last_name

#%%
# Creates a rolling average for defined columns
def Rolling_Average(df, n_rolls, roll_cols, sort_cols, col_title):
    rolling = df[roll_cols].sort_values(sort_cols).rolling(n_rolls).mean(skipna=True).shift(1)
    rolling_cols = [f'{col_title}_{col}_{n_rolls}' for col in rolling.columns]
    rolling.columns = rolling_cols
    
    return rolling

def Team_Abbr_Adj(team_abbr):
    incorrect_team_abbr = {'PHO':'PHX', 'UTH':'UTA', 'NOR':'NOP'}
    try:
        return incorrect_team_abbr[team_abbr]
    except:
        return team_abbr

#%%
# Import Player Data and Prop Data
player_data = pd.read_csv('CSVs/NBA_Player_Data.csv', index_col=0)
player_data['GAME_DATE'] = pd.to_datetime(player_data['GAME_DATE'])

prop_data = pd.read_csv('CSVs/Player_Prop_Data.csv', index_col=0)
prop_data['GAME_DATE'] = pd.to_datetime(prop_data['GAME_DATE'])

merge_data = player_data.merge(prop_data, how='outer')

#%%
# Clean the Data
player_data['WL'] = [1 if x == 'W' else 0 for x in player_data['WL']]
player_data['TEAM'] = [x.split(' ')[0] for x in player_data['MATCHUP']]
player_data['OPP'] = [x.split(' ')[2] for x in player_data['MATCHUP']]
player_data['HA'] = [1 if x.split(' ')[1] == '@' else 0 for x in player_data['MATCHUP']]
player_data['POS_CODE'] = player_data['POS'].astype('category').cat.codes
player_data['TEAM_CODE'] = player_data['TEAM'].astype('category').cat.codes
player_data['OPP_CODE'] = player_data['OPP'].astype('category').cat.codes
player_data['Off_Days'] = player_data["GAME_DATE"].diff().apply(lambda x: x/np.timedelta64(1, 'D')).fillna(0).astype('int64')
player_data['Off_Days'] = [0 if x > 100 else x for x in player_data['Off_Days']]

player_data_cols = player_data.columns

#%%
# Rolling averages
for pid in player_data['Player_ID']:
    pdf = player_data[player_data['Player_ID'] == pid]
    pdf_home = pdf[pdf['HA'] == 0]
    pdf_away = pdf[pdf['HA'] == 1]

    full_10 = Rolling_Average(pdf, 10, player_data_cols, ['Player_ID','GAME_DATE'], 'full')
    full_20 = Rolling_Average(pdf, 20, player_data_cols, ['Player_ID','GAME_DATE'], 'full')
    home_10 = Rolling_Average(pdf_home, 10, player_data_cols, ['Player_ID','GAME_DATE'], 'home')
    home_20 = Rolling_Average(pdf_home, 10, player_data_cols, ['Player_ID','GAME_DATE'], 'home')
    away_10 = Rolling_Average(pdf_away, 10, player_data_cols, ['Player_ID','GAME_DATE'], 'away')
    away_20 = Rolling_Average(pdf_away, 20, player_data_cols, ['Player_ID','GAME_DATE'], 'away')



#%%
# Merge prop data and player data
merge_data = player_data.merge(prop_data, how='outer', on=['GAME_DATE', 'Player_Name', 'MATCHUP'])
#%%
pts = merge_data[merge_data['PTS_PROP'].notna()].copy()
reb = merge_data[merge_data['REB_PROP'].notna()].copy()
ast = merge_data[merge_data['AST_PROP'].notna()].copy()

#%%
# 
pts['PTS_Hit'] = (pts['PTS'] > pts['PTS_PROP']).astype(int)
reb['REB_Hit'] = (reb['REB'] > reb['REB_PROP']).astype(int)
ast['AST_Hit'] = (ast['AST'] > ast['AST_PROP']).astype(int)
            
#%%
# Send the Full DataFrame to Excel and CSV files
FULL_RESULTS.to_excel('Excels/THE BIG ONE.xlsx')
FULL_RESULTS.to_csv('CSVs/THE_BIG_ONE.csv')

# %%