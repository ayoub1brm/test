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
        self.cache = {
            'roles': {},
            'channels': {},
            'messages': {}
        }

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.update_initial_data()
        self.loop.create_task(self.update_server_data())

    async def update_initial_data(self):
        for guild in self.guilds:
            latest_member_joined_at = self.db.get_latest_member_joined_at()
            latest_message_timestamp = self.db.get_latest_message_timestamp()

            await self.batch_insert_roles(guild.roles)
            await self.batch_insert_channels(guild.channels)

            await self.batch_insert_members(guild.members, latest_member_joined_at)

            await self.batch_fetch_messages(guild.text_channels, latest_message_timestamp)
            await self.batch_fetch_messages(guild.voice_channels, latest_message_timestamp)

            bienvenue_channel_pattern = re.compile(r"bienvenue", re.IGNORECASE)
            for channel in guild.text_channels:
                if bienvenue_channel_pattern.search(channel.name):
                    await self.batch_fetch_welcome_messages(channel)

    async def batch_insert_roles(self, roles):
        role_data = [(role.id, role.name) for role in roles]
        await self.db.batch_insert_role(role_data)

    async def batch_insert_channels(self, channels):
        channel_data = [(channel.id, channel.name) for channel in channels]
        await self.db.batch_insert_channel(channel_data)

    async def batch_insert_members(self, members, latest_member_joined_at):
        member_data = []
        for member in members:
            joined_at = member.joined_at.astimezone(self.tz) if member.joined_at else None
            if not latest_member_joined_at or (joined_at and joined_at > latest_member_joined_at.astimezone(self.tz)):
                for role in member.roles:
                    member_data.append((
                        member.id, member.name, member.discriminator,
                        joined_at, None, int(member.bot), "active",
                        self.get_role_id(role)
                    ))
        await self.db.batch_insert_member(member_data)

    async def batch_fetch_messages(self, channels, latest_message_timestamp):
        for channel in channels:
            latest_message_id = self.cache['messages'].get(channel.id)
            after = discord.Object(id=latest_message_id) if latest_message_id else None
            async for message in channel.history(limit=None, after=after):
                created_at = message.created_at.astimezone(self.tz)
                message_data = (
                    message.id, message.channel.id, f'{channel.type}', message.author.id,
                    message.content, created_at
                )
                await self.db.batch_insert_message([message_data])
                self.cache['messages'][channel.id] = message.id

    async def batch_fetch_welcome_messages(self, channel):
        latest_message_id = self.cache['messages'].get(channel.id)
        after = discord.Object(id=latest_message_id) if latest_message_id else None
        async for message in channel.history(limit=None, after=after):
            created_at = message.created_at.astimezone(self.tz)
            welcome_message_data = (
                message.id, message.mentions[0].id if message.mentions else None, message.content, created_at
            )
            await self.db.batch_insert_welcome_message([welcome_message_data])
            self.cache['messages'][channel.id] = message.id

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
                await self.db.batch_insert_invite([(invite.code, invite.uses, invite.inviter.id, created_at)])
                await self.db.batch_update_invite_uses([(invite.code, invite.uses)])

        joined_at = datetime.now(self.tz)
        member_data = (
            member.id, member.name, member.discriminator, joined_at,
            None, int(member.bot), "active", self.get_role_id(member.roles[0]) if member.roles else None
        )
        await self.db.batch_insert_member([member_data])

    async def on_invite_create(self, invite):
        created_at = invite.created_at.astimezone(self.tz)
        await self.db.batch_insert_invite([(invite.code, invite.uses, invite.inviter.id, created_at)])

    async def on_invite_delete(self, invite):
        await self.db.batch_delete_invite([invite.code])

    async def on_member_remove(self, member):
        leave_date = datetime.now(self.tz)
        await self.db.batch_update_member_leave_date([(member.id, leave_date)])

    async def on_voice_state_update(self, member, before, after):
        now = datetime.now(self.tz)
        if before.channel != after.channel:
            if after.channel is not None:
                await self.db.batch_insert_voice_activity([(member.id, after.channel.id, now, None)])
            if before.channel is not None:
                await self.db.batch_update_voice_activity_end_time([(member.id, now)])
        if after.self_stream and not before.self_stream:
            await self.db.batch_insert_stream([(member.id, after.channel.id, now)])
        elif not after.self_stream and before.self_stream:
            await self.db.batch_update_stream_end_time([(member.id, before.channel.id, now)])

    async def on_message(self, message):
        if message.author == self.user:
            return
        created_at = message.created_at.astimezone(self.tz)
        message_data = (
            message.id, message.channel.id, f'{message.channel.type}', message.author.id,
            message.content, created_at
        )
        await self.db.batch_insert_message([message_data])

        # Insert welcome message if it's from the "bienvenue" channel
        bienvenue_channel_pattern = re.compile(r"bienvenue", re.IGNORECASE)
        if bienvenue_channel_pattern.search(message.channel.name):
            welcome_message_data = (
                message.id, message.author.id, message.content, created_at
            )
            await self.db.batch_insert_welcome_message([welcome_message_data])

    async def on_reaction_add(self, reaction, user):
        created_at = datetime.now(self.tz)
        reaction_data = (
            reaction.message.id, user.id, str(reaction.emoji), created_at
        )
        await self.db.batch_insert_reaction([reaction_data])

    def get_role_id(self, role):
        return self.cache['roles'].get(role.name)

    async def update_server_data(self):
        while True:
            await self.update_initial_data()
            await asyncio.sleep(60)

def setup_discord_bot(token):
    db = Database('discord_bot.db')
    db.create_tables()
    intents = discord.Intents.all()
    bot = DiscordBot(command_prefix='', intents=intents, db=db)
    bot.run(token)
