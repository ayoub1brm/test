import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import total_members

def total_members_chart(db):
    total_members_count = total_members(db)
    st.metric(label="Total", value=total_members_count)
