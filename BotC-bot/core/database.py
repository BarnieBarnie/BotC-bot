#!/usr/bin/env python3.11

from pathlib import Path
import discord
import logging

logger = logging.getLogger('BotC')

class Database:
    def __init__(self, database_path: Path, guild: discord.Guild) -> None:
        self.database_path = database_path
        self.guild = guild
        self.guild_id = guild.id
        self.guild_name = guild.name