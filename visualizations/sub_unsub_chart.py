import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import sub,unsub
from datetime import datetime, timedelta


def sub_unsub_chart(db,start_date,end_date):
    sub_count = sub(db,start_date, end_date)
    unsub_count = unsub(db,start_date, end_date)
    if start_date and end_date:
        intervall = end_date - start_date
        diff_end = start_date - intervall
        diff_sub = sub(db,diff_end,start_date)
        diff_unsub = unsub(db,diff_end,start_date)
        difference_sub = sub_count - diff_sub
        difference_unsub = unsub_count - diff_unsub
    else:
        difference_sub = 0
        difference_unsub = 0

    return sub_count,difference_sub,unsub_count,difference_unsub
