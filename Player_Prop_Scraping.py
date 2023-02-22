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
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException
from nba_api.stats.static.players import find_players_by_full_name
from nba_api.stats.static import teams

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

def Team_Abbr_Adj(team_abbr):
    incorrect_team_abbr = {'PHO':'PHX', 'UTH':'UTA', 'NOR':'NOP'}
    try:
        return incorrect_team_abbr[team_abbr]
    except:
        return team_abbr

#%%
# See if there is pre-existing data for Player Props
try:
    master = pd.read_csv('CSVs/Player_Prop_Data.csv', index_col=0)
except:
    master = pd.DataFrame(columns=['GAME_DATE','Player_Name', 'MATCHUP',
                                    'PTS_PROP','REB_PROP','AST_PROP','BLK_PROP','STL_PROP',
                                    '3PTS_PROP','PRA_PROP','PR_PROP','PA_PROP','RA_PROP',
                                    'Player_ID','SEASON_ID'])

#%%
# Set the Start Date and date range
if master.empty:
    start_date = '2022-02-05'
else:
    master['GAME_DATE'] = pd.to_datetime(master['GAME_DATE'])
    start_date = master['GAME_DATE'].max()+timedelta(days=1)

dates = pd.date_range(start=start_date,end=date.today())

NBA_TEAMS_ABBRS = [x['abbreviation'] for x in teams.get_teams()]

#%%
# Set Settings for Selenium Web Driver
options = Options()
DRIVER = webdriver.Chrome(options=options)

#%%
# Begin for loop, looping through each date
for _date_ in dates:
    URL = f"https://www.bettingpros.com/nba/picks/prop-bets/?date={str(_date_).split(' ')[0]}"
    DRIVER.get(URL)
    try:
        WebDriverWait(DRIVER, 15).until(EC.presence_of_element_located((By.XPATH,'//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button/span')))
    except NoSuchWindowException:
        DRIVER.refresh()
        WebDriverWait(DRIVER, 15).until(EC.presence_of_element_located((By.XPATH,'//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button/span')))

    try:
        if DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button/span').text != 'ALL':
            DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button').click()
            DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/ul/li[1]').click()
            WebDriverWait(DRIVER, 15).until(EC.presence_of_element_located((By.XPATH,'//*[@id="props-app"]/div/div[1]/div[2]/div[7]/div/div/div/button/span')))

        # Find the number of pages of props for that specific Date
        pages = int(DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[2]/span').text.split(' ')[-1])
        for ref in range(pages):
            found_props = DRIVER.find_elements(By.ID, 'primary-info-container')
            for player_prop_row in found_props:
                player_info = player_prop_row.find_elements(By.XPATH, './child::*')[0].text
                player_prop_info = player_prop_row.find_elements(By.XPATH, './child::*')[1].text

                # Retrieve all necessary data
                matchup = player_info.split('\n')[0]
                player = player_info.split('\n')[1]
                team_a = matchup.split(' ')[0] if matchup.split(' ')[0] in NBA_TEAMS_ABBRS else Team_Abbr_Adj(matchup.split(' ')[0])
                team_b = matchup.split(' ')[-1] if matchup.split(' ')[-1] in NBA_TEAMS_ABBRS else Team_Abbr_Adj(matchup.split(' ')[-1])
                teams = [team_a, team_b]
                player_team = player_info.split('\n')[2].split(' ')[0]
                val = player_prop_info.split('\n')[0]
                stat = Stat_Switch_Case(player_prop_info.split('\n')[1])

                # Clean/Manipulate Data
                matchup = f'{teams[0]} @ {teams[1]}' if player_team == teams[0] else f'{teams[1]} vs. {teams[0]}'

                # If there is not a row for a player on the date, create one
                if (master[(master['GAME_DATE'] == _date_) & (master['Player_Name'] == player)]).empty:
                    master.loc[len(master)] = [_date_, player, matchup,
                                                np.nan, np.nan, np.nan, np.nan, np.nan,
                                                np.nan, np.nan, np.nan, np.nan, np.nan,
                                                np.nan, np.nan]
                    
                idx = master[(master['GAME_DATE'] == _date_) & (master['Player_Name'] == player)].index.tolist()
                master.at[idx[0], stat] = val

            DRIVER.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[2]/button[2]/span/i').click()
            except ElementClickInterceptedException:
                pass
    except NoSuchElementException:
            pass

DRIVER.quit()

#%%
# Create Player and Season ID
# Improve Player ID Search to more completely search for Players
master['Player_ID'] = [np.nan if not(find_players_by_full_name(x)) else find_players_by_full_name(x)[0]['id'] for x in master['Player_Name']]

months = master['GAME_DATE'].dt.month.tolist()
years = master['GAME_DATE'].dt.year.tolist()
master['SEASON_ID'] = ['2'+str(y-1) if x < 8 else '2'+str(y) for x,y in zip(months,years)]

#%%
# Create Excel and CSV Files from DataFrame
master.to_excel('Excels/Player_Prop_Data.xlsx')
master.to_csv('CSVs/Player_Prop_Data.csv')
#%%