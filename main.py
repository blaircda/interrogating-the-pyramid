import csv
import pandas as pd
import numpy as np
import streamlit as st
from config import *
from plotting import *
from import_process import *
from groupings import *
from monte_carlo_simulator import *
from season_simulator import *
from game_simulator import *

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"

# import all teams separately
teams = []

with open(teams_csv, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        teams.append(row["Team"])    

initial_ratings = {team:default_rating for team in teams}
initial_ratings["home_adv"] = initial_home_adv

ratings, season_ratings, home_success, home_winex = build_ratings(initial_ratings, scores_csv)

ratings_df = pd.DataFrame.from_dict(ratings)
ratings_df = ratings_df.set_index('date')       
ratings_df.index = pd.to_datetime(ratings_df.index)

season_ratings_df = pd.DataFrame.from_dict(season_ratings)
season_ratings_df = season_ratings_df.set_index('season_end')       

season_dates = get_seasons_daterange(scores_csv)
season_league_teams = get_seasons_tiers_teams(scores_csv)
season_list = season_league_teams.index.get_level_values("Season").unique().tolist()

start_date = min(ratings_df.index)
end_date = max(ratings_df.index)

start_season = min(season_dates.index)
end_season = max(season_dates.index)

tables = build_league_tables(scores_csv)

home_adv = build_home_adv(scores_csv)


model_set = {
        "elo_static": elo_to_poisson,
}
                        
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Interrogating the pyramid")
    col1, col2, col3 = st.columns([0.1,0.8,0.1])

    with col2:
        ratings_tab, home_adv_tab, season_sim_tab, live_season_sim_tab = st.tabs(["Historic ratings", "Home advantage", "Season simulations", "Current season simulation"])
        with ratings_tab:

            s1, s2 = st.select_slider("Season range",
                options = season_dates.index, value = (start_season, end_season)  )

            sel = st.multiselect(
            f"Team ({len(teams)} options)",
            teams,
            default = teams[0],
            max_selections = 50,
            key="team_sel")

            if sel:           
                filtered = ratings_df[ratings_df["team"].isin(sel)]
                filtered = filtered[ ( s1 <= filtered["season"]) & (filtered["season"] <= s2)]
                fig = plot_multi(filtered, sel)
                st.pyplot(fig,width='stretch')
                plt.close(fig)

        with home_adv_tab:

            record_tab, model_tab = st.tabs(["Historic home advantage", "Model home advantage"])

            with record_tab:
                s1, s2 = st.select_slider("Season range",
                options = season_dates.index, value = (start_season, end_season), key = "season_slider_ha"  )

                filtered = home_adv[ ( s1 <= home_adv.index) & (home_adv.index <= s2)]
                fig = plot_multi_cols(filtered, ["AvHomeSuccess", "AvHomeWins"])
                st.pyplot(fig,width='stretch')
                plt.close(fig)

            with model_tab:
                st.write(f"Starting from initial home advantage {initial_home_adv} rating points")
                st.write(f"Updating model home advantage at start of every season based on previous {N_matches_home_adv} matches")
                fig = plot_multi_cols(season_ratings_df, ["home_adv"], {"home_adv": "Model home advantage"})
                st.pyplot(fig,width='stretch')
                plt.close(fig)
                
                fig, ax = plt.subplots()

                accum_home_success = np.cumsum(home_success)
                av_accum_home_success = [ x/(i+1) for i,x in enumerate(accum_home_success)]
                accum_home_winex = np.cumsum(home_winex )
                av_accum_home_winex  = [ x/(i+1) for i,x in enumerate(accum_home_winex )]

                av_discr = [x-y for x,y in zip(av_accum_home_success,av_accum_home_winex)]
                
                #ax.plot(av_accum_home_success, label="home_success")
                #ax.plot(av_accum_home_winex, label="home win ex")
                ax.plot( av_discr, label="Home Success - Home Win Ex") 
                ax.legend()

                st.pyplot(fig,width='stretch')
                plt.close(fig)

        with season_sim_tab:

            with st.form("simulation_control"):
                sel_season = st.selectbox(
                "Choose season",
                season_list[1:],
                index = len(season_list)-2,
                key="sel_season")

                selected = season_league_teams.loc[sel_season]
                tier_divisions = selected.index.tolist()

                sel_league = st.selectbox(
                "Choose league",
                tier_divisions,
                index = None,
                format_func = lambda x:x[1],
                key="league_sel")

                if sel_league:
                    sel_teams = season_league_teams.loc[ (sel_season,*sel_league) ]
                    preseason_ratings = season_ratings_df[ season_ratings_df["season_start"] == sel_season ]
                    sel_preseason_ratings = {team: preseason_ratings[team].iloc[0] for team in sel_teams }

                    state = {
                    "teams": sel_teams,
                    "ratings": sel_preseason_ratings,
                    "home_adv": preseason_ratings["home_adv"].iloc[0]
                    }

                    if sel_season < change_to_goal_diff:
                        state["points_per_game"] = 2
                        state["goal_separator"] = "average"
                    elif change_to_goal_diff <= sel_season < change_to_three_points_per_win:
                        state["points_per_game"] = 2
                        state["goal_separator"] = "difference"
                    else:
                        state["points_per_game"] = 3
                        state["goal_separator"] = "difference"

                Nsims_options = [1,100,1000,10000,100000]
                Nsims = st.selectbox("Number of simulations", Nsims_options, index=None, key = "simulater")

                simulate = st.form_submit_button("Simulate")

            if simulate and not sel_league:
                st.write("Please choose a league")
                
            if simulate and sel_league:
                actual_table = tables.loc[(sel_season,*sel_league)]
                simulated_season = run_simulations(state, Nsims, model_set, fixtures=None)
                display_results(simulated_season, sel_teams, Nsims)
                display_actual_results(actual_table, sel_season)

                model_errors = get_errors(actual_table, simulated_season, Nsims)

                for model_name, model_error_data in model_errors.items():
                    st.write(f"Errors for model: {model_name}")
                    posn_mae, posn_log, points_mae, points_rmse =   model_error_data["posn_mae"], model_error_data["posn_log"], model_error_data["points_mae"], model_error_data["points_rmse"]
                    st.write(f"Position Mean Absolute Error: {posn_mae:.2f}")
                    st.write(f"Position Log Loss Error: {posn_log:.2f}")
                    st.write(f"Points Mean Absolute Error: {points_mae:.2f}")
                    st.write(f"Points Root Mean Squared Error: {points_rmse:.2f}")

        with live_season_sim_tab:
            sel_season = season_list[-1]
            selected = season_league_teams.loc[sel_season]
            
            tier_divisions = selected.index.tolist()

            sel_league = st.selectbox(
            "Choose league",
            tier_divisions,
            index = None,
            format_func = lambda x:x[1],
            key="live_league_sel")
  
            with st.form("live sim control"):
              if sel_league:
                    season_date_range = ratings_df[ (ratings_df["season"] == sel_season) & (ratings_df["division"] == sel_league[1]) ]
                    start_date, end_date = min(season_date_range.index), max(season_date_range.index)
                    end_point = st.select_slider("Date range",format_func = lambda x: x.strftime('%Y-%m-%d'),
                        options = season_date_range.index, value = end_date  )
                    sel_teams = season_league_teams.loc[ (sel_season,*sel_league) ]
                    preseason_ratings = season_ratings_df[ season_ratings_df["season_start"] == sel_season ]

                    if end_point:
                        initial_ratings = get_ratings_at_date(ratings_df, sel_teams, end_point)
                        matches = get_season_matches_to_date(scores_csv, sel_season, sel_league[1], end_point)
                        state = {
                            "teams": sel_teams,
                            "ratings": initial_ratings,
                            "home_adv": preseason_ratings["home_adv"].iloc[0],
                            "points_per_game": 3,
                            "goal_separator": "difference",
                            "matches": matches
                        }
                        
                    Nsims_options = [1,100,1000,10000,100000]
                    Nsims = st.selectbox("Number of simulations", Nsims_options, index=None, key = "live_simulater")

                    simulate = st.form_submit_button("Simulate")

            if simulate and not sel_league:
                st.write("Please choose a league")
                
            if simulate and sel_league:
                simulated_season = run_simulations(state, Nsims, model_set, fixtures=None)
                display_results(simulated_season, sel_teams, Nsims)
