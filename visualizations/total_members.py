import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import total_members

def total_members_chart(db):
    total_members_count = total_members(db)
    st.metric(label="Humans", value=total_members_count)
    # fig = go.Figure(go.Indicator(
    #     mode = "number",
    #     value = total_members_count,
    #     title = {"text": "Total Members"},
    # ))
    # st.plotly_chart(fig)