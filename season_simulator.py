from collections import defaultdict
from game_simulator import *
import itertools

def play(team1, team2, state, model, table):
    """
    generates the result of team1 vs team2
    updates table and records the result in matches
    """
    g1,g2 = play_game(team1, team2, state, model)
    # store matches for revisiting when computing ranking of tied teams
    #matches[(team1,team2)] = {team1: g1, team2:g2}
    # update table
    table[team1]["GF"] += g1
    table[team1]["GA"] += g2
    table[team2]["GF"] += g2
    table[team2]["GA"] += g1
    if (g1>g2):
        table[team1]["W"] += 1
        table[team2]["L"] += 1
    elif (g1<g2):
        table[team2]["W"] += 1
        table[team1]["L"] += 1
    else:
        table[team1]["D"] += 1
        table[team2]["D"] += 1

def play_partial(team1, team2, state, model, table):
    """
    generates the result of team1 vs team2
    uses known result if available, otherwise simulates
    updates table and records the result in matches
    """
    #if (team1, team2) in state["matches"]:
    #    g1, g2 = state["matches"][(team1, team2)]
    #else:
    #    g1,g2 = play_game(team1, team2, state, model)
    g1, g2 = state["matches"].get( (team1, team2), play_game(team1, team2, state, model) )
    # store matches for revisiting when computing ranking of tied teams
    #matches[(team1,team2)] = {team1: g1, team2:g2}
    # update table
    table[team1]["GF"] += g1
    table[team1]["GA"] += g2
    table[team2]["GF"] += g2
    table[team2]["GA"] += g1
    if (g1>g2):
        table[team1]["W"] += 1
        table[team2]["L"] += 1
    elif (g1<g2):
        table[team2]["W"] += 1
        table[team1]["L"] += 1
    else:
        table[team1]["D"] += 1
        table[team2]["D"] += 1

def run_season(state, model, fixtures = None):
    """
    simulates a single league season
    optionally can do this following the official sequence of fixtures (gameweek by gameweek)
    allowing one to update ELO ratings etc throughout the simulated season
    returns the final league table
    """
    tie = 0
    # iterate over groups and matches therein
    ts = state["teams"]
    #table = defaultdict(lambda: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS":0})
    table = defaultdict(lambda: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0})
    #matches = {}


    # if we are going to use partial results
    if "matches" in state:
        play_fn = play_partial
    else:
        play_fn = play

    if fixtures:
        for gameweek, games in fixtures.items():
            for pairing in games:
                play(pairing[0], pairing[1], state, model, table)
    else:
        for team1, team2 in itertools.combinations(ts,2):
            play_fn(team1, team2, state, model, table)
            play_fn(team2, team1, state, model, table)


    # update table
    # taking into account historical rules 
    
    for team in ts:
        if state["goal_separator"] == "difference":
            table[team]["GD"] = table[team]["GF"] - table[team]["GA"]
        else:
            table[team]["GD"] = table[team]["GF"] / table[team]["GA"]
        table[team]["PTS"] = state["points_per_game"]*table[team]["W"] + table[team]["D"]

    # will need to handle historical head to head, 2 points per game, use of goal differential
    table = list(sorted(table.items(),
        key=lambda item: (item[1]["PTS"], item[1]["GD"], item[1]["GF"]
        ), reverse=True))
    #print(f"\nFinal table:")
    #print(*table, sep="\n")
    return table

def update_results(table, team_results):
    """
    input: table = list of tuples (team name, dict {W, D, L, GF, GA, GD, PTS})
           results = dict of dicts
    """
    for i, team_data in enumerate(table):
        team = team_data[0]
        stats = team_data[1]
        #pts = stats["PTS"]
        team_results[team][i+1] += 1
        for k, v in stats.items():
            if k in ["PTS", "W", "D", "L", "GF", "GA"]:
            #if k in ["PTS", "W", "D", "L", "GF", "GA", "GD"]:
                team_results[team][k] += v
