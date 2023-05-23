#!/usr/bin/env python3.11

# commands.py

import discord
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BotC_bot import BotC


async def process_barnie_command(client: discord.Client, message: discord.Message, logger: logging.Logger):
    """
    Process the "barnie" command and send a barnie string in the channel.
    """
    barnie_string = '''
    ┊╱▔▔▔▔▔╲╭╮
    ╱▂▂╱▔▔▔╲╰━╮
    ▔▏┊┊▋┊▋╰╰╰╯
    ╭▏╱▔▔┊┈╮▕╮
    ╰▏╲▂▂╱┳┃▕╯
    ┊▏┗┳━━╱┃▕┊
    ▔▏┊▔▔▔┊┃╱▔▏
    '''

    await message.channel.send(barnie_string)

async def process_create_town_command(client: 'BotC', message: discord.Message, arguments: list[str], logger: logging.Logger):
    """
    Process the "create town" command and create a new town category channel.
    """
    town_name = arguments[2]
    for channel in client.get_all_channels():
        if not channel.category and channel.name == town_name:
            logger.error(f'Town with name "{town_name}" already exists, ignoring command')
            await message.channel.send(f'Town with name "{town_name}" already exists, skipping..')
            return
    await message.channel.send(f'Creating town "{town_name}"')
    await client.guilds[0].create_category_channel(town_name)

async def check_member_for_story_teller_role(message: discord.Message, logger: logging.Logger):
    """
    Check if a member has the "Storyteller" role.
    """
    member = message.author
    for role in member.roles:
        if role.name == 'Storyteller':
            return True
    return False

async def process_night_command(client: 'BotC', message: discord.Message, logger: logging.Logger):
    """
    Process the "night" command and move members to the night phase voice channels.
    """
    if not await check_member_for_story_teller_role(message, logger):
        await message.channel.send(f'User {message.author.name} does not have role: Storyteller!')
        return
    guild = message.guild
    database = client.load_database(guild.id)
    guild_database = database[guild.name]
    channel_dict = guild_database['voice_channels']
    role_dict = guild_database['roles']
    category_dict = guild_database['categories']
    channel_id_to_move_from = channel_dict['Town Square (main game)']
    channel_to_move_from = guild.get_channel(channel_id_to_move_from)
    role_id_to_move = role_dict['Townsfolk']

    members_to_move = []
    for member in channel_to_move_from.members:
        if member.get_role(role_id_to_move):
            members_to_move.append(member)

    night_phase_category_id = category_dict['Nacht Fase']
    channels_to_move_to = []
    for voice_channel in guild.voice_channels:
        if voice_channel.category_id == night_phase_category_id:
            channels_to_move_to.append(voice_channel)
    
    member: discord.Member
    for member in members_to_move:
        try:
            channel_to_move_to = channels_to_move_to.pop()
            await member.move_to(channel_to_move_to)
            logger.info(f'Moved {member.name} to {channel_to_move_to}')
        except discord.errors.Forbidden:
            logger.error(f'Could not move {member.name}, got 403 forbidden')

async def process_day_command(client: 'BotC', message: discord.Message, logger: logging.Logger):
    """
    Process the "day" command and move members to the town square voice channel.
    """
    if not await check_member_for_story_teller_role(message, logger):
        await message.channel.send(f'User {message.author.name} does not have role: Storyteller!')
        return
    guild = message.guild
    database = client.load_database(guild.id)
    guild_database = database[guild.name]
    channel_dict = guild_database['voice_channels']
    channel_id_to_move_to = channel_dict['Town Square (main game)']
    channel_to_move_to = guild.get_channel(channel_id_to_move_to)

    for voice_channel in guild.voice_channels:
        for member in voice_channel.members:
            await member.move_to(channel_to_move_to)
            logger.info(f'Moved {member.name} from {voice_channel.name}')
