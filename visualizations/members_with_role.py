import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import members_with_role

def members_with_role_chart(db,role_name):
    members_count = members_with_role(db,role_name)
    st.metric(label=f"{role_name}", value=members_count)

    # fig = go.Figure(go.Indicator(
    #     mode = "number",
    #     value = members_count,
    #     title = {"text": f"Members with Role '{role_name}'"},
    # ))
    # st.plotly_chart(fig)
