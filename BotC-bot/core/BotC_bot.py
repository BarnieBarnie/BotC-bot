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
    process_linda_command,
)
from pathlib import Path
from core.database import Database

logger = logging.getLogger('BotC')


class BotC(discord.Client):
    def __init__(self, *, intents: Intents, database_dir: Path, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.database_dir = database_dir


    async def on_ready(self):
        """
        Event handler called when the bot has successfully connected to Discord.
        """
        logger.info(f'Logged on as {self.user}!')
        self.guilds_dict = {guild.id: guild for guild in self.guilds}
        self.databases = {guild.name: Database(self.database_dir / f'{guild.name}.json', guild) for guild in self.guilds}

    async def on_message(self, message: discord.Message):
        """
        Event handler called when a new message is received.
        """
        if message.author == self.user:
            return

        logger.info(f'Message from {message.author}: {message.content}')

        message_content: str = message.content

        # check if this guild is known, if not create a new database
        # for new guilds that invite the bot for the first time
        if message.guild.id not in self.guilds_dict:
            logger.info(f'Guild {message.guild.name} ({message.guild.id}) is not known, creating database for guild')
            self.databases[message.guild.name] = Database(self.database_dir / f'{message.guild.name}.json', message.guild)

        # check if the message is a command
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

                case 'linda':
                    await process_linda_command(message)

        self.databases[message.guild.name].check_cache()
