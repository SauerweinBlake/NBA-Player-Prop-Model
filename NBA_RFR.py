#%%
# Import Libraries
import pandas as pd
from datetime import date
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score

#%%
# Import Data
Master = pd.read_csv('CSVs/THE_BIG_ONE.csv', index_col=0)

#%%
# Clean Data
Master['GAME_DATE'] = pd.to_datetime(Master['GAME_DATE'])

#%%
# Train Test Split
train = Master[Master['GAME_DATE'] < pd.to_datetime('2023-02-01')]
train.dropna(inplace=True)
test = Master[Master['GAME_DATE'] >= pd.to_datetime('2023-02-01')]
test.dropna(inplace=True)
# date.today()
to_be_predicted = Master[Master['GAME_DATE'] == pd.to_datetime('2023-02-14')]
to_be_predicted['SEASON_ID'] = Master['SEASON_ID'].max()
to_be_predicted = to_be_predicted[to_be_predicted['full_PTS_20'].notna()]

#%%
# Possibly keep Game_ID, but would need to get Game ID for any predictions for the day's games
temp = Master.copy()
temp.drop(['TEAM','OPP','GAME_DATE','WL','MIN','FGM','FGA','FG3M',
           'FG3A','FTM','FTA','OREB','DREB','REB','AST','STL',
           'BLK','TOV','PF','PTS','PLUS_MINUS','Player_Name','Game_ID',
           'MATCHUP','POS'], axis=1, inplace=True)
feature_cols = list(temp.columns)

print("Training Points Random Forest Regressor")
rfr_pts = RandomForestRegressor()
rfr_pts.fit(train[feature_cols], train['PTS'])
y_pred_pts = rfr_pts.predict(test[feature_cols])
test['pred_PTS'] = y_pred_pts.tolist()
r2 = rfr_pts.score(test[feature_cols], test['PTS'])
print(f"R-Squared: {r2}")

test['pred_PTS_PRED'] = (test['pred_PTS'] >= test['PTS_PROP']).astype(int)
acc = accuracy_score(test['PTS_Hit'], test['pred_PTS_PRED'])
print(acc)

to_be_predicted['pred_PTS'] = rfr_pts.predict(to_be_predicted[feature_cols]).tolist()
to_be_predicted['pred_PTS_PRED'] = (to_be_predicted['pred_PTS'] >= to_be_predicted['PTS_PROP']).astype(int)

print("Training Points Random Forest Regressor")
rfr_pts_prop = RandomForestRegressor()
rfr_pts_prop.fit(train[feature_cols], train['PTS_PROP'])
y_pred_pts_prop = rfr_pts_prop.predict(test[feature_cols])
test['pred_PTS_PROP'] = y_pred_pts_prop.tolist()
test['pred_PTS_PROP'] = (test['pred_PTS_PROP'] >= 0.5).astype(int)
r2 = rfr_pts_prop.score(test[feature_cols], test['PTS_PROP'])
acc = accuracy_score(test['PTS_Hit'], test['pred_PTS_PROP'])
print(acc)
print(f"R-Squared: {r2}")
#%%