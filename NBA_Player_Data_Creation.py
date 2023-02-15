#%%
# Import Libraries
import pandas as pd
import numpy as np
from nba_api.stats.static.players import find_players_by_full_name, find_players_by_first_name, find_players_by_last_name

#%%
# Creates a rolling average for defined columns
def Rolling_Average(df, n_rolls, roll_cols, sort_cols, col_title):
    rolling = df[roll_cols].sort_values(sort_cols)
    rolling.drop(sort_cols, axis=1, inplace=True)
    rolling = rolling.rolling(n_rolls).mean(skipna=True).shift(1)
    rolling_cols = [f'{col_title}_{col}_{n_rolls}' for col in rolling.columns]
    rolling.columns = rolling_cols
    
    return rolling

def Team_Abbr_Adj(team_abbr):
    inc_team_abbr = {'PHO':'PHX', 'UTH':'UTA', 'NOR':'NOP'}
    try:
        return inc_team_abbr[team_abbr]
    except:
        return team_abbr

def Player_Id_Relater(player_name):
    list_of_players_full = find_players_by_full_name(player_name)
    if len(list_of_players_full) > 1:
        list_of_players_full = [x for x in list_of_players_full if x['is_active']]
        if (len(list_of_players_full)) == 1:
            return list_of_players_full[0]['id']
        else:
            list_of_players_first = find_players_by_full_name(player_name.split(' ')[0])
            list_of_players_last = find_players_by_last_name(player_name.split(' ')[1])

            list_of_players_first = [x for x in list_of_players_first if x['is_active']]
            list_of_players_last = [x for x in list_of_players_last if x['is_active']]

            list_of_players_full = [x for x in list_of_players_full for y in list_of_players_first for z in list_of_players_last if x['id'] == y['id'] or x['id'] == z['id']]

            if (len(list_of_players_full)) == 1:
                return list_of_players_full[0]['id']
            else:
                return np.nan
    elif len(list_of_players_full) == 1:
        return list_of_players_full[0]['id']
    else:
        return np.nan

#%%
# NOT USED YET
def Hit_Calculation(stat_val, prop_val):
    if np.isnan(prop_val):
        return np.nan
    elif stat_val > prop_val:
        return 1
    elif stat_val < prop_val:
        return 0

#%%
# Import Player Data and Prop Data
NBA_PLAYER_DATA = pd.read_csv('CSVs/NBA_Player_Data.csv', index_col=0)
NBA_PLAYER_PROP = pd.read_csv('CSVs/Player_Prop_Data.csv', index_col=0)
FULL_RESULTS = pd.DataFrame()

#%%
# Clean the Data
NBA_PLAYER_PROP['MATCHUP'] = [' '.join([Team_Abbr_Adj(x.split(' ')[0]),
                                        x.split(' ')[1],
                                        Team_Abbr_Adj(x.split(' ')[2])])
                                        for x in NBA_PLAYER_PROP['MATCHUP']]
#%%
# Merge the data
merge_data = NBA_PLAYER_DATA.merge(NBA_PLAYER_PROP, on=['Player_Name','GAME_DATE', 'MATCHUP'], how='left')

#%%
# Clean the Data
# Can be re-factored or removed later, but for Random Forest Regressor predictions
# the NaN columns must be dropped
merge_data.drop(['BLK_PROP','STL_PROP','3PTS_PROP','PRA_PROP','PR_PROP','PA_PROP','RA_PROP'],
                inplace=True, axis=1)
# ID Relater is slow, needs to be improved
merge_data['Player_ID'] = [Player_Id_Relater(y) if str(x) == 'nan' else x for x,y in zip(merge_data['Player_ID'], merge_data['Player_Name'])]
merge_data['GAME_DATE'] = pd.to_datetime(merge_data['GAME_DATE'])
merge_data['TEAM'] = [x.split(' ')[0] for x in merge_data['MATCHUP']]
merge_data['OPP'] = [x.split(' ')[2] for x in merge_data['MATCHUP']]
merge_data['HA'] = [0 if x.split(' ')[1] == '@' else 1 for x in merge_data['MATCHUP']]
merge_data['WL'] = [1 if x == 'W' else 0 for x in merge_data['WL']]
merge_data['POS_CODE'] = merge_data['POS'].astype('category').cat.codes
merge_data['TEAM_CODE'] = merge_data['TEAM'].astype('category').cat.codes
merge_data['OPP_CODE'] = merge_data['OPP'].astype('category').cat.codes
# OFF DAYS DONE TWICE, HERE and PLAYER_DATA
merge_data['Off_Days'] = merge_data["GAME_DATE"].diff().apply(lambda x: x/np.timedelta64(1, 'D')).fillna(0).astype('int64')
merge_data['Off_Days'] = [0 if x > 100 else x for x in merge_data['Off_Days']]

merge_data = merge_data[merge_data['PTS_PROP'].notna()]
merge_data = merge_data[merge_data['REB_PROP'].notna()]
merge_data = merge_data[merge_data['AST_PROP'].notna()]
merge_data.reset_index(inplace=True, drop=True)

#%%
# 
merge_data['PTS_Hit'] = (merge_data['PTS'] > merge_data['PTS_PROP']).astype(int)
merge_data['REB_Hit'] = (merge_data['REB'] > merge_data['REB_PROP']).astype(int)
merge_data['AST_Hit'] = (merge_data['AST'] > merge_data['AST_PROP']).astype(int)

#%%
for player in merge_data['Player_ID'].unique():
# player = merge_data['Player_ID'].unique()[11]
# player_name = merge_data['Player_Name'].unique()[11]
    # If there is a DataFrame of stats, perform calculations
    if (merge_data[merge_data['Player_ID'] == player].empty) != True:
        full_player_gamelog = merge_data[merge_data['Player_ID'] == player]
        home_player_gamelog = merge_data[(merge_data['Player_ID'] == player) & (merge_data['HA'] == 0)]
        away_player_gamelog = merge_data[(merge_data['Player_ID'] == player) & (merge_data['HA'] == 1)]
        
        cols_to_not_roll = ['SEASON_ID','Player_ID','Game_ID','MATCHUP', 
                            'TEAM','TEAM_CODE','OPP','OPP_CODE','HA','POS',
                            'POS_CODE', 'PTS_PROP','REB_PROP','AST_PROP']
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
        
        full_rolling_10 = Rolling_Average(full_player_gamelog, 10, cols_to_roll, ['Player_Name', 'GAME_DATE'], 'full')
        cols_to_not_roll += list(full_rolling_10.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]

        full_rolling_20 = Rolling_Average(full_player_gamelog, 20, cols_to_roll, ['Player_Name', 'GAME_DATE'], 'full')
        cols_to_not_roll += list(full_rolling_20.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]

        home_rolling_10 = Rolling_Average(home_player_gamelog, 10, cols_to_roll, ['Player_Name', 'GAME_DATE'], 'home')
        cols_to_not_roll += list(home_rolling_10.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]

        home_rolling_20 = Rolling_Average(home_player_gamelog, 20, cols_to_roll, ['Player_Name', 'GAME_DATE'], 'home')
        cols_to_not_roll += list(home_rolling_20.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]

        away_rolling_10 = Rolling_Average(away_player_gamelog, 10, cols_to_roll, ['Player_Name', 'GAME_DATE'], 'away')
        cols_to_not_roll += list(away_rolling_10.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]

        away_rolling_20 = Rolling_Average(away_player_gamelog, 20, cols_to_roll, ['Player_Name', 'GAME_DATE'], 'away')
        cols_to_not_roll += list(away_rolling_20.columns)
        cols_to_roll = full_player_gamelog.columns[~full_player_gamelog.columns.isin(cols_to_not_roll)]
            
        full_player_gamelog = pd.concat([full_player_gamelog, full_rolling_10, full_rolling_20, home_rolling_10, home_rolling_20, away_rolling_10, away_rolling_20], axis=1)

        if FULL_RESULTS.empty:
            FULL_RESULTS = full_player_gamelog
        else:
            FULL_RESULTS = pd.concat([FULL_RESULTS, full_player_gamelog], axis=0)
            
#%%
# Send the Full DataFrame to Excel and CSV files
FULL_RESULTS.to_excel('Excels/THE BIG ONE.xlsx')
FULL_RESULTS.to_csv('CSVs/THE_BIG_ONE.csv')

# %%