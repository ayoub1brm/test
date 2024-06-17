import discord
from discord.ext import commands
from database.database import Database
from datetime import datetime
import asyncio
import pytz
import re

class DiscordBot(commands.Bot):
    def __init__(self, command_prefix, intents, db):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.db = db
        self.tz = pytz.timezone('Europe/Paris')

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.update_initial_data()
        self.loop.create_task(self.update_server_data())
    
    async def update_initial_data(self):
        for guild in self.guilds:
            latest_member_joined_at = self.db.get_latest_member_joined_at()
    
            for role in guild.roles:
                role_data = (role.id, role.name)
                self.db.insert_role(role_data)
            for channel in guild.channels:
                self.db.insert_channel(channel.id, channel.name)
            # Insert new members and roles
            for member in guild.members:
                joined_at = member.joined_at.astimezone(self.tz) if member.joined_at else None
                if not latest_member_joined_at or (joined_at and joined_at > latest_member_joined_at.astimezone(self.tz)):
                    for role in member.roles:
                        member_data = (
                            member.id, member.name, member.discriminator,
                            joined_at, None, int(member.bot), str(member.status),
                            self.get_role_id(role)
                        )
                        self.db.insert_member(member_data)
            
            # Fetch and insert new messages by channel
            bienvenue_channel_pattern = re.compile(r"bienvenue", re.IGNORECASE)
            for channel in guild.text_channels:
                latest_message_id = self.db.get_latest_message_id_for_channel(channel.id)
                after = discord.Object(id=latest_message_id) if latest_message_id else None
                if bool(bienvenue_channel_pattern.search(channel.name)):
                    async for message in channel.history(limit=None, after=after):
                        created_at = message.created_at.astimezone(self.tz)
                        welcome_message_data = (
                            message.id, message.mentions[0].id if message.mentions else None, created_at
                        )
                        self.db.insert_welcome_message(welcome_message_data)
                else:
                    async for message in channel.history(limit=None, after=after):
                        created_at = message.created_at.astimezone(self.tz)
                        message_data = (
                            message.id, message.channel.id, f'{channel.type}', message.author.id,
                            created_at
                        )
                        self.db.insert_message(message_data)
    
            for channel in guild.voice_channels:
                latest_message_id = self.db.get_latest_message_id_for_channel(channel.id)
                after = discord.Object(id=latest_message_id) if latest_message_id else None
                async for message in channel.history(limit=None, after=after):
                    created_at = message.created_at.astimezone(self.tz)
                    message_data = (
                        message.id, message.channel.id, f'{channel.type}', message.author.id,
                        created_at
                    )
                    self.db.insert_message(message_data)
    
    async def on_member_join(self, member):    
        joined_at = datetime.now(self.tz)
        for role in member.roles:
            member_data = (
                member.id, member.name, member.discriminator, joined_at,
                None, int(member.bot), str(member.status), self.get_role_id(role)
            )
            self.db.insert_member(member_data)
    
   
    async def on_member_remove(self, member):
        leave_date = datetime.now(self.tz)
        self.db.update_member_leave_date(member.id, leave_date)
    
    async def on_voice_state_update(self, member, before, after):
        now = datetime.now(self.tz)
        if before.channel != after.channel:
            if after.channel is not None:
                self.db.insert_voice_activity((member.id, after.channel.id, now, None))
            if before.channel is not None:
                self.db.update_voice_activity_end_time(member.id, now)
        if after.self_stream and not before.self_stream:
            self.db.insert_stream(member.id, after.channel.id, now)
        elif not after.self_stream and before.self_stream:
            self.db.update_stream_end_time(member.id, before.channel.id, now)
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        created_at = message.created_at.astimezone(self.tz)
        bienvenue_channel_pattern = re.compile(r"bienvenue", re.IGNORECASE)
        if bool(bienvenue_channel_pattern.search(message.channel.name)):
            welcome_message_data = (
                message.id, message.author.id, created_at
            )
            self.db.insert_welcome_message(welcome_message_data)
        else:
            message_data = (
                message.id, message.channel.id, f'{message.channel.type}', message.author.id,
                created_at
            )
            self.db.insert_message(message_data)

        # Insert welcome message if it's from the "bienvenue" channel


    async def on_presence_update(self,before,after):
        if before.status != after.status:
            activity_status = str(after.status)
            self.db.update_member_activity_status(after.id, activity_status)

    
    def get_role_id(self, role):
        cursor = self.db.execute('SELECT role_id FROM Roles WHERE role_name = ?', (role.name,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    async def update_server_data(self):
        while True:
            await self.update_initial_data()
            await asyncio.sleep(60)

def setup_discord_bot(token):
    db = Database('discord_bot.db')
    db.create_tables()
    intents = discord.Intents.all()
    bot = DiscordBot(command_prefix='!', intents=intents, db=db)
    bot.run(token)

