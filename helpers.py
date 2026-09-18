import streamlit as st

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

    tier_div_flat = tiers.loc[season].values.ravel().tolist()
    
    td = [(t,d) for t,d in zip(tier_div_flat[::2], tier_div_flat[1::2]) ]
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
        
def select_tier_by_season(season, tiers, key):
    l_tiers = get_tiers_by_season(season, tiers)
    max_tiers = l_tiers[-1][0]
    tier_choice = ["All"] + list(range(1,max_tiers+1))
    choose_tier = st.selectbox("Tier?", tier_choice, index= 0, key=f"{key}_tier")
    return choose_tier

@st.cache_data
def get_sorted_tables( table_df, sort_param, sort_order, tier = None, N = 20):
    df = table_df.copy()
    if tier:
        df =  df[
             (df.index.get_level_values("Tier")==tier)
            ].sort_values(by=sort_param, ascending=sort_order).head(20)

    else:
        df = df.sort_values(by=sort_param, ascending=sort_order).head(20)
    return df

# helper function to format date selection 
def format_matches_played(date, season_by_date_df):
    if date is not None:
        data = season_by_date_df.loc[season_by_date_df["Date"] == date, ["MatchesOnDate", "MatchesPlayed", "MatchesPlayedPercent"]].iloc[0]                        
        #played_on_date = data.loc[:,"MatchesOnDate"].iloc[0]
        played_by_date = int(data["MatchesPlayed"])
        played_perc = data["MatchesPlayedPercent"]
        return f"{date:%Y-%m-%d} ({played_by_date:d} matches played, {played_perc:.2f}% of season)"

    else:
        return "None"
