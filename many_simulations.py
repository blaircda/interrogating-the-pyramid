from main import *

def simulate_season(season, tier, div, season_league_teams, season_ratings_df, model_set, Nsims=100):
    
    sel_teams = season_league_teams[ (season, tier, div) ]
    preseason_ratings = season_ratings_df[ season_ratings_df["season_start"] == season ]
    sel_preseason_ratings = {team: preseason_ratings[team].iloc[0] for team in sel_teams }

    state = {
    "teams": sel_teams,
    "ratings": sel_preseason_ratings,
    "home_adv": preseason_ratings["home_adv"].iloc[0]
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
    #pre_season_date = season_dates.loc[season]["pre"]
    Nsims = 1000
    max_tier = 1
    for tier in range(1,max_tier+1):
    
        sel_teams = season_league_teams.xs( (season, tier), level=[0,1] )
    
        divisions = sel_teams.index.get_level_values("Division")
    
        if not divisions.empty:
            division_names = divisions.to_list()
    
            for div in division_names:
                print(season, tier, div)
                simulated_season = simulate_season(season, tier, div, season_league_teams, season_ratings_df, model_set, Nsims)
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
