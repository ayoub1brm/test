import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import retention_within_days
import pandas as pd
import altair as alt

def retention_7_14_chart(db,start_date,end_date):
    retention_rate = retention_within_days(db,start_date,end_date)
    interval = end_date - start_date
    diff_ret = retention_within_days(db,start_date-interval,start_date)
    st.metric(label="1 week retention", value=f"{round(retention_rate,2)}%",delta=f"{round(retention_rate-diff_ret,2)}%")
    # fig = go.Figure(go.Pie(
    #     values=[retention_rate, 100 - retention_rate],
    #     labels=['Retention', 'Other'],
    #     hole=0.7,
    #     marker=dict(colors=['#1f77b4', '#d3d3d3']),
    #     textinfo='none'
    # ))

    # fig.add_annotation(dict(
    #     text=f"{retention_rate}%",
    #     x=0.5, y=0.5,
    #     font_size=20,
    #     showarrow=False
    # ))

    # fig.update_layout(
    #     showlegend=False,
    #     margin=dict(t=0, b=0, l=0, r=0),
    #     title={"text": "Retetion on 1 week", "x": 0.5, "xanchor": "center"}
    # )

    # st.plotly_chart(fig)
