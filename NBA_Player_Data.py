import pandas as pd
import numpy as np
import time
from datetime import date
from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.endpoints import commonplayerinfo
pd.set_option('mode.chained_assignment', None)

def Retrieve_Team_ID(team_abbr):
    try:
        return teams.find_team_by_abbreviation(team_abbr)['id']
    except:
        return np.nan

MASTER = pd.DataFrame()
NBA_PLAYERS = [x for x in players.get_active_players()]
NBA_TEAMS = [x for x in teams.get_teams()]

CNT = 1

for player in NBA_PLAYERS:
    player_id = str(player['id'])
    player_name = str(player['full_name'])
    print(f"{player_name}...LOADING...", end='')
    try:
        time.sleep(1)
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all).get_data_frames()[0]
        playerinfo = commonplayerinfo.CommonPlayerInfo(player_id).get_data_frames()[0]
        position = playerinfo['POSITION'].iloc[0]
        gamelog['TEAM'] = [x.split(' ')[0] for x in gamelog.MATCHUP]
        gamelog['TEAM_ID'] = [Retrieve_Team_ID(x) for x in gamelog['TEAM']]
        gamelog['OPP'] = [x.split(' ')[2] for x in gamelog.MATCHUP]
        gamelog['OPP_ID'] = [Retrieve_Team_ID(x) for x in gamelog['OPP']]
        gamelog['HA'] = [1 if x.split(' ')[1] =='@' else 0 for x in gamelog.MATCHUP]
        gamelog['WL'] = [1 if x == 'W' else 0 for x in gamelog['WL']]
        gamelog['GAME_DATE'] = pd.to_datetime(gamelog.GAME_DATE)
        gamelog['Player_Name'] = player_name
        gamelog['POS'] = position
        gamelog.sort_values('GAME_DATE', ascending=True, inplace=True)
        gamelog.reset_index(inplace=True, drop=True)
                
    except IndexError as e:
        print(f'No Data for {player_name}, error: {e}')
             
    if gamelog.empty:
        print("COMPLETE...",end='')
        
        if CNT%97 == 0:
            print(f"\n\n{round((CNT/len(NBA_PLAYERS))*100,2)}% COMPLETE\n")
        CNT += 1
        continue
    else:
        next_game_df = pd.DataFrame([[None]*len(gamelog.columns)], columns=gamelog.columns)
        next_game_df['SEASON_ID'] = gamelog['SEASON_ID'].iloc[-1]
        next_game_df['GAME_DATE'] = pd.to_datetime(date.today())
        next_game_df['Player_ID'] = player_id
        next_game_df['Player_Name'] = player_name
        next_game_df['TEAM'] = gamelog['TEAM'].iloc[-1]
        next_game_df['POS'] = position
        
        gamelog = pd.concat([gamelog, next_game_df], axis=0, ignore_index=True)
        
        gamelog['Off_Days'] = gamelog["GAME_DATE"].diff().apply(lambda x: x/np.timedelta64(1, 'D')).fillna(0).astype('int64')
        gamelog['Off_Days'] = [0 if x > 100 else x for x in gamelog['Off_Days']]
        
        MASTER = pd.concat([MASTER, gamelog], axis=0, ignore_index=True)
        
        print("COMPLETE...",end='')
        
        if CNT%97 == 0:
            print(f"\n\n{round((CNT/len(NBA_PLAYERS))*100,2)}% COMPLETE\n")
        CNT += 1
        
MASTER['POS_CODE'] = MASTER.POS.astype('category').cat.codes
MASTER.drop(['VIDEO_AVAILABLE', 'FG_PCT', 'FG3_PCT', 'FT_PCT'], axis=1, inplace=True)

MASTER.to_excel('NBA_Player_Data.xlsx')