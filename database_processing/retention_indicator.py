from database.database import Database
from datetime import datetime, timedelta

def retention_within_seven_to_fourteen_days(db,start_date,end_date):
    # Calculate the number of members who joined between 7 and 14 days ago
    revisit_count = db.get_member_back_7_14(start_date,end_date)
    new_members = db.get_joined_since(start_date,end_date)

    # Calculate the proportion of revisited members
    if new_members:
        retention_rate = (revisit_count / new_members) * 100
        return retention_rate
    else:
        return 0
