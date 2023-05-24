#!/usr/bin/env python3.11

import logging
from typing import Any
import discord
from discord.flags import Intents
from core.commands import (
    process_barnie_command,
    process_create_town_command,
    process_night_command,
    process_day_command,
    process_c4rrotz_command,
)
from pathlib import Path
import json
from utils.log import get_logger

logger = logging.getLogger('BotC')


class BotC(discord.Client):
    def __init__(self, *, intents: Intents, database_dir: Path, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.database_dir = database_dir

    def create_databases(self):
        """
        Create databases for guilds that do not have one.
        """
        for database_path in self.database_paths.values():
            if not database_path.exists():
                database_path.write_text('{}')

    def save_database(self, guild_id: int, database: dict):
        """
        Save the guild's database to a file.
        """
        database_path = self.database_paths[guild_id]
        with open(database_path, 'w') as f:
            json.dump(database, f, indent=2)

    def load_database(self, guild_id: int):
        """
        Load the guild's database from a file.
        """
        database_path = self.database_paths[guild_id]
        with open(database_path, 'r') as f:
            return json.load(f)

    def save_guild(self, guild_id: int):
        """
        Save guild information to the guild's database.
        """
        database = self.load_database(guild_id)
        guild = self.guilds_dict[guild_id]
        database[guild.name] = {
            'categories': {categorie.name: categorie.id for categorie in guild.categories},
            'created_at': guild.created_at.strftime('%d-%m-%YT%H:%M:%S'),
            'default_role': guild.default_role.name,
            'description': guild.description,
            'id': guild.id,
            'name': guild.name,
            'owner': guild.owner.name if guild.owner else None,
            'roles': {role.name: role.id for role in guild.roles},
            'system_channel': guild.system_channel.name if guild.system_channel else None,
            'text_channels': [text_channel.name for text_channel in guild.text_channels],
            'voice_channels': {voice_channel.name: voice_channel.id for voice_channel in guild.voice_channels},
            'members': {member.name: member.id for member in guild.members}
            }
        self.save_database(guild_id, database)
        logger.info(f'saved guild {guild.name}({guild.id}) to: {self.database_paths[guild_id].absolute()}')


    async def on_ready(self):
        """
        Event handler called when the bot has successfully connected to Discord.
        """
        logger.info(f'Logged on as {self.user}!')
        self.database_paths = {guild.id: self.database_dir / f'{guild.name}-{guild.id}.json' for guild in self.guilds}
        self.guilds_dict = {guild.id: guild for guild in self.guilds}
        self.create_databases()
        for guild in self.guilds:
            self.save_guild(guild.id)

    async def on_message(self, message):
        """
        Event handler called when a new message is received.
        """
        if message.author == self.user:
            return

        logger.info(f'Message from {message.author}: {message.content}')

        message_content: str = message.content

        if message_content.startswith('/'):
            command_string = message_content[1:]
            arguments = command_string.split(' ')

            # Process commands using pattern matching (Python 3.10+)
            match arguments[0]:
                case 'barnie':
                    await process_barnie_command(message)

                case 'create':
                    match arguments[1]:
                        case 'town':
                            await process_create_town_command(self, message, arguments)

                case 'night':
                    await process_night_command(self, message)

                case 'day':
                    await process_day_command(self, message)

                case 'c4rrotz':
                    await process_c4rrotz_command(message)
