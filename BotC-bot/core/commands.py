#!/usr/bin/env python3.11

# commands.py

import discord
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.BotC_bot import BotC

logger = logging.getLogger('BotC')

async def process_barnie_command(message: discord.Message):
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

async def process_c4rrotz_command(message: discord.Message):
    """
    Process the "c4rrotz" command and send a c4rrotz string in the channel.
    """
    c4rrotz_string = '''
    ```
      /|\\
     |||||
     |||||
 /\  |||||
|||| |||||
|||| |||||  /\\
|||| ||||| ||||
 \|`-'|||| ||||
  \__ |||| ||||
     ||||`-'|||
     |||| ___/
     |||||
     |||||
-----------------
```
'''

    await message.channel.send(c4rrotz_string)

async def process_linda_command(message: discord.Message):
    """
    Process the "linda" command and send a linda string in the channel.
    """
    linda_string = """
    ```
                 .88888888:.
                88888888.88888.
              .8888888888888888.
              888888888888888888
              88' _`88'_  `88888
              88 88 88 88  88888
              88_88_::_88_:88888
              88:::,::,:::::8888
              88`:::::::::'`8888
             .88  `::::'    8:88.
            8888            `8:888.
          .8888'             `888888.
         .8888:..  .::.  ...:'8888888:.
        .8888.'     :'     `'::`88:88888
       .8888        '         `.888:8888.
      888:8         .           888:88888
    .888:88        .:           888:88888:
    8888888.       ::           88:888888
    `.::.888.      ::          .88888888
   .::::::.888.    ::         :::`8888'.:.
  ::::::::::.888   '         .::::::::::::
  ::::::::::::.8    '      .:8::::::::::::.
 .::::::::::::::.        .:888:::::::::::::
 :::::::::::::::88:.__..:88888:::::::::::'
  `'.:::::::::::88888888888.88:::::::::'
        `':::_:' -- '' -'-' `':_::::'`
```
"""
    await message.channel.send(linda_string)

async def process_create_town_command(client: 'BotC', message: discord.Message, arguments: list[str]):
    """
    Process the "create town" command and create a new town category channel.
    """
    town_name = arguments[2]
    guild_name = message.guild.name
    database = client.databases[guild_name]
    for category_name, category_id in database[guild_name]['categories'].items():
        if category_name.lower() == town_name.lower():
            logger.warning(f'Town with name "{town_name}" already exists, ignoring command')
            await message.channel.send(f'A town with the name "{town_name}" already exists.')
            return
    await message.channel.send(f'Creating town "{town_name}"')
    await message.guild.create_category_channel(town_name)
    logger.info(f'Created town "{town_name}"')
    database.get_state()

async def check_member_for_story_teller_role(message: discord.Message):
    """
    Check if a member has the "Storyteller" role.
    """
    member = message.author
    for role in member.roles:
        if role.name == 'Storyteller':
            return True
    return False

async def process_night_command(client: 'BotC', message: discord.Message):
    """
    Process the "night" command and move members to the night phase voice channels.
    """
    if not await check_member_for_story_teller_role(message):
        logger.warning(f'User {message.author.name} does not have role: Storyteller!')
        await message.channel.send(f'User {message.author.name} does not have role: Storyteller!')
        return
    guild = message.guild
    database = client.databases[guild.name]
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
    
    logger.info(f'Moving {len(members_to_move)} members to the night phase')
    member: discord.Member
    members_not_moved = []
    for member in members_to_move:
        try:
            channel_to_move_to = channels_to_move_to.pop()
            await member.move_to(channel_to_move_to)
            logger.info(f'Moved {member.name} to {channel_to_move_to}')
        except discord.errors.Forbidden:
            logger.error(f'Could not move {member.name}, got 403 forbidden, bot has unsificient permissions')
            members_not_moved.append(member)
    if members_not_moved:
        member_names = ', '.join([member.name for member in members_not_moved])        
        await message.channel.send(f'Could not move [{member_names}], bot has unsificient permissions')
        logger.error(f'Could not move [{member_names}], bot has unsificient permissions')

async def process_day_command(client: 'BotC', message: discord.Message):
    """
    Process the "day" command and move members to the town square voice channel.
    """
    if not await check_member_for_story_teller_role(message):
        await message.channel.send(f'User {message.author.name} does not have role: Storyteller!')
        return
    guild = message.guild
    database = client.databases(guild.name)
    guild_database = database[guild.name]
    channel_dict = guild_database['voice_channels']
    channel_id_to_move_to = channel_dict['Town Square (main game)']
    channel_to_move_to = guild.get_channel(channel_id_to_move_to)
    members_already_in_channel_to_move_to = {member.name for member in channel_to_move_to.members}

    for voice_channel in guild.voice_channels:
        for member in voice_channel.members:
            if member.name in members_already_in_channel_to_move_to:
                logger.info(f'Member {member.name} already in {channel_to_move_to.name}, skipping')
                continue
            await member.move_to(channel_to_move_to)
            logger.info(f'Moved {member.name} to {channel_to_move_to}')