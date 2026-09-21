import streamlit as st

about_page = st.Page("page_about.py", title="About", icon=":material/info:")
ratings_page = st.Page("page_ratings.py", title="Ratings", icon=":material/show_chart:")
stats_page = st.Page("page_stats.py", title="Damned Lies United", icon=":material/table_chart_view:")
tables_page = st.Page("page_tables.py", title="Tables", icon=":material/data_table:")
sim_page = st.Page("page_simulations.py", title="Simulations", icon=":material/sports_soccer:")
regr_page = st.Page("page_regressions.py", title="Regressions", icon=":material/chart_data:")

pg = st.navigation([
        about_page, ratings_page, stats_page, tables_page, sim_page, regr_page
        ])
pg.run()

