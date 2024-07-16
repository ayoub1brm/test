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
        name='Nouveaux membres'
    ))

    fig.update_layout(
        title='Nouveaux membres à traver le temps',
        xaxis_title='Date/heure',
        yaxis_title='Nombre de nouveaux membres',
        template='plotly_white'
    )

    st.plotly_chart(fig,use_container_width=True)
