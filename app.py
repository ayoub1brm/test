import streamlit as st
from discord_bot.discord_bot import setup_discord_bot
from datetime import datetime, timedelta
from visualizations.total_members import total_members_chart
from visualizations.members_with_role import members_with_role_chart
from visualizations.joined_across_time import joined_across_time_chart
from visualizations.active_members import active_members_chart
from visualizations.retention_7_14 import retention_7_14_chart
from visualizations.retention_join_leave import retention_join_leave_chart
from visualizations.role_distribution import role_distribution_chart
from visualizations.joined_left import joined_and_left_chart
from visualizations.channel_activity_bar import top_channels_bar_chart
from visualizations.channel_activity_line import channel_activity_line_chart
from data_processing import members_with_role
from database.database import Database
from streamlit_extras.stylable_container import stylable_container
import altair as alt
import os
import threading
import os
import subprocess
from discord_bot.discord_bot import setup_discord_bot
from database.database import Database
import pytz

# Initialize database
db = Database('discord_bot.db')
# Get the token from an environment variable
discord_token = os.getenv('DISCORD_TOKEN')

FILE_PATH = 'setup_status.txt'

# Function to read the setup status from file
def read_setup_status():
    try:
        with open(FILE_PATH, 'r') as file:
            return file.read().strip() == 'True'
    except FileNotFoundError:
        return False

# Function to write the setup status to file
def write_setup_status(status):
    with open(FILE_PATH, 'w') as file:
        file.write(str(status))

def run_discord_bot():
    setup_discord_bot(discord_token)

# Main Streamlit application code

# Check if setup has been done
discord_bot_setup_done = read_setup_status()

# If setup hasn't been done, perform setup and update status
if not discord_bot_setup_done:
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.start()
    write_setup_status(True)

roles = db.get_roles()

# Set up page configuration
st.set_page_config(
    page_title="Moulaclub Server Analytics Dashboard",
    page_icon="logo_mc.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme styling


# Sidebar for logo and time range selection
st.sidebar.image("logo_mc.png", use_column_width=False)
time_range = st.sidebar.selectbox("Select Time Range", ["Last 15 minutes", "Last hour", "Last 3 hours", "Last 24 hours", "Last 7 days", "Last month", "Last 6 months", "Last year","Last 2 year", "Custom", "Since creation"])
end_date = datetime.now(pytz.timezone('Europe/Paris'))
if time_range == "Last 15 minutes":
    start_date = end_date - timedelta(minutes=15)
    granularity = 'second'
elif time_range == "Last hour":
    start_date = end_date - timedelta(hours=1)
    granularity = 'minute'
elif time_range == "Last 3 hours":
    start_date = end_date - timedelta(hours=3)
    granularity = 'minute'
elif time_range == "Last 24 hours":
    start_date = end_date - timedelta(days=1)
    granularity = 'half_hour'
elif time_range == "Last 7 days":
    start_date = end_date - timedelta(days=7)
    granularity = 'hour'
elif time_range == "Last month":
    start_date = end_date - timedelta(days=30)
    granularity = 'day'
elif time_range == "Last 6 months":
    start_date = end_date - timedelta(days=180)
    granularity = 'week'
elif time_range == "Last year":
    start_date = end_date - timedelta(days=365)
    granularity = 'month'
elif time_range == "Last 2 year":
    start_date = end_date - timedelta(days=365*2)
    granularity = 'month'
elif time_range == "Custom":
    start_date = st.sidebar.date_input("Start date", value=datetime.now() - timedelta(days=1))
    end_date = st.sidebar.date_input("End date", value=datetime.now())
    if (end_date - start_date).days <= 1:
        granularity = 'minute'
    elif (end_date - start_date).days <= 7:
        granularity = 'hour'
    elif (end_date - start_date).days <= 30:
        granularity = 'day'
    elif (end_date - start_date).days <= 180:
        granularity = 'week'
    else:
        granularity = 'month'
elif time_range == "Since creation":
    start_date = None
    end_date = None
    granularity = 'month'

custom_css = """
    <style>
        /* Replace '.stAlert' with the specific class if needed */
        .stAlert {
            background-color: #f4cccc; /* Change to your desired background color */
            font-color:white;
        }
    </style>
    """
st.markdown(custom_css, unsafe_allow_html=True)

with stylable_container(
            key="container_dashboard",
            css_styles="""
                {
                    border: 5px solid rgba(49, 51, 63, 0.2);
                    border-radius: 1.5rem;
                    padding: calc(1em - 1px)
                }
                """,
        ):
    alt.themes.enable("dark")

    # Metrics section
    st.header("Server Overview")
    with stylable_container(
            key="container_dashboard",
            css_styles="""
                {
                    border: 5px solid rgba(49, 51, 63, 0.2);
                    border-radius: 1.5rem;
                    padding: calc(1em - 1px)
                }
                """,
        ):
        col1, col2,col3,col4,col5,col6 = st.columns(6,gap="medium")

        with col1:
            st.info("Total Members",icon="📊")
            total_members_chart(db)

        with col2:
            st.info("Online Members",icon="📊")
            active_members_chart(db, start_date, end_date)
        joined,delta_join,left,delta_left = joined_and_left_chart(db, start_date, end_date)
        with col3:
            st.info("Server Traffic",icon="📊")
            st.metric(label="Joined",value=joined,delta=delta_join)
        with col4:
            st.info("Server Traffic",icon="📊")
            st.metric(label="Left",value=(left*(-1)),delta=(delta_left*(-1)))
        with col5:
            st.info("Server Retention",icon="📊")
            retention_7_14_chart(db, start_date, end_date)
        with col6:
            st.info("Server Retention",icon="📊")
            retention_join_leave_chart(db, start_date, end_date)
    

    # Metrics section
    st.header("Server Overview")
    with stylable_container(
            key="container_dashboard",
            css_styles="""
                {
                    border: 5px solid rgba(49, 51, 63, 0.2);
                    border-radius: 1.5rem;
                    padding: calc(1em - 1px)
                }
                """,
        ):
        col1, col2,col3,col4,col5,col6 = st.columns(6,gap="medium")

        with col1:
            st.info("Total Members",icon="📊")
            members_with_role(db,"・ Membre Elite")

        with col2:
            st.info("Online Members",icon="📊")
            active_members_chart(db, start_date, end_date)
        joined,delta_join,left,delta_left = joined_and_left_chart(db, start_date, end_date)
        with col3:
            st.info("Server Traffic",icon="📊")
            st.metric(label="Joined",value=joined,delta=delta_join)
        with col4:
            st.info("Server Traffic",icon="📊")
            st.metric(label="Left",value=(left*(-1)),delta=(delta_left*(-1)))
        with col5:
            st.info("Server Retention",icon="📊")
            retention_7_14_chart(db, start_date, end_date)
        with col6:
            st.info("Server Retention",icon="📊")
            retention_join_leave_chart(db, start_date, end_date)

    
    col4, col5 = st.columns([3, 8])
    with stylable_container(
            key="container_dashboard",
            css_styles="""
                {
                    border: 5px solid rgba(49, 51, 63, 0.2);
                    border-radius: 1.5rem;
                    padding: calc(1em - 1px)
                }
                """,
        ):
        with col4:
            st.text("")
            st.text("")

            st.info("Members w/ Role",icon="📊")
            role_name = st.selectbox("", roles, key="role")
            members_with_role_chart(db, st.session_state['role'])
            st.text("")
            st.text("")
            st.text("")

            st.info("Role distribution",icon="📊")
            selected_roles = st.multiselect("Select Roles to Include in Pie Chart", roles, key="pie_chart_roles")
            role_distribution_chart(db, st.session_state['pie_chart_roles'])
    # Activity section
    with col5:
        
        joined_across_time_chart(db, start_date, end_date, granularity)
        channel_activity_line_chart(db, start_date, end_date, granularity)
        top_n = st.slider("Select number of top channels", 5, 20, 10)
        top_channels_bar_chart(db, start_date, end_date, top_n)

    # Role Distribution section

