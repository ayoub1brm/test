import streamlit as st
import plotly.graph_objects as go
from database_processing.data_processing import get_role_distribution,human_and_bots
from streamlit_echarts import  st_echarts


def role_distribution_chart(db,selected_roles):
    distribution = get_role_distribution(db)
    role_names = []
    member_counts = []

    for role_name, count in distribution:
        if role_name in selected_roles:
            role_names.append(role_name)
            member_counts.append(count)

    human_count, _ = human_and_bots(db)
    if human_count is None:
        st.error("No data available for the selected time range.")
        return

    if selected_roles:
        selected_count = sum([member_counts[role_names.index(role)] for role in selected_roles if role in role_names])
        percentage = (selected_count / human_count) * 100
        labels = selected_roles + ["Other"]
        values = [member_counts[role_names.index(role)] for role in selected_roles if role in role_names] + [human_count - selected_count]
    else:
        labels = ["All Human Members"]
        values = [human_count]
        percentage = [100]
    
    data = []
    for i in range(len(values)):
        data.append({"value" : values[i],"name":str(labels[i])})
    
    options = {
    "title": { "left": "center"},
    "tooltip": {"trigger": "item"},
    "legend": {"orient": "vertical", "left": "left",},
    "series": [
        {
            "name": "Role Distribution",
            "type": "pie",
            "radius": "50%",
            "data": data,
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                }
            },
        }
    ],
    }
    st_echarts(
    options=options, height="300px",
        )
