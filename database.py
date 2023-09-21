from global_vars import DATABASE_DIR
import discord
import json

class Database:
    def __init__(self, guild: discord.Guild) -> None:
        self.guild = guild
        self.guild_name = guild.name
        self.path = DATABASE_DIR / f'{self.guild_name}_{self.guild.id}.json'
        self.storyteller_role_id = None
        self.timers = {}

        if self.path.exists():
            with open(self.path, 'r') as f:
                self.dict = json.load(f)
                self.storyteller_role_id = self.dict["storyteller_role_id"]
        else:
            self.get_dict_from_guild()

        self.games = self.dict.get('games')
        self.linked_players = self.dict.get('linked_players')

    def save(self):
        self.dict["games"] = self.games
        self.dict["linked_players"] = self.linked_players
        self.dict["storyteller_role_id"] = self.storyteller_role_id 
        with open(self.path, 'w') as f:
            json.dump(self.dict, f, indent=2)

    def get_dict_from_guild(self) -> None:
        self.dict = {
            "guild": {
                "name": self.guild_name,
                "id": self.guild.id,
                "categories": {
                    category.name: {
                        "id": category.id, 
                        "children": {
                            channel.name: {
                                "type": channel.type.name, 
                                "id": channel.id
                                } for channel in category.channels
                                }} for category in self.guild.categories},
                "roles": {
                    role.name: {
                        "id": role.id,
                        "assignable": role.is_assignable(),
                        "bot_managed": role.is_bot_managed(),
                        "is_default": role.is_default(),
                        "permissions": {key: value for key, value in role.permissions.__iter__()}
                    } for role in self.guild.roles
                }
            },
            "games": {},
            "linked_players": {},
            "storyteller_role_id": None
        }
        self.save()
