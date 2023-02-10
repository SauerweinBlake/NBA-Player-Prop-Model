#%%
# Import Libraries
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
from datetime import date
from datetime import timedelta 
import re
from selenium.webdriver.common.by import By

def Stat_Switch_Case(stat):
    if stat == 'Pts':
        return 'PTS_PROP'
    elif stat == 'Reb':
        return 'REB_PROP'
    elif stat == 'Ast':
        return 'AST_PROP'
    elif stat == '3pts':
        return '3PTS_PROP'
    elif stat == 'Blk':
        return 'BLK_PROP'
    elif stat == 'Stl':
        return 'STL_PROP'
    elif stat == 'Pts + Ast + Reb':
        return 'PRA_PROP'
    elif stat == 'Pts + Ast':
        return 'PA_PROP'
    elif stat == 'Pts + Reb':
        return 'PR_PROP'
    elif stat == 'Reb + Ast':
        return 'RA_PROP'

#%%
# See if there is pre-existing data for Player Props
try:
    MASTER = pd.read_excel('Excels/Player_Prop_Data.xlsx', index_col=0)
except:
    MASTER = pd.DataFrame()

#%%
# Set the Start Date and date range
try:
    start_date = MASTER['GAME_DATE'].max()+timedelta(days=1)
except:
    start_date = '2022-02-05'

dates = pd.date_range(start=start_date,end=date.today())

#%%
# Set Settings for Selenium Web Driver
options = Options()
DRIVER = webdriver.Chrome(options=options)

#%%
# Begin for loop, looping through each date
for _date_ in dates:
    URL = f"https://www.bettingpros.com/nba/picks/prop-bets/?date={str(_date_).split(' ')[0]}"
    DRIVER.get(URL)
    WebDriverWait(DRIVER, 30).until(EC.presence_of_element_located((By.XPATH,"/html/body/div[2]/main/div/div/div[1]/div[2]/div[1]/div")))
    time.sleep(2)

    # Find the number of pages of props for that specific Date
    pages = int(DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[2]/span').text.split(' ')[-1])

    for ref in range(pages-1):
        found_props = DRIVER.find_elements(By.ID, 'primary-info-container')
        for player_prop_row in found_props:
            player_info = player_prop_row.find_elements(By.XPATH, './child::*')[0].text
            player_prop_info = player_prop_row.find_elements(By.XPATH, './child::*')[1].text

            # Retrieve all necessary data
            matchup = player_info.split('\n')[0]
            player = player_info.split('\n')[1]
            teams = [matchup.split(' ')[0], matchup.split(' ')[-1]]
            player_team = player_info.split('\n')[2].split(' ')[0]
            opp_team = teams[0] if player_team == teams[1] else teams[1]
            val = player_prop_info.split('\n')[0]
            stat = Stat_Switch_Case(player_prop_info.split('\n')[1])

            # Clean/Manipulate Data
            matchup = f'{teams[0]} @ {teams[1]}' if player_team == teams[0] else f'{teams[1]} vs. {teams[0]}'

            # If there is not a row for a player on the date, create one
            if (MASTER[(MASTER['GAME_DATE'] == _date_) & (MASTER['Player_Name'] == player)]).empty:
                MASTER.loc[len(MASTER)] = [_date_, player, matchup, player_team, opp_team, 
                                            np.nan, np.nan, np.nan, np.nan, np.nan,
                                            np.nan, np.nan, np.nan, np.nan, np.nan]
            
            idx = MASTER[(MASTER['GAME_DATE'] == _date_) & (MASTER['Player_Name'] == player)].index.tolist()
            if len(idx) > 1:
                print('NO WORK MORE THAN 1 IDX')
            else:
                MASTER.at[idx[0], stat] = val

        DRIVER.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[2]/button[2]/span/i').click()

#%%
MASTER.to_excel('Excels/Player_Prop_Data.xlsx')
MASTER.to_csv('CSVs/Player_Prop_Data.csv')

#%%