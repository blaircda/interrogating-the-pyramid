import argparse
import pandas as pd
import numpy as np
from config import *
from import_process import (
    process_data, build_partial_ratings,
    get_ratings_at_date, split_season_by_date, split_season_by_percent,
)
from simulation.vectorise_mc_sim import (
    run_season_monte_carlo
)
from plotting import get_errors

def simulate_season_percent(season, tier, div, season_league_teams, scores_df, season_ratings_start, model_name, Nsims=100, reality_percent = 0):
    """
    simulate a season taking into account the actual results of the first reality_percent percent matches
    """
    sel_teams = season_league_teams[ (season, tier, div) ]
    preseason_ratings = season_ratings_start.loc[ season ]
    initial_ratings = {team: preseason_ratings.loc[team] for team in sel_teams }
    home_adv = preseason_ratings.loc["home_adv"]
    league_size = len(sel_teams)

    matches_played, matches_to_play = split_season_by_percent(scores_df, season, div, reality_percent)

    if season == LIVE_SEASON:
        fixtures = f"data/current_fixtures/Tier{tier}.csv"
        df = pd.read_csv(fixtures, usecols=["home", "away"])
        fixtures_list = [ (row[0], row[1]) for row in df.itertuples(index=False) ]
        if not matches_played:
            matches_to_play = fixtures_list
        else:
            last_match = list(matches_played.keys())[-1]
            matches_to_play = fixtures_list[ fixtures_list.index(last_match)+1:]
    
    simulated_season = run_season_monte_carlo(
        season = season,
        ratings = initial_ratings,
        home_adv = home_adv,
        Nsims = Nsims, 
        model = model_name,
        games_played = matches_played,
        games_to_play = matches_to_play
    )
    return simulated_season


def simulation_loop( models_used, seasons_to_sim, max_tier, Nsims, percent, data, descr):

    teams = data.teams
    season_ratings_start, season_ratings_end = data.season_ratings
    ratings_df = data.ratings
    scores_df = data.scores 
    tables = data.tables
    season_league_teams = data.leagues
    
    for model in models_used:
        errors = {}
        for season in seasons_to_sim:
            for tier in range(1,max_tier+1):
                sel_teams = season_league_teams.xs( (season, tier), level=[0,1] )

                divisions = sel_teams.index.get_level_values("Division")

                if not divisions.empty:
                    division_names = divisions.to_list()

                    for div in division_names:
                        print(season, tier, div)
                        actual_table = tables.loc[ (season, tier, div) ]

                        for x in range(0,100,percent):
                            print(f"Simulation starting at {x}% of season")
                            simulated_season = simulate_season_percent(
                                season, tier, div,
                                season_league_teams, scores_df, season_ratings_start,
                                model, Nsims, reality_percent = x)
                            model_errors = get_errors(actual_table, simulated_season, Nsims)
                            errors[(season, div, x)] = model_errors

        savefile = "data/output/sim_errors/"+model+"_"+descr+"_errors.csv"
        df = pd.DataFrame.from_dict(errors, orient="index")
        df.to_csv(savefile, index=True, index_label=("Season", "Division", "SimulationStart"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--tiers", type=int, choices=range(1, 5), default=1)
    parser.add_argument("-s", "--seasons", type=int, choices=range(1, 21), default=1)
    parser.add_argument("-N", "--Nsims", type=int, default=10000)
    parser.add_argument("-p", "--percent", type=int, choices=[1,2,5,10,20,25,50], default=10)
    parser.add_argument("--random", action="store_true")

    args = parser.parse_args()

    teams_csv = "data/EnglishTeamActivePeriods.csv"
    scores_csv = "data/EnglandLeagueResults.csv"
    data = process_data(teams_csv, scores_csv)
    season_list = data.seasons

    models_used = ["elo_static", "elo_dynamic"]

    max_seasons = args.seasons
    max_tier = args.tiers
    Nsims = args.Nsims
    percent = args.percent
    
    if args.random:
        print(f"\nSimulating {max_seasons} random seasons of top {max_tier} tiers\n{Nsims} simulations each\nStarting simulation at each {percent} percent of season\nSimulation models:{models_used}\n")
        seasons_to_sim =  np.random.choice(season_list[1:-1], size=max_seasons, replace=False)
        descr = f"random_{max_seasons}_seasons_{max_tier}_tiers_{Nsims}_sims"
        simulation_loop(models_used, seasons_to_sim, max_tier, Nsims, percent, data, descr)
    else:
        print(f"\nSimulating {max_seasons} most recent seasons of top {max_tier} tiers\n{Nsims} simulations each\nStarting simulation at each {percent} percent of season\nSimulation models:{models_used}\n")
        seasons_to_sim = season_list[-(max_seasons+1):-1]
        descr = f"recent_{max_seasons}_seasons_{max_tier}_tiers_{Nsims}_sims"
        simulation_loop(models_used, seasons_to_sim, max_tier, Nsims, percent, data, descr)
