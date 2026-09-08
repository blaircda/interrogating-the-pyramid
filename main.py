import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from config import *
from import_process import (
    process_data,
    get_ratings_at_date, split_season_by_date,
    get_table_to_date, get_table_with_elo_to_date, get_season_matchcount_by_date
)
from plotting import (
    plot_multi_ratings, plot_multi_cols,
    display_results, display_actual_results, display_errors,
    plot_season_sim_errors, plot_season_sim_errors_multi, plot_season_start_errors
    )
from simulation.monte_carlo_simulator import (
    prepare_state, run_simulations, get_errors
)

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"


########################################################################
# Streamlit App
########################################################################
                        
if __name__ == "__main__":
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

    start_season = min(season_list)
    end_season = max(season_list) 
    
    st.set_page_config(layout="wide", page_title="Interrogating the pyramid")
    # control width of content display 
    padl, content, padr = st.columns([0.1,0.8,0.1])

    ########################################################################
    # Content
    ########################################################################
    with content:
        # define tabs 
        ratings_tab, tables_tab, home_adv_tab, season_sim_tab, backtest_tab = st.tabs(["Historical ratings", "Historical tables", "Historical vs model home advantage", "Season simulations", "Backtests"])

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
            data = season_ratings_end.xs("home_adv", level=1)
            fig, ax = plt.subplots()
            ax.plot(data, label="Model home advantage")
            ax.set_xticks(data.index[::10])
            ax.tick_params(axis='x', labelrotation=90)
            ax.grid(True, alpha=0.3)
            ax.legend()        
            st.pyplot(fig,width='stretch')
            plt.close(fig)

            # plot comparison between model home win ex and actual home success
            fig, ax = plt.subplots()
            #ax.plot(av_accum_home_success, label="home_success")
            #ax.plot(av_accum_home_winex, label="home win ex")
            X = 50
            ax.plot( av_discr[X:], label="Actual Home Success - Home Win Ex")
            ax.set_xlabel(f"Number of games (first {X} excluded)")
            ax.grid(True, alpha=0.3)
            ax.legend()
            st.pyplot(fig,width='stretch')
            plt.close(fig)


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
            
    ########################################################################
    # Tab: Historical tabs
    ########################################################################
    with tables_tab:

        tables_by_date_tab, all_tables_tab = st.tabs(["Tables by date", "All tables together"])

    with tables_by_date_tab:
        st.write("Historical tables, on any date")
        st.write("Caveat: these are calculated from the match results only ignoring points deductions")
        
        # choose a season
        # initial season excluded
        sel_season = st.selectbox(
            "Choose season",
            season_list,
            index = len(season_list)-1,
            key="tab_sel_season"
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
            key="tab_sel_league"
            )

        # select the teams from the league
        sel_teams = season_league_teams.loc[ (sel_season,*sel_league) ]
        league_size = len(sel_teams)
        # initialise their ratings prior to start of season
        preseason_ratings = season_ratings_start.loc[sel_season]

        # get a breakdown of matches by date  
        season_by_date_df = get_season_matchcount_by_date(scores_df, sel_season, sel_league, league_size)
        season_gamedays = season_by_date_df["Date"].to_list()

        # choose simulation start date
        table_date = st.selectbox(
            "Table at date",
            options = season_gamedays,
            index =len(season_gamedays)-1,
            format_func = format_matches_played,
            key = "tab_date_select"
            )
        
        if table_date is not None:
            # split the season fixtures by the date
            matches_played, matches_to_play = split_season_by_date(scores_df, sel_season, sel_league[1], table_date)
            # get initial ratings at that date 
            initial_ratings = get_ratings_at_date(ratings_df, sel_teams, table_date)                
            # display table as of results_to_date
            st.write(f"Table as of {table_date:%Y-%m-%d}")
            table = get_table_with_elo_to_date(ratings_df, scores_df, sel_season, sel_league, table_date, preseason_ratings.loc[sel_teams])
        else:
            table = tables.loc[(sel_season,*sel_league)]

        display_actual_results(table, sel_season)

    with all_tables_tab:
        st.dataframe(tables)


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
            results_to_date = st.selectbox(
                "Date range of results to include",
                options = [None] + season_gamedays.to_list(),
                format_func = format_matches_played
                )

            # choose number of simulations to perform
            Nsims_options = [1,100,1000,10000,100000]
            Nsims = st.selectbox("Number of simulations", Nsims_options, index=3, key = "simulator")
            simulate = st.form_submit_button("Simulate")

        if simulate:

            full_games_played =  league_size*(league_size - 1 )
            # if simulating including results up to the date chosen in results_to_date
            if results_to_date is not None:
                # split the season fixtures by the date
                matches_played, matches_to_play = split_season_by_date(scores_df, sel_season, sel_league[1], results_to_date)

                # get initial ratings at that date 
                initial_ratings = get_ratings_at_date(ratings_df, sel_teams, results_to_date)
                #initial_ratings_by_ff = build_partial_ratings(initial_ratings | {"home_adv": preseason_ratings["home_adv"].iloc[0]} , matches_played)

                # if simulating the current season we do not have the future fixtures accessible
                # so set matches_to_play to None
                # then simulation will organise remaining fixtures 
                if len(matches_played) + len(matches_to_play) != full_games_played:
                    matches_to_play = None
                    
                # display table as of results_to_date
                st.write(f"Table as of {results_to_date:%Y-%m-%d}")
                starting_table = get_table_with_elo_to_date(ratings_df, scores_df, sel_season, sel_league, results_to_date, preseason_ratings.loc[sel_teams])
                display_actual_results(starting_table, sel_season)
                
            # if simulating whole season
            else:
                initial_ratings = preseason_ratings
                matches_played = None
                matches_to_play = None

            # prepare the state dictionary passed to the simulation
            state = prepare_state(
                teams = sel_teams,
                ratings = initial_ratings,
                home_adv = preseason_ratings.loc["home_adv"],
                season = sel_season
            )

            # run the simulations
            # can extend this to loop over multiple models if present
            # models_used = ["elo_static"]
            # model_data = {}
            # for model in models_used:
            #   model_data[model] = run_simulations(...)
            # and similar loop in the error calculation
            
            simulated_season = run_simulations(state, Nsims, model_name = "elo_static", games_played = matches_played, games_to_play = matches_to_play)
            # display the resuts
            st.write("Simulation results:")
            display_results(simulated_season, sel_teams, Nsims)
            # get the actual final table
            actual_table = tables.loc[(sel_season,*sel_league)]
            games_played = actual_table["W"].sum(axis=0) + actual_table["D"].sum(axis=0)/2
            if games_played == full_games_played:
                st.write("Actual results:")
                display_actual_results(actual_table, sel_season)
                model_errors = get_errors(actual_table, simulated_season, Nsims)
                display_errors(model_errors)

    ########################################################################
    # Tab: Season Simulations
    ########################################################################
    with backtest_tab:

        st.write("Based on previously run simulations of various seasons starting at different points")
        #st.write("Currently a non-zero start point actually means include all actual results up to and including the first match date for which the percentage of matches played exceeds the number given")

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
