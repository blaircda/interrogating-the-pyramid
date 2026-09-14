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
    plot_model_home_adv, plot_model_home_adv_compare,
    display_results, display_league_table, display_errors,
    plot_season_sim_errors, plot_season_sim_errors_multi, plot_season_start_errors
    )
from sns_plotting import (
    table_labels, stats_positional, stats_fundamental,
    plot_line, plot_line_all_seasons,plot_team_line_all_seasons,
    plot_reg_values, plot_scatter, plot_heatmap
)   
from simulation.monte_carlo_simulator import (
    prepare_state, run_simulations, get_errors
)

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"

def select_season_division(seasons, tiers, key):
    """
    streamlit selectbox for picking a season and a division
    """
    # choose a season
    sel_season = st.selectbox(
        "Choose season",
        seasons,
        index = len(seasons)-1,
        key=f"{key}_sel_season"
        )

    # get the leagues and teams for selected season
    tier_divisions =  get_tiers_by_season(sel_season, tiers) 

    # choose a league
    sel_tier_league = st.selectbox(
        "Choose league",
        tier_divisions,
        index = 0,
        format_func = lambda x:x[1],
        key=f"{key}_sel_league"
        )
        
    return sel_season, sel_tier_league

def get_tiers_by_season(season, tiers):
    td = [tuple(y) for y in tiers.loc[season].values]
    tier_divisions =  sorted( td, key = lambda x:x[0] )
    # this is a list of tuples (int tier, str division_name)
    # e.g. (1, "Premier League"), (2, "EFL Championship"), ... ] 
    return tier_divisions

def get_teams_by_season_and_div(season, tier_div, season_league_teams):
    """
    returns a list of the teams for season and tier_div
    """
    return season_league_teams.loc[ (season,*tier_div) ]

def select_season_range(seasons, key):
        # season range slider
        s1, s2 = st.select_slider(
            "Season range",
            options = seasons,
            value = (min(seasons), max(seasons)),
            key = f"{key}_season_slider"
            )
        return s1, s2
        
def multiselect_teams(teams, key, max_sels = 25):
        # team multiselection
        sel = st.multiselect(
            f"Team ({len(teams)} options)",
            teams,
            default = teams[0],
            max_selections = max_sels,
            key=f"{key}_team_sel"
            )
        return sel

def filter_by_season_and_teams(df, s1, s2, teams):    
        filtered = df[ df["team"].isin(teams) & df["season"].between(s1, s2) ]
        return filtered
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
    tiers_by_season = data.tiers
    
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
        ratings_tab, tables_tab, stats_tab, home_adv_tab, season_sim_tab, backtest_tab = st.tabs(["Historical ratings", "Historical tables", "Damned Lies United", "Historical vs model home advantage", "Season simulations", "Backtests"])

    ########################################################################
    # Tab: Ratings
    ########################################################################
    with ratings_tab:
        s1, s2 = select_season_range(season_list, "ratings")
        sel_teams = multiselect_teams(teams, "ratings")
        filtered_ratings = filter_by_season_and_teams(ratings_df, s1, s2, sel_teams)
        fig = plot_multi_ratings(filtered_ratings, sel_teams)
        st.pyplot(fig,width='stretch')
        plt.close(fig)

    ########################################################################
    # Tab: Home Advantage
    ########################################################################
    with home_adv_tab:
        # subtabs
        #record_tab, model_tab = st.tabs(["Historic home advantage", "Model home advantage"])

    ########################################################################
    #  Historical Home Advantage
    ########################################################################
    #with record_tab:
        st.subheader("Historic home advantage")
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
        st.pyplot(fig)
        plt.close(fig)

    ########################################################################
    # subtab: Model Home Advantage
    ########################################################################
    #with model_tab:
        st.subheader("Model home advantage")
        st.write(f"Starting from initial home advantage {initial_home_adv} rating points")
        st.write(f"Updating model home advantage at start of every season based on previous {N_matches_home_adv} matches")

        # plot model home advantage over time
        fig = plot_model_home_adv( season_ratings_end.xs("home_adv", level=1) )
        st.pyplot(fig)
        plt.close(fig)
        # plot comparison between model home win ex and actual home success
        fig = plot_model_home_adv_compare(av_discr, 20)
        st.pyplot(fig)
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
    # Tab: Historical tables
    ########################################################################
    with tables_tab:

        tables_by_date_tab, all_tables_tab = st.tabs(["Tables by date", "All tables together"])

    with tables_by_date_tab:
        st.write("Historical tables, on any date")
        st.write("Caveat: these are calculated from the match results only ignoring points deductions")

        sel_season, sel_league = select_season_division(season_list, tiers_by_season, "tab")
        sel_teams = get_teams_by_season_and_div(sel_season, sel_league, season_league_teams)
        
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

        display_league_table(table, sel_season)

    with all_tables_tab:
        st.dataframe(tables)

    ########################################################################
    # Tab: Statistics
    ########################################################################
    with stats_tab:
        st.header("Statistics")
        scatter_tab, trends_tab, team_trends_tab, corrs_tab, records_tab = st.tabs(["Relationships", "Trends (collective)", "Trends (by team)", "Correlations", "Records"])
        incomplete_seasons = ["1939/1940", "2026/2027"]
        tables_data = tables.drop(incomplete_seasons, level="Season")
        seasons = tables_data.index.get_level_values("Season")
        seasons_l = seasons.unique()
        
    with trends_tab:
        df = tables_data
        with st.expander("All seasons/all tiers"):
            st.subheader("All season - all tier line plots showing average, max, min")
            # ALL SEASONS, ALL TIERS
            sel = st.selectbox("Choose data to plot",
                    stats_fundamental.keys(),
                    index = 0,
                    format_func = lambda x : stats_fundamental.get(x,x)[0],
                    key="sel_table_data"
                )

            fig = plot_line_all_seasons(df, "Season", sel, hue=None)
            st.pyplot(fig)
            plt.close(fig)

            fig = plot_line_all_seasons(df, "Season", sel, hue="Tier")
            st.pyplot(fig)
            plt.close(fig)

        with st.expander("All seasons/specific tier"):
            # ALL SEASONS, PICK TIER
            st.subheader("All season - specific tier line plots showing average, max, min")
            tiers = [1,2,3,4]
            sel_tier = st.selectbox("Choose tier",
                    tiers,
                    index = 0,
                    key="sel_tier_table_data"
            )
            df = df[ df.index.get_level_values("Tier")==sel_tier]
            sel2 = st.selectbox("Choose data to plot",
                    table_labels.keys(),
                    index = 0,
                    format_func = lambda x : table_labels.get(x,x)[0],
                    key="sel_table_data_2"
            )
            fig = plot_line_all_seasons(df, "Season", sel2, hue=None)
            st.pyplot(fig)
            plt.close(fig)
            fig = plot_line_all_seasons(df, "Season", sel2, hue="Division")
            st.pyplot(fig)
            plt.close(fig)
            
    with scatter_tab:
        s1,s2 = select_season_range(seasons_l, "relns")
        
        #sel_season, sel_league = select_season_division(seasons_l, tiers_by_season, "stats")
        #league_teams = get_teams_by_season_and_div(sel_season, sel_league, season_league_teams)
        selx = st.selectbox("Choose data to plot",
                table_labels.keys(),
                index = 0,
                format_func = lambda x : table_labels.get(x,x)[0],
                key="selx_table_data"
            )
        sely = st.selectbox("Choose data to plot",
                table_labels.keys(),
                index = 1,
                format_func = lambda x : table_labels.get(x,x)[0],
                key="sely_table_data"
            )
            
        if selx == sely:
            st.write("Please choose distinct options")
        else:
            if s1==s2:
                sel_season = s1
                df = tables_data[ seasons ==  sel_season ]
                fig = plot_scatter(df, selx, sely, hue="Division", selection=sel_season)
                st.pyplot(fig)
                plt.close(fig)

                fig = plot_reg_values(df, selx, sely, selection=sel_season)
                st.pyplot(fig)
                plt.close(fig)
                
                l_tiers = get_tiers_by_season(sel_season, tiers_by_season)
                for tier, div in l_tiers:
                    fig = plot_reg_values(df[ df.index.get_level_values("Division")==div], selx, sely, selection=f"{div} {sel_season}")
                    st.pyplot(fig)
                    plt.close(fig)
            else:
                df = tables_data[ (seasons >= s1) & ( seasons <= s2) ]
                fig = plot_scatter(df, selx, sely, hue="Tier", selection=f"{s1} to {s2}")
                st.pyplot(fig)
                plt.close(fig)
                        
                fig = plot_reg_values(df, selx, sely, selection=f"{s1} to {s2}")
                st.pyplot(fig)
                plt.close(fig)

                for n in range(1,5):
                    fig = plot_reg_values(df[ df.index.get_level_values("Tier")==n], selx, sely, selection=f"Tier {n} {s1} to {s2}")
                    st.pyplot(fig)
                    plt.close(fig)                    

    with team_trends_tab:        
        s1, s2 = select_season_range(seasons_l, "team_trends")
        sel_teams = multiselect_teams(teams, "team_trends", max_sels=5)
        df = tables_data[
                (tables_data.index.get_level_values("Team").isin(sel_teams)) &
                (seasons>=s1) & (seasons<=s2)
                ]

        sel = st.selectbox("Choose data to plot",
            table_labels.keys(),
            index = 0,
            format_func = lambda x : table_labels.get(x,x)[0],
            key="sel_team_trend_table_data"
        )

        if len(sel_teams) == 1:
            annotate_tier = True
        else:
            annotate_tier = False            
        fig = plot_team_line_all_seasons(df, "Season", sel, hue="Team", annotate_tier = annotate_tier)
        st.pyplot(fig)
        plt.close(fig)

    with corrs_tab:
        sel = st.multiselect(
            f"Statistics ({len(table_labels)} options)",
                table_labels.keys(),
                default = ["Rstart", "Rend"],
                max_selections = 50,
                format_func = lambda x: table_labels.get(x,x)[0],
                key=f"corr_multi_sel"
            )

        s1, s2 = select_season_range(seasons_l, "corrs")
        choose_tier = st.selectbox("Tier?", ["All", 1,2,3,4], index= 0, key="corr_tier_sel")

        if choose_tier == "All":
            df = tables_data[
                (seasons>=s1) & (seasons<=s2)
            ]
        else:
            df = tables_data[
                (tables_data.index.get_level_values("Tier")==choose_tier) &
                (seasons>=s1) & (seasons<=s2)
            ]
                
        if len(sel)>1:
            df = df[sel]
            fig = plot_heatmap(df)
            st.pyplot(fig)
            plt.close(fig)

    with records_tab:
        exclude_stats = ["POS", "Rstart_rank", "Rend_rank", "POSPyr", "RPyr_start", "RPyr_end"]
        record_stats = { k:v for k,v in table_labels.items() if k not in exclude_stats }
        
        sel = st.selectbox("Choose statistic",
            record_stats.keys(),
            index = 0,
            format_func = lambda x : record_stats.get(x,x)[0],
            key="records_table_data"
        )

        most_or_least = st.selectbox("Most or least?", ["Most", "Least"], index= 0)
        if most_or_least == "Most":
            sort_order = record_stats.get(sel)[1]
        else:
            sort_order = not record_stats.get(sel)[1]

        choose_tier = st.selectbox("Tier?", ["All", 1,2,3,4], index= 0)

        if choose_tier == "All":
            df = tables_data.sort_values(by=sel, ascending=sort_order).head(20)
        else:
            df = tables_data[ (tables_data.index.get_level_values("Tier")==choose_tier) ].sort_values(by=sel, ascending=sort_order).head(20)
        sel_name = record_stats.get(sel)[0]
        df = df.rename(columns={sel:sel_name})
        st.write(df[["POS", sel_name]] )
        
    ########################################################################
    # Tab: Season Simulations
    ########################################################################
    with season_sim_tab:
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

                # if simulating the current season we do not have the future fixtures accessible
                # so set matches_to_play to None
                # then simulation will organise remaining fixtures 
                if len(matches_played) + len(matches_to_play) != full_games_played:
                    matches_to_play = None
                    
                # display table as of results_to_date
                st.write(f"Table as of {results_to_date:%Y-%m-%d}")
                starting_table = get_table_with_elo_to_date(ratings_df, scores_df, sel_season, sel_league, results_to_date, preseason_ratings.loc[sel_teams])
                display_league_table(starting_table, sel_season)
                
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
            # display the results
            st.write("Simulation results:")
            display_results(simulated_season, sel_teams, Nsims)
            # get the actual final table
            actual_table = tables.loc[(sel_season,*sel_league)]
            games_played = actual_table["W"].sum(axis=0) + actual_table["D"].sum(axis=0)/2
            if games_played == full_games_played:
                st.write("Actual results:")
                display_league_table(actual_table, sel_season)
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
