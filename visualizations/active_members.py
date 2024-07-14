import streamlit as st
from database_processing.data_processing import active_members

def active_members_chart(db, role = False):
    active_members_count = active_members(db, role)
    st.metric(label="Active Members", value=active_members_count)
