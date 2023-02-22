#%%
# Import Libraries
import pandas as pd
import numpy as np
from datetime import date
from nba_api.stats.static import teams

#%%
# Creates a rolling average for defined columns
def Rolling_Average(df, n_rolls, roll_cols, col_title):
    rolling = df[roll_cols].rolling(n_rolls).mean(skipna=True).shift(1)
    rolling_cols = [f'{col_title}_{col}_{n_rolls}' for col in rolling.columns]
    rolling.columns = rolling_cols
    
    return rolling

#%%
# Constants
NBA_TEAMS_ABBRS = [x['abbreviation'] for x in teams.get_teams()]

#%%
# Import Player Data and Prop Data
player_data = pd.read_csv('CSVs/NBA_Player_Data.csv', index_col=0)
player_data['GAME_DATE'] = pd.to_datetime(player_data['GAME_DATE'])

prop_data = pd.read_csv('CSVs/Player_Prop_Data.csv', index_col=0)
prop_data['GAME_DATE'] = pd.to_datetime(prop_data['GAME_DATE'])

#%%
# Verify there are no missing/incorrect Team abbreviations from the Prop Data
inc_abbrs = []
prop_teams = [x.split(' ')[0] for x in prop_data['MATCHUP']]
for team in prop_teams:
    if team not in NBA_TEAMS_ABBRS:
        inc_abbrs.append(team)

if len(inc_abbrs) > 0:
    raise(ValueError)

# TEMP ROW
player_data = player_data[player_data['GAME_DATE'] != '2023-02-16']
# date.today()
prop_data_hist = prop_data[prop_data['GAME_DATE'] != '2023-02-16']
prop_data_today = prop_data[prop_data['GAME_DATE'] == '2023-02-16']

merge_data = player_data.merge(prop_data_hist, how='left', on=['Player_ID','GAME_DATE','MATCHUP','SEASON_ID','Player_Name'])
merge_data = pd.concat([merge_data,prop_data_today], axis=0)
merge_data.sort_values(['Player_ID','GAME_DATE'], inplace=True)
merge_data.reset_index(drop=True, inplace=True)

#%%
# Clean the Data
merge_data['WL'] = [1 if x == 'W' else 0 for x in merge_data['WL']]
merge_data['TEAM'] = [x.split(' ')[0] for x in merge_data['MATCHUP']]
merge_data['OPP'] = [x.split(' ')[2] for x in merge_data['MATCHUP']]
merge_data['HA'] = [1 if x.split(' ')[1] == '@' else 0 for x in merge_data['MATCHUP']]
merge_data['POS_CODE'] = merge_data['POS'].astype('category').cat.codes
merge_data['TEAM_CODE'] = merge_data['TEAM'].astype('category').cat.codes
merge_data['OPP_CODE'] = merge_data['OPP'].astype('category').cat.codes
merge_data['Off_Days'] = merge_data["GAME_DATE"].diff().apply(lambda x: x/np.timedelta64(1, 'D')).fillna(0).astype('int64')
merge_data['Off_Days'] = [0 if x > 100 else x for x in merge_data['Off_Days']]

player_data_cols = player_data.columns
cols_to_rem = ['SEASON_ID','Game_ID','GAME_DATE','MATCHUP',
                'Player_Name','POS','TEAM','OPP'] + list(prop_data.columns)
rolling_cols = [col for col in player_data_cols if col not in cols_to_rem]

#%%
# Rolling averages
for pid in merge_data['Player_ID'].unique():
    pdf = merge_data[merge_data['Player_ID'] == pid]
    pdf_home = pdf[pdf['HA'] == 0]
    pdf_away = pdf[pdf['HA'] == 1]

    full_10 = Rolling_Average(pdf, 10, rolling_cols, 'full')
    full_20 = Rolling_Average(pdf, 20, rolling_cols, 'full')
    home_10 = Rolling_Average(pdf_home, 10, rolling_cols, 'home')
    home_20 = Rolling_Average(pdf_home, 20, rolling_cols, 'home')
    away_10 = Rolling_Average(pdf_away, 10, rolling_cols, 'away')
    away_20 = Rolling_Average(pdf_away, 20, rolling_cols, 'away')
    
    ha_cols = list(home_10.columns) + list(home_20.columns) + list(away_10.columns) + list(away_20.columns)
    rolls = pd.concat([full_10,full_20,home_10,home_20,away_10,away_20], axis=1)
    rolls.fillna(method='ffill', inplace=True)

    full_player = pd.concat([pdf,rolls], axis=1)
    try:
        full_data = pd.concat([full_data,full_player], axis=0)
    except:
        full_data = full_player

# #%%
# pts = merge_data[merge_data['PTS_PROP'].notna()].copy()
# reb = merge_data[merge_data['REB_PROP'].notna()].copy()
# ast = merge_data[merge_data['AST_PROP'].notna()].copy()

# #%%
# # 
# pts['PTS_Hit'] = (pts['PTS'] > pts['PTS_PROP']).astype(int)
# reb['REB_Hit'] = (reb['REB'] > reb['REB_PROP']).astype(int)
# ast['AST_Hit'] = (ast['AST'] > ast['AST_PROP']).astype(int)
            
#%%
# Send the Full DataFrame to Excel and CSV files
full_data.to_excel('Excels/full_per_game_data.xlsx')
full_data.to_csv('CSVs/full_per_game_data.csv')

# %%