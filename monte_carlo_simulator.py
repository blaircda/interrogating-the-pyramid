from season_simulator import *
from time import perf_counter
import pandas as pd

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
    
def get_errors(actual_table, simulation_results, Nsims):

    model_errors = {}
    
    for model_name, model_data in simulation_results.items():
        df = pd.DataFrame.from_dict(model_data, orient="index")
        cols = ["PTS", "W", "D", "L", "GF", "GA"]
        df[cols] /= Nsims
        pos_cols = df.columns[df.columns.map(lambda x: isinstance(x, int))]
        df[pos_cols] = df[pos_cols]/Nsims
        df["xPOS"] = sum( pos * df[pos] for pos in pos_cols )
        new_col_names = { c: "x"+c for c in cols }
        df = df.rename(columns=new_col_names)
        df["POS"] = actual_table["POS"]
        df["PTS"] = actual_table["PTS"]

        #st.write(df[["POS", "xPOS", "PTS", "xPTS"]])

        # posn errors
        posn_mae = (df["POS"] - df["xPOS"]).abs().mean()
        df["log_err"] = -np.log( df.apply(lambda row: row[row["POS"]], axis=1) )
        posn_log = df["log_err"].mean()
        # points errors
        points_mae = (df["PTS"] - df["xPTS"]).abs().mean()
        points_rmse = np.sqrt( ( (df["PTS"] - df["xPTS"]) ** 2).mean() )

        model_errors[model_name] = { "posn_mae": posn_mae, "posn_log":posn_log, "points_mae":points_mae, "points_rmse":points_rmse }

    return model_errors


