#!/usr/bin/env python3.11

from pathlib import Path
import discord
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger('BotC')

class Database:
    def __init__(self, database_path: Path, guild: discord.Guild) -> None:
        self.database_path = database_path
        self.guild = guild
        self.guild_id = guild.id
        self.guild_name = guild.name
        self.create_database()
        self.database = self.load_database()
        self.get_state()

    def create_database(self):
        """
        Create database file if it doesn't exist.
        """
        if not self.database_path.exists():
            self.database_path.write_text('{}')

    def load_database(self):
        """
        Load the database from the database file.
        """
        with open(self.database_path, 'r') as f:
            return json.load(f)
        
    def save_database(self):
        """
        Save the database to the database file.
        """
        with open(self.database_path, 'w') as f:
            json.dump(self.database, f, indent=2)
        logger.info(f'saved database for {self.guild_name} to: {self.database_path.absolute()}')

    def get_state(self):
        """
        Save guild information to the database and save to the database file.
        """
        logger.info(f'getting state for {self.guild_name}')
        self.database[self.guild_name] = {
            'last_cached': datetime.now().strftime('%d-%m-%YT%H:%M:%S'),
            'categories': {categorie.name: categorie.id for categorie in self.guild.categories},
            'created_at': self.guild.created_at.strftime('%d-%m-%YT%H:%M:%S'),
            'default_role': self.guild.default_role.name,
            'description': self.guild.description,
            'id': self.guild_id,
            'name': self.guild_name,
            'owner': self.guild.owner.name if self.guild.owner else None,
            'roles': {role.name: role.id for role in self.guild.roles},
            'system_channel': self.guild.system_channel.name if self.guild.system_channel else None,
            'text_channels': [text_channel.name for text_channel in self.guild.text_channels],
            'voice_channels': {voice_channel.name: voice_channel.id for voice_channel in self.guild.voice_channels},
            'members': {member.name: member.id for member in self.guild.members}
            }
        self.save_database()

    def check_cache(self):
        """
        Check if the guild has been cached within the last minute.
        """
        logger.info(f'checking cache for {self.guild_name}')
        now = datetime.now()
        last_cached = datetime.strptime(self.database[self.guild_name]['last_cached'], '%d-%m-%YT%H:%M:%S')
        delta: timedelta = now - last_cached
        if delta.seconds > 60:
            logger.info(f'cache older than 1 minute ({delta.seconds}), renewing state for {self.guild_name}')
            self.get_state()
            return
        logger.info(f'cache is up to date for {self.guild_name} {delta.seconds}s old')