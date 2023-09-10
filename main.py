import discord
from discord import app_commands
from logger import logger
from utils import load_token_from_file
import time
from database import Database
from global_vars import SCRIPT_DIR, ROOMS, ROOMS_COUNT
import random
import asyncio

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

def pick_random_channel_names(amount_of_rooms: int) -> list[str]:
    rooms_count = ROOMS_COUNT
    local_rooms_copy = ROOMS[:]
    random_rooms = []

    for _ in range(amount_of_rooms):
        random_index = random.choice(range(rooms_count))
        random_rooms.append(local_rooms_copy.pop(random_index))
        rooms_count -= 1
    
    return random_rooms

def dict_to_str(dict: dict) -> str:
    string = ''
    for key,values in dict.items():
        string += f'- {key}\n'
        for value in values:
            string += f'  - {value}\n'
    return string

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

    @discord.ui.button(label='Cancel timer', style=discord.ButtonStyle.red)
    async def cancel_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        button_view = button.view
        if not is_owner(interaction, button_view.id):
            return
        user = interaction.user
        database: Database = databases.get(user.display_name)
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
        database = databases.get(user.display_name)
        storyteller_role = guild.get_role(database.storyteller_role_id)
        await user.remove_roles(storyteller_role)
        button_view.clear_items()
        databases.pop(user.display_name)
        await interaction.response.edit_message(content='Game ended', view=self)

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
        database: Database = databases.get(user.display_name)
        await interaction.response.send_message(f'Will return players to Town Square after {selected_value} minutes', ephemeral=True, delete_after=3)
        timer = Timer(time_to_sleep, database.game_chat_channel, interaction.guild.get_channel(database.day_category.get('id')), interaction.user, interaction.guild.get_channel(database.town_square[1]))
        database.timer = timer
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
    user = interaction.user
    game_owner = user.display_name
    if game_owner in databases:
        await interaction.response.send_message(f'You already have a running game, first quit the other game')
        return
    database = Database(game_owner)
    databases[game_owner] = database
    view = GameControls()
    database.view_id = view.id
    guild = interaction.guild
    roles = guild.roles
    storyteller_role = None
    for role in roles:
        if role.name == 'Storyteller':
            storyteller_role = role
    if not storyteller_role:
        logger.warning(f"No Storryteller role found! Adding now...")
        storyteller_role = await guild.create_role(name='Storyteller')
    database.storyteller_role_id = storyteller_role.id
    user_has_story_teller_role = False
    for role in user.roles:
        if role.name == 'Storyteller':
            user_has_story_teller_role = True
            break
    if not user_has_story_teller_role:
        await user.add_roles(storyteller_role)
    await interaction.response.send_message(f"Game commands for {game_owner}'s game", view=view)

@client.tree.command()
async def link_to_game(interaction: discord.Interaction, channel_with_players: discord.VoiceChannel, day_category: discord.CategoryChannel, night_category: discord.CategoryChannel):
    """Links players in a channel to your game and link a day and night category to your game"""
    command_caller = interaction.user.display_name
    if command_caller not in databases:
        await interaction.response.send_message(f"You do not have an active game, start one first with /game", ephemeral=True, delete_after=5)
        return
    database: Database = databases.get(command_caller)
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
    database.game_chat_channel = discord.utils.get(day_category.text_channels, name='game-chat')
    database.save_to_file()
    await interaction.response.send_message(f'Linked {member_count} players, "{day_category.name}" category as day and "{night_category.name}" category as night to your game', ephemeral=True, delete_after=5)

@client.tree.command()
async def create_game_channels(interaction: discord.Interaction, amount_of_players: int):
    """Creates channels for a new game"""
    command_caller = interaction.user.display_name
    logger.info(f'{command_caller} called create channels')
    random_night_channel_names = pick_random_channel_names(amount_of_players)
    logger.debug(f'Picked the following random night channel names:\n{random_night_channel_names}')
    random_day_channel_names = pick_random_channel_names(10)
    logger.debug(f'Picked the following random day channel names:\n{random_day_channel_names}')
    day_category_name = f"{command_caller}'s Game"
    night_category_name = f"{command_caller}'s Night"
    town_square_name = f"Town Square ({command_caller}'s game)"
    random_day_channel_names.append(town_square_name)

    channels_to_be_created = {
        day_category_name: random_day_channel_names,
        night_category_name: random_night_channel_names

    }

    response_message = f"""These channels will be created:
{dict_to_str(channels_to_be_created)}
"""
    logger.debug(response_message)

    await interaction.response.send_message(response_message, ephemeral=True, delete_after=5)

    guild = interaction.guild
    day_category = await guild.create_category(day_category_name)
    logger.info(f"Created {day_category_name} on {guild.name} for {command_caller}'s game")

    for channel_name in random_day_channel_names:
        await day_category.create_voice_channel(channel_name)
        logger.debug(f"Created {channel_name} in {day_category_name}")
    await day_category.create_text_channel('game-chat')
    logger.debug(f'Created "game-chat" in {day_category_name}')

    overwrites = {
    guild.default_role: discord.PermissionOverwrite(view_channel=False),
    discord.utils.get(guild.roles, name='Storyteller'): discord.PermissionOverwrite(view_channel=True, manage_channels=True),
    discord.utils.get(guild.roles, name='BotC-bot'): discord.PermissionOverwrite(view_channel=True, manage_channels=True),
    discord.utils.get(guild.roles, name='Admin'): discord.PermissionOverwrite(view_channel=True, manage_channels=True)
    }


    night_category = await guild.create_category(night_category_name)
    logger.info(f"Created {night_category_name} on {guild.name} for {command_caller}'s game")

    for channel_name in random_night_channel_names:
        await night_category.create_voice_channel(channel_name, overwrites=overwrites)
        logger.debug(f"Created {channel_name} in {night_category_name}")

@client.tree.command()
async def delete_game_channels(interaction: discord.Interaction, day_category: discord.CategoryChannel, night_category: discord.CategoryChannel):
    """Deletes game channels from a closed game"""
    await interaction.response.send_message(f"Deleting all channels in {day_category.name} and {night_category.name}...", ephemeral=True, delete_after=5)
    for category in [day_category, night_category]:
        for channel in category.channels:
            logger.debug(f'Deleting {channel.name} from {category.name}')
            await channel.delete()
        logger.info(f"Deleting {category.name}")
        await category.delete()

@client.tree.command()
async def clear_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Clears all messages from the channel"""
    await interaction.response.send_message(f"Purging {channel.name}...", ephemeral=True, delete_after=5)
    logger.info(f'Clearing {channel.name} of messages')
    await channel.purge()

client.run(TOKEN)
