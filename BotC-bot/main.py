#!/usr/bin/env python3.11

import discord
from pathlib import Path
import logging
from core.BotC_bot import BotC
from datetime import datetime
import sys


def main():
    # date string
    today = datetime.today().strftime('%d-%m-%Y')
    
    # Set up file paths
    SCRIPT_DIR = Path(__name__).parent
    TOKEN_PATH = SCRIPT_DIR / 'token.txt'
    LOG_DIR_PATH = SCRIPT_DIR / 'logs'
    LOG_DIR_PATH.mkdir(exist_ok=True)
    LOG_FILE_PATH = LOG_DIR_PATH / f'{today}.log'
    DATABASE_DIR = SCRIPT_DIR / 'database'
    DATABASE_DIR.mkdir(exist_ok=True)

    # Configure logging
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    logging.getLogger('discord.http').setLevel(logging.INFO)

    date_format = '%d-%m-%Y %H:%M:%S'
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', date_format)
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Check if token file exists
    if not TOKEN_PATH.exists():
        TOKEN_PATH.write_text('DISCORD_TOKEN')
        logging.error(f'No token.txt found! Created the token.txt file. Add your token at {TOKEN_PATH.absolute()}')
        exit(1)

    # Read token from file
    TOKEN = TOKEN_PATH.read_text()

    # Configure Discord intents
    intents = discord.Intents.default()
    intents.message_content = True

    # Initialize bot client
    client = BotC(intents=intents, logger=logger, database_dir=DATABASE_DIR)

    # Run the bot with the provided token
    client.run(TOKEN, log_handler=None)


if __name__ == '__main__':
    main()
