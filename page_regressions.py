import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
import json
from config import *
from import_process import (
    process_data,
    get_ratings_at_date, split_season_by_date,
    get_table_to_date, get_table_with_elo_to_date, get_season_matchcount_by_date
)

teams_csv = "data/EnglishTeamActivePeriods.csv"
scores_csv = "data/EnglandLeagueResults.csv"
data = process_data(teams_csv, scores_csv)
tables = data.tables

st.set_page_config(layout="wide", page_title="Regression | Interrogating the pyramid")

st.header("Regressive predictions")
st.write("Based on ridge regression with feature and parameter grid search")
regr_ha_tab, regr_pl_tab = st.tabs(["Predicting home advantage", "Predicting PL 2026/2027"])
path = "data/output/regr/"

with regr_ha_tab:
    st.subheader("All seasons, all tiers")
    with open(path+"All_Seasons_All_Tiers_WHpg.json", "r") as f:
        data = json.load(f)
    st.write(f"Predicted WHpg for 2026/2027: {data['pred']:.4f}")
    st.image(path+"All_Seasons_All_Tiers_WHpg.png")
    for n in range(1,5):
        st.subheader(f"Tier {n}")
        with open(path+f"All_Seasons_Tier_{n}_WHpg.json", "r") as f:
            data = json.load(f)
        st.write(f"Predicted WHpg for 2026/2027: {data['pred']:.4f}")
        st.image(path+f"All_Seasons_Tier_{n}_WHpg.png")


with regr_pl_tab:

    st.subheader("Predicted table from regression")
    df = (
        pd.read_csv(path+"PL.csv", index_col=0)
        .rename(columns={"PTS_wd": "PTS"})
        .sort_values(by="PTS", ascending=False)
    )
    st.dataframe(df)

    st.write(f"Game discrepancy: { 100*(df['W'].sum() + 0.5*df['D'].sum() - 380)/380:.2f}% of season missing")
    
    selSeason = "2026/2027"
    selT1 = tables.xs(
        (selSeason, 1),
        level=["Season", "Tier"]
        ).index.get_level_values("Team").unique()

    choose_team = st.selectbox(
        "See details for team:",
        selT1,
        index=0,
        key="pl_reg_choose_team"
    )
        
    targets = ["Wpg", "Dpg", "GFpg", "GApg", "Rend"]
    for target in targets:
        st.image(path+"PL_"+choose_team+"_"+target+".png")
