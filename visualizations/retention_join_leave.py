import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import retention_join_leave

def retention_join_leave_chart(db,start_date, end_date):
    retention_rate = retention_join_leave(db,start_date, end_date)
    interval = end_date - start_date
    diff_ret = retention_join_leave(db,start_date-interval,start_date)
    st.metric(label="Join leave retention",value=f"{round(retention_rate,2)}%",delta=f"{round(retention_rate-diff_ret,2)}%")