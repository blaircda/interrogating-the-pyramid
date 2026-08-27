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
df = pd.read_csv(teams_csv, usecols=["Team"])
teams = df["Team"].to_list()

initial_ratings = {team:default_rating for team in teams}
initial_ratings["home_adv"] = initial_home_adv

# build ratings - direct from csv
ratings, season_ratings, home_success, home_winex = build_ratings(initial_ratings, scores_csv)

ratings_df = pd.DataFrame.from_dict(ratings)
ratings_df = ratings_df.set_index('date')       
ratings_df.index = pd.to_datetime(ratings_df.index)

season_ratings_df = pd.DataFrame.from_dict(season_ratings)
season_ratings_df = season_ratings_df.set_index('season_end')       

# read scores_csv into df
scores_df = pd.read_csv(scores_csv)

season_dates = get_seasons_daterange(scores_df)
season_league_teams = get_seasons_tiers_teams(scores_df)
season_list = season_league_teams.index.get_level_values("Season").unique().tolist()

start_date = min(ratings_df.index)
end_date = max(ratings_df.index)

start_season = min(season_dates.index)
end_season = max(season_dates.index)

tables = build_league_tables(scores_df)
home_adv = build_home_adv(scores_df)


model_set = {
        "elo_static": elo_to_poisson,
}
                        
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Interrogating the pyramid")
    col1, col2, col3 = st.columns([0.1,0.8,0.1])

    with col2:
        ratings_tab, home_adv_tab, season_sim_tab, accuracy_tab = st.tabs(["Ratings", "Home advantage", "Season simulations", "Accuracy assessments"])
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
                #
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
            simulate = 0
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
                league_size = len(sel_teams)
                season_by_date_df = get_season_matchcount_by_date(scores_df, sel_season, sel_league, league_size)
                season_date_range = season_by_date_df["Date"]
                start_date, end_date = min(season_date_range), max(season_date_range)
                
                def format_matches_played(date):
                    if date is not None:
                        data = season_by_date_df.loc[season_by_date_df["Date"] == date, ["MatchesOnDate", "MatchesPlayed", "MatchesPlayedPercent"]].iloc[0]                        
                        #played_on_date = data.loc[:,"MatchesOnDate"].iloc[0]
                        played_by_date = int(data["MatchesPlayed"])
                        played_perc = data["MatchesPlayedPercent"]

                        return f"{date:%Y-%m-%d} ({played_by_date:d} matches played, {played_perc:.2f}% of season)"
                    else:
                        return "None"
                    
                with st.form("simulation_control"):
                    end_point = st.selectbox("Date range of results to include",
                        options = [None] + season_date_range.to_list(),
                        #format_func = lambda x: x.strftime('%Y-%m-%d') if not isinstance(x, str) else x,
                        format_func = format_matches_played
                        )
                    Nsims_options = [1,100,1000,10000,100000]
                    Nsims = st.selectbox("Number of simulations", Nsims_options, index=None, key = "simulator")
                    simulate = st.form_submit_button("Simulate")
                
                if simulate:
                    if end_point is not None:
                        initial_ratings = get_ratings_at_date(ratings_df, sel_teams, end_point)
                        matches = get_season_matches_to_date(scores_df, sel_season, sel_league[1], end_point)
                        st.write(f"Table as of {end_point:%Y-%m-%d}")
                        starting_table = get_table_to_date(scores_df, sel_season, sel_league, end_point)
                        display_actual_results(starting_table, sel_season)
                    else:
                        initial_ratings = {team: preseason_ratings[team].iloc[0] for team in sel_teams }
                        matches = {}

                    state = prepare_state(
                        teams = sel_teams, ratings = initial_ratings,
                        home_adv = preseason_ratings["home_adv"].iloc[0], matches = matches,
                        season = sel_season
                    )
                                        
                    simulated_season = run_simulations(state, Nsims, model_set, fixtures=None)
                    display_results(simulated_season, sel_teams, Nsims)
                    
                    actual_table = tables.loc[(sel_season,*sel_league)]

                    if sel_season == season_list[-1]:
                        gp = actual_table["W"].sum(axis=0) + actual_table["D"].sum(axis=0)/2
                        full_gp = len(actual_table)*(len(actual_table)-1)
                        if gp == full_gp:
                            st.write("Actual results:")
                            display_actual_results(actual_table, sel_season)
                            model_errors = get_errors(actual_table, simulated_season, Nsims)
                            display_errors(model_errors)
                    else:
                            st.write("Actual results:")
                            display_actual_results(actual_table, sel_season)
                            model_errors = get_errors(actual_table, simulated_season, Nsims)
                            display_errors(model_errors)
    with accuracy_tab:

        season_tab, start_tab = st.tabs(["Accuracy by season", "Accuracy by start point"])
        
        df = pd.read_csv("data/output/season_errors.csv", index_col=[0,1,2])
        #st.write(df)

        with season_tab:
            seasons_checked = df.index.get_level_values(0).unique()
            seasons_checked = set( (x,y) for x,y in zip(df.index.get_level_values(0), df.index.get_level_values(1)) )
            sel_season_acc = st.selectbox(
                    "Choose season",
                    seasons_checked,
                    index = len(seasons_checked)-1,
                    format_func =lambda x: f"{x[0]} {x[1]}",
                    key="sel_season_acc")
                    
            if sel_season_acc:
                st.write(df.loc[sel_season_acc])
                fig = plot_season_sim_errors(df.loc[sel_season_acc])
                st.pyplot(fig,width='stretch')
                plt.close(fig)
        with start_tab:
            start_points = df.index.get_level_values(2).unique()
            sel_start_acc = st.selectbox(
                    "Choose simulation start (percentage of season)",
                    start_points,
                    index =0,
                    key="sel_start_acc")

            st.write(df.loc[(slice(None), slice(None), sel_start_acc)])
            fig = plot_season_start_errors(df.loc[(slice(None), slice(None), sel_start_acc)])
            st.pyplot(fig,width='stretch')
            plt.close(fig)
