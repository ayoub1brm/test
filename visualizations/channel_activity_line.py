import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import get_messages_activity_line
from datetime import datetime, timedelta
import pandas as pd


def channel_activity_line_chart(db,start_date, end_date, granularity):
    df = get_messages_activity_line(db,start_date, end_date,granularity) 

    df_pivot = df.pivot(index='timestamp', columns='channel_name', values='message_count').fillna(0)
    
    fig = go.Figure()

    for channel_name in df_pivot.columns:
        fig.add_trace(go.Scatter(
            x=df_pivot.index,
            y=df_pivot[channel_name],
            mode='lines',
            fill='tozeroy',  # Fill the area under the curve
            name=f'{channel_name}'
        ))

    fig.update_layout(
        title='Message Activity by Channel Over Time',
        xaxis_title='Time',
        yaxis_title='Number of Messages',
        template='plotly_white'
    )

    st.plotly_chart(fig)