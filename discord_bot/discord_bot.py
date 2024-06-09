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
            latest_message_timestamp = self.db.get_latest_message_timestamp()

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
                            joined_at, None, int(member.bot), "active",
                            self.get_role_id(role)
                        )
                        self.db.insert_member(member_data)

            # Fetch and insert new messages by channel
            for channel in guild.text_channels:
                async for message in channel.history(limit=None, after=latest_message_timestamp):
                    created_at = message.created_at.astimezone(self.tz)
                    message_data = (
                        message.id, message.channel.id, f'{channel.type}', message.author.id,
                        message.content, created_at
                    )
                    self.db.insert_message(message_data)

            for channel in guild.voice_channels:
                async for message in channel.history(limit=None, after=latest_message_timestamp):
                    created_at = message.created_at.astimezone(self.tz)
                    message_data = (
                        message.id, message.channel.id, f'{channel.type}', message.author.id,
                        message.content, created_at
                    )
                    self.db.insert_message(message_data)

            bienvenue_channel_pattern = re.compile(r"bienvenue", re.IGNORECASE)
            for channel in guild.text_channels:
                if bienvenue_channel_pattern.search(channel.name):
                    async for message in channel.history(limit=None, after=latest_message_timestamp):
                        created_at = message.created_at.astimezone(self.tz)
                        welcome_message_data = (
                            message.id, message.mentions[0].id if message.mentions else None, message.content, created_at
                        )
                        self.db.insert_welcome_message(welcome_message_data)

    async def on_member_join(self, member):
        guild_invites = await member.guild.invites()
        current_invites = {invite.code: invite.uses for invite in guild_invites}

        db_invites = dict(self.db.get_all_invites())
        used_invite = None

        for code, uses in current_invites.items():
            if code in db_invites and uses > db_invites[code]:
                used_invite = code
                break

        if used_invite:
            invite = next((inv for inv in guild_invites if inv.code == used_invite), None)
            if invite:
                created_at = invite.created_at.astimezone(self.tz)
                self.db.insert_invite(invite.code, invite.uses, invite.inviter.id, created_at)
                self.db.update_invite_uses(invite.code, invite.uses)

        joined_at = datetime.now(self.tz)
        member_data = (
            member.id, member.name, member.discriminator, joined_at,
            None, int(member.bot), "active", self.get_role_id(member.roles[0]) if member.roles else None
        )
        self.db.insert_member(member_data)

    async def on_invite_create(self, invite):
        created_at = invite.created_at.astimezone(self.tz)
        self.db.insert_invite(invite.code, invite.uses, invite.inviter.id, created_at)

    async def on_invite_delete(self, invite):
        self.db.delete_invite(invite.code)

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
        message_data = (
            message.id, message.channel.id, f'{message.channel.type}', message.author.id,
            message.content, created_at
        )
        self.db.insert_message(message_data)

        # Insert welcome message if it's from the "bienvenue" channel
        bienvenue_channel_pattern = re.compile(r"bienvenue", re.IGNORECASE)
        if bienvenue_channel_pattern.search(message.channel.name):
            welcome_message_data = (
                message.id, message.author.id, message.content, created_at
            )
            self.db.insert_welcome_message(welcome_message_data)

    async def on_reaction_add(self, reaction, user):
        created_at = datetime.now(self.tz)
        reaction_data = (
            reaction.message.id, user.id, str(reaction.emoji), created_at
        )
        self.db.insert_reaction(*reaction_data)

    def get_role_id(self, role):
        self.db.cursor.execute('SELECT role_id FROM Roles WHERE role_name = ?', (role.name,))
        result = self.db.cursor.fetchone()
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
