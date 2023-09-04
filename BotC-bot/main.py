#!/usr/bin/env python3.11

import discord
from pathlib import Path
import logging
from core.BotC_bot import BotC
from datetime import datetime
from utils.log import get_logger
import argparse
from core.commands import botc, barnie, c4rrotz, linda

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", type=str, default=None, help="Bot token")
    parser.add_argument("-f", "--tokenfile", default=None, help="Bot token file")
    return parser.parse_args()

def main():
    arguments = parse_args()

    if arguments.tokenfile:
        TOKEN = Path(arguments.tokenfile).absolute().read_text()
    elif arguments.token:
        TOKEN = arguments.token
    else:
        # Check if token file exists
        if not TOKEN_PATH.exists():
            TOKEN_PATH.write_text('DISCORD_TOKEN')
            logger.error(f'No token.txt found! Add your token at {TOKEN_PATH.absolute()} or use the -t or -f option.')
            exit(1)

        # Read token from file
        TOKEN = TOKEN_PATH.read_text()

    # Configure Discord intents
    intents = discord.Intents.default()
    intents.message_content = True

    # Initialize bot
    bot = BotC(intents=intents, database_dir=DATABASE_DIR)
    bot.add_command(botc)
    bot.add_command(barnie)
    bot.add_command(c4rrotz)
    bot.add_command(linda)

    # Run the bot with the provided token
    bot.run(TOKEN)

if __name__ == '__main__':
    # date string
    today = datetime.today().strftime('%d-%m-%Y')
    
    # Set up file paths
    SCRIPT_DIR = Path(__name__).parent
    TOKEN_PATH = SCRIPT_DIR / 'token.txt'
    DATABASE_DIR = SCRIPT_DIR / 'database'
    DATABASE_DIR.mkdir(exist_ok=True)
    LOG_DIR_PATH = SCRIPT_DIR / 'logs'
    LOG_DIR_PATH.mkdir(exist_ok=True)
    LOG_FILE_PATH = LOG_DIR_PATH / f'{today}.log'

    # setup main logger
    logger = get_logger('BotC', LOG_FILE_PATH)

    # Configure discord logger
    discord_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', '%d-%m-%Y %H:%M:%S')
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)

    discord_file_handler = logging.FileHandler(filename=LOG_FILE_PATH)
    discord_file_handler.setFormatter(discord_formatter)
    discord_logger.addHandler(discord_file_handler)

    discord_console_handler = logging.StreamHandler()
    discord_console_handler.setFormatter(discord_formatter)
    discord_console_handler.setLevel(logging.ERROR)
    discord_logger.addHandler(discord_console_handler)
    logging.getLogger('discord.http').setLevel(logging.INFO)
    main()
