from main import *
#import matplotlib
#matplotlib.use("TkAgg")
#import matplotlib.pyplot as plt

def simulate_season(season, tier, div, season_league_teams, scores_df, season_ratings_df, model_set, Nsims=100, reality_percent = 0):
    """
    simulate a season taking into account results up to and including the earliest date s.t. reality_percent percent of matches have been played
    """
    sel_teams = season_league_teams[ (season, tier, div) ]
    preseason_ratings = season_ratings_df[ season_ratings_df["season_start"] == season ]
    league_size = len(sel_teams)
    season_by_date_df = get_season_matchcount_by_date(scores_df, season, (tier, div), league_size)

    if reality_percent > 0:
        row = season_by_date_df.loc[season_by_date_df["MatchesPlayedPercent"] >= reality_percent].iloc[0]
        #print(f"Reality percent: {reality_percent}")
        end_point = row["Date"]
        initial_ratings = get_ratings_at_date(ratings_df, sel_teams, end_point)
        matches_played, matches_to_play = split_season_by_date(scores_df, season, div, results_to_date)
    else:
        initial_ratings = {team: preseason_ratings[team].iloc[0] for team in sel_teams }
        matches_played = None
        matches_to_play = None
        
    # prepare the state dictionary passed to the simulation
    state = prepare_state(
        teams = sel_teams,
        ratings = initial_ratings,
        home_adv = preseason_ratings["home_adv"].iloc[0],
        season = sel_seasonys
    )

    simulated_season = run_simulations(state, Nsims, model_set, games_played = matches_played, games_to_play = matches_to_play)
    return simulated_season

def simulate_season_percent(season, tier, div, season_league_teams, scores_df, season_ratings_df, model_set, Nsims=100, reality_percent = 0):
    """
    simulate a season taking into account the actual results of the first reality_percent percent matches
    """
    sel_teams = season_league_teams[ (season, tier, div) ]
    preseason_ratings = season_ratings_df[ season_ratings_df["season_start"] == season ]
    initial_ratings = {team: preseason_ratings[team].iloc[0] for team in sel_teams }
    home_adv = preseason_ratings["home_adv"].iloc[0]
    
    league_size = len(sel_teams)

    if reality_percent > 0:
        #print(f"Reality percent: {reality_percent}")
        matches_played, matches_to_play = split_season_by_percent(scores_df, season, div, reality_percent)
        initial_ratings = build_partial_ratings(initial_ratings | {"home_adv": home_adv}, matches_played)
    else:
        matches_played = None
        matches_to_play = None
        
    # prepare the state dictionary passed to the simulation
    state = prepare_state(
        teams = sel_teams,
        ratings = initial_ratings,
        home_adv = home_adv,
        season = season
    )

    simulated_season = run_simulations(state, Nsims, model_set, games_played = matches_played, games_to_play = matches_to_play)
    return simulated_season


model_set = {
    "elo_static": elo_to_poisson,
}

errors = {}

max_seasons = 4
max_tier = 4
for season in season_list[-(max_tier+1):-1]:
    for tier in range(1,max_tier+1):
    
        sel_teams = season_league_teams.xs( (season, tier), level=[0,1] )
    
        divisions = sel_teams.index.get_level_values("Division")
    
        if not divisions.empty:
            division_names = divisions.to_list()
    
            for div in division_names:
                print(season, tier, div)
                actual_table = tables.loc[ (season, tier, div) ]
                #print(actual_table)
                for x in range(0,100,10):
                    print(f"Simulation starting at {x}% of season")
                    simulated_season = simulate_season_percent(season, tier, div, season_league_teams, scores_df, season_ratings_df, model_set, many_sims_N_sims, reality_percent = x)
                    model_errors = get_errors(actual_table, simulated_season, many_sims_N_sims)
                    for model_name, model_error_data in model_errors.items():
                        #posn_mae, posn_log, points_mae, points_rmse =   model_error_data["posn_mae"], model_error_data["posn_log"], model_error_data["points_mae"], model_error_data["points_rmse"]
                        # only 1 model
                        errors[(season, div, x)] = model_error_data

df = pd.DataFrame.from_dict(errors, orient="index")
#print(df.to_string())

df.to_csv("data/output/season_errors.csv", index=True, index_label=("Season", "Division", "SimulationStart"))
