import csv
import pandas as pd
from config import *
from plotting import *
from import_process import *
from groupings import *
from monte_carlo_simulator import *
from season_simulator import *
from game_simulator import *

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"

teams, ratings = build_ratings(teams_csv, scores_csv)

ratings_df = pd.DataFrame.from_dict(ratings)
ratings_df = ratings_df.set_index('date')       
ratings_df.index = pd.to_datetime(ratings_df.index)

season_dates = get_seasons_daterange(scores_csv)
season_league_teams = get_seasons_tiers_teams(scores_csv)
season_list = season_league_teams.index.get_level_values("Season").unique().tolist()

start_date = min(ratings_df.index)
end_date = max(ratings_df.index)

start_season = min(season_dates.index)
end_season = max(season_dates.index)

tables = build_league_tables(scores_csv)

def simulate_season(season, tier, div, season_league_teams, ratings_df, model_set, Nsims=100):
    
    sel_teams = season_league_teams[ (season, tier, div) ]
    filtered = ratings_df[ratings_df["team"].isin(sel_teams)  & (ratings_df.index <= pre_season_date)]

    sel_preseason_ratings = {}
    new_teams = []
    for team in sel_teams:
        filtered_team = filtered[ filtered["team"] == team ]
        if not filtered_team.empty:
            sel_preseason_ratings[team] = int(filtered[(filtered["team"]==team)].iloc[-1]["rating"])
        else:
            new_teams.append(team)

    if new_teams:
        av_rating = round(sum(sel_preseason_ratings.values())/len(sel_preseason_ratings),0)
        for team in new_teams:
            sel_preseason_ratings[team] = int(av_rating)
            #sel_preseason_ratings[team] = 1500

    state = {
    "teams": sel_teams,
    "ratings": sel_preseason_ratings,
    }

    if season < change_to_goal_diff:
        state["points_per_game"] = 2
        state["goal_separator"] = "average"
    elif change_to_goal_diff <= season < change_to_three_points_per_win:
        state["points_per_game"] = 2
        state["goal_separator"] = "difference"
    else:
        state["points_per_game"] = 3
        state["goal_separator"] = "difference"
        
    simulated_season = run_simulations(state, Nsims, model_set, fixtures=None)
    return simulated_season

model_set = {
    "elo_static": elo_to_poisson,
}

errors = {}
    
for season in season_list[-20:-1]:
    pre_season_date = season_dates.loc[season]["pre"]
    Nsims = 1000
    max_tier = 1
    for tier in range(1,max_tier+1):
    
        sel_teams = season_league_teams.xs( (season, tier), level=[0,1] )
    
        divisions = sel_teams.index.get_level_values("Division")
    
        if not divisions.empty:
            division_names = divisions.to_list()
    
            for div in division_names:
                print(season, tier, div)
                simulated_season = simulate_season(season, tier, div, season_league_teams, ratings_df, model_set, Nsims)
                actual_table = tables.loc[ (season, tier, div) ]
                #print(actual_table)
                model_errors = get_errors(actual_table, simulated_season, Nsims)

                for model_name, model_error_data in model_errors.items():
                    posn_mae, posn_log, points_mae, points_rmse =   model_error_data["posn_mae"], model_error_data["posn_log"], model_error_data["points_mae"], model_error_data["points_rmse"]
                    #print(f"Errors for model: {model_name}")
                    #print(f"Position Mean Absolute Error: {posn_mae:.2f}")
                    #print(f"Position Log Loss Error: {posn_log:.2f}")
                    #print(f"Points Mean Absolute Error: {points_mae:.2f}")
                    #print(f"Points Root Mean Squared Error: {points_rmse:.2f}")

                    # only 1 model
                    errors[season] = model_error_data

df = pd.DataFrame.from_dict(errors, orient="index")
print(df)
