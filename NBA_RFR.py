import pandas as pd
from datetime import date
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
pd.set_option('mode.chained_assignment', None)

def Rolling_Average(df, n_rolls, roll_cols, sort_cols):
    roll_cols = roll_cols.tolist()
    rolling = df[roll_cols].sort_values(sort_cols)
    roll_cols = [col for col in roll_cols if col not in sort_cols]
    rolling = df[roll_cols].rolling(n_rolls).mean().shift(1)
    rolling_cols = [f'{col}_{n_rolls}' for col in rolling.columns]
    rolling.columns = rolling_cols
    
    return rolling

print("Loading (Massive) Excel File")
Master = pd.read_excel('NBA_Player_Data.xlsx', index_col=0)

print("Performing Train Test Split")
train = Master[Master['GAME_DATE'] < pd.to_datetime('2022-11-01')]
train.dropna(inplace=True)
test = Master[Master['GAME_DATE'] >= pd.to_datetime('2022-11-01')]
test.dropna(inplace=True)
to_be_predicted = Master[Master['GAME_DATE'] == pd.to_datetime(date.today())]

# Possibly keep Game_ID, but would need to get Game ID for any predictions for the day's games
temp = Master.copy()
temp.drop(['TEAM', 'OPP', 'GAME_DATE','WL', 'MIN', 'FGM', 'FGA', 'FG3M',
           'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'STL',
           'BLK', 'TOV', 'PF', 'PTS', 'PLUS_MINUS', 'Player_Name', 'Game_ID',
           'MATCHUP', 'POS'], axis=1, inplace=True)
feature_cols = list(temp.columns)

acc_agn_arr = [1] * len(test.index)

print("Training Points Random Forest Regressor")
rfr_pts = RandomForestRegressor()
rfr_pts.fit(train[feature_cols], train['PTS'])
y_pred_pts = rfr_pts.predict(test[feature_cols])
test['pred_PTS'] = y_pred_pts.tolist()
# test['pts_cor'] = 0
# for row in range(len(test.index)):
#     if test['PTS'].iloc[row]-3 <= test['pred_PTS'].iloc[row] <= test['PTS'].iloc[row]+3:
#         test['pts_cor'].iloc[row] = 1
# print(f"Accuracy: {accuracy_score(acc_agn_arr,test['pts_cor'])}")
r2 = rfr_pts.score(test[feature_cols], test['PTS'])
print(f"R-Squared: {r2}")

print("Training Rebounds Random Forest Regressor")
rfr_reb = RandomForestRegressor()
rfr_reb.fit(train[feature_cols], train['REB'])
y_pred_reb = rfr_reb.predict(test[feature_cols])
test['pred_REB'] = y_pred_reb.tolist()
# test['reb_cor'] = 0
# for row in range(len(test.index)):
#     if test['REB'].iloc[row]-1 <= test['pred_REB'].iloc[row] <= test['REB'].iloc[row]+1:
#         test['reb_cor'].iloc[row] = 1
# x = [1] * len(test.index)
# print(f"Accuracy: {accuracy_score(x,test['reb_cor'])}")
r2 = rfr_reb.score(test[feature_cols], test['REB'])
print(f"R-Squared: {r2}")

print("Training Assists Random Forest Regressor")
rfr_ast = RandomForestRegressor()
rfr_ast.fit(train[feature_cols], train['AST'])
y_pred_ast = rfr_ast.predict(test[feature_cols])
test['pred_AST'] = y_pred_ast.tolist()
# test['ast_cor'] = 0
# for row in range(len(test.index)):
#     if test['AST'].iloc[row]-1 <= test['pred_AST'].iloc[row] <= test['AST'].iloc[row]+1:
#         test['ast_cor'].iloc[row] = 1
# x = [1] * len(test.index)
# print(f"Accuracy: {accuracy_score(x,test['ast_cor'])}")
r2 = rfr_ast.score(test[feature_cols], test['AST'])
print(f"R-Squared: {r2}")

### Player Predictions Current ###
data = {'player_name': [],
        'predicted_pts':[],
        'predicted_reb':[],
        'predicted_ast':[]}
stat_preds = pd.DataFrame(data)
print("Loading Daily Lineups")
dl = pd.read_excel('Daily_Lineups.xlsx')
for row in range(len(dl.index)):
    try:
        player_name = dl['player_name'].iloc[row]
        opp_init = dl['opp_short'].iloc[row]
        ha = dl['ha'].iloc[row]
        
        prediction = pd.DataFrame([[None]*len(stat_preds.columns)], columns=stat_preds.columns)
        
        player_pred = to_be_predicted[to_be_predicted['Player_Name'] == player_name]
        player_pred['HA'] = ha
        player_pred['OPP'] = opp_init
        player_pred['OPP_CODE'] = Master[Master['OPP'] == opp_init]['OPP_CODE'].iloc[0]
        
        prediction['player_name'] = player_name
        prediction['predicted_pts'] = rfr_pts.predict(player_pred[feature_cols])
        prediction['predicted_reb'] = rfr_reb.predict(player_pred[feature_cols])
        prediction['predicted_ast'] = rfr_ast.predict(player_pred[feature_cols])
        
        stat_preds = pd.concat([stat_preds, prediction], axis=0, ignore_index=True)
    except:
        print(f"Unable to predict {player_name}, there is no data\n")
        
stat_preds.dropna(inplace=True)
stat_preds.to_excel('Daily_Predictions.xlsx')