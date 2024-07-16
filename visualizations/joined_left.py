import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import get_join_and_leave_stats
from database_processing.data_processing import get_actual_member_left
from datetime import datetime, timedelta


def joined_and_left_chart(db,start_date,end_date):
    joined_count,_ = get_join_and_leave_stats(db,start_date, end_date)
    left_count = get_actual_member_left(db,start_date, end_date)
    if start_date and end_date:
        intervall = end_date - start_date
        diff_end = start_date - intervall
        diff_joined, _ = get_join_and_leave_stats(db,diff_end,start_date)
        diff_left = get_actual_member_left(db,diff_end,start_date)
        difference_joined = joined_count - diff_joined
        difference_left = left_count - diff_left
    else:
        difference_joined = 0
        difference_left = 0

    return joined_count,difference_joined,left_count,difference_left
    
