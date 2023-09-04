import discord

async def check_member_for_story_teller_role(member: discord.Member):
    """
    Check if a member has the "Storyteller" role.
    """
    for role in member.roles:
        if role.name == 'Storyteller':
            return True
    return False