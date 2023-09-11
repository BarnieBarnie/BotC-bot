from pathlib import Path
from logger import logger
import discord
from global_vars import DATABASES, ROOMS_COUNT, ROOMS
import random

def load_token_from_file(file: Path) -> str:
    if not file.exists():
        logger.critical(f'{file} does not exist, either wrong path was specified or no token file exists')
        exit(1)
    logger.debug(f'Loading token from {file}')
    token = file.read_text()
    if token:
        logger.debug(f'Succesfully loaded token from {file}')
        return token
    logger.critical(f'Token file {file} seems to be empty, please add the token to the file')
    exit(1)

def is_owner(interaction: discord.Interaction, view_id: int) -> bool:
    user_that_clicked = interaction.user.display_name
    database = DATABASES.get(user_that_clicked)
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

def get_storyteller_role(interaction: discord.Interaction) -> discord.Role:
    guild = interaction.guild
    roles = guild.roles
    storyteller_role = None
    for role in roles:
        if role.name == 'Storyteller':
            storyteller_role = role
    return storyteller_role

def check_if_user_has_story_teller_role(interaction: discord.Interaction) -> bool:
    user_has_story_teller_role = False
    for role in interaction.user.roles:
        if role.name == 'Storyteller':
            user_has_story_teller_role = True
            break
    return user_has_story_teller_role