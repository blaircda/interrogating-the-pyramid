import pandas as pd

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"

teams = pd.read_csv(teams_csv, usecols=["Team"])["Team"].to_list()
df = pd.read_csv(scores_csv, usecols=["HomeTeam", "AwayTeam"])
teams1 = list(pd.concat([df["HomeTeam"], df["AwayTeam"]]).unique())

print(f"The following teams appear in {scores_csv} but not in {teams_csv}")
print( set(teams1) - set(teams) )
