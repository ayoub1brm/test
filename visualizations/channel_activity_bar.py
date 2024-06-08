import streamlit as st
import plotly.express as px
from database_processing.data_processing import get_message_activity_bar
from datetime import datetime, timedelta
import pandas as pd

def top_channels_bar_chart(db,start_date, end_date,top_n):
    df = get_message_activity_bar(db,start_date, end_date, top_n)
    
    fig = px.bar(df, x='message_count', y='channel_name', orientation='h', title='Top Channels by Message Activity')
    
    st.plotly_chart(fig)