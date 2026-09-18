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
    plot_reg_values, plot_scatter, plot_reg_values_seasons,
    plot_heatmap_df
)
from helpers import (
    multiselect_teams,
    select_season_range, select_season_division, select_tier_by_season,
    get_sorted_tables
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
incomplete_seasons = ["1939/1940", "2026/2027"]
tables_data = tables.drop(incomplete_seasons, level="Season")
seasons = tables_data.index.get_level_values("Season")
seasons_l = seasons.unique()


st.set_page_config(layout="wide", page_title="Damned Lies United | Interrogating the pyramid")
# control width of content display 
#padl, content, padr = st.columns([0.1,0.8,0.1])

st.header("Statistics")
s1, s2 = select_season_range(seasons_l, "stats_overall")


scatter_tab, trends_tab, team_trends_tab, corrs_tab, records_tab = st.tabs(["Relationships", "Trends (collective)", "Trends (by team)", "Correlations", "Records"])


with trends_tab:
    choose_tier = select_tier_by_season(s2, tiers_by_season, "collective_trends")

    sel = st.selectbox("Choose data to plot",
            stats_fundamental.keys(),
            index = 0,
            format_func = lambda x : stats_fundamental.get(x,x)[0],
            key="sel_table_data"
        )
        
    if choose_tier == "All":
        df = tables_data[
            (seasons>=s1) & (seasons<=s2)
        ]
        hue="Tier"
        selection=None
    else:
        df = tables_data[
            (tables_data.index.get_level_values("Tier")==choose_tier) &
            (seasons>=s1) & (seasons<=s2)
        ]
        hue="Division"
        selection=f"Tier {choose_tier}"

    #with st.expander(f"{table_labels[sel][0]} by Season"):
    fig = plot_line_all_seasons(df, "Season", sel, hue=None, selection=selection)
    st.pyplot(fig)
    plt.close(fig)
    #with st.expander(f"{table_labels[sel][0]} by Season by {hue}"):
    fig = plot_line_all_seasons(df, "Season", sel, hue=hue, selection=selection)
    st.pyplot(fig)
    plt.close(fig)

    #with st.expander(f"Linear regression of {table_labels[sel][0]} by Season"):
    #    fig = plot_reg_values_seasons(df, "Season", sel, selection=selection)
    #    st.pyplot(fig)
    #    plt.close(fig)
    #fig = plot_line_all_seasons(df, "Season", sel, hue="GOAL_RULE", selection=selection)
    #st.pyplot(fig)
    #plt.close(fig)
    #fig = plot_line_all_seasons(df, "Season", sel, hue="PTS_RULE", selection=selection)
    #st.pyplot(fig)
    #plt.close(fig)
                   
with scatter_tab:  
    choose_tier = select_tier_by_season(s2, tiers_by_season, "scatter")

    if choose_tier == "All":
        df = tables_data[
            (seasons>=s1) & (seasons<=s2)
        ]
        hue="Tier"
    else:
        df = tables_data[
            (tables_data.index.get_level_values("Tier")==choose_tier) &
            (seasons>=s1) & (seasons<=s2)
        ]
        hue="None"

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
            selection = sel_season
        else:
            selection = f"{s1} to {s2}"
            
        fig = plot_scatter(df, selx, sely, hue=hue, selection=f"{s1} to {s2}")
        st.pyplot(fig)
        plt.close(fig)
                
        fig = plot_reg_values(df, selx, sely, selection=f"{s1} to {s2}")
        st.pyplot(fig)
        plt.close(fig)

        #l_tiers = get_tiers_by_season(s2, tiers_by_season)
        #for tier, div in l_tiers:
        #    fig = plot_reg_values(df[ df.index.get_level_values("Division")==div], selx, sely, selection=f"{div} {s1} to {s2}")
        #    st.pyplot(fig)
        #    plt.close(fig)                


with team_trends_tab:        
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
        annotate_tier = False
    else:
        annotate_tier = False            
    fig = plot_team_line_all_seasons(df, "Season", sel, hue="Team", annotate_tier = annotate_tier)
    st.pyplot(fig)
    plt.close(fig)

with corrs_tab:
    choose_tier = select_tier_by_season(s2, tiers_by_season, "corrs")

    sel = st.multiselect(
        f"Statistics ({len(table_labels)} options)",
            table_labels.keys(),
            default = ["Rstart", "Rend"],
            max_selections = 50,
            format_func = lambda x: table_labels.get(x,x)[0],
            key=f"corr_multi_sel"
        )


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
        fig = plot_heatmap_df(df)
        st.pyplot(fig)
        plt.close(fig)

with records_tab:
    exclude_stats = ["POS", "Rstart_rank", "Rend_rank", "POSPyr", "RPyr_start", "RPyr_end"]
    record_stats = { k:v for k,v in table_labels.items() if k not in exclude_stats }

    choose_tier = select_tier_by_season(s2, tiers_by_season, "records")
          
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


    if choose_tier == "All":
        df = tables_data[
            (seasons>=s1) & (seasons<=s2)
        ]
    else:
        df = tables_data[
            (tables_data.index.get_level_values("Tier")==choose_tier) &
            (seasons>=s1) & (seasons<=s2)
        ]

    df = get_sorted_tables( df, sel, sort_order, N= 20)
    sel_name = record_stats.get(sel)[0]
    df = df.rename(columns={sel:sel_name})
    st.write(df[["POS", sel_name]] )
