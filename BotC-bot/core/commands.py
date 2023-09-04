#!/usr/bin/env python3.11

# commands.py

import discord
from discord.ext import commands
from discord.ui import View
from core.buttons import NightButton, DayButton
from utils.helpers import check_member_for_story_teller_role
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.BotC_bot import BotC

logger = logging.getLogger('BotC')

@commands.command('botc')
async def botc(ctx: commands.Context) -> None:
    member = ctx.author
    is_story_teller = await check_member_for_story_teller_role(member)
    disabled = not is_story_teller
    logger.info(f'{member.name} issued the "botc" command, disabled={disabled}, is_story_teller={is_story_teller}')
    view = View()
    view.add_item(NightButton("Night", disabled=disabled))
    view.add_item(DayButton("Day", disabled=disabled))
    await ctx.send("Select an action", view=view)

@commands.command('barnie')
async def barnie(ctx: commands.Context) -> None:
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

    await ctx.channel.send(barnie_string)

@commands.command('c4rrotz')
async def c4rrotz(ctx: commands.Context) -> None:
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

    await ctx.channel.send(c4rrotz_string)

@commands.command('linda')
async def linda(ctx: commands.Context) -> None:
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
    await ctx.channel.send(linda_string)

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