from season_simulator import *
from time import perf_counter

# helper functions for creating defaultdicts to store simulation results
def make_posn_stats():
    #return {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS":0}
    return {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "PTS":0}
def make_team_stats(league_size):
    return {i: 0 for i in range(1, league_size+1)} | make_posn_stats()

# main simulation function
def run_simulations(state, Nsims, model_set, fixtures=None):

    store_team_results, store_posn_results = {}, {}
    Nmodels =len(model_set)
    model_count = 1

    league_size = len(state["teams"])
    
    # loop over models
    for model_name, model_fn in model_set.items():
        start = perf_counter()
        print(f"Simulating league with game model: {model_name} ({model_count}/{Nmodels})")
        # dicts to store simulation results
        team_results = defaultdict(lambda : make_team_stats(league_size))

        # run Nsims simulations with the given model
        for N in range(Nsims):
            if model_name == "elo_live":
                orig_elo = state["ratings"].copy()

            # run a season
            results = run_season(state, model_fn, fixtures=fixtures)
            # add season results to team_results, posn_results
            update_results(results, team_results)

            if model_name == "elo_live":    
                state["ratings"] = orig_elo.copy()

        # save results for model
        store_team_results[model_name] = team_results
        
        elapsed = perf_counter() - start
        print(f"Simulation finished in {elapsed:.6f} s")
        model_count += 1 

    return store_team_results
    


