from logger import logger
import discord
import asyncio
import time
from utils import is_owner
from discord import app_commands
from database import Database


class Timer:
    def __init__(self, time_to_sleep: int, channel_to_notify: discord.TextChannel, day_category: discord.CategoryChannel, user_to_ignore: discord.User, channel_to_move_to: discord.VoiceChannel) -> None:
        self.time_to_sleep = time_to_sleep
        self.cancelled = False
        self.channel_to_notify = channel_to_notify
        self.day_category = day_category
        self.user_to_ignore = user_to_ignore
        self.channel_to_move_to = channel_to_move_to

    async def run(self):
        while self.time_to_sleep > 0 and not self.cancelled:
            logger.info(f'Sleeping for another second... {self.time_to_sleep} left')
            if self.time_to_sleep % 30 == 0:
                logger.info(f'Notifing {self.channel_to_notify.name}')
                await self.channel_to_notify.send(content=f'You have {self.time_to_sleep / 60:.1f} minutes before voting!', delete_after=30)
            await asyncio.sleep(1)
            self.time_to_sleep -= 1
        await self.finish()
    
    async def cancel(self):
        self.cancelled = True
        await self.channel_to_notify.send(content=f'Timer was cancelled!', delete_after=10)
        logger.warning(f'Timer was cancelled!')

    async def finish(self):
        if self.cancelled:
            return
        for channel in self.day_category.voice_channels:
            if channel == self.channel_to_move_to:
                continue
            for member in channel.members:
                if member == self.user_to_ignore:
                    continue
                await member.move_to(self.channel_to_move_to)

class GameControls(discord.ui.View):

    @discord.ui.button(label='Day', style=discord.ButtonStyle.success)
    async def day(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction, button.view.id):
            return
        guild = interaction.guild
        database = Database(guild)
        game_owner = interaction.user.display_name
        game: dict = database.games[game_owner]
        button.label = 'Moving players...'
        await interaction.response.edit_message(view=self)
        town_square_channel = guild.get_channel(game["town_square_channel"][0])
        night_category = guild.get_channel(game["night_category"][0])
        for channel in night_category.voice_channels:
            channel_name = channel.name
            if channel_name == town_square_channel.name:
                continue
            for member in channel.members:
                if member.display_name == game_owner:
                    continue
                await member.move_to(town_square_channel)

        button.label = 'Day'
        await interaction.followup.edit_message(interaction.message.id, view=self)

    @discord.ui.button(label='Night', style=discord.ButtonStyle.gray)
    async def night(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction, button.view.id):
            return
        game_owner = interaction.user.display_name
        guild = interaction.guild
        database = Database(guild)
        game = database.games[game_owner]
        button.label = 'Moving players...'
        await interaction.response.edit_message(view=self)
        town_square_channel = guild.get_channel(game["town_square_channel"][0])
        night_category = guild.get_channel(game["night_category"][0])
        night_channels = [channel for channel in night_category.voice_channels]
        for member in town_square_channel.members:
            if member.display_name == game_owner:
                continue
            await member.move_to(night_channels.pop(0))

        button.label = 'Night'
        await interaction.followup.edit_message(interaction.message.id, view=self)

    @discord.ui.button(label='Cancel timer', style=discord.ButtonStyle.red)
    async def cancel_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        button_view = button.view
        if not is_owner(interaction, button_view.id):
            return
        game_owner = interaction.user.display_name
        guild = interaction.guild
        database = Database(guild)
        timer: Timer = database.timers.get(game_owner)
        if not timer:
            button.label = 'No timer found!'
            await interaction.response.edit_message(view=self)
            time.sleep(3)
            button.label = 'Cancel timer'
            await interaction.followup.edit_message(interaction.message.id, view=self)
            return
        button.label = 'Timer cancelled!'
        await interaction.response.edit_message(view=self)
        await timer.cancel()
        time.sleep(3)
        button.label = 'Cancel timer'
        await interaction.followup.edit_message(interaction.message.id, view=self)
        

    @discord.ui.button(label='Quit game', style=discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        button_view = button.view
        if not is_owner(interaction, button_view.id):
            return
        game_owner = interaction.user
        game_owner_name = game_owner.display_name
        guild = interaction.guild
        database = Database(guild)
        storyteller_role = guild.get_role(database.storyteller_role_id)
        try:
            logger.info(f'Attempting to remove storyteller role from {game_owner_name}')
            await game_owner.remove_roles(storyteller_role)
            logger.info(f'Successfully removed storyteller role from {game_owner_name}')
        except discord.errors.Forbidden:
            logger.error(f'Could not remove storyteller role from {game_owner_name} because user probably has higher privileges')
        button_view.clear_items()
        database.games.pop(game_owner_name)
        await interaction.response.edit_message(content='Game ended', view=self, delete_after=10)

    @discord.ui.select(min_values=1, max_values=1, options=[discord.SelectOption(label=f'{i*0.5} minutes') for i in range(4,27)], placeholder='Select time players have until vote')
    async def timer(self, interaction: discord.Interaction, select: discord.ui.Select):
        select_view: discord.ui.View = select.view
        if not is_owner(interaction, select_view.id):
            return
        game_owner = interaction.user
        game_owner_name = game_owner.display_name
        guild = interaction.guild
        selected_value = select.values[0]
        logger.info(f"{game_owner_name} started a timer of {selected_value} minutes")
        time_to_sleep = float(selected_value.replace(' minutes', '')) * 60
        logger.info(f"I got {time_to_sleep}:.2f seconds to sleep")
        database = Database(guild)
        game = database.games[game_owner_name]
        await interaction.response.send_message(f'Will return players to Town Square after {selected_value} minutes', ephemeral=True, delete_after=3)
        timer = Timer(time_to_sleep, guild.get_channel(game["game_chat_channel"][0]), guild.get_channel(game["day_category"][0]), game_owner, guild.get_channel(game["town_square_channel"][0]))
        database.timers[game_owner] = timer
        children = select_view.children
        for child in children:
            if isinstance(child, discord.ui.Select):
                child.placeholder = 'Select time players have until vote'
                await interaction.followup.edit_message(interaction.message.id, view=select_view)
        await timer.run()
            
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
