import discord
from logger import logger
from utils import (
    load_token_from_file, 
    dict_to_str, 
    pick_random_channel_names, 
    get_storyteller_role, 
    check_if_user_has_story_teller_role,
    )
from global_vars import SCRIPT_DIR, DATABASES
from classes import MyClient, GameControls, Database

TOKEN_PATH = SCRIPT_DIR / 'token.txt'
TOKEN = load_token_from_file(TOKEN_PATH)

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

@client.tree.command()
async def game(interaction: discord.Interaction):
    """Gives storyteller buttons to manage the game with"""
    user = interaction.user
    game_owner = user.display_name
    if game_owner in DATABASES:
        await interaction.response.send_message(f'You already have a running game, first quit the other game', ephemeral=True, delete_after=5)
        return
    database = Database(game_owner)
    DATABASES[game_owner] = database
    view = GameControls(timeout=None)
    database.view_id = view.id
    guild = interaction.guild
    storyteller_role = get_storyteller_role(guild)

    if not storyteller_role:
        logger.warning(f"No Storryteller role found! Adding now...")
        storyteller_role = await guild.create_role(name='Storyteller')
    
    database.storyteller_role_id = storyteller_role.id
    user_has_story_teller_role = check_if_user_has_story_teller_role(interaction)

    if not user_has_story_teller_role:
        try:
            logger.info(f'Attempting to add storyteller role to {game_owner}')
            await user.add_roles(storyteller_role)
            logger.info(f'Successfully added storyteller role to {game_owner}')
        except discord.errors.Forbidden:
            logger.error(f'Could not add storyteller role to {game_owner} because of lacking permissions, add role manually')
            await interaction.response.send_message(f'Could not add Storyteller role to {game_owner}, probably because the user has a higher tier role. Please add manually and try again', ephemeral=True, delete_after=5)
            DATABASES.pop(game_owner)
            return
    await interaction.response.send_message(f"Game commands for {game_owner}'s game", view=view)

@client.tree.command()
async def link_to_game(interaction: discord.Interaction, channel_with_players: discord.VoiceChannel, day_category: discord.CategoryChannel, night_category: discord.CategoryChannel):
    """Links players in a channel to your game and link a day and night category to your game"""
    command_caller = interaction.user.display_name
    if command_caller not in DATABASES:
        await interaction.response.send_message(f"You do not have an active game, start one first with /game", ephemeral=True, delete_after=5)
        return
    database: Database = DATABASES.get(command_caller)
    member_count = len(channel_with_players.members)
    for member in channel_with_players.members:
        logger.info(f"Linking {member.display_name} to {command_caller}'s game")
        database.players[member.display_name] = member.id
    logger.info(f'Linked {member_count} players')

    logger.info(f'Linking "{day_category.name}" (day) to {database.game_name}')
    database.day_category = {"name": day_category.name, "id": day_category.id, "children": [(channel.name, channel.id) for channel in day_category.voice_channels]}

    logger.info(f'Linking "{night_category.name}" (night) to {database.game_name}')
    database.night_category = {"name": night_category.name, "id": night_category.id, "children": [(channel.name, channel.id) for channel in night_category.voice_channels]}

    logger.info('Finding and adding Town Square channel to database')
    database.find_town_square()
    logger.info(f'Got: {database.town_square[0]} as a result')

    database.linked_objects = True
    database.game_chat_channel = discord.utils.get(day_category.text_channels, name='game-chat')
    logger.info(f'Saving database to: {database.path}')
    database.save_to_file()

    await interaction.response.send_message(f'Linked {member_count} players, "{day_category.name}" category as day and "{night_category.name}" category as night to your game', ephemeral=True, delete_after=5)

@client.tree.command()
async def create_game_channels(interaction: discord.Interaction, amount_of_players: int):
    """Creates channels for a new game"""
    command_caller = interaction.user.display_name
    logger.info(f'{command_caller} called create channels')

    night_category_name = f"{command_caller}'s Night"
    random_night_channel_names = pick_random_channel_names(amount_of_players)
    logger.debug(f'Picked the following random night channel names:\n{random_night_channel_names}')

    day_category_name = f"{command_caller}'s Game"
    random_day_channel_names = pick_random_channel_names(10)
    logger.debug(f'Picked the following random day channel names:\n{random_day_channel_names}')

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
    await interaction.response.send_message(response_message, ephemeral=True, delete_after=10)

    guild = interaction.guild
    day_category = await guild.create_category(day_category_name)
    logger.info(f"Created {day_category_name} on {guild.name} for {command_caller}'s game")

    for channel_name in random_day_channel_names:
        await day_category.create_voice_channel(channel_name)
        logger.info(f"Created {channel_name} in {day_category_name}")
    await day_category.create_text_channel('game-chat')
    logger.info(f'Created "game-chat" in {day_category_name}')


    overwrites = {
    guild.default_role: discord.PermissionOverwrite(view_channel=False),
    discord.utils.get(guild.roles, name='Storyteller'): discord.PermissionOverwrite(view_channel=True, manage_channels=True),
    discord.utils.get(guild.roles, name='BotC-bot'): discord.PermissionOverwrite(view_channel=True, manage_channels=True),
    discord.utils.get(guild.roles, name='Admin'): discord.PermissionOverwrite(view_channel=True, manage_channels=True)
    }

    night_category = await guild.create_category(night_category_name, overwrites=overwrites)
    logger.info(f"Created {night_category_name} on {guild.name} for {command_caller}'s game")

    for channel_name in random_night_channel_names:
        await night_category.create_voice_channel(channel_name, overwrites=overwrites)
        logger.info(f"Created {channel_name} in {night_category_name}")

@client.tree.command()
async def delete_game_channels(interaction: discord.Interaction, day_category: discord.CategoryChannel, night_category: discord.CategoryChannel):
    """Deletes game channels from a closed game"""
    await interaction.response.send_message(f"Deleting all channels in {day_category.name} and {night_category.name}...", ephemeral=True, delete_after=10)
    for category in [day_category, night_category]:
        for channel in category.channels:
            logger.info(f'Deleting {channel.name} from {category.name}')
            await channel.delete()
        logger.info(f"Deleting {category.name}")
        await category.delete()

@client.tree.command()
async def clear_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Clears all messages from the channel"""
    await interaction.response.send_message(f"Purging {channel.name}...", ephemeral=True, delete_after=10)
    logger.info(f'Clearing {channel.name} of messages')
    await channel.purge()

client.run(TOKEN)
