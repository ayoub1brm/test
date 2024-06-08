import streamlit as st
from database_processing.data_processing import active_members

def active_members_chart(db,start_date, end_date):
    active_members_count = active_members(db,start_date, end_date)
    interval = end_date - start_date
    diff_ret = active_members(db,start_date-interval,start_date)
    st.metric(label="Active Members", value=active_members_count,delta=active_members_count-diff_ret)