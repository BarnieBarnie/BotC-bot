from logger import logger
import discord
import asyncio
from global_vars import DATABASES, DATABASE_DIR
import time
from utils import is_owner
import json
from discord import app_commands


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
                await self.channel_to_notify.send(content=f'You have {self.time_to_sleep / 60:.1f} minutes before voting!', delete_after=29)
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
        database = DATABASES.get(interaction.user.display_name)
        if not is_owner(interaction, button.view.id):
            return
        if not database.linked_objects:
            button.label = 'No categories or players linked to this game yet! Run /link_to_game'
            await interaction.response.edit_message(view=self)
            time.sleep(1)
            button.label = 'Day'
            await interaction.followup.edit_message(interaction.message.id, view=self)
            return
        button.label = 'Moving players...'
        await interaction.response.edit_message(view=self)
        guild = interaction.guild
        town_square_channel = guild.get_channel(database.town_square[1])
        for channel_data in database.night_category["children"]:
            channel_name, channel_id = channel_data
            if channel_name == town_square_channel.name:
                continue
            channel = guild.get_channel(channel_id)
            for member in channel.members:
                if member.display_name == database.owner:
                    continue
                await member.move_to(town_square_channel)

        button.label = 'Day'
        await interaction.followup.edit_message(interaction.message.id, view=self)

    @discord.ui.button(label='Night', style=discord.ButtonStyle.gray)
    async def night(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction, button.view.id):
            return
        database = DATABASES.get(interaction.user.display_name)
        if not database.linked_objects:
            button.label = 'No categories or players linked to this game yet! Run /link_to_game'
            await interaction.response.edit_message(view=self)
            time.sleep(1)
            button.label = 'Night'
            await interaction.followup.edit_message(interaction.message.id, view=self)
            return
        button.label = 'Moving players...'
        await interaction.response.edit_message(view=self)
        guild = interaction.guild
        town_square_channel = guild.get_channel(database.town_square[1])
        night_channels = [guild.get_channel(channel_data[1]) for channel_data in database.night_category["children"]]
        for member in town_square_channel.members:
            if member.display_name == database.owner:
                continue
            await member.move_to(night_channels.pop(0))

        button.label = 'Night'
        await interaction.followup.edit_message(interaction.message.id, view=self)

    @discord.ui.button(label='Cancel timer', style=discord.ButtonStyle.red)
    async def cancel_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        button_view = button.view
        if not is_owner(interaction, button_view.id):
            return
        user = interaction.user
        database: Database = DATABASES.get(user.display_name)
        timer: Timer = database.timer
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
        user = interaction.user
        guild = interaction.guild
        database = DATABASES.get(user.display_name)
        storyteller_role = guild.get_role(database.storyteller_role_id)
        try:
            logger.info(f'Attempting to remove storyteller role from {user.display_name}')
            await user.remove_roles(storyteller_role)
            logger.info(f'Successfully removed storyteller role from {user.display_name}')
        except discord.errors.Forbidden:
            logger.error(f'Could not remove storyteller role from {user.display_name} because user probably has higher privileges')
        button_view.clear_items()
        DATABASES.pop(user.display_name)
        await interaction.response.edit_message(content='Game ended', view=self, delete_after=10)

    @discord.ui.select(min_values=1, max_values=1, options=[discord.SelectOption(label=f'{i*0.5} minutes') for i in range(4,27)], placeholder='Select time players have until vote')
    async def timer(self, interaction: discord.Interaction, select: discord.ui.Select):
        select_view: discord.ui.View = select.view
        if not is_owner(interaction, select_view.id):
            return
        user = interaction.user
        selected_value = select.values[0]
        logger.info(f"{user.display_name} started a timer of {selected_value} minutes")
        time_to_sleep = float(selected_value.replace(' minutes', '')) * 60
        logger.info(f"I got {time_to_sleep}:.2f seconds to sleep")
        database: Database = DATABASES.get(user.display_name)
        await interaction.response.send_message(f'Will return players to Town Square after {selected_value} minutes', ephemeral=True, delete_after=3)
        timer = Timer(time_to_sleep, database.game_chat_channel, interaction.guild.get_channel(database.day_category.get('id')), interaction.user, interaction.guild.get_channel(database.town_square[1]))
        database.timer = timer
        children = select_view.children
        for child in children:
            if isinstance(child, discord.ui.Select):
                child.placeholder = 'Select time players have until vote'
                await interaction.followup.edit_message(interaction.message.id, view=select_view)
        await timer.run()

class Database:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.filename = self.owner.strip(' ')
        self.path = DATABASE_DIR / f'{self.filename}.json'
        self.game_name = f"{self.owner}'s game"
        self.view_id = None
        self.linked_objects = False
        self.storyteller_role_id = None
        self.players: dict = {}
        self.day_category = {}
        self.night_category = {}
        self.town_square = []
        self.game_chat_channel = None
        self.timer = None

    def to_dict(self):
        return {
            "owner": self.owner,
            "game_name": self.game_name,
            "view_id": self.view_id,
            "players": self.players,
            "day_category": self.day_category,
            "night_category": self.night_category,
            "town_square": self.town_square
        }
    
    def save_to_file(self):
        with open(self.path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def find_town_square(self):
        for channel in self.day_category['children']:
            if channel[0].startswith("Town Square"):
                self.town_square = channel
                return
            
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
