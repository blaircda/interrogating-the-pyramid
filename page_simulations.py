import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from config import *
from import_process import (
    process_data,
    get_ratings_at_date, split_season_by_date,
    get_table_to_date, get_table_with_elo_to_date, get_season_matchcount_by_date
)
from plotting import (
    plot_multi_cols, display_results,
    display_league_table, display_errors,
    plot_season_sim_errors, plot_season_sim_errors_multi, plot_season_start_errors
    )
from helpers import (
    multiselect_teams, filter_by_season_and_teams,
    select_season_range, select_season_division, select_tier_by_season,
    get_sorted_tables, get_teams_by_season_and_div, format_matches_played
)
from simulation.monte_carlo_simulator import (
    prepare_state, run_simulations, get_errors
)

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"

data = process_data(teams_csv, scores_csv)

teams = data.teams
season_list = data.seasons
season_ratings_start, season_ratings_end = data.season_ratings
ratings_df = data.ratings
scores_df = data.scores 
home_adv = data.home_adv
av_discr = data.home_adv_discr
tables = data.tables
season_league_teams = data.leagues
tiers_by_season = data.tiers

start_season = min(season_list)
end_season = max(season_list) 

st.set_page_config(layout="wide", page_title="Tables | Interrogating the pyramid ")

st.header("Simulations")
st.write("Based on Monte Carlo modelling of rating implied win expectancy via Poisson statistics")
sim_launch_tab, backtest_tab = st.tabs(["Run simulation", "Backtests"])

with sim_launch_tab:
    
    # on/off switch for running the simulation
    simulate = 0

    sel_season, sel_league = select_season_division(season_list[1:], tiers_by_season, "sim")
    sel_teams = get_teams_by_season_and_div(sel_season, sel_league, season_league_teams)
    league_size = len(sel_teams)

    # initialise their ratings prior to start of season
    preseason_ratings = season_ratings_start.loc[sel_season]
    
    # get a breakdown of matches by date  
    season_by_date_df = get_season_matchcount_by_date(scores_df, sel_season, sel_league, league_size)
    season_gamedays = season_by_date_df["Date"]

    ################################################################
    # Form: Simulation Launch
    ################################################################
    # to prevent a simulation rerunning when selections are made on other tabs
    # put the decision to launch it into a form
    with st.form("simulation_control"):

        # choose simulation start date
        sim_start_date = st.selectbox(
            "Date range of results to include",
            options = [None] + season_gamedays.to_list(),
            format_func = lambda x: format_matches_played(x, season_by_date_df)
            )

        # choose number of simulations to perform
        Nsims_options = [1,100,1000,10000,100000]
        Nsims = st.selectbox("Number of simulations", Nsims_options, index=3, key = "simulator")
        simulate = st.form_submit_button("Simulate")

    if simulate:

        full_games_played =  league_size*(league_size - 1 )

        # simulating an ongoing season
        if sel_season == live_season:
            # simulating the whole season
            if sim_start_date is None:
                matches_played = None
                # assuming we don't have the true fixture list available set matches_to_play to None
                # then the simulator will iterate over all permutations
                # in principle is not good for dynamic rating updates
                matches_to_play = None
                initial_ratings = preseason_ratings
            else:
                # split the season fixtures by the date
                matches_played, matches_to_play = split_season_by_date(scores_df, sel_season, sel_league[1], sim_start_date)
                # assuming we don't have the true fixture list available set matches_to_play to None
                # then the simulator will iterate over all permutations
                # in principle is not good for dynamic rating updates
                matches_to_play = None
                # get initial ratings at that date 
                initial_ratings = get_ratings_at_date(ratings_df, sel_teams, sim_start_date)
        # simulating a completed season
        elif sel_season != live_season:
            # simulating the whole season
            if sim_start_date is None:
                # get all fixtures in historical order for compatibility with dynamic rating updates in simulation
                matches_played, matches_to_play = split_season_by_date(scores_df, sel_season, sel_league[1], season_gamedays[0]- pd.Timedelta("1 day"))
                initial_ratings = preseason_ratings
            else:
                # split the season fixtures by the date
                matches_played, matches_to_play = split_season_by_date(scores_df, sel_season, sel_league[1], sim_start_date)
                matches_to_play = None
                # get initial ratings at that date 
                initial_ratings = get_ratings_at_date(ratings_df, sel_teams, sim_start_date)

        if sim_start_date:
            # display table as of results_to_date
            starting_table = get_table_with_elo_to_date(ratings_df, scores_df, sel_season, sel_league, sim_start_date, preseason_ratings.loc[sel_teams])
            st.write(f"Table as of {sim_start_date:%Y-%m-%d}")
            display_league_table(starting_table, sel_season)
            
        # prepare the state dictionary passed to the simulation
        state = prepare_state(
            teams = sel_teams,
            ratings = initial_ratings,
            home_adv = preseason_ratings.loc["home_adv"],
            season = sel_season
        )

        if sel_season != live_season:
            # get the actual final table
            actual_table = tables.loc[(sel_season,*sel_league)]
            st.write("Actual results:")
            display_league_table(actual_table, sel_season)

        # run the simulations
        # can extend this to loop over multiple models if present
        models_used = ["elo_static", "elo_dynamic"]
        for model in models_used:
            st.subheader(f"Model: {model}")
            simulated_season = run_simulations(
                                    state, Nsims,
                                    model_name = model,
                                    games_played = matches_played,
                                    games_to_play = matches_to_play
                                )            
            # display the results
            st.write("Simulation results:")
            display_results(simulated_season, sel_teams, Nsims)
            #games_played = actual_table["W"].sum(axis=0) + actual_table["D"].sum(axis=0)/2
            if sel_season != live_season:
                model_errors = get_errors(actual_table, simulated_season, Nsims)
                display_errors(model_errors)

########################################################################
# Tab: Season Simulations
########################################################################
with backtest_tab:

    st.write("Based on previously run simulations of various seasons starting at different points")
    #st.write("Currently a non-zero start point actually means include all actual results up to and including the first match date for which the percentage of matches played exceeds the number given")

    path = "data/output/sim_errors/"
    files = [x for x in os.listdir(path) if x.endswith(".csv")]
    choose_backtest_file = st.selectbox(
        "Choose error file",
        files,
        index=0,
        key="choose_error"
    )        
    df = pd.read_csv(path+choose_backtest_file, index_col=[0,1,2])
    #st.write(df)
    season_tab, start_tab = st.tabs(["Select season", "Select start point"])

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
