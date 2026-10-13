import pandas as pd

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"
fixtures_csvs = [ f"data/current_fixtures/Tier{n}.csv" for n in range(1,5) ]

teams = set( pd.read_csv(teams_csv, usecols=["Team"])["Team"].to_list() )
df = pd.read_csv(scores_csv, usecols=["HomeTeam", "AwayTeam"])
teams1 = list(pd.concat([df["HomeTeam"], df["AwayTeam"]]).unique())
invalids = set(teams1) - teams
if len(invalids):
    print(f"The following teams appear in {scores_csv} but not in {teams_csv}")

for file in fixtures_csvs:
    df = pd.read_csv(file, usecols=["home", "away"])
    teams1 = list(pd.concat([df["home"], df["away"]]).unique())
    invalids = set(teams1) - teams
    if len(invalids):
        print(f"The following teams appear in {file} but not in {teams_csv}")
        print(invalids)
