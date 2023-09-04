from discord.enums import ButtonStyle
from discord.ui import Button
import discord
import logging
from discord.ext import commands

logger = logging.getLogger('BotC')

class DayButton(Button):
    def __init__(self, label: str, disabled=True):
        super().__init__(style=ButtonStyle.green, label=label, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        """
        Process the "day" button and move members to the town square voice channel.
        """
        await interaction.response.send_message("Gathering all user to town square...", ephemeral=True)
        guild = interaction.guild
        database = interaction.client.databases[guild.name]
        guild_database = database.database[guild.name]
        channel_dict = guild_database['voice_channels']
        channel_id_to_move_to = channel_dict['Town Square (main game)']
        channel_to_move_to = guild.get_channel(channel_id_to_move_to)
        members_already_in_channel_to_move_to = {member.name for member in channel_to_move_to.members}

        moved_members = []
        for voice_channel in guild.voice_channels:
            for member in voice_channel.members:
                if member.name in members_already_in_channel_to_move_to:
                    logger.info(f'Member {member.name} already in {channel_to_move_to.name}, skipping')
                    continue
                await member.move_to(channel_to_move_to)
                logger.info(f'Moved {member.name} to {channel_to_move_to}')
                moved_members.append(member.name)
        await interaction.followup.send(f'Moved {len(moved_members)} members to {channel_to_move_to.name}')

class NightButton(Button):
    def __init__(self, label, disabled=True):
        super().__init__(style=ButtonStyle.red, label=label, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        """
        Process the "night" button and move members to the Night channels
        """
        await interaction.response.send_message("Sending all members to night channels...", ephemeral=True)
        message = interaction.message
        guild = message.guild
        database = interaction.client.databases[guild.name]
        guild_database = database.database[guild.name]
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
        await interaction.followup.send(f'Moved {len(members_to_move)} members to the night phase channels', ephemeral=True)
        