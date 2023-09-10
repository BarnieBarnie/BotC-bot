import discord
from discord import app_commands
from logger import logger
from utils import load_token_from_file
from pathlib import Path
import time
from database import Database

SCRIPT_DIR = Path(__file__).parent
TOKEN_PATH = SCRIPT_DIR / 'token.txt'
TOKEN = load_token_from_file(TOKEN_PATH)
databases = {}

def is_owner(interaction: discord.Interaction, view_id: int) -> bool:
    user_that_clicked = interaction.user.display_name
    database = databases.get(user_that_clicked)
    if database:
        user_is_owner = True if view_id == database.view_id else False
        if user_is_owner:
            return True
        logger.warning(f"{user_that_clicked} clicked on button it has no rights to!")
    return False

class GameControls(discord.ui.View):

    @discord.ui.button(label='Day', style=discord.ButtonStyle.success)
    async def day(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction, button.view.id):
            return
        database = databases.get(interaction.user.display_name)
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
        database = databases.get(interaction.user.display_name)
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

    @discord.ui.button(label='Quit game', style=discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        button_view = button.view
        if not is_owner(interaction, button_view.id):
            return
        button_view.clear_items()
        databases.pop(interaction.user.display_name)
        await interaction.response.edit_message(content='Game ended', view=self)
        

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id}), connected to {len(client.guilds)} guilds')
    logger.info('------')
    for guild in client.guilds:
        guild_name = guild.name
        logger.info(f"Copying commands to {guild_name}[{guild.id}]")
        client.tree.copy_global_to(guild=guild)
        await client.tree.sync(guild=guild)

        for channel in guild.channels:
            channel_type = channel.type.name
            if channel_type == 'voice':
                user_limit = channel.user_limit
                members_names = [member.name for member in channel.members]
                members_names_string = ', '.join(members_names)
            else:
                user_limit = '-'
                members_names_string = '-'

            channel_category = channel.category
            channel_category_name = channel_category.name if channel_category else '-'
                
            logger.debug(f'[{guild_name}], name: {channel.name}, category: {channel_category_name}, id: {channel.id}, members: [{members_names_string}], type: {channel.type}, user_limit: {user_limit}')
        logger.debug('--------------------------------')

@client.tree.command()
async def game(interaction: discord.Interaction):
    """Gives storyteller buttons to manage the game with"""
    game_owner = interaction.user.display_name
    if game_owner in databases:
        await interaction.response.send_message(f'You already have a running game, first quit the other game')
        return
    database = Database(game_owner)
    databases[game_owner] = database
    view = GameControls()
    database.view_id = view.id
    await interaction.response.send_message(f"Game commands for {game_owner}'s game", view=view)

@client.tree.command()
async def link_to_game(interaction: discord.Interaction, channel_with_players: discord.VoiceChannel, day_category: discord.CategoryChannel, night_category: discord.CategoryChannel):
    """Links players in a channel to your game and link a day and night category to your game"""
    command_caller = interaction.user.display_name
    if command_caller not in databases:
        await interaction.response.send_message(f"You do not have an active game, start one first with /game")
        return
    database = databases.get(command_caller)
    member_count = len(channel_with_players.members)
    for member in channel_with_players.members:
        logger.info(f"Linking {member.display_name} to {command_caller}'s game")
        database.players[member.display_name] = member.id
    logger.info(f'Linked {member_count} players')

    logger.info(f'Linking "{day_category.name}" (day) to {database.game_name}')
    database.day_category = {"name": day_category.name, "id": day_category.id, "children": [(channel.name, channel.id) for channel in day_category.voice_channels]}

    logger.info(f'Linking "{night_category.name}" (night) to {database.game_name}')
    database.night_category = {"name": night_category.name, "id": night_category.id, "children": [(channel.name, channel.id) for channel in night_category.voice_channels]}
    database.find_town_square()
    database.linked_objects = True
    database.save_to_file()
    await interaction.response.send_message(f'Linked {member_count} players, "{day_category.name}" category as day and "{night_category.name}" category as night to your game')


client.run(TOKEN)
