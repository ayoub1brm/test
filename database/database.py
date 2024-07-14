__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import sqlite3
from datetime import datetime, timedelta, time
from threading import Lock

class Database:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize(*args, **kwargs)
            return cls._instance

    def _initialize(self, db_path):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL;')
        return conn

    def execute(self, query, params=(), retries=5):
        for i in range(retries):
            try:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    time.sleep(2 ** i)  # Exponential backoff
                else:
                    raise
            except Exception as e:
                print(f"Error executing query: {e}")
                raise


    def create_tables(self):
        self.execute('''
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
        self.execute('''
            CREATE TABLE IF NOT EXISTS Roles (
                role_id INTEGER PRIMARY KEY,
                role_name TEXT
            )
        ''')
        self.execute('''
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
        self.execute('''
            CREATE TABLE IF NOT EXISTS Messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                channel_type TEXT,
                member_id INTEGER,
                timestamp DATETIME,
                FOREIGN KEY (channel_id) REFERENCES Channels(channel_id),
                FOREIGN KEY (member_id) REFERENCES Members(member_id)
            )
        ''')
        self.execute('''
            CREATE TABLE IF NOT EXISTS WelcomeMessages (
                message_id INTEGER PRIMARY KEY,
                member_id INTEGER,
                timestamp DATETIME
            )
        ''')
        self.execute('''
            CREATE TABLE IF NOT EXISTS Channels (
                channel_id INTEGER PRIMARY KEY,
                channel_name TEXT
            )
        ''')


    def insert_member(self, member_data):
        self.execute('''
             INSERT INTO Members (member_id, username, discriminator, join_date, leave_date, is_bot, activity_status, role_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', member_data)

    def insert_role(self, role_data):
        self.execute('''
            INSERT OR IGNORE INTO Roles (role_id, role_name)
            VALUES (?, ?)
        ''', role_data)

    def insert_voice_activity(self, activity_data):
        self.execute('''
            INSERT INTO VoiceActivity (member_id, channel_id, start_time, end_time)
            VALUES (?, ?, ?, ?)
        ''', activity_data)

    def insert_message(self, message_data):
        self.execute('''
            INSERT OR IGNORE INTO Messages (message_id, channel_id, channel_type, member_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', message_data)
    
    def insert_welcome_message(self, message_data):
        self.execute('''
            INSERT OR IGNORE INTO WelcomeMessages (message_id, member_id, timestamp)
            VALUES (?, ?, ?)
        ''', message_data)
    
    def insert_channel(self, channel_id, channel_name):
        self.execute('''
            INSERT OR IGNORE INTO Channels (channel_id, channel_name)
            VALUES (?, ?)
        ''', (channel_id, channel_name))

    def get_channels(self):
        cursor = self.execute('SELECT channel_id, channel_name FROM Channels')
        return cursor.fetchall()

    def update_member_leave_date(self, member_id, leave_date):
        self.execute('''
            UPDATE Members SET leave_date = ? WHERE member_id = ?
        ''', (leave_date, member_id))

    def update_voice_activity_end_time(self, member_id, end_time):
        self.execute('''
            UPDATE VoiceActivity SET end_time = ? WHERE member_id = ? AND end_time IS NULL
        ''', (end_time, member_id))
    
    def update_member_activity_status(self,member_id,activity_status):
        # Update activity status for the member
        self.execute('''
                UPDATE Members
                SET activity_status = ?
                WHERE member_id = ?
            ''', (activity_status, member_id))

    def has_data(self):
        cursor = self.execute("SELECT * FROM Members LIMIT 1")
        return bool(cursor.fetchone())

    def get_total_member_count(self):
        cursor = self.execute('''
            SELECT COUNT(*) FROM (SELECT * FROM Members GROUP BY member_id) WHERE leave_date is NULL AND is_bot = 0
        ''')
        return cursor.fetchone()[0]
    
    def get_role_distribution(self):
        cursor = self.execute('''
            SELECT Roles.role_name, COUNT(Members.member_id) 
            FROM Members 
            JOIN Roles ON Members.role_id = Roles.role_id
            WHERE Members.is_bot = 0
            GROUP BY Roles.role_name
        ''')
        return cursor.fetchall()

    def get_member_count_with_role(self, role_name):
        query = '''
            SELECT COUNT(*) FROM Members
            JOIN Roles ON Members.role_id = Roles.role_id
            WHERE Roles.role_name = ? AND Members.leave_date is NULL AND Members.is_bot = 0
        '''
        params = [role_name]
        cursor = self.execute(query, params)
        return cursor.fetchone()[0]

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
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def get_welcome_messages_between_dates(self, start_date=None, end_date=None):
        params = []
        query = '''
            SELECT member_id, timestamp FROM WelcomeMessages
        '''
        if start_date and end_date:
            params = [start_date, end_date]
            query += '''WHERE timestamp BETWEEN ? AND ?'''
        cursor = self.execute(query,params)
        return cursor.fetchall()
    
    def get_current_members(self,start=None,end=None):
        params = []
        query = '''
            SELECT COUNT(member_id) FROM (SELECT * FROM Members GROUP BY member_id)
            WHERE leave_date IS NULL
        '''
        if start and end:
            params = [start,end]
            query += '''AND join_date BETWEEN ? and ?'''
        cursor = self.execute(query,params)
        return cursor.fetchone()[0]

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
        cursor = self.execute(query, params)
        return cursor.fetchone()[0]

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
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def get_channel_message_counts(self, start_date=None, end_date=None):
        query = '''
            SELECT channel_id, COUNT(*) AS message_count
            FROM Messages
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY channel_id
        '''
        cursor = self.execute(query, (start_date, end_date))
        return dict(cursor.fetchall())
    
    def get_joined_since(self,start=None,end=None):
        query = '''
            SELECT COUNT(member_id) FROM WelcomeMessages
        '''
        params = []
        if start and end:
            query += ' WHERE timestamp BETWEEN ? AND ?'
            params.extend([start, end])
        cursor = self.execute(query, params)
        return cursor.fetchone()[0]

    def get_latest_message_id_for_channel(self, channel_id):
        cursor = self.execute('''
            SELECT message_id 
            FROM Messages 
            WHERE channel_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (channel_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_roles(self):
        cursor = self.execute('SELECT role_name FROM Roles')
        return [row[0] for row in cursor.fetchall()]
    
    def get_message_activity_by_channel(self,start_date=None, end_date=None):
        query = '''
            SELECT Channels.channel_name, COUNT(*) AS message_count, timestamp AS date
            FROM Messages JOIN Channels ON Channels.channel_id = Messages.channel_id
            '''
        params = []
        if start_date and end_date:
            query += ''' WHERE timestamp BETWEEN ? AND ?'''
            params = [start_date,end_date]
        query +=''' GROUP BY Channels.channel_name, date
                '''
        cursor = self.execute(query, params)
        return cursor.fetchall()

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
        cursor = self.execute(query,params)
        return cursor.fetchall()
    
    def get_active_members(self,role_id=None):
        if role_id:
            cursor = self.execute(f"SELECT COUNT(*) FROM (SELECT * FROM Members WHERE role_id = {role_id} GROUP BY member_id HAVING is_bot=0) WHERE activity_status != \"offline\" AND leave_date is NULL")
        else:
            cursor = self.execute('SELECT COUNT(*) FROM (SELECT * FROM Members GROUP BY member_id HAVING is_bot=0) WHERE activity_status != \"offline\" AND leave_date is NULL ')            
        result = cursor.fetchone()[0]
        return result

    def get_latest_member_joined_at(self):
        cursor = self.execute('SELECT MAX(join_date) FROM Members')
        result = cursor.fetchone()[0]
        if result:
            return datetime.fromisoformat(result)
        return None

    def get_latest_message_timestamp(self):
        cursor = self.execute('SELECT MAX(timestamp) FROM Messages')
        return cursor.fetchone()[0]

    def get_latest_voice_activity_join_time(self):
        cursor = self.execute('SELECT MAX(start_time) FROM VoiceActivity')
        return cursor.fetchone()[0]
    
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
        cursor = self.execute(query,params)
        return cursor.fetchone()[0]
