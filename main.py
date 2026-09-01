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

########################################################################
# Data imports
########################################################################

# import all teams and set their default rating
teams = pd.read_csv(teams_csv, usecols=["Team"])["Team"].to_list()
initial_ratings = {team:default_rating for team in teams}
initial_ratings["home_adv"] = initial_home_adv

# build full ratings - direct from csv
ratings, season_ratings, home_success, home_winex = build_ratings(initial_ratings, scores_csv)

ratings_df = pd.DataFrame.from_dict(ratings).set_index('date') 
ratings_df.index = pd.to_datetime(ratings_df.index)

start_date, end_date = min(ratings_df.index), max(ratings_df.index)

season_ratings_df = pd.DataFrame.from_dict(season_ratings).set_index('season_end')       

# compute averages of home success (from actual results) and model home win expectancy
# and their discrepancy 
accum_home_success = np.cumsum(home_success)
av_accum_home_success = [ x/(i+1) for i,x in enumerate(accum_home_success)]
accum_home_winex = np.cumsum(home_winex )
av_accum_home_winex  = [ x/(i+1) for i,x in enumerate(accum_home_winex )]
av_discr = [x-y for x,y in zip(av_accum_home_success,av_accum_home_winex)]

# read scores_csv into df
scores_df = pd.read_csv(scores_csv)

season_dates = get_seasons_daterange(scores_df)
season_league_teams = get_seasons_tiers_teams(scores_df)
season_list = season_dates.index.tolist()
start_season = min(season_list)
end_season = max(season_list)

# tables
tables = build_league_tables(scores_df)

# home advantage
home_adv = build_home_adv(scores_df)

# simulation model(s)
model_set = {
        "elo_static": elo_to_poisson,
}
                        
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Interrogating the pyramid")
    # control width of content display 
    padl, content, padr = st.columns([0.1,0.8,0.1])

    ########################################################################
    # Content
    ########################################################################
    with content:
        # define tabs 
        ratings_tab, home_adv_tab, season_sim_tab, accuracy_tab = st.tabs(["Ratings", "Home advantage", "Season simulations", "Accuracy assessments"])

    ########################################################################
    # Tab: Ratings
    ########################################################################
    with ratings_tab:

        # season range slider
        s1, s2 = st.select_slider(
            "Season range",
            options = season_list,
            value = (start_season, end_season),
            key = "ratings_season_slider"
            )

        # team multiselection
        sel = st.multiselect(
            f"Team ({len(teams)} options)",
            teams,
            default = teams[0],
            max_selections = 50,
            key="ratings_team_sel"
            )

        # graph ratings of all selected team over season range from slider
        if sel:           
            filtered = ratings_df[ratings_df["team"].isin(sel)]
            filtered = filtered[ ( s1 <= filtered["season"]) & (filtered["season"] <= s2)]
            fig = plot_multi_ratings(filtered, sel)
            st.pyplot(fig,width='stretch')
            plt.close(fig)

    ########################################################################
    # Tab: Home Advantage
    ########################################################################
    with home_adv_tab:

        # subtabs
        record_tab, model_tab = st.tabs(["Historic home advantage", "Model home advantage"])

        ########################################################################
        # subtab: Historical Home Advantage
        ########################################################################
        with record_tab:

            st.write("This shows average home wins as a proportion of all results, and average home success for which a win counts as 1 and a draw as 0.5")
            # season range slider
            s1, s2 = st.select_slider(
                "Season range",
                options = season_list,
                value = (start_season, end_season),
                key = "homeadv_season_slider"
                )

            filtered = home_adv[ ( s1 <= home_adv.index) & (home_adv.index <= s2)]
            fig = plot_multi_cols(
                    filtered,
                    ["AvHomeSuccess", "AvHomeWins"],
                    {"AvHomeSuccess": "Av. Home Success", "AvHomeWins": "Av. Home Wins"}
                    )
            st.pyplot(fig,width='stretch')
            plt.close(fig)

        ########################################################################
        # subtab: Model Home Advantage
        ########################################################################
        with model_tab:
            st.write(f"Starting from initial home advantage {initial_home_adv} rating points")
            st.write(f"Updating model home advantage at start of every season based on previous {N_matches_home_adv} matches")

            # plot model home advantage over time
            fig = plot_multi_cols(
                    season_ratings_df,
                    ["home_adv"],
                    {"home_adv": "Model home advantage"}
                    )
            st.pyplot(fig,width='stretch')
            plt.close(fig)

            # plot comparison between model home win ex and actual home success
            fig, ax = plt.subplots()
            #ax.plot(av_accum_home_success, label="home_success")
            #ax.plot(av_accum_home_winex, label="home win ex")
            ax.plot( av_discr, label="Home Success - Home Win Ex") 
            ax.legend()
            st.pyplot(fig,width='stretch')
            plt.close(fig)

    ########################################################################
    # Tab: Season Simulations
    ########################################################################
    with season_sim_tab:
        # on/off switch for running the simulation
        simulate = 0

        # choose a season
        # initial season excluded
        sel_season = st.selectbox(
            "Choose season",
            season_list[1:],
            index = len(season_list)-2,
            key="sim_sel_season"
            )

        # get the leagues and teams for selected season
        selected = season_league_teams.loc[sel_season]
        tier_divisions = selected.index.tolist()
        # this is a list of tuples (int tier, str division_name)
        # e.g. [ (1, "Premier League"), (2, "EFL Championship"), ... ] 

        # choose a league
        sel_league = st.selectbox(
            "Choose league",
            tier_divisions,
            index = 0,
            format_func = lambda x:x[1],
            key="sim_sel_league"
            )

        # select the teams from the league
        sel_teams = season_league_teams.loc[ (sel_season,*sel_league) ]
        league_size = len(sel_teams)

        # initialise their ratings prior to start of season
        preseason_ratings = season_ratings_df[ season_ratings_df["season_start"] == sel_season ]
        # get a breakdown of matches by date  
        season_by_date_df = get_season_matchcount_by_date(scores_df, sel_season, sel_league, league_size)
        season_gamedays = season_by_date_df["Date"]
        start_date, end_date = min(season_gamedays), max(season_gamedays)

        # helper function to format date selection 
        def format_matches_played(date):
            if date is not None:
                data = season_by_date_df.loc[season_by_date_df["Date"] == date, ["MatchesOnDate", "MatchesPlayed", "MatchesPlayedPercent"]].iloc[0]                        
                #played_on_date = data.loc[:,"MatchesOnDate"].iloc[0]
                played_by_date = int(data["MatchesPlayed"])
                played_perc = data["MatchesPlayedPercent"]
                return f"{date:%Y-%m-%d} ({played_by_date:d} matches played, {played_perc:.2f}% of season)"

            else:
                return "None"

        ################################################################
        # Form: Simulation Launch
        ################################################################
        # to prevent a simulation rerunning when selections are made on other tabs
        # put the decision to launch it into a form
        with st.form("simulation_control"):

            # choose simulation start date
            results_to_date = st.selectbox(
                "Date range of results to include",
                options = [None] + season_gamedays.to_list(),
                format_func = format_matches_played
                )

            # choose number of simulations to perform
            Nsims_options = [1,100,1000,10000,100000]
            Nsims = st.selectbox("Number of simulations", Nsims_options, index=None, key = "simulator")
            simulate = st.form_submit_button("Simulate")

        if simulate:

            # if simulating including results up to the date chosen in results_to_date
            if results_to_date is not None:
                # get initial ratings at that date 
                initial_ratings = get_ratings_at_date(ratings_df, sel_teams, results_to_date)
                # get all matches up to that date
                # TO DO: change this to a split_season(..., by = date)
                # which returns the matches up to date as results and the matches after date as fixtures for the simulation to run
                matches = get_season_matches_to_date(scores_df, sel_season, sel_league[1], results_to_date)
                # display table as of results_to_date
                st.write(f"Table as of {results_to_date:%Y-%m-%d}")
                starting_table = get_table_to_date(scores_df, sel_season, sel_league, results_to_date)
                display_actual_results(starting_table, sel_season)
            # if simulating whole season
            else:
                initial_ratings = {team: preseason_ratings[team].iloc[0] for team in sel_teams }
                matches = {}

            # prepare the state dictionary passed to the simulation
            state = prepare_state(
                teams = sel_teams,
                ratings = initial_ratings,
                home_adv = preseason_ratings["home_adv"].iloc[0],
                 matches = matches,
                season = sel_season
            )

            # run the simulations 
            simulated_season = run_simulations(state, Nsims, model_set, fixtures=None)
            # display the resuts
            display_results(simulated_season, sel_teams, Nsims)
            # get the actual final table
            actual_table = tables.loc[(sel_season,*sel_league)]

            # the most recent season may be incomplete
            # brute force checking this 
            if sel_season == season_list[-1]:
                games_played = actual_table["W"].sum(axis=0) + actual_table["D"].sum(axis=0)/2
                full_games_played = len(actual_table)*(len(actual_table)-1)
                if games_played == full_games_played:
                    st.write("Actual results:")
                    display_actual_results(actual_table, sel_season)
                    model_errors = get_errors(actual_table, simulated_season, Nsims)
                    display_errors(model_errors)
            # otherwise nothing to check
            else:
                    st.write("Actual results:")
                    display_actual_results(actual_table, sel_season)
                    model_errors = get_errors(actual_table, simulated_season, Nsims)
                    display_errors(model_errors)

    ########################################################################
    # Tab: Season Simulations
    ########################################################################
    with accuracy_tab:

        st.write("Based on previously run simulations (10,000 simulations each) of various seasons starting at different points")
        st.write("Currently a non-zero start point actually means include all actual results up to and including the first match date for which the percentage of matches played exceeds the number given")

        season_tab, start_tab = st.tabs(["Select season", "Select start point"])
        
        df = pd.read_csv("data/output/season_errors.csv", index_col=[0,1,2])
        #st.write(df)

        ########################################################################
        # subtab: Season information by start point
        ########################################################################
        with season_tab:
            seasons_checked = list(set( (season,div) for season,div in zip(df.index.get_level_values(0), df.index.get_level_values(1)) ))
            seasons_checked.sort()
            selection = st.multiselect(
                    "Choose season",
                    seasons_checked,
                    format_func =lambda x: f"{x[0]} {x[1]}",
                    key="sel_season_acc")
            if selection:
                fig = plot_season_sim_errors_multi(df, selection)
                #for sel in selection:
                #    st.write(df.loc[sel])
                #    fig = plot_season_sim_errors(df.loc[sel])
                st.pyplot(fig,width='stretch')
                plt.close(fig)

        ########################################################################
        # subtab: Start point information by season
        ########################################################################
        with start_tab:
            start_points = df.index.get_level_values(2).unique()
            sel_start_acc = st.selectbox(
                    "Choose simulation start (percentage of season)",
                    start_points,
                    index =0,
                    key="sel_start_acc")

            #st.write(df.loc[(slice(None), slice(None), sel_start_acc)])
            fig = plot_season_start_errors(df.loc[(slice(None), slice(None), sel_start_acc)])
            st.pyplot(fig,width='stretch')
            plt.close(fig)
