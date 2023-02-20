#%%
# Import Libraries
import pandas as pd
import numpy as np
import time
from datetime import date
from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.endpoints import commonplayerinfo

#%%
# Create DataFrame and get list of active players and teams
MASTER = pd.DataFrame()
NBA_PLAYERS = [x for x in players.get_active_players()]
NBA_TEAMS = [x for x in teams.get_teams()]

#%%
# Loop through each Active player and retrieve their entire career of gamelogs
for player in NBA_PLAYERS:
    player_id = str(player['id'])
    player_name = str(player['full_name'])
    print(f"{player_name}...LOADING...", end='')
    try:
        time.sleep(1)
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all).get_data_frames()[0]
        playerinfo = commonplayerinfo.CommonPlayerInfo(player_id).get_data_frames()[0]
        position = playerinfo['POSITION'].iloc[0]
        gamelog['Player_Name'] = player_name
        gamelog['POS'] = position
        gamelog['GAME_DATE'] = pd.to_datetime(gamelog['GAME_DATE'])
        gamelog.sort_values('GAME_DATE', ascending=True, inplace=True)
        gamelog.reset_index(inplace=True, drop=True)
                
    except IndexError as e:
        print(f'No Data for {player_name}, error: {e}')
             
    # If the gamelog is empty, report that the data retrieval is complete
    if gamelog.empty:
        print("COMPLETE...",end='')
        continue
    # If the gamelog is not empty, create a dataframe for the next game
    else:
        MASTER = pd.concat([MASTER, gamelog], axis=0, ignore_index=True)
        
        print("COMPLETE...",end='')
        
MASTER.drop(['VIDEO_AVAILABLE', 'FG_PCT', 'FG3_PCT', 'FT_PCT'], axis=1, inplace=True)

#%%
# Create the DataFrame as an Excel and CSV file
MASTER.to_excel('Excels/NBA_Player_Data.xlsx')
MASTER.to_csv('CSVs/NBA_Player_Data.csv')
#%%