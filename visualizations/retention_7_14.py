import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import retention_within_days
import pandas as pd
import altair as alt

def retention_7_14_chart(db,start_date,end_date):
    retention_rate = retention_within_days(db,start_date,end_date)
    interval = end_date - start_date
    diff_ret = retention_within_days(db,start_date-interval,start_date)
    st.metric(label="Retour après 1 semaine", value=f"{round(retention_rate,2)}%",delta=f"{round(retention_rate-diff_ret,2)}%")

