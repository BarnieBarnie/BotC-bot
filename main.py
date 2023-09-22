import discord
from logger import logger
from utils import (
    load_token_from_file, 
    dict_to_str, 
    pick_random_channel_names, 
    get_storyteller_role, 
    check_if_user_has_story_teller_role,
    response,
    )
from global_vars import SCRIPT_DIR, DOCUMENTATION_STRINGS
from classes import MyClient, GameControls
from database import Database
from discord import app_commands

TOKEN_PATH = SCRIPT_DIR / 'token.txt'
TOKEN = load_token_from_file(TOKEN_PATH)

intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id}), connected to {len(client.guilds)} guilds')
    logger.info('------')
    for guild in client.guilds:
        logger.info(f'Setting up Database for {guild.name}')
        database = Database(guild)
        database.get_dict_from_guild()
        guild_name = guild.name
        logger.info(f"Copying commands to {guild_name}[{guild.id}]")
        client.tree.copy_global_to(guild=guild)
        await client.tree.sync(guild=guild)

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    database = Database(member.guild)
    try:
        if member.display_name in database.linked_players:
            spectators = database.linked_players[member.display_name]
            for spectator_name in spectators:
                for member in before.channel.members:
                    if member.display_name == spectator_name:
                        logger.info(f"{spectator_name} was in same channel as {member.display_name} moving {spectator_name} to {after.channel.name}")
                        await member.move_to(after.channel)
                        return
                logger.info(f"{spectator_name} was not in same channel as {member.display_name} moving {spectator_name} to {after.channel.name}")
                slave = member.guild.get_member_named(spectator_name)
                await slave.move_to(after.channel)
    except AttributeError:
        logger.error(f'Got error while trying to move {spectator_name} to {member.display_name} because {member.display_name} most likely left all voice channels or just joined again')


@client.tree.command()
async def spectate(interaction: discord.Interaction, user_to_spectate: discord.Member):
    """Link yourself to another member, when they move channels you move with them"""
    database = Database(interaction.guild)
    user = interaction.user
    user_to_spectate_name = user_to_spectate.display_name
    logger.info(f"{user.display_name} called /spectate {user_to_spectate_name}")

    if user.display_name in database.linked_players and user_to_spectate_name in database.linked_players[user.display_name]:
        logger.error(f'Infinite spectate loop detected, {user_to_spectate_name} is spectating {user.display_name} so {user.display_name} cannot spectate {user_to_spectate_name} aswell')
        await response(interaction, f'{user_to_spectate_name} is spectating you, you cannot spectate eachother at the same time, ask {user_to_spectate_name} to call /stop_spectate')
        return

    for spectated, spectators in database.linked_players.items():
        for spectator in spectators:
            if spectator == user.display_name:
                logger.warning(f"{user.display_name} is already spectating {spectated}")
                await response(interaction, f'You are already spectating {spectated}! First unlink from {spectated}!')
                return
            
    if user_to_spectate_name in database.linked_players:
        database.linked_players[user_to_spectate_name].append(user.display_name)
        database.save()
        await response(interaction, f'You are now spectating {user_to_spectate_name}, you will follow them around until you run /stop_spectate')
        return

    database.linked_players[user_to_spectate_name] = [user.display_name]
    database.save()
    logger.info(f'{user.display_name} is now spectating {user_to_spectate_name}')
    await response(interaction, f'You are now spectating {user_to_spectate_name}, you will follow them around until you run /stop_spectate')

@client.tree.command()
async def stop_spectate(interaction: discord.Interaction):
    """Unlink yourself from other members, you no longer move where they move"""
    database = Database(interaction.guild)
    user_display_name = interaction.user.display_name
    logger.info(f'{user_display_name} called /stop_spectate')
    found = False
    for spectated, spectators in database.linked_players.items():
        for spectator in spectators:
            if spectator == user_display_name:
                spectators.pop(spectators.index(user_display_name))
                found = True
                database.save()
                await response(interaction, f'You are no longer spectating {spectated}')
                logger.info(f'Unlinked {user_display_name} from {spectated}')
    if not found:
        await response(interaction, f'You are not spectating anyone!')
        logger.warning(f'{user_display_name} was not spectating anyone')

@client.tree.command()
async def game(interaction: discord.Interaction, day_category: discord.CategoryChannel, night_category: discord.CategoryChannel, town_square_channel: discord.VoiceChannel):
    """Gives storyteller buttons to manage the game with"""
    guild = interaction.guild
    database = Database(guild)
    user = interaction.user
    game_owner = user.display_name
    logger.info(f'{game_owner} called /game "{day_category.name}" "{night_category.name}" "{town_square_channel.name}"')
    if game_owner in database.games:
        await response(interaction, f'You already have a running game, first quit the other game')
        logger.warning(f'{game_owner} already has a running game')
        return
    
    view = GameControls(timeout=None)
    game_chat_channel = discord.utils.get(day_category.text_channels, name='game-chat')
    database.games[game_owner] = {
        "view_id": view.id, 
        "day_category": [day_category.id, day_category.name], 
        "night_category": [night_category.id, night_category.name], 
        "game_chat_channel": [game_chat_channel.id, game_chat_channel.name],
        "town_square_channel": [town_square_channel.id, town_square_channel.name]
        }
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
            await response(interaction, f'Could not add Storyteller role to {game_owner}, probably because the user has a higher tier role. Please add manually and try again')
            database.games.pop(game_owner)
            return
        
    database.save()
    await interaction.response.send_message(f"Game commands for {game_owner}'s game", view=view)

@client.tree.command()
async def stop_game(interaction: discord.Interaction):
    """Stop game if you have any game running, only use this if game controls no longer work"""
    database = Database(interaction.guild)
    game_owner = interaction.user
    game_owner_name = game_owner.display_name
    logger.info(f'{game_owner_name} called /stop_game')

    if game_owner_name in database.games:
        database.games.pop(game_owner_name)
        await response(interaction, f'Ended your game, you can now start a new game')
        database.save()
        return
    
    await response(interaction, f'No game found for {game_owner_name}, you can freely start a new game')

@client.tree.command()
async def create_game_channels(interaction: discord.Interaction, amount_of_players: int):
    """Creates channels for a new game"""
    command_caller = interaction.user.display_name
    logger.info(f'{command_caller} called /create_game_channels {amount_of_players}')

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
    await response(interaction, response_message)

    guild = interaction.guild

    overwrites = {discord.utils.get(guild.roles, name='BotC-bot'): discord.PermissionOverwrite(view_channel=True, manage_channels=True)}

    day_category = await guild.create_category(day_category_name, overwrites=overwrites)
    logger.info(f"Created {day_category_name} on {guild.name} for {command_caller}'s game")

    for channel_name in random_day_channel_names:
        await day_category.create_voice_channel(channel_name, overwrites=overwrites)
        logger.info(f"Created {channel_name} in {day_category_name}")
    await day_category.create_text_channel('game-chat', overwrites=overwrites)
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
    day_category_overwrites = day_category.overwrites
    night_category_overwrites = night_category.overwrites
    logger.info(f'{interaction.user.display_name} called /delete_game_channels "{day_category.name}" "{night_category.name}"')

    allowed_to_delete_day = False
    for role in day_category_overwrites:
        if role.name == 'BotC-bot':
            allowed_to_delete_day = True
            break

    if not allowed_to_delete_day:
        await response(interaction, f'The category {day_category.name} was not made by this bot, will not delete anything.')
        logger.warning(f'The category {day_category.name} was not made by this bot, will not delete anything')
        return
    
    allowed_to_delete_night = False
    for role in night_category_overwrites:
        if role.name == 'BotC-bot':
            allowed_to_delete_night = True
            break

    if not allowed_to_delete_night:
        await response(interaction, f'The category {night_category.name} was not made by this bot, will not delete anything.')
        logger.warning(f'The category {night_category.name} was not made by this bot, will not delete anything')
        return
    
    await response(interaction, f"Deleting all channels in {day_category.name} and {night_category.name}...")
    logger.info(f"Deleting all channels in {day_category.name} and {night_category.name}...")
    for category in [day_category, night_category]:
        for channel in category.channels:
            logger.info(f'Deleting {channel.name} from {category.name}')
            await channel.delete()
        logger.info(f"Deleting {category.name}")
        await category.delete()

@client.tree.command()
async def clear_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Clears all messages from the channel"""
    channel_overwrites = channel.overwrites
    allowed_to_clear_channel = False
    logger.info(f'{interaction.user.display_name} called /clean_channel "{channel.name}"')

    for role in channel_overwrites:
        if role.name == 'BotC-bot':
            allowed_to_clear_channel = True
            break

    if not allowed_to_clear_channel:
        await response(interaction, f'Channel {channel.name} was not created by this bot, will not clear this channel')
        logger.warning(f'Channel {channel.name} was not created by this bot, will not clear this channel')
        return

    await response(interaction, f"Purging {channel.name}...")
    logger.info(f'Clearing {channel.name} of messages')
    await channel.purge()

@client.tree.command()
async def st(interaction: discord.Interaction):
    """Gives you the Storyteller role or removes it if you already have it"""
    user = interaction.user
    logger.info(f'{user.display_name} called /st')
    guild = interaction.guild
    database = Database(guild)
    storyteller_role_id = database.storyteller_role_id
    if storyteller_role_id:
        storyteller_role = guild.get_role(storyteller_role_id)
    else:
        storyteller_role = get_storyteller_role(guild)
    user_has_story_teller_role = check_if_user_has_story_teller_role(interaction)
    if user_has_story_teller_role:
        await response(interaction, "You already had the Storyteller role, removing role now")
        try:
            logger.info(f'User {user.display_name} already has the Storryteller role, removing it now')
            await user.remove_roles(storyteller_role)
            logger.info(f'Successfully removed storyteller role from {user.display_name}')
        except discord.Forbidden:
            await response(interaction, 'Bot is not allowed to remove Storyteller role from you, ask a moderator')
            logger.error(f'Could not remove Storyteller role from {user.display_name} due to lack of authorization')
        return
    try:
        logger.info(f'Giving Storyteller role to {user.display_name}')
        await user.add_roles(storyteller_role)
        logger.info(f'Successfully added Storyteller role to {user.display_name}')
        await response(interaction, 'Successfully gave you Storyteller role')
    except discord.Forbidden:
        await response(interaction, 'Bot is not allowed to give you Storyteller role, ask a moderator')
        logger.error(f'Could not add Storyteller role to {user.display_name} due to lack of authorization')

@client.tree.command()
async def help(interaction: discord.Interaction, page: app_commands.Range[int, 1, 2]):
    """Lists all commands with explanation about what they do, page 1 or 2"""
    logger.info(f'{interaction.user.display_name} called /help {page}')
    index = page -1
    await interaction.response.send_message(DOCUMENTATION_STRINGS[index], ephemeral=True, delete_after=180)


client.run(TOKEN)
