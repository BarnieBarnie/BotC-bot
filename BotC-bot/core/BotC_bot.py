#!/usr/bin/env python3.11

import logging
from typing import Any
from discord.flags import Intents
from pathlib import Path
from core.database import Database
from discord.ext import commands

logger = logging.getLogger('BotC')


class BotC(commands.Bot):
    def __init__(self, intents: Intents, database_dir: Path) -> None:
        super().__init__(intents=intents, command_prefix='/')
        self.database_dir = database_dir

    async def on_ready(self):
        """
        Event handler called when the bot has successfully connected to Discord.
        """
        logger.info(f'Logged on as {self.user}!')
        self.guilds_dict = {guild.id: guild for guild in self.guilds}
        self.databases = {guild.name: Database(self.database_dir / f'{guild.name}.json', guild) for guild in self.guilds}
