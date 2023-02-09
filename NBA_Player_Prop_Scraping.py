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
    pages = DRIVER.find_element(By.XPATH, '//*[@id="props-app"]/div/div[2]/span').text.split(' ')[-1]
    
#%%
    full_day_props = pd.DataFrame(columns=['date','player_name','stat','val'])
    temp_df = pd.DataFrame(columns=['date','player_name','stat','val'])
    if pages != 0:
        for pag_num in range(1,pages+1,1):
            found_props = DRIVER.find_elements(By.ID, 'primary-info-container')
            for player_prop_row in found_props:
                player_prop_row.findElements(By.XPATH, './child::*')
#%%


            time.sleep(2)
            page_html = DRIVER.page_source
            page_soup = BeautifulSoup(page_html, 'html.parser')
            a = page_soup.find_all("a")
            players = [x.text.replace('\n','').strip() for x in a if '/nba/odds/player-props/' in x['href']]
            players = [x for x in players if x != 'Player Props']
            
            mydivs = page_soup.find_all("div", "class" == "flex card__prop-container")
            children = []
            
            pts = []
            reb = []
            ast = []
            tpm = []
            stl = []
            blk = []
            pra = []
            pa = []
            pr = []
            ra = []
            
            props = [pts, reb, ast, tpm, stl, blk, pra, pa, pr, ra]
            
            val = []
            stat = []
            for x in mydivs:
                children.append(x.findChildren("span"))
                
            for t in children:
                pts.append(re.findall(">Pts</span>", str(t)))
                reb.append(re.findall(">Reb</span>", str(t)))
                ast.append(re.findall(">Ast</span>", str(t)))
                tpm.append(re.findall(">3pts</span>", str(t)))
                stl.append(re.findall(">Stl</span>", str(t)))
                blk.append(re.findall(">Blk</span>", str(t)))
                pra.append(re.findall(">Pts...Ast...Reb</span>", str(t)))
                pa.append(re.findall(">Pts...Ast</span>", str(t)))
                pr.append(re.findall(">Pts...Reb</span>", str(t)))
                ra.append(re.findall(">Reb...Ast</span", str(t)))
                val.append(re.findall(".[0-9].[0-9]</span>", str(t)))
                
            for i in range(len(pts)):
                for j in range(len(props)):
                    if props[j][i] != []:
                        stat.append(props[j][i])
            
            val = [w for w in val if len(w) == 3]
            
            temp = []
            for i in val:
                temp.append(i[0].split('<')[0].split('>')[-1])
            val = temp
            
            stat = [w[0].split('<')[0].split('>')[-1] for w in stat if len(w) == 1]
            num_plays = len(val)
            stat = stat[len(stat)-(num_plays*4):]
            
            temp = []
            for i in range(0,len(stat),4):
                temp.append(stat[i])
            stat = temp
            
            temp_df = pd.DataFrame(columns=['DATE','PLAYER_NAME','STAT','VAL'])
            temp_df['PLAYER_NAME'] = players
            temp_df['STAT'] = stat
            temp_df['VAL'] = val
            temp_df['DATE'] = pd.to_datetime(str(_date_).split(' ')[0])
            
            if pag_num != pages:
                DRIVER.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                next_page = DRIVER.find_element(By.XPATH,"/html/body/div[2]/main/div/div/div[2]/button[2]")
                next_page.click()
                
            full_day_props = pd.concat([full_day_props, temp_df], axis=0, ignore_index=True)
                
        uniq_players = full_day_props['PLAYER_NAME'].unique()
        for player in uniq_players:
            try:
                pts_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Pts')]['VAL'].iloc[0]
            except:
                pts_prop = np.nan
                
            try:
                ast_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Ast')]['VAL'].iloc[0]
            except:
                ast_prop = np.nan
                
            try:
                reb_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Reb')]['VAL'].iloc[0]
            except:
                reb_prop = np.nan
                
            try:
                tpts_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == '3pts')]['VAL'].iloc[0]
            except:
                tpts_prop = np.nan
                
            try:
                blk_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Blk')]['VAL'].iloc[0]
            except:
                blk_prop = np.nan
                
            try:
                stl_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Stl')]['VAL'].iloc[0]
            except:
                stl_prop = np.nan
                
            try:
                pra_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Pts + Reb + Ast')]['VAL'].iloc[0]
            except:
                pra_prop = np.nan
                
            try:
                pa_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Pts + Ast')]['VAL'].iloc[0]
            except:
                pa_prop = np.nan
                
            try:
                pr_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Pts + Reb')]['VAL'].iloc[0]
            except:
                pr_prop = np.nan
                
            try:
                ra_prop = full_day_props[(full_day_props['PLAYER_NAME'] == player) & (full_day_props['STAT'] == 'Reb + Ast')]['VAL'].iloc[0]
            except:
                ra_prop = np.nan
            
            data = {'GAME_DATE': [_date_], 'Player_Name': [player], 'PTS_PROP': [pts_prop], 'AST_PROP': [ast_prop],
                    'REB_PROP': [reb_prop], '3PTS_PROP': [tpts_prop], 'BLK_PROP': [blk_prop], 'STL_PROP': [stl_prop],
                    'PRA_PROP': [pra_prop], 'PR_PROP': [pr_prop], 'PA_PROP': [pa_prop], 'RA_PROP': [ra_prop]}
            
            prop_df = pd.DataFrame(data)
            
            MASTER = pd.concat([MASTER, prop_df], axis=0, ignore_index=True)

MASTER.to_excel('Player_Prop_Data.xlsx')

# %%
