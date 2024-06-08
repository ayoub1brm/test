__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()


    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Members (
                member_id INTEGER,
                username TEXT,
                discriminator TEXT,
                join_date DATETIME,
                leave_date DATETIME,
                is_bot INTEGER,
                activity_status TEXT,
                role_id INTEGER,
                FOREIGN KEY (role_id) REFERENCES Roles(role_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Roles (
                role_id INTEGER PRIMARY KEY,
                role_name TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS VoiceActivity (
                activity_id INTEGER PRIMARY KEY,
                member_id INTEGER,
                channel_id INTEGER,
                start_time DATETIME,
                end_time DATETIME,
                FOREIGN KEY (channel_id) REFERENCES Channels(channel_id),
                FOREIGN KEY (member_id) REFERENCES Members(member_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                channel_type TEXT,
                member_id INTEGER,
                message_content TEXT,
                timestamp DATETIME,
                FOREIGN KEY (channel_id) REFERENCES Channels(channel_id),
                FOREIGN KEY (member_id) REFERENCES Members(member_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS WelcomeMessages (
                message_id INTEGER PRIMARY KEY,
                member_id INTEGER,
                message_content TEXT,
                timestamp DATETIME
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Channels (
                channel_id INTEGER PRIMARY KEY,
                channel_name TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Invites (
                code TEXT PRIMARY KEY,
                uses INTEGER,
                inviter_id INTEGER,
                created_at TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def insert_invite(self, code, uses, inviter_id, created_at):
        self.cursor.execute('''
            INSERT OR REPLACE INTO Invites (code, uses, inviter_id, created_at)
            VALUES (?, ?, ?, ?)
        ''', (code, uses, inviter_id, created_at))
        self.conn.commit()

    def update_invite_uses(self, code, uses):
        self.cursor.execute('''
            UPDATE Invites
            SET uses = ?
            WHERE code = ?
        ''', (uses, code))
        self.conn.commit()

    def delete_invite(self, code):
        self.cursor.execute('DELETE FROM Invites WHERE code = ?', (code,))
        self.conn.commit()

    def get_invite_uses(self, code):
        self.cursor.execute('SELECT uses FROM Invites WHERE code = ?', (code,))
        return self.cursor.fetchone()

    def get_all_invites(self):
        self.cursor.execute('SELECT code, uses FROM Invites')
        return self.cursor.fetchall()

    def insert_member(self, member_data):
        self.cursor.execute('''
            INSERT INTO Members (member_id, username, discriminator, join_date, leave_date, is_bot, activity_status, role_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', member_data)
        self.conn.commit()

    def insert_role(self, role_data):
        self.cursor.execute('''
            INSERT INTO Roles (role_id, role_name)
            VALUES (?, ?)
        ''', role_data)
        self.conn.commit()

    def insert_voice_activity(self, activity_data):
        self.cursor.execute('''
            INSERT INTO VoiceActivity (member_id, channel_id, start_time, end_time)
            VALUES (?, ?, ?, ?)
        ''', activity_data)
        self.conn.commit()

    def insert_message(self, message_data):
        self.cursor.execute('''
            INSERT INTO Messages (message_id, channel_id, channel_type, member_id, message_content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', message_data)
        self.conn.commit()
    
    def insert_welcome_message(self, message_data):
        self.cursor.execute('''
            INSERT INTO WelcomeMessages (message_id, member_id, message_content, timestamp)
            VALUES (?, ?, ?, ?)
        ''', message_data)
        self.conn.commit()
    
    def insert_channel(self, channel_id, channel_name):
        self.cursor.execute('''
            INSERT OR IGNORE INTO Channels (channel_id, channel_name)
            VALUES (?, ?)
        ''', (channel_id, channel_name))
        self.conn.commit()

    def get_channels(self):
        self.cursor.execute('SELECT channel_id, channel_name FROM Channels')
        return self.cursor.fetchall()

    def update_member_leave_date(self, member_id, leave_date):
        self.cursor.execute('''
            UPDATE Members SET leave_date = ? WHERE member_id = ?
        ''', (leave_date, member_id))
        self.conn.commit()

    def update_voice_activity_end_time(self, member_id, end_time):
        self.cursor.execute('''
            UPDATE VoiceActivity SET end_time = ? WHERE member_id = ? AND end_time IS NULL
        ''', (end_time, member_id))
        self.conn.commit()

    def has_data(self):
        self.cursor.execute("SELECT * FROM Members LIMIT 1")
        return bool(self.cursor.fetchone())

    def get_total_member_count(self):
        self.cursor.execute('''
            SELECT COUNT(*) FROM (SELECT * FROM Members GROUP BY member_id) WHERE leave_date is NULL AND is_bot = 0
        ''')
        return self.cursor.fetchone()[0]
    
    def get_role_distribution(self):
        self.cursor.execute('''
            SELECT Roles.role_name, COUNT(Members.member_id) 
            FROM Members 
            JOIN Roles ON Members.role_id = Roles.role_id
            WHERE Members.is_bot = 0
            GROUP BY Roles.role_name
        ''')
        return self.cursor.fetchall()

    def get_member_count_with_role(self, role_name):
        query = '''
            SELECT COUNT(*) FROM Members
            JOIN Roles ON Members.role_id = Roles.role_id
            WHERE Roles.role_name = ? AND Members.leave_date is NULL AND Members.is_bot = 0
        '''
        params = [role_name]
        self.cursor.execute(query, params)
        return self.cursor.fetchone()[0]

    def get_human_bot_count(self, start_date=None, end_date=None):
        query = '''
            SELECT 
                SUM(CASE WHEN is_bot = 0 AND leave_date is NULL THEN 1 ELSE 0 END) AS human_count,
                SUM(CASE WHEN is_bot = 1 AND leave_date is NULL THEN 1 ELSE 0 END) AS bot_count
            FROM (SELECT * FROM Members GROUP BY member_id)
        '''
        params = []
        if start_date and end_date:
            query += ' WHERE join_date BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        self.cursor.execute(query, params)
        return self.cursor.fetchone()
    
    def get_welcome_messages_between_dates(self, start_date=None, end_date=None):
        params = []
        query = '''
            SELECT member_id, timestamp FROM WelcomeMessages
        '''
        if start_date and end_date:
            params = [start_date, end_date]
            query += '''WHERE timestamp BETWEEN ? AND ?'''
        self.cursor.execute(query,params)
        return self.cursor.fetchall()
    
    def get_current_members(self,start=None,end=None):
        params = []
        query = '''
            SELECT COUNT(member_id) FROM (SELECT * FROM Members GROUP BY member_id)
            WHERE leave_date IS NULL
        '''
        if start and end:
            params = [start,end]
            query += '''AND join_date BETWEEN ? and ?'''
        self.cursor.execute(query,params)
        return self.cursor.fetchone()[0]

    def get_members_left(self, start_date=None, end_date=None):
        query = '''
            SELECT COUNT(*)
            FROM (SELECT * FROM Members GROUP BY member_id)
            WHERE leave_date is not NULL
        '''
        params = []
        if start_date and end_date:
            query += ' AND leave_date BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        self.cursor.execute(query, params)
        return self.cursor.fetchone()[0]

    def get_member_join_events_across_time(self, start_date=None, end_date=None):
        query = '''
            SELECT join_date, COUNT(*) AS count
            FROM Members
            WHERE join_date IS NOT NULL
        '''
        params = []
        if start_date and end_date:
            query += ' AND join_date BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        query += ' GROUP BY join_date ORDER BY join_date'
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_active_member_count(self, start_date=None, end_date=None):
        query = '''
            SELECT COUNT(DISTINCT member_id) FROM MemberActivity
            WHERE activity_date BETWEEN ? AND ?
        '''
        self.cursor.execute(query, (start_date, end_date))
        return self.cursor.fetchone()[0]

    def get_channel_message_counts(self, start_date=None, end_date=None):
        query = '''
            SELECT channel_id, COUNT(*) AS message_count
            FROM Messages
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY channel_id
        '''
        self.cursor.execute(query, (start_date, end_date))
        return dict(self.cursor.fetchall())
    
    def get_joined_since(self,start=None,end=None):
        query = '''
            SELECT COUNT(member_id) FROM WelcomeMessages
        '''
        params = []
        if start and end:
            query += ' WHERE timestamp BETWEEN ? AND ?'
            params.extend([start, end])
        self.cursor.execute(query, params)
        return self.cursor.fetchone()[0]

    
    def get_roles(self):
        self.cursor.execute('SELECT role_name FROM Roles')
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_message_activity_by_channel(self,start_date=None, end_date=None):
        query = '''
            SELECT Channels.channel_name, COUNT(*) AS message_count, DATE(timestamp) AS date
            FROM Messages JOIN Channels ON Channels.channel_id = Messages.channel_id
            '''
        params = []
        if start_date and end_date:
            query += ''' WHERE timestamp BETWEEN ? AND ?'''
            params = [start_date,end_date]
        query +=''' GROUP BY Channels.channel_name, date
                '''
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_top_channels(self,start_date=None, end_date=None, top_n=None):
        params = []
        query = '''
            SELECT Channels.channel_name, COUNT(*) AS message_count
            FROM Messages JOIN Channels ON Channels.channel_id = Messages.channel_id
        '''
        if start_date and end_date:
            query += ''' WHERE timestamp BETWEEN ? AND ?'''
            params = [start_date,end_date]
        query +=''' GROUP BY Channels.channel_name
            ORDER BY message_count DESC
            '''
        if top_n:
            query += ''' LIMIT ?
                '''
            params.append(top_n)
        self.cursor.execute(query,params)
        return self.cursor.fetchall()

    def get_latest_member_joined_at(self):
        self.cursor.execute('SELECT MAX(join_date) FROM Members')
        return self.cursor.fetchone()[0]

    def get_latest_audit_log_created_at(self):
        self.cursor.execute('SELECT MAX(timestamp) FROM AuditLogs')
        return self.cursor.fetchone()[0]

    def get_latest_message_timestamp(self):
        self.cursor.execute('SELECT MAX(timestamp) FROM Messages')
        return self.cursor.fetchone()[0]

    def get_latest_voice_activity_join_time(self):
        self.cursor.execute('SELECT MAX(start_time) FROM VoiceActivity')
        return self.cursor.fetchone()[0]
    
    def get_member_back_7_14(self,start_date=None,end_date=None):
        params = []
        query = '''SELECT COUNT(*) FROM (SELECT member_id, join_date,MAX(timestamp) AS maximum, MIN(timestamp) AS minimum FROM (SELECT Messages.member_id AS member_id, Messages.timestamp AS timestamp , WelcomeMessages.timestamp AS join_date FROM Messages JOIN WelcomeMessages ON WelcomeMessages.member_id = Messages.member_id
                    '''
        if start_date and end_date:        
            query += ''' WHERE join_date BETWEEN ? AND ? 
                        UNION
                SELECT VoiceActivity.member_id AS member_id, VoiceActivity.start_time AS timestamp , WelcomeMessages.timestamp AS join_date FROM VoiceActivity JOIN WelcomeMessages ON WelcomeMessages.member_id = VoiceActivity.member_id)
                WHERE join_date BETWEEN ? AND ? '''
            params = [start_date,end_date,start_date,end_date]
        else:
            query += '''UNION
            SELECT VoiceActivity.member_id AS member_id, VoiceActivity.start_time AS timestamp , WelcomeMessages.timestamp AS join_date FROM VoiceActivity JOIN WelcomeMessages ON WelcomeMessages.member_id = VoiceActivity.member_id)'''
        
        query += '''GROUP BY member_id
                HAVING maximum BETWEEN datetime(join_date,'+7 days') AND datetime(join_date,'+14 days') OR minimum BETWEEN datetime(join_date,'+7 days') AND datetime(join_date,'+14 days'))'''
        self.cursor.execute(query,params)
        return self.cursor.fetchone()[0]

    def close(self):
        self.conn.close()
