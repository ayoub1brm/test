from database.database import Database
from datetime import datetime, timedelta
from database_processing.retention_indicator import retention_within_seven_to_fourteen_days
import pandas as pd

def total_members(db):
    return db.get_total_member_count()

def members_with_role(db, role_name):
    return db.get_member_count_with_role(role_name)

def human_and_bots(db,wd=False, start_date=None, end_date=None):
    if wd:
        human_count, bot_count = db.get_human_bot_count(start_date, end_date)
    else:
        human_count, bot_count = db.get_human_bot_count()
    return human_count, bot_count

def members_joined_and_left(db, start_date=None, end_date=None):
    return db.get_members_joined_and_left(start_date, end_date)

def member_join_events_across_time(db,start_date=None, end_date=None):
    join_events = db.get_member_join_events_across_time(start_date, end_date)
    join_events_by_date = {}
    for event in join_events:
        date = event['join_date'].date()
        join_events_by_date[date] = join_events_by_date.get(date, 0) + 1
    return join_events_by_date

def active_members(db, start_date=None, end_date=None):
    # Define criteria for active members and fetch count from the database
    return db.get_active_member_count(start_date, end_date)

def channel_activity(db, start_date=None, end_date=None):
    return db.get_channel_message_counts(start_date, end_date)

# Retention Within 7-14 Days
def retention_within_days(db,start_date,end_date):
    return retention_within_seven_to_fourteen_days(db,start_date,end_date)

def get_role_distribution(db):
    distribution = db.get_role_distribution()
    return distribution

def get_roles(db):
    roles = db.get_roles()
    print(f"Roles: {roles}")  # Debug print
    return roles

def get_joined_since_date(db,start=None,end=None):
    joined_count = db.get_joined_since(start,end)
    return joined_count

def get_join_and_leave_stats(db,start_date=None, end_date=None):
    joined_members = db.get_joined_since(start_date, end_date)
    current_members = db.get_current_members(start_date, end_date)
    db_left_members = db.get_members_left()
    left_count = joined_members-current_members

    if db_left_members > left_count:
        return joined_members, db_left_members
    else:
        return joined_members, left_count

def get_joined_across_time(db,start_date, end_date, granularity):
    welcome_messages = db.get_welcome_messages_between_dates(start_date, end_date)
    data = pd.DataFrame(welcome_messages, columns=['member_id', 'timestamp'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True, errors='coerce')
    data.set_index('timestamp', inplace=True)

    # Resample based on the specified granularity
    if granularity == 'minute':
        joined_counts = data.resample('T').count()
    elif granularity == 'half_hour':
        joined_counts = data.resample('30T').count()
    elif granularity == 'hour':
        joined_counts = data.resample('H').count()
    elif granularity == 'day':
        joined_counts = data.resample('D').count()
    elif granularity == 'week':
        joined_counts = data.resample('W').count()
    elif granularity == 'month':
        joined_counts = data.resample('M').count()
    else:
        raise ValueError("Invalid granularity")

    joined_counts = joined_counts.rename(columns={'member_id': 'joined_count'})
    return joined_counts


def get_messages_activity_line(db,start_date,end_date,granularity):
    data = db.get_message_activity_by_channel(start_date,end_date)
    df = pd.DataFrame(data, columns=['channel_name', 'message_count', 'timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')

    if granularity == 'minute':
        df.set_index('timestamp', inplace=True)
        df = df.groupby(['channel_name', pd.Grouper(freq='T')]).sum().reset_index()
    elif granularity == 'half_hour':
        df.set_index('timestamp', inplace=True)
        df = df.groupby(['channel_name', pd.Grouper(freq='30T')]).sum().reset_index()
    elif granularity == 'hour':
        df.set_index('timestamp', inplace=True)
        df = df.groupby(['channel_name', pd.Grouper(freq='H')]).sum().reset_index()
    elif granularity == 'day':
        df.set_index('timestamp', inplace=True)
        df = df.groupby(['channel_name', pd.Grouper(freq='D')]).sum().reset_index()
    elif granularity == 'week':
        df.set_index('timestamp', inplace=True)
        df = df.groupby(['channel_name', pd.Grouper(freq='W')]).sum().reset_index()
    elif granularity == 'month':
        df.set_index('timestamp', inplace=True)
        df = df.groupby(['channel_name', pd.Grouper(freq='M')]).sum().reset_index()
    else:
        raise ValueError("Invalid granularity")
    return df

def get_message_activity_bar(db,start_date,end_date,top_n):
    data = db.get_top_channels(start_date,end_date,top_n)
    return pd.DataFrame(data, columns=['channel_name', 'message_count'])

def retention_join_leave(db, start_date=None, end_date=None):
    # Calculate the number of members who joined and left within the given time period
    new_members,left_members = get_join_and_leave_stats(db,start_date, end_date)

    # Calculate the retention percentage
    if new_members:
        retention_percentage = ((new_members - left_members) / new_members) * 100
        return retention_percentage
    else:
        return 0
