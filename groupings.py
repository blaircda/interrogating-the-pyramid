import pandas as pd

scores_file = "data/EnglandLeagueResults.csv"
#Date,Season,HomeTeam,AwayTeam,Score,hGoal,aGoal,Division,Tier,Result

def get_seasons_daterange(scores_file):
    df = pd.read_csv(scores_file, usecols=["Date", "Season"])
    df = df.groupby(["Season"]).agg(
    start=("Date", "min"),
    end=("Date", "max")
    )
    df["pre"] = df["end"].shift(1)
    #print(df)
    return df

def get_seasons_tiers(scores_file):
    df = pd.read_csv(scores_file, usecols=["Season", "Tier", "Division"])
    df = df[["Season", "Tier", "Division"]].drop_duplicates()
    #print(df.index)
    return df

def get_seasons_tiers_teams(scores_file):
    df = pd.read_csv(scores_file, usecols=["Season", "Tier", "Division", "HomeTeam"])
    df = df.groupby(["Season", "Tier", "Division"])["HomeTeam"].unique().apply(sorted)
    #print(df)
    return df
