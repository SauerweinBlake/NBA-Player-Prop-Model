#%%
# Import Libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
from datetime import date
from datetime import timedelta 
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from nba_api.stats.static.players import find_players_by_full_name, find_players_by_first_name, find_players_by_last_name

#%%
# Define Functions
# Calculate Odds of the opposite bet, given the original odds, 4.5% vig
# NOT USED AS OF NOW, MAY BE MOVED TO ANOTHER .py
def Odds_Vig_Calc(odds):
    if odds < 0:
        vig_odds = int((100*((191 * abs(odds)) - 900)) / ((9 * abs(odds)) + 20900))
        if vig_odds < 100:
            return (-100) - (100 - vig_odds)
        else:
            return vig_odds
    else:
        return int((100 * ((209 * abs(odds)) + 900)) / ((9 * abs(odds)) - 19100))

# Case Switch
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
    MASTER = pd.read_csv('CSVs/Player_Prop_Data.csv', index_col=0)
except:
    MASTER = pd.DataFrame(columns=['GAME_DATE','Player_Name', 'MATCHUP',
                                    'PTS_PROP','REB_PROP','AST_PROP','BLK_PROP','STL_PROP',
                                    '3PTS_PROP','PRA_PROP','PR_PROP','PA_PROP','RA_PROP',
                                    'Player_ID','SEASON_ID'])

#%%
# Set the Start Date and date range
if MASTER.empty:
    start_date = '2022-02-05'
else:
    MASTER['GAME_DATE'] = pd.to_datetime(MASTER['GAME_DATE'])
    start_date = MASTER['GAME_DATE'].max()+timedelta(days=1)

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
    WebDriverWait(DRIVER, 30).until(EC.presence_of_element_located((By.XPATH,'//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button/span')))
    
    try:
        if DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button/span').text != 'ALL':
            DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button').click()
            DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/ul/li[1]').click()
            WebDriverWait(DRIVER, 30).until(EC.presence_of_element_located((By.XPATH,'//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button/span')))

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
                val = player_prop_info.split('\n')[0]
                stat = Stat_Switch_Case(player_prop_info.split('\n')[1])

                # Clean/Manipulate Data
                matchup = f'{teams[0]} @ {teams[1]}' if player_team == teams[0] else f'{teams[1]} vs. {teams[0]}'

                # If there is not a row for a player on the date, create one
                if (MASTER[(MASTER['GAME_DATE'] == _date_) & (MASTER['Player_Name'] == player)]).empty:
                    MASTER.loc[len(MASTER)] = [_date_, player, matchup,
                                                np.nan, np.nan, np.nan, np.nan, np.nan,
                                                np.nan, np.nan, np.nan, np.nan, np.nan,
                                                np.nan, np.nan]
                    
                idx = MASTER[(MASTER['GAME_DATE'] == _date_) & (MASTER['Player_Name'] == player)].index.tolist()
                MASTER.at[idx[0], stat] = val

            DRIVER.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[2]/button[2]/span/i').click()
    except NoSuchElementException:
            pass

DRIVER.quit()

#%%
# Create Player and Season ID
# Improve Player ID Search to more completely search for Players
MASTER['Player_ID'] = [np.nan if not(find_players_by_full_name(x)) else find_players_by_full_name(x)[0]['id'] for x in MASTER['Player_Name']]

months = MASTER['GAME_DATE'].dt.month.tolist()
years = MASTER['GAME_DATE'].dt.year.tolist()
MASTER['SEASON_ID'] = ['2'+str(y-1) if x < 8 else '2'+str(y) for x,y in zip(months,years)]

#%%
# Create Excel and CSV Files from DataFrame
MASTER.to_excel('Excels/Player_Prop_Data.xlsx')
MASTER.to_csv('CSVs/Player_Prop_Data.csv')

#%%