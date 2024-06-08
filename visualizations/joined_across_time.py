import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import get_joined_across_time
from streamlit_echarts import  st_echarts


def joined_across_time_chart(db,start_date, end_date,granularity):
    joined_counts = get_joined_across_time(db,start_date, end_date, granularity)
   
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=joined_counts.index,
        y=joined_counts['joined_count'],
        fill='tozeroy',
        mode='lines',
        line=dict(color='darkblue'),
        fillcolor='lightblue',
        name='Members Joined'
    ))

    fig.update_layout(
        title='Members Joined Across Time',
        xaxis_title='Time',
        yaxis_title='Number of Members',
        template='plotly_white'
    )

    st.plotly_chart(fig,use_container_width=True)
