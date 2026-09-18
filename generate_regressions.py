import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

from regression.season_regressor import (
    drop_incomplete_seasons,
    regress_seasons,
    regress_seasons_tier,
    regress_seasons_team
)
from import_process import process_data

output_dir = "data/output/regr/"
output_fig_dir = "data/output/regr/"

# start by building the tables
teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"
data = process_data(teams_csv, scores_csv)
tables = data.tables
tables = drop_incomplete_seasons(tables, ["1939/1940"])

# all season/all tiers regression for WHpg
base_cols = [ "WHpg", "GFHpg", "GAHpg", "Rdiff_to_mean_start"]
target = ["WHpg"]
lag_cols = ["WHpg", "GFHpg", "GAHpg", "Rdiff_to_mean_start"]
ave_cols = ["WHpg", "GFHpg", "GAHpg"]
leaky_cols = [ "WHpg", "GFHpg", "GAHpg" ]
future_split = "2026/2027"

preds, corrs = regress_seasons( tables, target, base_cols, lag_cols, ave_cols, leaky_cols, future_split)

for target, data in preds.items():
    data["fig"].savefig( output_fig_dir+f"All_Seasons_All_Tiers_{target}.png", bbox_inches = "tight")
    del data["fig"]
    data["pred"] = data["pred"][0]
    with open(output_dir+f"All_Seasons_All_Tiers_{target}.json", "w") as f:
        json.dump(data,f)

# all season/tierwise regression for WHpg
for n in range(1,5):
    preds, corrs = regress_seasons_tier(n, tables, target, base_cols, lag_cols, ave_cols, leaky_cols, future_split)

    for target, data in preds.items():
        data["fig"].savefig( output_fig_dir+f"All_Seasons_Tier_{n}_{target}.png", bbox_inches = "tight")
        del data["fig"]
        data["pred"] = data["pred"][0]
        with open(output_dir+f"All_Seasons_Tier_{n}_{target}.json", "w") as f:
            json.dump(data, f)

# current PL season
selSeason = "2026/2027"
selT1 = tables.xs(
    (selSeason, 1),
    level=["Season", "Tier"]
    ).index.get_level_values("Team").unique()
    
team_preds = {}
team_corrs = {}
base_cols = ["Wpg", "Dpg", "GFpg","GApg", "Rstart", "Rend", "Rbelow_start", "Rdiff_to_mean_start"]
targets = ["Wpg", "Dpg", "GFpg", "GApg", "Rend"]
lag_cols =  ["Wpg", "Dpg", "GFpg","GApg", "Rstart", "Rbelow_start", "Rdiff_to_mean_start"]
ave_cols = lag_cols
leaky_cols =  ["Wpg", "Dpg", "GFpg", "GApg", "Rend"]
future_split = "2026/2027"

for team in selT1:
    preds, corrs = regress_seasons_team( team, tables, targets, base_cols, lag_cols, ave_cols, leaky_cols, selSeason)
    for target, data in preds.items():
        data["fig"].savefig( output_fig_dir+f"PL_{team}_{target}.png", bbox_inches = "tight")
        del data["fig"]
    team_preds[team] = preds
    team_corrs[team]  = corrs

pred_table = {}
for team, data in team_preds.items():
    pred_table[team] = {}
    for stat in targets:
        pred_table[team][stat] = data[stat]["pred"][0]
        
df = pd.DataFrame.from_dict(pred_table, orient="index")
df[["W","D", "GF", "GA"]] = 38*df[["Wpg", "Dpg", "GFpg", "GApg"]]
df["PTS_wd"] = 38*3*df["Wpg"] + 38*df["Dpg"]
df.sort_values(by="Rend", ascending=False)
df.to_csv(output_dir+"PL.csv", index=True, index_label=("Team") )
